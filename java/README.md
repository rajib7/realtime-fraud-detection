# FraudOps — Java / Kafka Implementation

Same system as the Python reference (see `/backend`, `/frontend`) but built
with the tech stack the original assignment specified:

- **Transaction, Fraud Scoring, Alert** microservices — Spring Boot 3.2 / Java 21
- **Kafka** (single-broker via Bitnami image) for `transactions.raw`,
  `fraud.scores`, `alerts.raised`
- **ML model** exposed as a standalone Python FastAPI service and consumed
  over HTTP by the fraud scoring service (with Resilience4j circuit breaker
  + rule-only fallback)
- **MongoDB** for persistence (shared across services)
- **Prometheus scrape endpoints** at `/actuator/prometheus` on every JVM

```
             POST /api/tx/transactions
Client ─────────────────────────────────▶ Transaction Service ─┐
                                                               │ Kafka: transactions.raw  (key=userId)
                                                               ▼
                                              Fraud Scoring Service
                                              ┌───────────────────────────────┐
                                              │ ML API call (WebClient)       │
                                              │  ↓ CircuitBreaker + fallback  │
                                              │  ↓ RuleEngine (java)          │
                                              │  ↓ Mongo write                │
                                              │  ↓ produce fraud.scores       │
                                              └───────────────────────────────┘
                                                               │
                                                               ▼
                                                        Alert Service
                                                        raises + persists
                                                        produces alerts.raised
```

## Project layout

```
java/
├── pom.xml                     # parent POM (Spring Boot 3.2 + Java 21)
├── docker-compose.yml          # one-command demo
├── common/                     # shared DTOs & topic constants
│   └── src/main/java/io/fraudops/common/
│       ├── Topics.java
│       ├── RiskLevel.java
│       ├── TransactionEvent.java
│       ├── FraudScoreEvent.java
│       └── AlertEvent.java
├── transaction-service/        # POST /api/tx/transactions
├── fraud-scoring-service/      # KafkaListener + WebClient(ML) + POST /api/fraud/score
├── alert-service/              # KafkaListener + REST /api/alerts/{recent,ack}
└── ml-model-service/           # FastAPI + scikit-learn IsolationForest
```

## Run the whole thing

```bash
cd java
docker compose up --build
```

That brings up: Zookeeper → Kafka → MongoDB → ML model service →
transaction / fraud-scoring / alert services. Give it 30 seconds on
first boot for Kafka to elect a leader.

## Try it out

```bash
# 1. Ingest a normal transaction
curl -X POST http://localhost:8081/api/tx/transactions \
  -H 'content-type: application/json' \
  -d '{"userId":"u_1","amount":42.50,"merchant":"m_1","merchantCategory":"grocery","country":"US"}'

# 2. Score directly against the ML API through fraud-scoring-service
curl -X POST http://localhost:8082/api/fraud/score \
  -H 'content-type: application/json' \
  -d '{"amount":5000,"merchant_category":"crypto_exchange","hour":3,
       "is_foreign":true,"cross_border":true,
       "velocity_1h":8,"distinct_countries_24h":4}'
# → { "ml_score":..., "rule_score":..., "fraud_score":..., "risk_level":"FRAUD",
#     "decision":"block", "reasons":[...], "scoring_latency_ms":..., "model_version":... }

# 3. Post a fraudy tx — pipeline should produce an alert within ~200ms
curl -X POST http://localhost:8081/api/tx/transactions \
  -H 'content-type: application/json' \
  -d '{"userId":"u_9","amount":6400,"merchant":"m_1","merchantCategory":"crypto_exchange",
       "country":"SG","isForeign":true,"crossBorder":true,"velocity1h":8,"distinctCountries24h":4}'

# 4. Read the alert queue
curl http://localhost:8083/api/alerts/recent | jq

# 5. Acknowledge it
curl -X POST http://localhost:8083/api/alerts/<alert_id>/ack

# 6. Prometheus metrics on every JVM
curl http://localhost:8082/actuator/prometheus | head -20
```

## Verifying Kafka event flow

```bash
docker compose exec kafka \
  /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic fraud.scores --from-beginning --max-messages 5
```

## Design highlights

**At-least-once semantics.**  All producers set `acks=all` and enable
idempotence; consumers set `enable.auto.commit=false` and use
`AckMode.RECORD` so offsets commit only after the downstream side effect
(Mongo write + next-topic publish) succeeded.

**Keyed partitioning.**  Every publish is keyed on `userId`. This
preserves per-user ordering across partitions — required for the
`velocity_1h` and `distinct_countries_24h` features to be meaningful when
computed downstream.

**Circuit breaker on the ML API.**  Resilience4j `@CircuitBreaker` +
`@TimeLimiter` in `MLModelClient`. If the model service exceeds 500 ms
timeout or reaches the failure/slow-call thresholds, fraud-scoring falls
back to `RuleEngine.score(tx)` — safer to approve on rules alone than to
freeze the stream.

**Model is a service, not a library.**  `ml-model-service` is deployed
separately. New model versions ship as new container images; the JVM
services don't need to rebuild. Canary via a service mesh (Istio /
Linkerd) header split on `X-Model-Version`.

**Observability.**  Every service exposes `/actuator/prometheus` and
uses Micrometer counters/timers keyed on risk_level, severity, etc.
Prometheus + Grafana bolt on cleanly (compose file left minimal for the
demo).

## Kafka topology summary

| Topic             | Producer                  | Consumer                   | Key      |
| ----------------- | ------------------------- | -------------------------- | -------- |
| `transactions.raw`| transaction-service       | fraud-scoring-service      | userId   |
| `fraud.scores`    | fraud-scoring-service     | alert-service              | userId   |
| `alerts.raised`   | alert-service             | (external — PagerDuty etc.)| userId   |

## Related deliverables

- Python reference implementation (working live app + observability
  console): `/backend`, `/frontend`
- End-to-end walkthrough video, screenshots, presentation deck: `/docs`
