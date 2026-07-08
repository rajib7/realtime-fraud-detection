"""Traffic simulator router - starts/stops the synthetic transaction stream."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .auth import ROLE_ADMIN, get_current_user, require_role
from .simulator import state
from .transaction_service import publish_transaction


router = APIRouter(prefix="/simulator", tags=["simulator"])


class SimulatorConfig(BaseModel):
    tps: float = Field(3.0, ge=0.1, le=25.0)
    fraud_bias: float = Field(0.08, ge=0.0, le=1.0)


async def _loop() -> None:
    while state.running:
        try:
            tx = state.build_tx()
            await publish_transaction(tx)
        except Exception:  # pragma: no cover - keep loop alive
            pass
        sleep_for = 1.0 / max(state.tps, 0.1)
        await asyncio.sleep(sleep_for)


def _ensure_task() -> None:
    if state._task is None or state._task.done():
        state._task = asyncio.create_task(_loop())


@router.post("/start")
async def start(
    config: SimulatorConfig | None = None,
    _user=Depends(require_role(ROLE_ADMIN)),
) -> Dict[str, Any]:
    if config:
        state.tps = config.tps
        state.fraud_bias = config.fraud_bias
    state.running = True
    _ensure_task()
    return state.status()


@router.post("/stop")
async def stop(_user=Depends(require_role(ROLE_ADMIN))) -> Dict[str, Any]:
    state.running = False
    if state._task:
        try:
            state._task.cancel()
        except Exception:
            pass
    return state.status()


@router.post("/config")
async def configure(
    config: SimulatorConfig,
    _user=Depends(require_role(ROLE_ADMIN)),
) -> Dict[str, Any]:
    state.tps = config.tps
    state.fraud_bias = config.fraud_bias
    return state.status()


@router.post("/inject-fraud")
async def inject_fraud(
    count: int = 1,
    _user=Depends(require_role(ROLE_ADMIN)),
) -> Dict[str, Any]:
    injected = []
    for _ in range(max(1, min(count, 20))):
        tx = state.build_tx(force_fraud=True)
        await publish_transaction(tx)
        injected.append(tx["tx_id"])
    return {"injected": injected}


@router.get("/status")
async def status(_user=Depends(get_current_user)) -> Dict[str, Any]:
    return state.status()
