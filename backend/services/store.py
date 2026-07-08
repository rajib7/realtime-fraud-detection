"""In-memory ring buffers used for the live dashboard.

MongoDB persists the same events for durability, but hot reads come from these
lightweight rolling buffers to keep the dashboard snappy without hammering
the DB.
"""
from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, List


class RollingStore:
    def __init__(self, maxlen: int = 500) -> None:
        self._buf: Deque[Dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = Lock()
        self.total: int = 0

    def add(self, item: Dict[str, Any]) -> None:
        with self._lock:
            self._buf.appendleft(item)
            self.total += 1

    def recent(self, n: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(list(self._buf)[:n])

    def all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._buf)


transactions_store = RollingStore(maxlen=500)
scores_store = RollingStore(maxlen=500)
alerts_store = RollingStore(maxlen=200)
