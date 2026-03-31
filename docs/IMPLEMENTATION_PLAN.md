# Implementation Plan - MVP (1-2 Months)

## Overview

This document breaks down the MVP delivery into manageable phases, tasks, and checkpoints.

---

## Phase 1: Foundation & Data Infrastructure (Week 1-2)

### 1.1 Objective
Establish data ingestion pipeline, normalize disparate sources, and build graph foundation.

### 1.2 Tasks

#### Task 1.1: Set Up Event Streaming Infrastructure
- **Milestone**: Streaming topics ready for ingestion
- **Deliverables**:
  - [ ] Kafka cluster or Azure Event Hubs configured
  - [ ] 5 input topics: mobile_events, web_events, atm_events, upi_events, bank_events
  - [ ] Dead-letter queue for failed messages
  - [ ] Monitoring: dashboard showing msg/sec per topic
- **Acceptance Criteria**:
  - Can ingest 100 msg/sec per topic
  - End-to-end latency < 100ms
  - Data persisted for 30 days
- **Owner**: Data Engineering
- **Effort**: 3-4 days
- **Dependencies**: None

#### Task 1.2: Build Data Normalization Engine
- **Milestone**: All channel events mapped to standard schema
- **Deliverables**:
  - [ ] Normalization library (Python)
  - [ ] Channel-specific mappers (Mobile→Std, ATM→Std, etc.)
  - [ ] PII hashing (phone, email, document IDs)
  - [ ] Data quality checks (completeness, validity)
  - [ ] Unit tests with sample data from each channel
- **Acceptance Criteria**:
  - 100% of fields mapped correctly
  - No data loss
  - Hash functions produce consistent output
  - Data validation failures logged
- **Owner**: Data Engineering
- **Effort**: 4-5 days
- **Dependencies**: Task 1.1

#### Task 1.3: Set Up Neo4j Aura Graph Database
- **Milestone**: Graph DB ready with schema
- **Deliverables**:
  - [ ] Neo4j Aura instance created (dev tier for MVP)
  - [ ] Graph schema defined (nodes, relationships)
  - [ ] Indexes & constraints created (performance)
  - [ ] Backup & restore procedures documented
  - [ ] Access control (read/write roles)
- **Acceptance Criteria**:
  - Query performance: < 50ms for basic queries
  - Can load 1M nodes successfully
  - Backup runs in < 5 minutes
- **Owner**: Data Infrastructure
- **Effort**: 2-3 days
- **Dependencies**: None

#### Task 1.4: Build Entity Linking Engine
- **Milestone**: Account deduplication & resolution
- **Deliverables**:
  - [ ] Probabilistic entity matching (phone + email + device)
  - [ ] Blocking algorithm to reduce candidate pairs
  - [ ] Matching confidence scores
  - [ ] Unit tests & manual verification
- **Acceptance Criteria**:
  - Precision > 95% (false positive < 5%)
  - Recall > 90% (false negative < 10%)
  - Handles 1M+ accounts
  - Deterministic output (same input → same output)
- **Owner**: Data Science
- **Effort**: 4-5 days
- **Dependencies**: Task 1.2

#### Task 1.5: Historical Data Ingestion Pipeline
- **Milestone**: Graph populated with baseline data
- **Deliverables**:
  - [ ] Batch loader script (processes 1M+ transactions)
  - [ ] Data from last 6 months
  - [ ] Deduplicated entities
  - [ ] Relationships created
  - [ ] Data validation report
- **Acceptance Criteria**:
  - All historical data loaded
  - Graph consistent (no orphaned nodes)
  - Loader is idempotent (safe to re-run)
- **Owner**: Data Engineering
- **Effort**: 3 days
- **Dependencies**: Tasks 1.2, 1.3, 1.4

#### Task 1.6: Real-Time Graph Update Stream
- **Milestone**: Each new transaction updates graph in <10ms
- **Deliverables**:
  - [ ] Stream processor (Kafka Streams / Spark)
  - [ ] Incremental graph updates
  - [ ] Handles new users, accounts, devices
  - [ ] Duplicate transaction detection
  - [ ] Performance benchmarks
- **Acceptance Criteria**:
  - Update latency < 10ms
  - 99.9% transaction success rate
  - Handles 1000 txns/sec throughput
