"""Traffic simulator - generates synthetic transactions and injects fraud patterns.

Mirrors what you'd run as a load-generator / k6 script against the Java service.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .ml_model import HIGH_RISK_MERCHANTS, NORMAL_MERCHANTS

USERS = [f"user_{i:04d}" for i in range(1, 61)]
COUNTRIES = ["US", "GB", "DE", "FR", "IN", "SG", "BR", "NG", "RU", "JP"]
HOME_COUNTRY = "US"


class SimulatorState:
    def __init__(self) -> None:
        self.running: bool = False
        self.tps: float = 3.0
        self.fraud_bias: float = 0.08  # probability of injecting a fraudy tx
        self._task: Optional[asyncio.Task] = None
        self.velocity: Dict[str, int] = {}
        self.countries_seen: Dict[str, set] = {}

    def build_tx(self, force_fraud: bool = False) -> Dict[str, Any]:
        user = random.choice(USERS)
        fraudy = force_fraud or random.random() < self.fraud_bias

        if fraudy:
            merchant = random.choice(list(HIGH_RISK_MERCHANTS))
            amount = round(random.uniform(900, 7500), 2)
            country = random.choice([c for c in COUNTRIES if c != HOME_COUNTRY])
            hour = random.choice([1, 2, 3, 4, 23])
            velocity_boost = random.randint(4, 9)
            distinct_bump = random.randint(2, 4)
        else:
            merchant = random.choice(NORMAL_MERCHANTS)
            amount = round(abs(random.gauss(48, 35)) + 3.0, 2)
            country = HOME_COUNTRY if random.random() > 0.06 else random.choice(COUNTRIES)
            hour = random.choice(list(range(7, 22)))
            velocity_boost = 0
            distinct_bump = 0

        current_v = self.velocity.get(user, 0) + 1 + velocity_boost
        self.velocity[user] = current_v
        seen = self.countries_seen.setdefault(user, set())
        seen.add(country)
        if distinct_bump:
            for extra in random.sample(COUNTRIES, k=min(distinct_bump, len(COUNTRIES))):
                seen.add(extra)

        return {
            "tx_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user,
            "amount": amount,
            "currency": "USD",
            "merchant": f"m_{random.randint(1000, 9999)}",
            "merchant_category": merchant,
            "country": country,
            "is_foreign": country != HOME_COUNTRY,
            "cross_border": country != HOME_COUNTRY,
            "hour": hour,
            "velocity_1h": current_v,
            "distinct_countries_24h": len(seen),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "tps": self.tps,
            "fraud_bias": self.fraud_bias,
        }


state = SimulatorState()
