from fastapi import APIRouter, Depends

from .auth import get_current_user
from .metrics import metrics
from .event_bus import bus

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def snapshot(_user=Depends(get_current_user)):
    snap = metrics.snapshot()
    snap["topics"] = {t: c for t, c in bus.published_count.items()}
    return snap