- **Owner**: Data Engineering
- **Effort**: 4-5 days
- **Dependencies**: Tasks 1.1, 1.3

#### Task 1.7: Phase 1 Testing & Validation
- **Milestone**: Foundation validated end-to-end
- **Deliverables**:
  - [ ] Integration tests (ingestion → normalization → graph)
  - [ ] Performance load tests
  - [ ] Data quality report
  - [ ] Documentation
- **Acceptance Criteria**:
  - All tests passing
  - Performance within SLA
- **Owner**: QA
- **Effort**: 2 days
- **Dependencies**: All Phase 1 tasks

---

## Phase 2: Detection & Risk Scoring (Week 3)

### 2.1 Objective
Build GNN model and risk scoring engine for mule detection.

### 2.2 Tasks

#### Task 2.1: Feature Engineering Pipeline
- **Milestone**: Node & edge features computed and available
- **Deliverables**:
  - [ ] Feature computation (user, account, transaction level)
  - [ ] Window aggregations (24h, 1h, 5m)
  - [ ] Anomaly scoring (velocity, geography)
  - [ ] Feature store (cache computed features)
  - [ ] Unit tests
- **Acceptance Criteria**:
  - All features computed within SLA
  - Features are statistically sound
  - No data leakage between train/test
- **Owner**: Data Science
- **Effort**: 4-5 days
- **Dependencies**: Phase 1

#### Task 2.2: GNN Model Development
- **Milestone**: Trained GNN for mule ring classification
- **Deliverables**:
  - [ ] Model architecture (GraphSAGE with 2 layers)
  - [ ] Training pipeline (PyTorch Geometric)
  - [ ] Train/val/test splits (70/15/15)
  - [ ] Hyperparameter tuning
  - [ ] Model card (architecture, performance, limitations)
- **Acceptance Criteria**:
  - F1-score > 0.85 on test set
  - Inference time < 50ms per batch
  - Model checkpoints saved
- **Owner**: ML Engineer
- **Effort**: 5-6 days
- **Dependencies**: Task 2.1

#### Task 2.3: Risk Scoring Engine
- **Milestone**: Composite risk scores for transactions & users
- **Deliverables**:
  - [ ] Component scorers (velocity, account_diversity, etc.)
  - [ ] Weighted combination logic
  - [ ] Risk thresholds (LOW: 0-0.3, MEDIUM: 0.3-0.7, HIGH: 0.7+)
  - [ ] Unit tests & validation
- **Acceptance Criteria**:
  - Scores calibrated (95% confidence intervals)
  - No NaN/Inf values
  - Scores between 0-1
- **Owner**: Data Science
- **Effort**: 3-4 days
- **Dependencies**: Task 2.1

#### Task 2.4: Model Explainability
- **Milestone**: Understand why model makes decisions
- **Deliverables**:
  - [ ] SHAP values for feature importance
  - [ ] Per-decision explanation
  - [ ] Feature contribution analysis
  - [ ] Bias audit (false positive rates by demographic)
- **Acceptance Criteria**:
  - Can explain top 5 factors for each decision
  - No systematic bias detected
- **Owner**: ML Engineer
- **Effort**: 3-4 days
- **Dependencies**: Task 2.2

#### Task 2.5: Phase 2 Testing & Validation
- **Milestone**: Model quality validated
- **Deliverables**:
  - [ ] Cross-validation on historical data
  - [ ] Backtest on recent transactions
  - [ ] ROC/AUC curves
  - [ ] False positive analysis
- **Acceptance Criteria**:
  - Model performance stable across time periods
- **Owner**: QA
- **Effort**: 2-3 days
- **Dependencies**: Tasks 2.1-2.4

---

## Phase 3: Real-Time Pipeline & Alerts (Week 4)

### 3.1 Objective
Build low-latency inference pipeline and decision engine.

### 3.2 Tasks

#### Task 3.1: Real-Time Inference Service
- **Milestone**: GNN predictions on live transactions
- **Deliverables**:
  - [ ] Inference API (REST/gRPC)
  - [ ] Batch inference (10s windows)
  - [ ] Caching layer (Redis)
  - [ ] Performance monitoring
- **Acceptance Criteria**:
  - Latency < 50ms p99
  - Throughput > 1000 req/sec
  - 99.99% availability
- **Owner**: ML Engineering
- **Effort**: 4-5 days
- **Dependencies**: Phase 2

