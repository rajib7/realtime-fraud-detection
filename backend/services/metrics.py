"""Metrics accumulator - tracks TPS, latency, fraud rate for the dashboard."""
from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Deque, Dict, List, Tuple


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        # (timestamp, latency_ms, risk_level)
        self._events: Deque[Tuple[float, float, str]] = deque(maxlen=2000)
        # per-second buckets for sparkline
        self._tps_history: Deque[Tuple[int, int]] = deque(maxlen=60)
        self._alert_count: int = 0
        self._total: int = 0

    def record(self, latency_ms: float, risk_level: str, is_alert: bool) -> None:
        now = time.time()
        with self._lock:
            self._events.append((now, latency_ms, risk_level))
            self._total += 1
            if is_alert:
                self._alert_count += 1

    def snapshot(self) -> Dict[str, object]:
        now = time.time()
        with self._lock:
            events = list(self._events)

        recent = [e for e in events if now - e[0] <= 10.0]
        window = max(1.0, min(10.0, (now - events[0][0]) if events else 1.0))
        tps = round(len(recent) / window, 2) if recent else 0.0
        avg_latency = round(
            sum(e[1] for e in recent) / len(recent), 2
        ) if recent else 0.0
        p95 = 0.0
        if recent:
            sorted_lat = sorted(e[1] for e in recent)
            p95 = round(sorted_lat[int(0.95 * (len(sorted_lat) - 1))], 2)

        fraud_count = sum(1 for e in recent if e[2] == "fraud")
        suspicious_count = sum(1 for e in recent if e[2] == "suspicious")
        fraud_rate = round(100.0 * fraud_count / len(recent), 2) if recent else 0.0

        # 20-bucket sparkline of last 20 seconds (TPS per second).
        buckets: List[int] = [0] * 20
        for ts, _, _ in events:
            delta = int(now - ts)
            if 0 <= delta < 20:
                buckets[19 - delta] += 1

        latency_buckets: List[float] = [0.0] * 20
        latency_counts: List[int] = [0] * 20
        for ts, lat, _ in events:
            delta = int(now - ts)
            if 0 <= delta < 20:
                latency_buckets[19 - delta] += lat
                latency_counts[19 - delta] += 1
        latency_series = [
            round(latency_buckets[i] / latency_counts[i], 2) if latency_counts[i] else 0.0
            for i in range(20)
        ]

        return {
            "tps": tps,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95,
            "fraud_rate_pct": fraud_rate,
            "fraud_count_10s": fraud_count,
            "suspicious_count_10s": suspicious_count,
            "total_processed": self._total,
            "total_alerts": self._alert_count,
            "tps_sparkline": buckets,
            "latency_sparkline": latency_series,
        }


metrics = Metrics()
