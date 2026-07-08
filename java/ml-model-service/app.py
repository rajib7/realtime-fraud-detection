"""FraudOps ML Model Service.

Standalone FastAPI service exposing the fraud detection model as an HTTP API.
The three Java microservices treat it as a black box — they POST features,
get back an explainable score. This lets the model be versioned, canaried
and scaled independently of the message-driven services.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest

app = FastAPI(title="FraudOps ML Model API", version="1.0.0")

HIGH_RISK_MERCHANTS = {"crypto_exchange", "gift_cards", "wire_transfer", "gambling"}


class ScoreRequest(BaseModel):
    amount: float = Field(..., gt=0)
    merchant_category: str
    hour: int = 12
    is_foreign: bool = False
    cross_border: bool = False
    velocity_1h: float = 0.0
    distinct_countries_24h: int = 1


def _synth_normal(n: int, rng: np.random.Generator) -> np.ndarray:
    amount   = np.abs(rng.normal(45.0, 30.0, n))
    hour     = rng.integers(6, 22, n).astype(float)
    is_foreign        = (rng.random(n) < 0.05).astype(float)
    is_high_risk_m    = (rng.random(n) < 0.02).astype(float)
    velocity_1h       = np.clip(rng.normal(1.5, 0.9, n), 0, None)
    cross_border      = (rng.random(n) < 0.03).astype(float)
    distinct_countries= np.clip(rng.normal(1.0, 0.3, n), 1, None)
    return np.stack([amount, hour, is_foreign, is_high_risk_m,
                     velocity_1h, cross_border, distinct_countries], axis=1)


class Model:
    def __init__(self) -> None:
        rng = np.random.default_rng(seed=42)
        X = _synth_normal(5000, rng)
        self.iforest = IsolationForest(n_estimators=120, contamination=0.03, random_state=42)
        self.iforest.fit(X)
        raw = -self.iforest.score_samples(X)
        self.lo, self.hi = float(raw.min()), float(raw.max())
        self.trained_at = time.time()

    def _ml(self, feats: np.ndarray) -> float:
        raw = -self.iforest.score_samples(feats.reshape(1, -1))[0]
        span = self.hi - self.lo or 1e-9
        return float(np.clip((raw - self.lo) / span, 0.0, 1.0))

    @staticmethod
    def _rule(req: ScoreRequest) -> Tuple[float, List[str]]:
        r: List[str] = []
        s = 0.0
        if req.amount >= 2500:
            s += 0.45; r.append("high_amount")
        elif req.amount >= 1000:
            s += 0.20; r.append("elevated_amount")
        if req.is_foreign:
            s += 0.15; r.append("foreign_transaction")
        if req.merchant_category in HIGH_RISK_MERCHANTS:
            s += 0.35; r.append(f"high_risk_merchant:{req.merchant_category}")
        if req.velocity_1h >= 6:
            s += 0.25; r.append("high_velocity")
        if req.cross_border:
            s += 0.20; r.append("cross_border")
        if req.distinct_countries_24h >= 3:
            s += 0.20; r.append("country_hopping")
        if req.hour < 5 or req.hour >= 23:
            s += 0.08; r.append("odd_hour")
        return min(s, 1.0), r

    def score(self, req: ScoreRequest) -> Dict[str, Any]:
        feats = np.array([
            req.amount, req.hour,
            1.0 if req.is_foreign else 0.0,
            1.0 if req.merchant_category in HIGH_RISK_MERCHANTS else 0.0,
            req.velocity_1h,
            1.0 if req.cross_border else 0.0,
            float(req.distinct_countries_24h),
        ])
        t0 = time.perf_counter()
        ml = self._ml(feats)
        rule, reasons = self._rule(req)
        fused = round(0.6 * ml + 0.4 * rule, 4)
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)

        if fused >= 0.75:
            risk, decision = "fraud", "block"
        elif fused >= 0.5:
            risk, decision = "suspicious", "review"
        else:
            risk, decision = "safe", "approve"

        return {
            "ml_score": round(ml, 4),
            "rule_score": round(rule, 4),
            "fraud_score": fused,
            "risk_level": risk,
            "decision": decision,
            "reasons": reasons or ["nominal_pattern"],
            "scoring_latency_ms": latency_ms,
            "model_version": "isolation-forest-v1.0",
        }


model = Model()


@app.get("/health")
async def health():
    return {"status": "UP", "model": "isolation-forest-v1.0"}


@app.post("/score")
async def score(req: ScoreRequest):
    return model.score(req)


@app.get("/model/info")
async def info():
    return {
        "name": "isolation-forest-v1.0",
        "algorithm": "IsolationForest + rule engine (fused)",
        "features": [
            "amount", "hour", "is_foreign", "is_high_risk_merchant",
            "velocity_1h", "cross_border", "distinct_countries_24h",
        ],
        "weights": {"ml": 0.6, "rules": 0.4},
        "thresholds": {"suspicious": 0.5, "fraud": 0.75},
    }
