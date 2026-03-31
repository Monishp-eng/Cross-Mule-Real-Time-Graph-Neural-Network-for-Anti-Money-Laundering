# Architecture Reference & Key Decisions

## 1. System Architecture Diagram

```
                          MULE DETECTION SYSTEM
                          
┌────────────────────────────────────────────────────────────────────┐
│                      DATA INGESTION LAYER                          │
├────────────────────────────────────────────────────────────────────┤
│
│  Mobile App       Web Portal        ATM Network       UPI/Bank
│  (iOS/Android)    (Browser)         (HTTPS)           (APIs)
│        │               │                 │                │
│        └───────────────┼─────────────────┼────────────────┘
│                        │
│                        ▼
│            [Azure Event Hubs / Kafka]
│            5 Topics: mobile, web, atm, upi, bank
│            - Retention: 7 days
│            - Partitions: 2 per topic
│            - Throughput: 1000 msg/sec
│
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│           NORMALIZATION & QUALITY ASSURANCE                        │
├────────────────────────────────────────────────────────────────────┤
│
│  [Normalizer Microservice]
│  ├─ Channel mappers (Mobile→Std, ATM→Std, etc.)
│  ├─ PII hashing (phone, email, document)
│  ├─ Data quality checks (completeness, validity)
│  └─ Deduplication (txn_id uniqueness)
│
│  Output: Standard transaction schema
│  {
│    event_id, timestamp, source_account, dest_account,
│    amount, currency, channel, device_id, location
│  }
│
└────────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        
        [Graph DB Update]  [Stream Output]  [Store for ML]
             
┌──────────────────────────────────────┐
│      ENTITY GRAPH LAYER              │
├──────────────────────────────────────┤
│                                      │
│  [Neo4j Aura - Graph Database]       │
│                                      │
│  Nodes:                              │
│  ├─ USER (account owner)             │
│  ├─ ACCOUNT (payment accounts)       │
│  ├─ TRANSACTION (transfer event)     │
│  ├─ DEVICE (mobile, web, ATM)        │
│  └─ LOCATION (geographic)            │
│                                      │
│  Edges:                              │
│  ├─ HAS_ACCOUNT (USER→ACCOUNT)       │
│  ├─ SENT_TO (ACCOUNT→ACCOUNT)        │
│  ├─ IS_ON_DEVICE (ACCOUNT→DEVICE)    │
│  ├─ LOCATED_AT (DEVICE→LOCATION)     │
│  └─ LINKED_WITH (USER→USER)          │
│                                      │
│  Indexes: account_id, user_id, txn_id│
│  Constraints: UNIQUE account_id, etc │
│                                      │
│  Update latency: < 10ms              │
│  Query latency: < 50ms               │
│                                      │
└──────────────────────────────────────┘
        │
        ├─────────────────┬─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ FEATURE          │  │ GNN DETECTOR     │  │ RISK SCORER      │
│ EXTRACTION       │  │                  │  │                  │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│                  │  │                  │  │                  │
│ Window Agg:      │  │ Node Features:   │  │ Component        │
│ - 24h volume     │  │ ├─ Account age   │  │ Scores:          │
│ - 1h velocity    │  │ ├─ Velocity      │  │ ├─ Velocity      │
│ - 5m anomaly     │  │ ├─ Balance       │  │ ├─ Diversity     │
│                  │  │ ├─ Device count  │  │ ├─ Geography     │
│ Entity-level:    │  │ └─ ...           │  │ ├─ Structuring   │
│ ├─ User profile  │  │                  │  │ ├─ Account age   │
│ ├─ Account stats │  │ Graph Agg:       │  │ ├─ Device count  │
│ └─ Device info   │  │ ├─ Neighbor feat │  │ └─ Jurisdiction  │
│                  │  │ ├─ Edge weights  │  │                  │
│ Enrichment:      │  │ └─ Max pooling   │  │ Weighted combo:  │
│ ├─ Geo IP        │  │                  │  │ Score = Σ(w*s)   │
│ ├─ Reputation    │  │ Classification:  │  │ where Σw = 1.0   │
│ └─ KYC score     │  │ ├─ GraphSAGE     │  │                  │
│                  │  │   embedding      │  │ Output: 0-1      │
│ Features        │  │ ├─ Neural net    │  │ LOW: 0-0.3       │
│ available for:   │  │   head           │  │ MED: 0.3-0.7     │
│ - Real-time      │  │ └─ Softmax       │  │ HIGH: 0.7-1.0    │
│   scoring        │  │                  │  │                  │
│ - Model training │  │ Output:          │  │ Factors:         │
│ - Explanability  │  │ ├─ Probability   │  │ [velocity, ...]  │
│                  │  │ ├─ Confidence    │  │                  │
│                  │  │ ├─ Pattern type  │  │ Confidence:      │
│                  │  │ └─ Explanation   │  │ 0.8-0.95         │
│                  │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        │                    │                        │
        └────────────────────┼────────────────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │  DECISION ENGINE       │
                ├────────────────────────┤
                │                        │
                │ Combine signals:       │
                │ Risk Score: 0.65       │
                │ Mule Prob:  0.72       │
                │ ─────────────────      │
                │ Combined:   0.685      │
                │                        │
                │ Threshold checks:      │
                │ if > 0.7 → BLOCK       │
                │ if > 0.4 → FLAG        │
                │ else → ALLOW           │
                │                        │
                │ Policy overrides:      │
                │ (manual, KYC, etc)     │
                │                        │
                └────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    
    [ALLOW]          [FLAG]            [BLOCK]
    Transaction      Case Created       Account
    Approved         + Alert            Frozen
                     + Investigation    Alert
                                       Case
```

