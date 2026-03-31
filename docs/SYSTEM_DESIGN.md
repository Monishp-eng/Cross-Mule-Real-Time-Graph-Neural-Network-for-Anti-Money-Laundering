# Cross-Channel Mule Detection System Design

## Executive Summary

This document outlines a **Graph Neural Network (GNN)-based real-time transaction monitoring platform** that detects money mule rings operating across multiple payment channels. The system integrates disparate sources (Mobile App, Web, ATM, UPI) into a unified Entity Graph, scores structural patterns and transaction velocity, and identifies high-risk clusters in near real-time.

---

## 1. Problem Statement

### Current Pain Points

**Siloed Detection**: Fraud rules operate within single channels
- ATM rule: "Withdrawal >$5k = Alert"
- App rule: "Transfer >$10k = Block"
- **Problem**: Mule sends $3k via app → wallet → ATM in 5 minutes (no alert!)

**Missing Context**: No correlation across channels
- Why did this account suddenly link to 50 wallets?
- Why are 10 accounts moving funds to the same Bitcoin exchange?
- Which accounts are coordinated (same mule ring)?

**Velocity Blindness**: High-frequency fragmentation
- Structuring: Multiple $1k transfers to evade thresholds
- Nesting: A→B→C→D→E (5-hop laundering)
- Cascade: Account clusters rapidly moving funds in sequence

**Compliance Gaps**:
- No end-to-end visibility for regulators
- Limited sanctions screening beyond watchlists
- Poor audit trails for suspicious activity

---

