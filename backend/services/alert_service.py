"""Alert microservice.

Consumes fraud.scores. If risk_level == fraud (or 'suspicious' with high score),
raises an alert to alerts.raised and stores it for the dashboard.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from .auth import ROLE_ADMIN, ROLE_ANALYST, get_current_user, require_role
from .event_bus import TOPIC_ALERTS, TOPIC_FRAUD_SCORES, bus
from .store import alerts_store


router = APIRouter(prefix="/alerts", tags=["alert-service"])

_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db = _client[os.environ["DB_NAME"]]


def _severity(score: float) -> str:
    if score >= 0.9:
        return "critical"
    if score >= 0.75:
        return "high"
    return "medium"


async def _on_score(evt: Dict[str, Any]) -> None:
    if evt["risk_level"] != "fraud":
        return
    alert = {
        "alert_id": f"al_{uuid.uuid4().hex[:12]}",
        "tx_id": evt["tx_id"],
        "user_id": evt["user_id"],
        "amount": evt["amount"],
        "merchant_category": evt["merchant_category"],
        "country": evt.get("country"),
        "fraud_score": evt["fraud_score"],
        "severity": _severity(evt["fraud_score"]),
        "reasons": evt["reasons"],
        "decision": evt["decision"],
        "raised_at": datetime.now(timezone.utc).isoformat(),
        "acknowledged": False,
    }
    alerts_store.add(alert)
    await _db.alerts.insert_one({**alert})
    await bus.publish(TOPIC_ALERTS, alert)


bus.subscribe(TOPIC_FRAUD_SCORES, _on_score)


async def rehydrate_alerts_store(limit: int = 200) -> int:
    """Load recent alerts from MongoDB into the in-memory store on cold start."""
    cursor = _db.alerts.find({}, {"_id": 0}).sort("raised_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    docs.reverse()  # so newest ends up on top after successive add() calls
    for doc in docs:
        alerts_store.add(doc)
    return len(docs)


@router.get("/recent")
async def recent_alerts(limit: int = 50, _user=Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "total": alerts_store.total,
        "items": alerts_store.recent(limit),
    }


@router.post("/{alert_id}/ack")
async def acknowledge(
    alert_id: str,
    _user=Depends(require_role(ROLE_ADMIN, ROLE_ANALYST)),
) -> Dict[str, Any]:
    for item in alerts_store.all():
        if item["alert_id"] == alert_id:
            item["acknowledged"] = True
            await _db.alerts.update_one(
                {"alert_id": alert_id}, {"$set": {"acknowledged": True}}
            )
            return {"ok": True, "alert_id": alert_id}
    # Fallback: not in memory but might be in Mongo (e.g., old alert).
    result = await _db.alerts.update_one(
        {"alert_id": alert_id}, {"$set": {"acknowledged": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"ok": True, "alert_id": alert_id}


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "service": "alert-service",
        "status": "UP",
        "consumes": TOPIC_FRAUD_SCORES,
        "produces": TOPIC_ALERTS,
        "raised": bus.published_count.get(TOPIC_ALERTS, 0),
    }
