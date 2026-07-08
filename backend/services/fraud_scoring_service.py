"""Fraud Scoring microservice.

Consumes transactions.raw, calls the ML model API, and publishes fraud.scores.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from .auth import get_current_user
from .event_bus import TOPIC_FRAUD_SCORES, TOPIC_TX_RAW, bus
from .ml_model import model
from .metrics import metrics
from .store import scores_store


router = APIRouter(prefix="/fraud", tags=["fraud-scoring-service"])

_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db = _client[os.environ["DB_NAME"]]


class ScoreRequest(BaseModel):
    amount: float
    merchant_category: str
    hour: int = 12
    is_foreign: bool = False
    cross_border: bool = False
    velocity_1h: float = 0
    distinct_countries_24h: int = 1


async def _on_transaction(tx: Dict[str, Any]) -> None:
    result = model.score(tx)
    event = {
        "tx_id": tx["tx_id"],
        "user_id": tx["user_id"],
        "amount": tx["amount"],
        "merchant_category": tx["merchant_category"],
        "country": tx.get("country"),
        "scored_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    scores_store.add(event)
    await _db.fraud_scores.insert_one({**event})
    metrics.record(
        latency_ms=result["scoring_latency_ms"],
        risk_level=result["risk_level"],
        is_alert=result["risk_level"] == "fraud",
    )
    await bus.publish(TOPIC_FRAUD_SCORES, event)


bus.subscribe(TOPIC_TX_RAW, _on_transaction)


@router.post("/score")
async def score(req: ScoreRequest, _user=Depends(get_current_user)) -> Dict[str, Any]:
    """Direct ML API - the assignment requires the model to be exposed via API."""
    return model.score(req.model_dump())


@router.get("/scores/recent")
async def recent_scores(limit: int = 50, _user=Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "total": scores_store.total,
        "items": scores_store.recent(limit),
    }


@router.get("/model/info")
async def model_info(_user=Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "name": "isolation-forest-v1.0",
        "algorithm": "IsolationForest + rule engine (fused)",
        "features": [
            "amount", "hour", "is_foreign", "is_high_risk_merchant",
            "velocity_1h", "cross_border", "distinct_countries_24h",
        ],
        "trained_samples": model.training_samples,
        "weights": {"ml": 0.6, "rules": 0.4},
        "thresholds": {"suspicious": 0.5, "fraud": 0.75},
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "service": "fraud-scoring-service",
        "status": "UP",
        "consumes": TOPIC_TX_RAW,
        "produces": TOPIC_FRAUD_SCORES,
        "scored": bus.published_count.get(TOPIC_FRAUD_SCORES, 0),
    }
