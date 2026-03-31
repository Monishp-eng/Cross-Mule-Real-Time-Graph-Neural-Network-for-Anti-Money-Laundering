# Data Specification & Schemas

## 1. Transaction Events

Input events from multiple channels standardized to common schema.

### 1.1 Standard Transaction Event

```json
{
  "event_type": "TRANSACTION",
  "event_id": "EVT_abc123def456",
  "timestamp": "2024-03-23T14:35:00.123Z",
  "transaction": {
    "txn_id": "TXN_xyz789",
    "source_account": {
      "account_id": "ACC_12345",
      "account_type": "WALLET",
      "channel": "MOBILE",
      "provider": "PayPal"
    },
    "dest_account": {
      "account_id": "ACC_67890",
      "account_type": "BANK_ACCOUNT",
      "channel": "BANK",
      "provider": "Chase"
    },
    "amount": {
      "value": 1000.00,
      "currency": "USD"
    },
    "status": "COMPLETED",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "country_code": "US",
      "city": "New York"
    },
    "device": {
      "device_id": "DEVICE_fingerprint_hash",
      "device_type": "MOBILE_APP",
      "ip_address": "hash_of_ip",
      "ip_country": "US"
    }
  }
}
```

### 1.2 Channel-Specific Event Mappings

**Mobile App Event**
```json
{
  "channel": "MOBILE",
  "raw_event": {
    "user_id": "MOBILE_USER_001",
    "app_version": "2.1.0",
    "transfer_to_wallet": "wallet_id_xyz",
    "transfer_amount": 1000,
    "transfer_time": "2024-03-23T14:35:00Z"
  },
  "normalized": {
    "source_account_id": "ACC_MOBILE_001",
    "dest_account_id": "ACC_WALLET_XYZ",
    "amount": 1000,
    "currency": "USD",
    "channel": "MOBILE"
  }
}
```

**ATM Event**
```json
{
  "channel": "ATM",
  "raw_event": {
    "terminal_id": "ATM_NYC_001",
    "card_number_last4": "1234",
    "withdrawal_amount": 500,
    "withdrawal_time": "2024-03-23T14:37:00Z",
    "location": {"lat": 40.7201, "lon": -74.0065}
  },
  "normalized": {
    "source_account_id": "ACC_DEBIT_1234",
    "dest_account_id": "ACC_CASH_NYC_001",  // Physical cash
    "amount": 500,
    "channel": "ATM",
    "location": {"latitude": 40.7201, "longitude": -74.0065, "country": "US"}
  }
}
```

**UPI Event**
```json
{
  "channel": "UPI",
  "raw_event": {
    "upi_id": "user@paytm",
    "recipient_upi": "merchant@okhdfcbank",
    "txn_amount": 2000,
    "txn_ref_id": "220399001089",
    "timestamp": "2024-03-23T14:35:00Z"
  },
  "normalized": {
    "source_account_id": "ACC_UPI_paytm",
    "dest_account_id": "ACC_UPI_okhdfcbank",
    "amount": 2000,
    "currency": "INR",
    "channel": "UPI"
  }
}
```

---

## 2. Graph Schema (Neo4j)

### 2.1 Node Types & Properties

#### USER Node
```cypher
CREATE CONSTRAINT unique_user_id ON (u:User) ASSERT u.user_id IS UNIQUE;

CREATE (u:User {
  user_id: "USER_001",
  kyc_status: "VERIFIED",              // UNVERIFIED, VERIFIED, REJECTED
  kyc_score: 0.95,                      // 0-1, higher = more verified
  phone_hash: "sha256_hash",
  email_hash: "sha256_hash",
  document_id_hash: "sha256_hash",
  account_count: 5,                     // Number of linked accounts
  created_at: timestamp(),
  updated_at: timestamp(),
  countries: ["US", "UK"],              // Countries of activity
  risk_profile: "LOW",                  // LOW, MEDIUM, HIGH, BLOCKED
  is_blocked: false,
  block_reason: null,
  metadata: {
    source_system: "KYC_DB",
    confidence: 0.99
  }
});
```