#### Task 3.2: Decision Engine with Policy Rules
- **Milestone**: Translate risk scores to actions
- **Deliverables**:
  - [ ] Rule engine (score → ALLOW/FLAG/BLOCK)
  - [ ] Override capabilities (manual approval)
  - [ ] Appeal workflow
  - [ ] Configurable thresholds
- **Acceptance Criteria**:
  - Rules apply consistently
  - Manual overrides logged
- **Owner**: Backend
- **Effort**: 3-4 days
- **Dependencies**: Task 3.1

#### Task 3.3: Alert & Notification System
- **Milestone**: SOC receives high-priority alerts
- **Deliverables**:
  - [ ] Alert routing (Slack, PagerDuty, Jira)
  - [ ] Alert severity levels
  - [ ] Deduplication (no spam)
  - [ ] Escalation workflows
- **Acceptance Criteria**:
  - Alerts delivered within 5 seconds
  - < 5% false alert rate
- **Owner**: Backend
- **Effort**: 2-3 days
- **Dependencies**: Task 3.2

#### Task 3.4: Case Management Integration
- **Milestone**: Flagged accounts escalate to investigation
- **Deliverables**:
  - [ ] Case creation API
  - [ ] Link to graph visualization
  - [ ] Investigation notes & follow-up
  - [ ] Integration with existing CASE_DB
- **Acceptance Criteria**:
  - Cases created automatically for HIGH_RISK
  - Analysts can add notes/findings
- **Owner**: Backend
- **Effort**: 3-4 days
- **Dependencies**: Task 3.2

#### Task 3.5: Monitoring & Observability
- **Milestone**: Real-time health of detection system
- **Deliverables**:
  - [ ] Metrics dashboard (latency, throughput, alerts)
  - [ ] Logs aggregation (ELK/Loki)
  - [ ] Health checks & SLO tracking
  - [ ] Alerting for system issues
- **Acceptance Criteria**:
  - SLO defined and tracked
  - Can diagnose issues within 5 minutes
- **Owner**: DevOps
- **Effort**: 3-4 days
- **Dependencies**: All Phase 3 tasks

#### Task 3.6: Phase 3 Testing & Validation
- **Milestone**: End-to-end pipeline validated
- **Deliverables**:
  - [ ] Chaos engineering (failure scenarios)
  - [ ] Load testing (1000s txns/sec)
  - [ ] Failover testing
  - [ ] UAT with analysts
- **Acceptance Criteria**:
  - System handles failures gracefully
  - No data loss
  - Acceptable user experience
- **Owner**: QA + Product
- **Effort**: 3-4 days
- **Dependencies**: All Phase 3 tasks

---

## Phase 4: Production Hardening & Deployment (Week 5-8)

### 4.1 Objective
Enterprise-grade system ready for production.

### 4.2 Tasks

#### Task 4.1: Performance Optimization
- **Milestone**: System meets SLA under load
- **Deliverables**:
  - [ ] Query optimization (indexing, caching)
  - [ ] Feature computation optimization
  - [ ] Model serving optimization (quantization, batching)
  - [ ] Performance report
- **Owner**: DevOps + ML Eng
- **Effort**: 3-4 days

#### Task 4.2: High Availability & Failover
- **Milestone**: System survives component failures
- **Deliverables**:
  - [ ] Multi-region deployment
  - [ ] Database replication
  - [ ] Load balancing
  - [ ] Failover testing
- **Owner**: DevOps
- **Effort**: 4-5 days

#### Task 4.3: Compliance & Audit Trail
- **Milestone**: System meets regulatory requirements
- **Deliverables**:
  - [ ] Audit logging (all decisions logged)
  - [ ] Data encryption (AES-256 at rest, TLS in transit)
  - [ ] GDPR compliance (right to be forgotten)
  - [ ] Access control (RBAC)
  - [ ] Compliance documentation
- **Owner**: Security + Backend
- **Effort**: 4-5 days

#### Task 4.4: Regulatory Reporting Module
- **Milestone**: Generate SAR/CTF reports
- **Deliverables**:
  - [ ] Report templates (SAR, CTF, SR)
  - [ ] Risk score & confidence integration
  - [ ] Audit trail export
  - [ ] Digital signature support
  - [ ] API for regulator submission
- **Owner**: Compliance
- **Effort**: 4 days

