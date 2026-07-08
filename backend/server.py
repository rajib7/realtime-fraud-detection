"""FastAPI orchestrator that hosts all fraud-detection microservices.

In production these would be independent Spring Boot services. Here they live
in the same process for demo simplicity, but are wired through an in-memory
event bus that mimics Kafka topic semantics.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from services.alert_service import rehydrate_alerts_store  # noqa: E402
from services.alert_service import router as alert_router  # noqa: E402
from services.auth import (  # noqa: E402
    ensure_indexes,
    get_db,
    seed_default_users,
)
from services.auth_router import router as auth_router  # noqa: E402
from services.download_router import router as download_router  # noqa: E402
from services.event_bus import bus  # noqa: E402
from services.fraud_scoring_service import router as fraud_router  # noqa: E402
from services.metrics_router import router as metrics_router  # noqa: E402
from services.simulator_router import router as simulator_router  # noqa: E402
from services.transaction_service import router as tx_router  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    await ensure_indexes(db)
    await seed_default_users(db)
    restored = await rehydrate_alerts_store()
    bus.start()
    logger.info(
        "startup complete | subscribers=%s | alerts_rehydrated=%d",
        list(bus._subscribers.keys()),
        restored,
    )
    yield
    await bus.stop()
    logger.info("shutdown complete")


app = FastAPI(title="Real-time Fraud Detection", version="1.1.0", lifespan=lifespan)
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {
        "name": "Real-time Fraud Detection Microservice",
        "version": "1.1.0",
        "services": [
            "auth",
            "transaction-service",
            "fraud-scoring-service",
            "alert-service",
            "simulator",
            "metrics",
        ],
        "topics": ["transactions.raw", "fraud.scores", "alerts.raised"],
    }


@api_router.get("/health")
async def health():
    return {
        "status": "UP",
        "topics": {t: c for t, c in bus.published_count.items()},
    }


api_router.include_router(auth_router)
api_router.include_router(tx_router)
api_router.include_router(fraud_router)
api_router.include_router(alert_router)
api_router.include_router(simulator_router)
api_router.include_router(metrics_router)
api_router.include_router(download_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