#### ACCOUNT Node
```cypher
CREATE CONSTRAINT unique_account_id ON (a:Account) ASSERT a.account_id IS UNIQUE;

CREATE (a:Account {
  account_id: "ACC_12345",
  channel: "MOBILE",                    // MOBILE, WEB, ATM, UPI, BANK
  account_type: "WALLET",               // WALLET, CARD, BANK_ACCOUNT, CRYPTO
  provider: "PayPal",
  status: "ACTIVE",                     // ACTIVE, SUSPENDED, BLOCKED, CLOSED
  balance: 5000.00,
  created_at: timestamp(),
  linked_at: timestamp(),               // When user linked this account
  transaction_count: 42,
  last_transaction_at: timestamp(),
  risk_score: 0.45,                     // Calculated score for this account
  is_new: false,                        // Created < 7 days?
  high_velocity: false                  // > 10 txns/hour?
});
```

#### TRANSACTION Node
```cypher
CREATE (t:Transaction {
  txn_id: "TXN_xyz789",
  amount: 1000.00,
  currency: "USD",
  timestamp: timestamp(),
  channel: "MOBILE",
  status: "COMPLETED",                  // COMPLETED, PENDING, FAILED, BLOCKED
  velocity_score: 0.75,                 // Anomaly vs. baseline
  location: {
    latitude: 40.7128,
    longitude: -74.0060,
    country: "US"
  }
});
```

#### DEVICE Node
```cypher
CREATE CONSTRAINT unique_device_id ON (d:Device) ASSERT d.device_id IS UNIQUE;

CREATE (d:Device {
  device_id: "device_fingerprint_hash",
  device_type: "MOBILE_APP",            // MOBILE_APP, WEB, ATM_TERMINAL
  ip_address_hash: "ip_hash",
  user_agent_hash: "ua_hash",
  country: "US",
  risk_score: 0.3,
  is_known_malicious: false,
  first_seen: timestamp(),
  last_seen: timestamp(),
  account_count: 15                     // Number of accounts from this device
});
```

#### LOCATION Node (Optional)
```cypher
CREATE (loc:Location {
  location_id: "LOC_NYC_ATM_001",
  latitude: 40.7201,
  longitude: -74.0065,
  country: "US",
  city: "New York",
  location_type: "ATM",                 // ATM, BRANCH, MERCHANT
  transaction_count_24h: 250,
  suspicious_activity_flag: false
});
```

### 2.2 Relationship Types & Properties

#### HAS_ACCOUNT (USER → ACCOUNT)
```cypher
CREATE (u:User)-[r:HAS_ACCOUNT {
  linked_at: timestamp(),
  verified_at: timestamp(),
  is_primary: true,
  linked_devices: ["device1_id", "device2_id"],
  confidence: 0.99                      // Confidence of linkage
}]->(a:Account);
```

#### SENT_TO (ACCOUNT → ACCOUNT)
```cypher
CREATE (src:Account)-[r:SENT_TO {
  amount: 1000.00,
  txn_count: 5,                         // Number of transfers
  velocity_score: 0.85,
  frequency: "HIGH",                    // LOW, MEDIUM, HIGH
  first_txn: timestamp(),
  last_txn: timestamp(),
  time_window_minutes: 120              // Span between first & last
}]->(dst:Account);
```

#### IS_ON_DEVICE (USER/ACCOUNT → DEVICE)
```cypher
CREATE (u:User)-[r:IS_ON_DEVICE {
  first_seen: timestamp(),
  last_seen: timestamp(),
  login_count: 150,
  suspicious_activity: false
}]->(d:Device);
```

#### LOCATED_AT (DEVICE → LOCATION)
```cypher
CREATE (d:Device)-[r:LOCATED_AT {
  timestamp: timestamp(),
  duration_minutes: 10,
  frequency: 1                          // Transaction count at this location
}]->(loc:Location);
```