## 2. Solution Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-CHANNEL EVENT INGESTION                   │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│  Mobile App  │  Web Portal  │  ATM Network │  UPI/Bank APIs       │
│   Events     │   Events     │   Events     │   Events             │
└──────────────┴──────────────┴──────────────┴──────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA NORMALIZATION LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│  • Schema mapping (timestamp, user_id, amount, channel)             │
│  • PII hashing & anonymization                                      │
│  • Data quality checks & enrichment                                │
│  • Duplicate detection                                             │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTITY GRAPH CONSTRUCTION                        │
├─────────────────────────────────────────────────────────────────────┤
│ Graph Nodes:                                                         │
│  • USER: Individual accounts (phone, email, document)               │
│  • ACCOUNT: Payment accounts (wallet, bank, card)                   │
│  • TRANSACTION: Transfer event                                      │
│  • DEVICE: Phone, IP, fingerprint                                   │
│  • LOCATION: Geographic coordinates (ATM, branch)                   │
│                                                                      │
│ Graph Edges:                                                         │
│  • HAS_ACCOUNT, IS_ON_DEVICE, LOCATED_AT                           │
│  • SENT_TO, RECEIVED_FROM (with amount, velocity)                   │
│  • LINKED_WITH (same owner, related devices)                        │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME DETECTION ENGINE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ GNN-Based Detection:                                    │        │
│  │ • GraphSAGE: Learn node embeddings from neighborhood    │        │
│  │ • Identify structural patterns: rings, stars, chains    │        │
│  │ • Classify as NORMAL, SUSPICIOUS, HIGH_RISK, BLOCKED   │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ Risk Scoring:                                           │        │
│  │ • Transaction velocity (# transfers/hour)               │        │
│  │ • Account diversity (# of linked accounts)              │        │
│  │ • Geographic inconsistency (ATM in NY, then TX in 2hrs) │        │
│  │ • Fractional transfers (structuring patterns)           │        │
│  │ • Jurisdiction risk (target country, regulatory status) │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ Behavioral Sanctions Screening:                         │        │
│  │ • Typology matching (structuring, nesting, cascade)     │        │
│  │ • Behavioral signals beyond watchlist                   │        │
│  │ • Cross-bank intelligence correlation                   │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DECISION & RESPONSE LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│  • Risk Threshold Evaluation                                         │
│  • Decision Points: ALLOW / FLAG / BLOCK / ESCALATE                 │
│  • Real-time Alerts to SOC                                          │
│  • Automatic Account Freeze (if BLOCKED)                            │
│  • Regulatory Case Management                                       │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE & REPORTING                           │
├─────────────────────────────────────────────────────────────────────┤
│  • Investigation Case Files (graph visualization)                   │
│  • SAR/CTF Reports (Regulator-ready)                                │
│  • Audit Logs (full transaction lineage)                            │
│  • Privacy-Safe Intelligence Sharing (federated channels)           │
│  • ML Model Explainability (why was this flagged?)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Capabilities

### 3.1 Multi-Channel Integration
- **Input**: Transactions from 5+ channels (Mobile, Web, ATM, UPI, Bank APIs)
- **Processing**: Real-time normalization to standard schema
- **Output**: Unified transaction stream feeding graph

### 3.2 Entity Linking & Deduplication
- Phone number → multiple user IDs (same person, different channels)
- Device fingerprint → account clustering
- Address → geographic risk profiling
- **Algorithm**: Probabilistic entity resolution with configurable thresholds

### 3.3 Graph-Based Structural Detection
- **Ring Detection**: Accounts forming circular transfer patterns (A→B→C→A)
- **Star Pattern**: Central hub account connected to 50+ spokes
- **Chain Pattern**: Sequential transfers increasing in amount (structuring)
- **Cascade**: Parallel accounts moving funds simultaneously
- **Temporal Anomalies**: Impossible geography (NYC ATM then Tokyo ATM in 30 mins)

### 3.4 GNN-Based Classification
```python
# Simplified GNN flow
node_features = {
    user_id: [
        num_accounts,           # User maintains 5 accounts
        total_volume_24h,       # $50k in 24 hours
        velocity_score,         # High (many txns/hour)
        geographic_variance,    # Very high (3 countries)
        account_age,           # Recent (created 2 days ago)
        device_count,          # Many (15 devices)
        ...
    ]
}

edge_features = {
    (user_a, user_b): [
        transfer_amount,         # $1,000
        time_to_transfer,        # 5 minutes
        transfer_frequency,      # 10x today
        amount_percentage,       # 50% of user_a balance
        ...
    ]
}

# GraphSAGE: Learn embeddings from 2-hop neighborhood
embeddings = gnn_model(node_features, edge_features, graph)

# Classification head
risk_score, confidence = classifier(embeddings)
# Output: 0.92 risk (92% confidence mule ring)
```

### 3.5 Jurisdiction-Based Risk Scoring
```
Base Risk = 0.3

Risk Factors:
+ Target Country Risk (FATF grey list): +0.3
+ Transaction Velocity (50 txns/hour): +0.2
+ Structuring Pattern (fragmentation): +0.1
+ Account Age (2 days): +0.1
+ Device Count (15 devices): +0.05
- KYC Score (verified): -0.1

Final Risk Score = 0.92 (92%)
Decision = BLOCK
```

### 3.6 Behavior-Based Sanctions Screening
- Traditional: "Is user on watchlist?" → Binary
- Enhanced: "Does user exhibit watchlist behavior?" → Continuous
  - Multiple rapid transfers to high-risk countries
  - Rapid account linking & delinking patterns
  - Structuring to individual limit thresholds
  - Use of cash-to-crypto gateways

### 3.7 Privacy-Safe Intelligence Sharing
- **Approach**: Share anonymized mule patterns between banks without exposing customer data
- **Method**: Publish to secure channel: "Ring pattern detected: 12 accounts, feature vector X"
- **Flow**: Bank A detects pattern → Publishes to Consortium DB → Bank B verifies against own graph

### 3.8 Regulatory Reporting
```json
{
  "report_type": "SAR",
  "case_id": "MULE_RING_2024_001",
  "detection_date": "2024-03-23T14:35:00Z",
  "accounts_involved": ["ACC001", "ACC002", "ACC003"],
  "mule_ring_structure": "star",
  "confidence_score": 0.92,
  "total_value": 125000,
  "time_window": "2 hours",
  "jurisdiction": "US",
  "typology": "Structuring + Rapid Account Linking",
  "model_version": "GNN_v2.1",
  "audit_trail": [...],
  "recommended_action": "BLOCK + ESCALATE"
}
```

---

## 4. Data Model

### 4.1 Core Entities

#### USER Node
```graphql
node User {
  user_id: String!           # Unique identifier
  phone: String              # Hashed phone number
  email: String              # Hashed email
  document_id: String        # National ID (KYC)
  kyc_score: Float           # 0-1, higher = more verified
  created_at: DateTime
  countries: [String]        # Countries of residence/activity
  risk_profile: String       # LOW, MEDIUM, HIGH, BLOCKED
}
```

#### ACCOUNT Node
```graphql
node Account {
  account_id: String!        # Unique account identifier
  channel: String!           # MOBILE, WEB, ATM, UPI, BANK
  account_type: String       # WALLET, CARD, BANK_ACC
  provider: String           # PayPal, Stripe, etc.
  balance: Float
  status: String             # ACTIVE, SUSPENDED, BLOCKED
  created_at: DateTime
  linked_at: DateTime        # When linked to user
}
```

#### TRANSACTION Node
```graphql
node Transaction {
  txn_id: String!            # Unique transaction ID
  source_account: String!    # Account ID
  dest_account: String!      # Account ID
  amount: Float!             # In USD equivalent
  currency: String           # USD, INR, etc.
  timestamp: DateTime!       # Transaction time
  channel: String            # Mobile, ATM, UPI
  status: String             # COMPLETED, PENDING, FAILED
  velocity_score: Float      # How fast relative to typical?
  location: Location         # Geographic coordinates
}
```

#### DEVICE Node
```graphql
node Device {
  device_id: String!         # Mobile device fingerprint or IP
  device_type: String        # MOBILE, WEB, ATM
  ip_address: String         # Hashed IP
  country: String            # Geo-IP country
  device_risk_score: Float   # Known malicious patterns
}
```

### 4.2 Graph Edges

| Edge Type | From | To | Properties |
|-----------|------|-----|-----------|
| **HAS_ACCOUNT** | USER | ACCOUNT | linked_at, verified_at |
| **SENT_TO** | ACCOUNT | ACCOUNT | amount, txn_count, velocity_score |
| **IS_ON_DEVICE** | ACCOUNT,USER | DEVICE | first_seen, last_seen, login_count |
| **LOCATED_AT** | DEVICE | LOCATION | timestamp, frequency |
| **LINKED_WITH** | USER | USER | relationship_type, confidence |

---

## 5. Real-Time Processing Pipeline

### 5.1 Latency Requirements
- **Ingestion to Decision**: < 100ms (critical for blocking)
- **Graph Update**: < 10ms (must be sub-second)
- **Risk Scoring**: < 50ms
- **Alerts**: < 1s

### 5.2 Architecture

```
     Transactions              Graph DB
          │                        ▲
          ▼                        │
    ┌──────────────┐         ┌────────────┐
    │ Event Stream │    ┌──→ │  Neo4j     │
    │ (Kafka/AEH)  │    │    │  Aura      │
    └──────────────┘    │    └────────────┘
          │             │           ▲
          ▼             │           │
    ┌──────────────┐    │      ┌────────────┐
    │  Normalization   │      │ Incremental│
    │  Transformer     │      │  Graph     │
    └──────────────┘    │      │  Updates   │
          │             │      └────────────┘
          ▼             │           ▲
    ┌──────────────┐    │           │
    │  Window Agg  │    └───────────┤
    │  (5s window) │                │
    └──────────────┘                │
          │                         │
          ├─────────────────────────┘
          │
          ▼
    ┌──────────────────────┐
    │ GNN Detector         │
    │ (Batch: every 10s)   │
    └──────────────────────┘
          │
          ▼
    ┌──────────────────────┐
    │ Risk Scorer          │
    │ (Score each node)    │
    └──────────────────────┘
          │
          ▼
    ┌──────────────────────┐
    │ Decision Engine      │
    │ (Apply policies)     │
    └──────────────────────┘
          │
          ├─────────────────────────┬──────────────┬──────────────┐
          ▼                         ▼              ▼              ▼
      [ALLOW]                   [FLAG]          [BLOCK]       [ESCALATE]
     (Continue)                (Monitor)       (Freeze)      (SAR Case)
```

---

## 6. Implementation Phases (MVP Timeline)

### Phase 1: Foundation (Week 1-2)
**Deliverables**: Data ingestion + Graph construction
- [ ] Kafka/Event Hub topics for 5 channels
- [ ] Data normalization engine (PII hashing, deduplication)
- [ ] Neo4j Aura setup with schema
- [ ] Initial entity linking algorithm
- [ ] Graph population from historical data

### Phase 2: Detection (Week 3)
**Deliverables**: GNN model + Basic risk scoring
- [ ] GNN model training (GraphSAGE)
- [ ] Node embedding generation
- [ ] Mule ring classification head
- [ ] Risk scoring engine (velocity, diversity, geography)
- [ ] Unit tests for each module

### Phase 3: Real-Time Pipeline (Week 4)
**Deliverables**: Low-latency streaming + alerts
- [ ] Streaming transformer → Graph updates
- [ ] Real-time GNN inference (batch mode)
- [ ] Decision engine with policy rules
- [ ] Alert routing to SOC/Case management
- [ ] Dashboard with live metrics

### Phase 4: Hardening (Week 5-8)
**Deliverables**: Production-grade system
- [ ] Performance optimization (caching, indexing)
- [ ] High availability setup (multi-region)
- [ ] Compliance & audit trail
- [ ] Regulatory reporting module
- [ ] Privacy-safe intelligence sharing
- [ ] Production deployment & runbook

---

## 7. Technology Stack

| Layer | Component | Choice | Rationale |
|-------|-----------|--------|-----------|
| **Ingestion** | Streaming | Kafka / Azure Event Hubs | Low latency, scalable |
| **Processing** | Stream Processor | Kafka Streams / Spark Streaming | Python-friendly, GNN support |
| **Graph DB** | Graph Storage | Neo4j Aura / Azure Cosmos | Fast traversal, ACID transactions |
| **ML/GNN** | Framework | PyTorch Geometric / DGL | Mature, community support |
| **Compute** | Deployment | Docker / Azure Container Apps | Serverless, auto-scaling |
| **Orchestration** | Workflow | Kubernetes / Azure AKS | Production grade |
| **Monitoring** | Observability | Prometheus / Azure Monitor | Real-time metrics |
| **Language** | Primary | Python 3.11+ | Rich DS/ML ecosystem |

---

## 8. API Contracts

### 8.1 Ingest Transaction
```
POST /api/v1/transactions/ingest
Content-Type: application/json

{
  "source_account": "ACC_12345",
  "dest_account": "ACC_67890",
  "amount": 1000,
  "currency": "USD",
  "channel": "MOBILE",
  "timestamp": "2024-03-23T14:35:00Z",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "country": "US"
  }
}

Response:
{
  "transaction_id": "TXN_xyz123",
  "risk_score": 0.45,
  "decision": "ALLOW",
  "confidence": 0.87,
  "timestamp": "2024-03-23T14:35:00.123Z"
}
```

### 8.2 Query Graph
```
POST /api/v1/graph/query
Content-Type: application/json

{
  "query": "MATCH (u:User)-[r:HAS_ACCOUNT]->(a:Account) WHERE u.user_id = $userId RETURN u, a, r",
  "parameters": {
    "userId": "USER_123"
  }
}

Response:
{
  "nodes": [...],
  "edges": [...],
  "execution_time_ms": 45
}
```

### 8.3 Get Risk Score
```
GET /api/v1/users/{user_id}/risk-score

Response:
{
  "user_id": "USER_123",
  "risk_score": 0.72,
  "confidence": 0.89,
  "factors": {
    "velocity_score": 0.9,
    "account_diversity": 0.6,
    "geographic_inconsistency": 0.8,
    "structuring_pattern": 0.5,
    "jurisdiction_risk": 0.3
  },
  "decision": "BLOCK",
  "timestamp": "2024-03-23T14:35:00Z",
  "reasoning": "High-velocity transfers from newly created account with device fingerprint matching blocked user"
}
```

---

## 9. Compliance & Privacy

### 9.1 Audit Trail
- Every transaction decision logged with timestamp, model version, risk factors
- User consent & GDPR compliance (right to be forgotten, data portability)
- Two-factor approval for BLOCK decisions (human + AI)

### 9.2 Model Explainability
- SHAP values for each risk factor contribution
- Feature importance dashboard
- Regular model audit & bias assessment

### 9.3 Privacy-Safe Sharing
- Share anonymized threat intelligence (mule patterns) without PII
- Federated learning for cross-bank model improvement
- Differential privacy for aggregated statistics

---

## 10. Security Considerations

- **Data Encryption**: TLS for transit, AES-256 at rest
- **PII Handling**: Hash phone/email, mask transaction details
- **Access Control**: RBAC for analyst/admin operations
- **Rate Limiting**: Prevent API abuse
- **Model Poisoning**: Validate training data, detect adversarial inputs

---

## Next Steps

1. **Review [DATA_SPEC.md](DATA_SPEC.md)** for detailed schema
2. **Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** for sprint breakdown
3. **Read [API_CONTRACTS.md](API_CONTRACTS.md)** for endpoint specifications
4. **Deploy infrastructure** using templates in `infra/`
