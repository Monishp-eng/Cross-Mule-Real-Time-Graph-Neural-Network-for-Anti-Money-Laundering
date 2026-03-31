# API Contracts & Service Interfaces

## Overview

This document specifies the APIs for all major system components.

---

## 1. Transaction Ingestion API

### 1.1 Ingest Transaction

#### Endpoint
```
POST /api/v1/transactions/ingest
```

#### Request
```json
{
  "source_account": {
    "account_id": "ACC_12345",
    "channel": "MOBILE",
    "provider": "PayPal"
  },
  "dest_account": {
    "account_id": "ACC_67890",
    "channel": "BANK",
    "provider": "Chase"
  },
  "amount": 1000.00,
  "currency": "USD",
  "timestamp": "2024-03-23T14:35:00Z",
  "channel": "MOBILE",
  "transaction_metadata": {
    "device_id": "device_fingerprint_hash",
    "ip_address": "ip_hash",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "country": "US"
    }
  }
}
```

#### Response (Synchronous Decision)
```json
{
  "transaction_id": "TXN_abc123",
  "status": "COMPLETED",
  "decision": "ALLOW",
  "risk_score": 0.35,
  "confidence": 0.89,
  "processing_time_ms": 45,
  "factors": {
    "velocity_score": 0.3,
    "account_diversity": 0.2,
    "geographic_inconsistency": 0.1,
    "structuring_pattern": 0.0,
    "jurisdiction_risk": 0.4,
    "account_age_risk": 0.6
  },
  "timestamp": "2024-03-23T14:35:00.045Z"
}
```

#### Status Codes
| Code | Meaning |
|------|---------|
| 202 | ALLOW - Transaction approved |
| 202 | BLOCK - Transaction blocked (account frozen) |
| 202 | FLAG - Transaction approved but flagged for review |
| 202 | ESCALATE - Escalated to human review |
| 400 | Bad request (missing fields) |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## 2. Risk Scoring API

### 2.1 Get User Risk Score

#### Endpoint
```
GET /api/v1/users/{user_id}/risk-score
```

#### Query Parameters
```
?include_factors=true&time_window=24h
```

#### Response
```json
{
  "user_id": "USER_123",
  "overall_risk_score": 0.72,
  "confidence": 0.89,
  "risk_category": "HIGH",
  "decision": "BLOCK",
  "factors": {
    "velocity_score": {
      "value": 0.9,
      "contribution": 0.225,
      "reason": "50 transactions in 24 hours (baseline: 5)"
    },
    "account_diversity": {
      "value": 0.6,
      "contribution": 0.12,
      "reason": "15 linked accounts (baseline: 3)"
    },
    "geographic_inconsistency": {
      "value": 0.8,
      "contribution": 0.16,
      "reason": "Transactions in 3 countries within 24 hours"
    },
    "structuring_pattern": {
      "value": 0.5,
      "contribution": 0.075,
      "reason": "All transactions between $900-$1000"
    },
    "account_age": {
      "value": 0.7,
      "contribution": 0.07,
      "reason": "Account created 2 days ago"
    },
    "device_count": {
      "value": 0.8,
      "contribution": 0.08,
      "reason": "15 unique devices"
    }
  },
  "recommendation": "BLOCK + ESCALATE",
  "case_ids": ["CASE_001", "CASE_002"],
  "timestamp": "2024-03-23T14:35:00Z",
  "valid_until": "2024-03-23T15:35:00Z"
}
```

### 2.2 Get Account Risk Score

#### Endpoint
```
GET /api/v1/accounts/{account_id}/risk-score
```

#### Response
```json
{
  "account_id": "ACC_12345",
  "risk_score": 0.65,
  "confidence": 0.85,
  "velocity_score": 0.8,
  "account_age_days": 2,
  "incoming_txn_24h": 50,
  "outgoing_txn_24h": 45,
  "total_volume_24h": 45000,
  "linked_user": "USER_123",
  "devices": ["DEVICE_001", "DEVICE_002"],
  "high_risk_counterparties": 5
}
```

---

## 3. Graph Query API

### 3.1 Query Graph

#### Endpoint
```
POST /api/v1/graph/query
```

#### Request
```json
{
  "query": "MATCH (u:User {user_id: $userId})-[r:HAS_ACCOUNT]->(a:Account) RETURN u, r, a",
  "parameters": {
    "userId": "USER_123"
  },
  "limit": 100,
  "timeout_ms": 5000
}
```

#### Response
```json
{
  "nodes": [
    {
      "id": "USER_123",
      "type": "User",
      "properties": {
        "user_id": "USER_123",
        "kyc_score": 0.95,
        "risk_profile": "HIGH",
        "account_count": 5
      }
    },
    {
      "id": "ACC_12345",
      "type": "Account",
      "properties": {
        "account_id": "ACC_12345",
        "channel": "MOBILE",
        "balance": 5000,
        "status": "ACTIVE"
      }
    }
  ],
  "edges": [
    {
      "from": "USER_123",
      "to": "ACC_12345",
      "type": "HAS_ACCOUNT",
      "properties": {
        "linked_at": "2024-03-20T10:00:00Z",
        "confidence": 0.99
      }
    }
  ],
  "execution_time_ms": 45,
  "row_count": 5
}
```

### 3.2 Find Mule Ring

#### Endpoint
```
POST /api/v1/graph/mule-rings
```

