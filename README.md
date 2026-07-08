# FraudOps — Real-time Fraud Detection Microservice with ML

A production-shape reference implementation of a real-time fraud detection
system built as **three cooperating microservices** (Transaction, Fraud
Scoring, Alert) wired together through an **event bus** with Kafka-style
topic semantics, powered by a **scikit-learn ML model exposed via HTTP
API**, and fronted by a **live operations console** with **JWT auth +
role-based access control**.

The original assignment specified Java Spring Boot + Kafka. This project
demonstrates the same architecture on a portable Python stack (FastAPI +
MongoDB + React) so the design, latency, resilience, scaling and
observability story remains identical, but the whole thing runs on your
laptop in one process.

---

## Quick start (60 seconds)

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in MONGO_URL + JWT_SECRET
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 2. Frontend (in a second shell)
cd frontend
yarn install
cp .env.example .env    # set REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

Open http://localhost:3000 and log in with one of the seeded demo accounts:

| Role    | Email                    | Password    |
| ------- | ------------------------ | ----------- |
| admin   | admin@fraudops.io        | admin123    |
| analyst | analyst@fraudops.io      | analyst123  |
| viewer  | viewer@fraudops.io       | viewer123   |

Then click **Start Stream** and watch transactions flow through the
Kafka-style topics: `transactions.raw → fraud.scores → alerts.raised`.

---

## Two implementations, one design

| Stack | Path | Runtime |
| --- | --- | --- |
| **Python reference** — FastAPI + in-process asyncio event bus + React SPA | `backend/`, `frontend/` | `uvicorn` + `yarn start` |
| **Java / Kafka assignment target** — Spring Boot 3.2 + Kafka + WebClient → Python ML API | `java/` | `docker compose up` |

The Java version is the one that literally matches the assignment
prompt (Transaction / Fraud Scoring / Alert microservices in Spring
Boot, real Kafka topics, ML model as an HTTP API). See
[`java/README.md`](java/README.md) for one-command setup.

The Python version is the same design translated to a single portable
process — it powers the live demo, the RBAC console and the walkthrough
video.

---

## Documentation

- **[Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md)** — architecture,
  every code path, Mermaid diagrams, latency / resilience / scaling
  discussion, and the ML story.
- **[Demo Script](docs/DEMO_SCRIPT.md)** — a scripted end-to-end
  walkthrough with the exact clicks and API calls, ready to record.

---

## Directory layout

```
.
├── backend/
│   ├── server.py                        # FastAPI orchestrator + lifespan
│   ├── requirements.txt
│   ├── .env.example
│   └── services/
│       ├── auth.py                      # JWT + bcrypt + RBAC dependency
│       ├── auth_router.py               # /api/auth/{register,login,me,logout,roles}
│       ├── event_bus.py                 # In-process pub/sub (Kafka simulator)
│       ├── ml_model.py                  # IsolationForest + rule engine
│       ├── metrics.py                   # TPS / latency / fraud-rate rollup
│       ├── metrics_router.py            # GET /api/metrics
│       ├── simulator.py                 # Synthetic tx generator
│       ├── simulator_router.py          # /api/simulator/{start,stop,inject-fraud,config,status}
│       ├── store.py                     # In-memory ring buffers
│       ├── transaction_service.py       # /api/tx/transactions
│       ├── fraud_scoring_service.py     # /api/fraud/score + subscribes tx topic
│       └── alert_service.py             # /api/alerts/recent + ack + rehydration
│
├── frontend/
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── App.js                       # Router + auth gate + layout
│       ├── lib/
│       │   ├── api.js                   # axios client + auth interceptor
│       │   ├── auth.jsx                 # AuthProvider / useAuth
│       │   └── format.js                # risk styles, formatters
│       ├── constants/testIds/
│       │   └── dashboard.js             # data-testid catalogue
│       └── components/                  # LoginScreen, KpiCards, DemoControls,
│                                        # TransactionStream, AlertsPanel,
│                                        # ArchitectureDiagram, ApiExplorer,
│                                        # DesignNotes, Sparkline
│
└── docs/
    ├── TECHNICAL_DEEP_DIVE.md
    └── DEMO_SCRIPT.md
```

---

## Packaging for submission

```bash
./scripts/package_submission.sh
# → fraudops-submission.tar.gz  (source only, no secrets, no caches)

# want a zip instead?
./scripts/package_submission.sh fraudops-submission.zip
```

The script stages a clean copy, strips caches and virtual envs, and
refuses to build if any origin-platform brand name leaks into the
staged files. Ship the resulting archive.

---

## License

MIT.
