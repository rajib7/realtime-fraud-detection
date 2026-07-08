"""
In-memory event bus that simulates Kafka topics.

Java/Spring Boot equivalent would use spring-kafka with KafkaTemplate + @KafkaListener.
Here we use asyncio.Queue per topic and register handlers as consumers.

Topics:
- transactions.raw      -> published by transaction service
- fraud.scores          -> published by fraud scoring service
- alerts.raised         -> published by alert service
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List

logger = logging.getLogger("event_bus")

Handler = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)
        self._queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._workers: List[asyncio.Task] = []
        self._running: bool = False
        self.published_count: Dict[str, int] = defaultdict(int)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    async def publish(self, topic: str, event: Dict[str, Any]) -> None:
        self.published_count[topic] += 1
        await self._queues[topic].put(event)

    async def _consume_topic(self, topic: str) -> None:
        while True:
            event = await self._queues[topic].get()
            for handler in self._subscribers[topic]:
                try:
                    await handler(event)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("handler failed for topic %s: %s", topic, exc)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Spawn one worker per topic (mirrors Kafka consumer per topic)
        for topic in list(self._subscribers.keys()):
            self._workers.append(asyncio.create_task(self._consume_topic(topic)))

    async def stop(self) -> None:
        for w in self._workers:
            w.cancel()
        self._workers.clear()
        self._running = False


bus = EventBus()

TOPIC_TX_RAW = "transactions.raw"
TOPIC_FRAUD_SCORES = "fraud.scores"
TOPIC_ALERTS = "alerts.raised"