#### Request
```json
{
  "account_id": "ACC_12345",
  "max_hops": 3,
  "include_features": true
}
```

#### Response
```json
{
  "ring_id": "RING_001",
  "center_account": "ACC_12345",
  "accounts": ["ACC_12345", "ACC_67890", "ACC_11111"],
  "total_flow": 50000,
  "pattern": "STAR",
  "confidence": 0.92,
  "nodes": [...],
  "edges": [...]
}
```

---

## 4. Investigation & Case Management API

### 4.1 Create Case

#### Endpoint
```
POST /api/v1/cases
```

#### Request
```json
{
  "case_type": "SUSPECTED_MULE_RING",
  "priority": "HIGH",
  "accounts": ["ACC_12345"],
  "reason": "High velocity, new account, structuring pattern",
  "assigned_to": "analyst_001"
}
```

#### Response
```json
{
  "case_id": "CASE_2024_001",
  "status": "OPEN",
  "created_at": "2024-03-23T14:35:00Z",
  "accounts": ["ACC_12345"],
  "graph_snapshot": {...}
}
```

### 4.2 Add Investigation Note

#### Endpoint
```
POST /api/v1/cases/{case_id}/notes
```

#### Request
```json
{
  "note": "Verified with customer. Claims unfamiliar transfers.",
  "severity": "CRITICAL",
  "recommendation": "FREEZE_ACCOUNT"
}
```

---

## 5. Compliance & Reporting API

### 5.1 Generate SAR Report

#### Endpoint
```
POST /api/v1/reports/sar
```

#### Request
```json
{
  "case_id": "CASE_2024_001",
  "report_type": "SAR",
  "format": "JSON"
}
```

#### Response
```json
{
  "report_id": "SAR_2024_001",
  "status": "DRAFT",
  "filing_institution": "Bank Name",
  "account_id": "ACC_12345",
  "aggregate_amount": 50000,
  "filing_deadline": "2024-04-22",
  "typology": "Structuring + Rapid Account Linking",
  "summary": "Multiple rapid transfers from newly created account to multiple wallets...",
  "supporting_evidence": [...],
  "confidence_score": 0.92,
  "created_at": "2024-03-23T14:35:00Z"
}
```

### 5.2 Generate Audit Report

#### Endpoint
```
GET /api/v1/reports/audit?start_date=2024-03-01&end_date=2024-03-31
```

#### Response
```json
{
  "period": "2024-03-01 to 2024-03-31",
  "summary": {
    "total_transactions": 1000000,
    "flagged_transactions": 15000,
    "blocked_transactions": 500,
    "escalated_cases": 50
  },
  "by_channel": {...},
  "alerts": [...]
}
```

---

## 6. Real-Time Streaming API

### 6.1 Subscribe to Alerts

#### Connection
```
WebSocket /api/v1/ws/alerts?auth_token=xyz
```

#### Alert Message
```json
{
  "event_type": "TRANSACTION_FLAGGED",
  "transaction_id": "TXN_abc123",
  "account_id": "ACC_12345",
  "risk_score": 0.85,
  "decision": "BLOCK",
  "severity": "CRITICAL",
  "timestamp": "2024-03-23T14:35:00.123Z",
  "action_required": true
}
```

---

## 7. Model & Configuration API

### 7.1 Model Status

#### Endpoint
```
GET /api/v1/model/status
```

#### Response
```json
{
  "version": "GNN_v2.1",
  "trained_at": "2024-03-20T10:00:00Z",
  "performance": {
    "precision": 0.92,
    "recall": 0.87,
    "f1_score": 0.89,
    "auc": 0.94
  },
  "latency_p99_ms": 48,
  "throughput_rps": 1200,
  "uptime_percent": 99.95,
  "data_drift_detected": false
}
```

### 7.2 Update Risk Thresholds

#### Endpoint
```
PUT /api/v1/config/risk-thresholds
```

#### Request
```json
{
  "thresholds": {
    "LOW": {"min": 0.0, "max": 0.3},
    "MEDIUM": {"min": 0.3, "max": 0.7},
    "HIGH": {"min": 0.7, "max": 1.0}
  },
  "action_map": {
    "LOW": "ALLOW",
    "MEDIUM": "FLAG",
    "HIGH": "BLOCK"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "BAD_REQUEST",
  "message": "Missing required field: source_account",
  "timestamp": "2024-03-23T14:35:00Z"
}
```

### 401 Unauthorized
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token",
  "timestamp": "2024-03-23T14:35:00Z"
}
```

### 429 Rate Limited
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Retry after 60 seconds.",
  "retry_after": 60,
  "timestamp": "2024-03-23T14:35:00Z"
}
```

### 500 Internal Error
```json
{
  "error": "INTERNAL_ERROR",
  "message": "Service temporarily unavailable",
  "trace_id": "trace_123abc",
  "timestamp": "2024-03-23T14:35:00Z"
}
```

---

## Rate Limiting

- **Ingest API**: 10,000 req/min per account
- **Query API**: 1,000 req/min per user
- **Reporting API**: 100 req/min per user

---

## Authentication

All endpoints require Bearer token:
```
Authorization: Bearer <jwt_token>
```

Token claims:
```json
{
  "sub": "user_123",
  "scp": ["transactions:read", "cases:write", "reports:read"],
  "exp": 1711190100
}
```

---

** Next**: Review starter code in `src/` directory.
