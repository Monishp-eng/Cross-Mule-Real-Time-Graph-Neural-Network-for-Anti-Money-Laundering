# Cross-Channel Mule Account Detection Graph

A Graph Neural Network (GNN)-based real-time transaction monitoring system for detecting money mule rings across multiple payment channels.

## Internal Analyst Platform (Current UI)

This repository now exposes an internal, staff-only analyst console in the frontend.

- Frontend URL: http://127.0.0.1:5173
- Backend URL: http://127.0.0.1:8000
- Login API: POST /login
- Main analyst routes:
        - /dashboard
        - /alerts
        - /users/:userId
        - /compliance

### Default Staff Credentials

These users are seeded automatically at backend startup:

- Analyst
        - Identity: EMP-1001 (or analyst@bank.local)
        - Password: Analyst@123
        - Role: ANALYST
- Admin
        - Identity: EMP-9001 (or admin@bank.local)
        - Password: Admin@123
        - Role: ADMIN

You can override these defaults with STAFF_BOOTSTRAP_USERS using:

- email|employee_id|password|role|full_name;email|employee_id|password|role|full_name

### Local Run

Backend:

1. Open a terminal at the repository root.
2. Run: .\\.venv\\Scripts\\python.exe -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000

Frontend:

1. Open a terminal in frontend.
2. Run: npm run dev -- --host 127.0.0.1

Optional production build check:

- In frontend, run: npm run build

### Analyst APIs Wired in Frontend

- POST /login
- GET /alerts
- POST /alerts/{alert_id}/action
- GET /users
- GET /users/{user_id}
- GET /risk-score?user_id=...
- GET /transactions
- GET /graph
- GET /compliance/sar
- GET /compliance/risk-summary

## Quick Start

```
docs/
├── SYSTEM_DESIGN.md          # High-level system architecture
├── ARCHITECTURE.md            # Detailed technical design
├── IMPLEMENTATION_PLAN.md     # Phased MVP approach
├── DATA_SPEC.md              # Data model & schemas
└── API_CONTRACTS.md          # System APIs

src/                          # Source code modules
├── data-ingestion/           # Multi-channel log ingestion
├── graph-builder/            # Entity graph construction
├── gnn-detector/             # GNN model for mule detection
├── risk-scoring/             # Anomaly & risk scoring
├── real-time-engine/         # Low-latency transaction processing
└── compliance-reporting/     # Regulatory reports & audit

infra/                        # Infrastructure as Code

tests/                        # Unit & integration tests
```

## System Overview

### Core Problem
Money mules operate across channels (Mobile App → Linked Wallet → ATM) in minutes, evading siloed fraud rules.

### Solution
- **Unified Entity Graph**: Correlates accounts across payment channels
- **GNN Detector**: Identifies structural patterns of mule rings in near real-time
- **Risk Scoring**: Rates transaction velocity, fund fragmentation, and unusual routing
- **Compliance Ready**: Generates audit trails and regulator reports with confidence scores

### Key Capabilities
✅ Multi-channel transaction ingestion (App, Web, ATM, UPI, etc.)
✅ Real-time entity linking and graph updates
✅ ML-based mule ring detection
✅ Behavior-based sanctions screening
✅ Privacy-safe intelligence sharing
✅ Jurisdiction-based risk scoring
✅ Production-grade audit & reporting

## Architecture Overview

```
Payment Channels          Data Ingestion          Graph DB            Real-time Engine
─────────────────        ──────────────         ──────────           ─────────────────
Mobile App       ───┐
Web Portal       ─┐ │─→ [Event Stream] ───→ [Neo4j/CosmosDB] ───→ [Spark/Kafka] 
ATM Network      ─┤ │─→ [Normalizer]        [Graph Storage]        [GNN Detector]
UPI/Bank APIs    ─└─→ [Transformer]         [Entity Index]         [Risk Scorer]
                                                                    
                                            ↓
                                    [Decision Engine]
                                    [Alert Manager]
                                    [Compliance Reports]
```

## MVP Timeline (1-2 Months)

**Phase 1 (Week 1-2)**: Data ingestion + graph foundation
**Phase 2 (Week 3)**: GNN model & risk scorer  
**Phase 3 (Week 4)**: Real-time pipeline + alerts
**Phase 4 (Week 5-8)**: Hardening, testing, deployment

## Technology Stack

| Component | Recommended | Alternative |
|-----------|-------------|------------|
| **Graph DB** | Neo4j Aura (Cloud) | ArangoDB, TigerGraph |
| **Streaming** | Kafka / Pub/Sub | Azure Event Hubs, Kinesis |
| **ML/GNN** | PyTorch Geometric | DGL, Spektral |
| **Processing** | Apache Spark | Flink, Beam |
| **Computing** | Container services | Kubernetes, managed containers |
| **Data Lake** | GCS / Blob Storage | S3, Azure Blob Storage |
| **Monitoring** | Cloud Operations + OpenTelemetry | Prometheus, Datadog |
| **Language** | Python 3.11+ | Java, Go |

---

## Next Steps

1. **Read [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)** for end-to-end architecture
2. **Review [DATA_SPEC.md](docs/DATA_SPEC.md)** for entity models
3. **Check [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)** for MVP roadmap
4. **Run tests** to validate each module

---

## Key Decision Points for Your Team

- [ ] Choose Graph DB (Neo4j vs. Cosmos vs. ArangoDB)
- [ ] Streaming platform (Kafka vs. Pub/Sub vs. Pulsar)
- [ ] GNN model complexity (basic classification vs. advanced anomaly detection)
- [ ] Privacy framework (differential privacy, federated learning?)
- [ ] Compliance scope (GDPR, AML/KYC, jurisdiction-specific rules)

See [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md) for detailed analysis.