---

## 2. Technology Stack Choice Rationale

### Graph Database: Neo4j Aura

**Why Neo4j?**
- ✅ ACID transactions (data consistency)
- ✅ Cypher query language (SQL-like for graphs)
- ✅ Fully managed (Aura) → no ops burden
- ✅ Fast traversal (native graph storage)
- ✅ Mature ecosystem (PyNeo4j, visualization tools)
- ✅ Scalability (tested to billions of nodes)

**Alternatives considered:**
- Amazon Neptune: Overkill for MVP, higher cost
- ArangoDB: Strong multimodel, less graph-native
- TigerGraph: Fastest for analytics, less mature

**Decision**: Neo4j Aura (managed) for MVP

---

### Streaming Platform: Azure Event Hubs + Kafka

**Why Event Hubs?**
- ✅ Azure-native (easy integration)
- ✅ Sub-second latency
- ✅ Partition-based ordering
- ✅ Built-in monitoring

**Why Kafka (alternative)?**
- ✅ Open-source (no vendor lock-in)
- ✅ Ecosystem maturity
- ✅ Larger community

**Decision**: Event Hubs for MVP (Azure managed), consider Kafka for production portability

---

### ML Framework: PyTorch Geometric

**Why PyTorch Geometric?**
- ✅ GNN-native (GraphSAGE, GAT, GCN all built-in)
- ✅ Production-ready (Pinterest, Snap using it)
- ✅ Performance optimizations (sparse to dense, GPU)
- ✅ Active community

**Alternatives:**
- DGL: Close competitor, also good
- Spektral (Keras): Simpler, less scalable

**Decision**: PyTorch Geometric for MVP, can switch to DGL if needed

---

### Microservices: Azure Container Apps

**Why Container Apps?**
- ✅ Serverless (auto-scaling, no cluster management)
- ✅ Built-in scale-to-zero
- ✅ Event-driven (integrate with Event Hubs)
- ✅ Cost-effective for MVP

**Alternatives:**
- AKS (Kubernetes): overkill for MVP
- Azure Functions: Less flexible for CPU-bound
- App Service: Traditional, manual scaling

**Decision**: Container Apps for MVP simplicity

---

## 3. Data Flow Deep Dive

### Scenario: Money Mule Ring Detection in Real-Time