#### LINKED_WITH (USER → USER)
```cypher
CREATE (u1:User)-[r:LINKED_WITH {
  relationship_type: "SAME_DEVICE",     // SAME_DEVICE, SHARED_EMAIL, SHARED_ADDRESS
  confidence: 0.92,
  linked_since: timestamp(),
  evidence: ["ip_match", "device_fingerprint"]
}]->(u2:User);
```

---

## 3. Feature Vectors for GNN

### 3.1 Node Features

#### User Features
```python
user_features = {
    # Account-level aggregates
    'num_accounts': 5,
    'total_balance': 15000.0,
    'account_age_days': 30,
    
    # Transaction-level
    'total_volume_24h': 50000.0,
    'transaction_count_24h': 120,
    'avg_transaction_amount': 416.67,
    'transaction_frequency_per_hour': 5.0,
    
    # Risk indicators
    'velocity_score': 0.92,              # High velocity
    'account_diversity': 0.8,            # Connects to many accounts
    'geographic_variance': 0.95,         # High (3+ countries)
    'device_count': 15,
    'is_new_account': True,              # Created < 7 days
    'has_multiple_devices': True,
    
    # KYC
    'kyc_score': 0.95,
    'kyc_verified_days_ago': 1,
    
    # Historical
    'avg_activity_level': 0.5,           # Baseline activity
    'current_activity_level': 0.95       # Current activity
}
```

#### Account Features
```python
account_features = {
    'account_age_days': 2,
    'balance': 100.0,
    'incoming_txn_count_24h': 50,
    'outgoing_txn_count_24h': 45,
    'total_volume_24h': 12000.0,
    'avg_transaction_amount': 240.0,
    'transaction_frequency': 1.875,      # txns per hour
    'unique_counterparties_24h': 38,
    'velocity_score': 0.88,
    'high_risk_correlations': 5,         # Transfers to high-risk accounts
    'is_high_velocity': True,
    'channel': 0,                        # One-hot: MOBILE=0
    'kyc_linked': True
}
```

### 3.2 Edge Features

#### SENT_TO Edge Features
```python
edge_features = {
    'amount': 1000.0,
    'time_to_transfer_minutes': 5,       # How quickly after receiving
    'transfer_frequency': 10,            # Times transferred today
    'amount_percentage': 0.5,            # 50% of sender's balance
    'counterparty_risk_score': 0.75,
    'structuring_score': 0.65,           # Fragmentation pattern
    'temporal_anomaly': 0.8,             # Unusual timing
    'geographic_jump': 0.9               # Large geographic distance
}
```

---

## 4. Aggregation Windows

For computing time-series features:

```python
WINDOWS = {
    '24h': {
        'transactions': [txn for txn in recent if (now - txn.time).days < 1],
        'features': ['total_volume', 'txn_count', 'avg_amount', 'velocity']
    },
    '1h': {
        'transactions': [txn for txn in recent if (now - txn.time).minutes < 60],
        'features': ['velocity_score', 'structuring_pattern']
    },
    '5m': {
        'transactions': [txn for txn in recent if (now - txn.time).seconds < 300],
        'features': ['real_time_anomaly']
    }
}
```

---

## 5. Risk Factor Scoring

### 5.1 Component Scores (0-1 scale)