#### Task 4.5: Privacy-Safe Intelligence Sharing
- **Milestone**: Share threat intelligence with peers
- **Deliverables**:
  - [ ] Anonymization pipeline (remove PII)
  - [ ] Mule pattern abstraction
  - [ ] Secure transmission (encrypted, signed)
  - [ ] Reciprocal intelligence ingestion
- **Owner**: Security + Product
- **Effort**: 3-4 days

#### Task 4.6: Model Governance & Monitoring
- **Milestone**: Model stays fair and effective over time
- **Deliverables**:
  - [ ] Model drift detection (performance degradation)
  - [ ] Retraining pipeline (automated)
  - [ ] A/B testing framework
  - [ ] Model versioning
  - [ ] Bias monitoring
- **Owner**: ML Eng + Data Science
- **Effort**: 4-5 days

#### Task 4.7: Documentation & Runbook
- **Milestone**: Operations team can manage system
- **Deliverables**:
  - [ ] Architecture guide
  - [ ] Runbook (deployment, troubleshooting)
  - [ ] API documentation
  - [ ] Analyst guide (using alerts, cases)
  - [ ] Training materials
- **Owner**: Technical Writer
- **Effort**: 3-4 days

#### Task 4.8: Production Deployment
- **Milestone**: System live in production
- **Deliverables**:
  - [ ] Infrastructure provisioned (Azure/AWS/GCP)
  - [ ] CI/CD pipelines configured
  - [ ] Secrets management (vaults)
  - [ ] Deployment runbook
  - [ ] Rollback procedures
- **Owner**: DevOps
- **Effort**: 2-3 days

---

## Gantt Chart

```
Week 1    Week 2    Week 3    Week 4    Week 5-8
├─────────┼─────────┼─────────┼─────────┼─────────────────┤

[Phase 1 Foundation]
├─ 1.1 Streaming ────┤
├─ 1.2 Normalization ─────┤
├─ 1.3 Graph DB ──┤
├─ 1.4 Entity Linking ────┤
├─ 1.5 Hist Data ─────┤
├─ 1.6 Real-time Updates ──────┤
├─ 1.7 Testing ────┤
                  [Phase 2 Detection]
                  ├─ 2.1 Features ─────┤
                  ├─ 2.2 GNN Model ────────┤
                  ├─ 2.3 Risk Scoring ─┤
                  ├─ 2.4 Explainability ──┤
                  ├─ 2.5 Testing ──┤
                              [Phase 3 Real-time]
                              ├─ 3.1 Inference ────┤
                              ├─ 3.2 Decision Engine ──┤
                              ├─ 3.3 Alerts ────┤
                              ├─ 3.4 Case Mgmt ──┤
                              ├─ 3.5 Monitoring ──┤
                              ├─ 3.6 Testing ──┤
                                          [Phase 4 Hardening]
                                          ├─ 4.1-4.8 Production prep ───┤
```

---

## Risk & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Graph DB performance issues | Medium | High | Early POC with 100M+ nodes; caching strategy |
| Data quality issues | High | Medium | Robust validation; data quality dashboard |
| GNN model underperforms | Medium | High | Multiple model architectures; ensemble approach |
| Real-time latency budget exceeded | Low | High | Performance optimization early; load testing |
| Production stability | Low | Critical | Chaos engineering; multi-region failover |
| Regulatory feedback late | Medium | High | Compliance engagement from Week 1 |

---

## Success Criteria (MVP)

By end of Week 8:

- ✅ **Functional**: Detects mule rings with 85%+ F1-score
- ✅ **Scalable**: Handles 1000+ txns/sec in <100ms
- ✅ **Reliable**: 99.9% uptime, <1% data loss
- ✅ **Compliant**: Full audit trail, GDPR-ready
- ✅ **Observable**: Metrics, logs, tracing visible
- ✅ **Documented**: Architecture, runbook, API docs

---

## KPIs to Track

- **Detection**: Precision, Recall, F1-score
- **Performance**: P50/P95/P99 latency, throughput
- **Reliability**: Uptime %, error rate
- **Business**: True alerts/day, false alarm rate, investigator time/case
- **Compliance**: % cases with full audit trail, SAR submission latency

---

**Next**: Review [API_CONTRACTS.md](API_CONTRACTS.md) for service interfaces.