```
T=0ms:   Mobile User sends $1,000
         └─ Event Hub ingestion

T=5ms:   Normalizer processes:
         └─ Maps Mobile event to standard schema
         └─ Hashes PII (phone → hash_xyz)
         └─ Validates data quality

T=10ms:  Graph Builder updates Neo4j:
         └─ CREATE Account node (if new)
         └─ CREATE User-HAS_ACCOUNT relationship
         └─ MERGE SENT_TO edge (source → dest)
         └─ CREATE Device & Location nodes

T=15ms:  Feature Extraction sees:
         └─ User now has 5 accounts
         └─ 20 transactions in last hour
         └─ 15 devices detected
         └─ 38 unique counterparties
         └─ Account age: 2 days

T=30ms:  Risk Scorer computes:
         ├─ Velocity: 20 txns/hr vs baseline 5 → 0.9
         ├─ Diversity: 38 accounts / 50 → 0.76
         ├─ Structuring: Amounts $950-$1050 → 0.88
         ├─ Account age: 2 days → 0.93
         ├─ Device count: 15 / 10 → 1.0
         └─ Combined: 0.89 (HIGH RISK)

T=50ms:  GNN Detector runs:
         ├─ Query graph: anchor account neighborhood
         ├─ Extract node features (account_age, velocity, etc)
         ├─ Aggregate neighbor features (GraphSAGE)
         ├─ Classification head (neural net)
         └─ Output: 0.85 mule probability

T=65ms:  Decision Engine:
         ├─ Risk: 0.89
         ├─ Mule Prob: 0.85
         ├─ Combined: 0.87
         ├─ > 0.7 → DECISION: BLOCK
         └─ Account frozen, alert sent

T=70ms:  Response to user:
         {"decision": "BLOCK", "reason": "Suspicious activity", ...}

T=100ms: Case Management:
         ├─ Create investigation case
         ├─ Alert SOC team (Slack, PagerDuty)
         ├─ Graph snapshot saved for review
         └─ Audit log recorded
```

**Success**: Transaction blocked in <100ms ✓

---

## 4. Key Decision Points & Trade-offs

| Decision | MVP Choice | Rationale | Trade-offs |
|----------|-----------|-----------|-----------|
| **Graph DB** | Neo4j Aura | Managed, battle-tested | Vendor lock-in |
| **Streaming** | Event Hubs | Azure integrated | Kafka has larger ecosystem |
| **GNN Library** | PyTorch Geometric | Production-ready | More dependencies |
| **Compute** | Container Apps | Serverless, simple | Less control vs K8s |
| **Model Training** | Batch (not real-time) | Simpler, faster MVP | Not continuous learning |
| **Privacy** | Hashing (not FHE) | Practical & performant | Deterministic hash reversible |
| **Multi-region** | Single region | MVP scope | Needs HA for production |
| **Alerts** | Synchronous API | Low latency | Blocks transaction |

---

## 5. Scaling Strategy (Post-MVP)

### Phase 1 (Current): Single region, ~100 txns/sec
- Neo4j Aura Professional tier
- Single Event Hub namespace
- Container Apps: 1-2 replicas

### Phase 2 (Month 3): Multi-region, ~1K txns/sec
- Neo4j Aura Enterprise tier
- Event Hub: increased partitions
- Container Apps: auto-scale to 10+ replicas
- Add distributed caching (Redis)

### Phase 3 (Month 6): Global scale, ~100K txns/sec
- Neo4j cluster (on-premise or federation)
- Global Event Hubs
- Kubernetes (AKS) instead of Container Apps
- Model serving (TorchServe, Seldon)
- Cache layer (Memcached)

---

## 6. Cost Estimation (MVP)

| Component | SKU | Monthly Cost |
|-----------|-----|------|
| Neo4j Aura | Professional (15GB) | $500 |
| Event Hubs | Standard (100 TU) | $300 |
| Container Apps | 0.5 CPU, 1 GB mem | $150/app × 3 |
| Storage (Blobs) | 100 GB LRS | $50 |
| Monitor/Insights | | $100 |
| **Total** | | **~$1,500/month** |

*After MVP (production)*: ~$10-20K/month (depends on volume)

---

## 7. Security Considerations

```
Data Lifecycle: Raw → Normalized → Hashed → Stored

Input Validation:
├─ Amount: $0.01 - $1M
├─ Timestamp: within 60s of ingestion
└─ Account IDs: format validation

PII Protection:
├─ Hashing: SHA256(field + salt)
├─ No plain storage of phone, email, document
└─ GDPR: Right to be forgotten → delete nodes

Audit Trail:
├─ Every decision logged (ALLOW/FLAG/BLOCK)
├─ User ID, timestamp, risk factors
└─ Compliance reports (SAR, CTF)

API Security:
├─ JWT bearer tokens
├─ RBAC (analyst, reviewer, admin roles)
├─ Rate limiting (1000 req/min per user)
└─ TLS encryption (in transit)
```

---

## Next Steps

1. ✅ Review this architecture
2. → Deploy [infra/deployment.md](deployment.md)
3. → Implement Phase 1 tasks from [IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md)
4. → Run tests in `tests/` directory

---

**Questions about architecture?** Reference [SYSTEM_DESIGN.md](../docs/SYSTEM_DESIGN.md) for detailed explanations.