```python
RISK_COMPONENTS = {
    'velocity_score': {
        # Transaction frequency anomaly
        'baseline': user.avg_hourly_txns,
        'current': txn_count_last_hour,
        'score': min(current / (baseline + 0.1), 1.0),  # Normalize to 0-1
        'weight': 0.25                                   # 25% of total
    },
    
    'account_diversity': {
        # How many different accounts linked?
        'unique_accounts': len(set(txn.counterparty for txn in txns)),
        'score': min(unique_accounts / 50, 1.0),
        'weight': 0.20
    },
    
    'geographic_inconsistency': {
        # Impossible geography check
        'countries_24h': len(set(txn.location.country for txn in txns)),
        'max_distance_km': max distance between successive txns
        'min_time_between_km': time to cover max_distance
        'physically_possible': max_distance_km / min_time_between_km <= airplane_speed
        'score': 0.95 if not physically_possible else 0.2,
        'weight': 0.20
    },
    
    'structuring_pattern': {
        # Fragmentation into small amounts
        'amounts': [txn.amount for txn in txns],
        'avg_amount': mean(amounts),
        'is_structured': all(amt < threshold for amt in amounts),
        'score': 0.88 if is_structured else 0.1,
        'weight': 0.15
    },
    
    'account_age': {
        # Fresh accounts higher risk
        'days_old': (now - account.created_at).days,
        'score': max(0, 1.0 - (days_old / 30)),       # Decays over 30 days
        'weight': 0.10
    },
    
    'device_count': {
        # Many devices = higher risk
        'device_ids': len(set(txn.device_id for txn in txns)),
        'score': min(device_ids / 10, 1.0),
        'weight': 0.10
    }
}

# Composite score
total_weight = sum(component['weight'] for component in RISK_COMPONENTS.values())
risk_score = sum(
    (component['score'] * component['weight']) / total_weight
    for component in RISK_COMPONENTS.values()
)
```

---

## 6. Data Quality Checks

```python
DATA_QUALITY_CHECKS = {
    'completeness': {
        'required_fields': ['source_account', 'dest_account', 'amount', 'timestamp'],
        'acceptable_missing_rate': 0.01  # 1% allowed
    },
    'validity': {
        'amount_range': (0.01, 1000000),
        'timestamp_skew_minutes': 60  # Must be within 60 min of ingestion
    },
    'uniqueness': {
        'duplicate_check': 'txn_id',
        'duplicate_tolerance': 0.001  # 0.1% allowed
    },
    'distribution': {
        'amount_median_change_factor': 10,  # Alert if median changes >10x
        'velocity_p99_threshold': 100       # Alert if p99 > 100 txns/hour
    }
}
```

---

## 7. Example Graph Queries

### Query 1: Find All Accounts of a User
```cypher
MATCH (u:User {user_id: "USER_123"})-[r:HAS_ACCOUNT]->(a:Account)
RETURN u, r, a
ORDER BY r.linked_at DESC;
```

### Query 2: Detect Transaction Chains (Laundering Pattern)
```cypher
MATCH (acc1:Account)-[r1:SENT_TO]->(acc2:Account)
      -[r2:SENT_TO]->(acc3:Account)
      -[r3:SENT_TO]->(acc4:Account)
WHERE r1.timestamp < r2.timestamp 
  AND r2.timestamp < r3.timestamp
  AND (r3.timestamp - r1.timestamp) < 3600  // Within 1 hour
RETURN acc1, acc2, acc3, acc4, r1, r2, r3;
```

### Query 3: Find Accounts on Same Device (Ring Detection)
```cypher
MATCH (acc1:Account)-[r1:IS_ON_DEVICE]->(dev:Device)<-[r2:IS_ON_DEVICE]-(acc2:Account)
WHERE acc1.account_id < acc2.account_id  // Avoid duplicates
  AND acc1.channel != acc2.channel       // Different channels
RETURN acc1, acc2, dev
     ORDER BY dev.account_count DESC;
```

### Query 4: High-Risk Account Neighborhood
```cypher
MATCH (acc:Account {account_id: "ACC_123"})-[r:SENT_TO|RECEIVED_FROM]-(neighbor:Account)
WHERE r.velocity_score > 0.7
RETURN acc, neighbor, r
ORDER BY r.velocity_score DESC
LIMIT 20;
```

---

## 8. Data Retention & Compliance

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Transactions | 7 years | Regulatory requirement (AML) |
| User KYC | 5 years | GDPR, can request deletion after |
| Device fingerprints | 90 days | Risk assessment, then purge |
| Investigation cases | 10 years | Audit trail for regulators |
| Model training data | 2 years | Retraining & bias audits |

---

**Next**: Review [API_CONTRACTS.md](API_CONTRACTS.md) for service endpoints.
