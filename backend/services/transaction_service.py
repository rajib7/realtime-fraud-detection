"""Transaction microservice.

Java equivalent: @RestController POST /transactions -> kafkaTemplate.send("transactions.raw", tx)
Here: /api/tx/transactions publishes to the in-process event bus.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from .auth import get_current_user
from .event_bus import TOPIC_TX_RAW, bus
from .store import transactions_store


router = APIRouter(prefix="/tx", tags=["transaction-service"])

_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db = _client[os.environ["DB_NAME"]]


class TransactionIn(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    merchant: str
    merchant_category: str
    country: str = "US"
    hour: Optional[int] = None
    velocity_1h: float = 0
    distinct_countries_24h: int = 1
    is_foreign: Optional[bool] = None
    cross_border: Optional[bool] = None


async def publish_transaction(tx: Dict[str, Any]) -> Dict[str, Any]:
    tx.setdefault("tx_id", f"tx_{uuid.uuid4().hex[:12]}")
    tx.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    if tx.get("hour") is None:
        tx["hour"] = datetime.now(timezone.utc).hour
    if tx.get("is_foreign") is None:
        tx["is_foreign"] = tx.get("country", "US") != "US"
    if tx.get("cross_border") is None:
        tx["cross_border"] = tx["is_foreign"]

    transactions_store.add(tx)
    await _db.transactions.insert_one({**tx})
    await bus.publish(TOPIC_TX_RAW, tx)
    return tx


@router.post("/transactions")
async def create_transaction(
    payload: TransactionIn,
    _user=Depends(get_current_user),
) -> Dict[str, Any]:
    tx = payload.model_dump()
    return await publish_transaction(tx)


@router.get("/transactions/recent")
async def recent_transactions(limit: int = 50, _user=Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "total": transactions_store.total,
        "items": transactions_store.recent(limit),
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "service": "transaction-service",
        "status": "UP",
        "topic": TOPIC_TX_RAW,
        "published": bus.published_count.get(TOPIC_TX_RAW, 0),
    }
