import React from "react";
import { Gauge, ShieldCheck, Layers, Waves } from "lucide-react";

const SECTIONS = [
  {
    Icon: Gauge,
    accent: "#00E5FF",
    title: "Latency budget",
    points: [
      "p95 scoring latency stays under ~8 ms because IsolationForest inference is O(n_estimators · log(depth)); the rule engine is O(1).",
      "Producers are non-blocking. Transaction Service returns 202-style ack the instant the event lands on transactions.raw; scoring happens async downstream.",
      "In the Java/Kafka version: KafkaTemplate + async send + linger.ms=5 for micro-batching. Consumers use max.poll.records=500 with parallel processing.",
    ],
  },
  {
    Icon: ShieldCheck,
    accent: "#00FF66",
    title: "Resilience",
    points: [
      "At-least-once delivery: consumer commits offsets only after Mongo write and downstream publish succeed.",
      "Dead Letter Queue: scoring failures (model timeout, malformed payload) route to fraud.scores.dlq for reprocessing; alert-service ignores DLQ topic.",
      "ML API circuit breaker (Resilience4j) — falls back to rule-only scoring if the model service exceeds p99 latency SLA.",
    ],
  },
  {
    Icon: Layers,
    accent: "#FFB000",
    title: "Scaling",
    points: [
      "Kafka partitions keyed by user_id preserve per-user ordering (velocity + country-hopping features need it).",
      "Fraud Scoring Service is horizontally scaled: N pods == N partitions of transactions.raw; consumer group rebalance is automatic.",
      "ML model served as an isolated service (fast-api / triton). Autoscale on CPU + p95 latency SLO; model versions rotated via canary.",
    ],
  },
  {
    Icon: Waves,
    accent: "#FF3366",
    title: "Data & ML",
    points: [
      "Features are computed streaming (velocity_1h, distinct_countries_24h) — in production, backed by Flink or Kafka Streams state stores.",
      "IsolationForest catches novel anomalies; the rule engine enforces regulatory blocks and gives explainable reason codes for the alert.",
      "Fused score = 0.6 · ml + 0.4 · rules. Threshold 0.75 → block, 0.5 → review. Both drift-monitored via daily PSI/KS reports.",
    ],
  },
];

export default function DesignNotes() {
  return (
    <div className="card-surface p-4 sm:p-6">
      <div className="mb-4">
        <div className="text-xs uppercase tracking-[0.2em] font-semibold text-[#F8FAFC]">
          System Design Notes
        </div>
        <div className="text-[11px] font-mono text-[#64748B]">
          latency · resilience · scaling · ml — talking points for the demo
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        {SECTIONS.map(({ Icon, accent, title, points }) => (
          <div key={title} className="border border-[#222630] rounded p-4">
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-7 h-7 rounded flex items-center justify-center"
                style={{ background: `${accent}18`, color: accent }}
              >
                <Icon size={14} />
              </div>
              <div className="text-sm font-semibold text-[#F8FAFC]">
                {title}
              </div>
            </div>
            <ul className="space-y-2">
              {points.map((p, i) => (
                <li
                  key={i}
                  className="text-[12.5px] leading-relaxed text-[#94A3B8] flex gap-2"
                >
                  <span
                    className="mt-1.5 w-1 h-1 rounded-full flex-none"
                    style={{ background: accent }}
                  />
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
