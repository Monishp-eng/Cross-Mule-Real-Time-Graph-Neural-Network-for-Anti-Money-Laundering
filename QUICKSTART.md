# Quick Start Guide - Get Running in 10 Minutes

## Prerequisites Check

```bash
# Verify Python >= 3.11
python --version

# Check Git
git --version

# Azure CLI (if using Azure)
az --version
```

---

## 1. Clone & Setup (2 min)

```bash
# You should already be in the project directory
# cd Cross\ Mule\ Detection

# Create virtual environment
python -m venv venv

# Activate (choose based on your shell)
venv\Scripts\activate          # Windows CMD
.\venv\Scripts\Activate.ps1   # Windows PowerShell
source venv/bin/activate      # Git Bash / Linux / Mac

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep neo4j  # Should show neo4j version
```

---

## 2. Configure (2 min)

Create `.env` file:

```dotenv
# Neo4j
NEO4J_URI=bolt+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>

# Event Hub (if using Azure)
EVENTHUB_CONNECTION_STRING=Endpoint=sb://...

# Logging
LOG_LEVEL=INFO
```

---

## 3. Test End-to-End (3 min)

```bash
# Run main orchestrator
python src/orchestrator.py
```

Expected output:
```
Pipeline Results:
[
  {
    "status": "SUCCESS",
    "transaction_id": "MOB_...",
    "decision": "ALLOW",
    "risk_score": 0.35,
    "confidence": 0.89,
    ...
  }
]

Statistics: {...}
```

---

## 4. Run Unit Tests (2 min)

```bash
# Run all tests
pytest tests/ -v

# Specific module
pytest tests/test_normalizer.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 5. Start Services (Optional)

### Option A: Local Demo

```bash
# Terminal 1: Start event consumer
python src/data-ingestion/consumer.py

# Terminal 2: Start API server
python src/api/server.py --host 0.0.0.0 --port 8000

# Terminal 3: Send test events
python tests/send_test_events.py --count 100
```

Visit: http://localhost:8000/docs (SwaggerUI)

### Option B: Docker

```bash
# Build image
docker build -f Dockerfile -t mule-detector:latest .

# Run
docker run -p 8000:8000 \
  -e NEO4J_URI=$NEO4J_URI \
  -e NEO4J_PASSWORD=$NEO4J_PASSWORD \
  mule-detector:latest
```

---

## 6. Explore Code Structure

```
src/
├── data-ingestion/     # Channel normalization
│   └── normalizer.py   ← Start here
├── graph-builder/      # Neo4j updates
│   └── graph_builder.py
├── gnn-detector/       # ML model
│   └── gnn_detector.py
├── risk-scoring/       # Risk scoring
│   └── risk_scorer.py
└── orchestrator.py     ← Main flow

docs/
├── SYSTEM_DESIGN.md    ← Architecture
├── DATA_SPEC.md        ← Data models
└── IMPLEMENTATION_PLAN.md ← Sprint plan
```

---

## 7. Key Directories

| Directory | Purpose |
|-----------|---------|
| `docs/` | Design docs, API specs, data models |
| `src/` | Production code (normalizer, scorer, etc) |
| `tests/` | Unit & integration tests |
| `infra/` | CloudFormation/Bicep templates |
| `architecture/` | Architecture diagrams & reference |

---

## 8. Common Tasks

### Test a specific transaction type

```python
# test_mobile.py
from src.data_ingestion.normalizer import DataNormalizer

normalizer = DataNormalizer()

mobile_event = {
    "channel": "MOBILE",
    "raw_event": {
        "user_id": "USER_001",
        "transfer_to_wallet": "wallet_xyz",
        "transfer_amount": 1000,
        ...
    }
}

result = normalizer.normalize_event(mobile_event)
print(result.to_dict())
```

### Query the risk scorer

```python
from src.risk_scoring.risk_scorer import RiskScorer

scorer = RiskScorer()

result = scorer.score_transaction(
    current_txn_count_1h=50,
    unique_counterparties=30,
    locations_24h=[(40.7, -74.0, 0), (35.6, 139.7, 120)],
    time_gaps_minutes=[120],
    amounts=[1000, 950, 980],
    account_age_days=2,
    device_count=10,
    target_countries=["US"]
)

print(f"Risk: {result.overall_score:.2f}")
print(f"Decision: {result.recommendation}")
```

### Run GNN detection

```python
from src.gnn_detector.gnn_detector import SimpleGNNDetector

detector = SimpleGNNDetector()

result = detector.detect_mule_ring(
    anchor_account={"account_id": "ACC_001", ...},
    connected_accounts=[...],
    transaction_graph={}
)

print(f"Mule Probability: {result['mule_probability']:.3f}")
```

---

## 9. Next Steps

### For Backend Engineers
1. Start with [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
2. Implement Phase 1 from [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
3. Deploy to Azure using [infra/deployment.md](infra/deployment.md)

### For Data Scientists
1. Review [docs/DATA_SPEC.md](docs/DATA_SPEC.md) for features
2. Build GNN model: see `src/gnn-detector/train.py`
3. Evaluate on test set with performance metrics

### For DevOps
1. Review [infra/deployment.md](infra/deployment.md)
2. Set up Azure resources
3. Configure CI/CD pipeline

### For Product/Compliance
1. Read [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) section 9 (Compliance)
2. Review [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) for reporting APIs
3. Plan compliance requirements gathering

---

## 10. Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'neo4j'`

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: `Neo4j connection refused`

```bash
# Check URI and credentials
python -c "
import os
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)
print(driver.verify_connectivity())
"
```

### Issue: Tests fail

```bash
# Run with verbose output
pytest tests/test_normalizer.py -v -s

# Check test dependencies
pip install -r requirements-dev.txt
```

---

## 11. Documentation

| Document | For |
|----------|-----|
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Architecture, capabilities, design |
| [DATA_SPEC.md](docs/DATA_SPEC.md) | Data models, feature vectors |
| [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Sprint breakdown, tasks, timelines |
| [API_CONTRACTS.md](docs/API_CONTRACTS.md) | API endpoints, request/response |
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | Technology choices, trade-offs |
| [deployment.md](infra/deployment.md) | Deployment steps, troubleshooting |

---

## 12. Key Contacts & Resources

- **Architecture Questions**: → See [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
- **Implementation Help**: → See [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- **Deployment Issues**: → See [infra/deployment.md](infra/deployment.md)
- **API Usage**: → See [API_CONTRACTS.md](docs/API_CONTRACTS.md)

---

**You're ready!** Run:

```bash
python src/orchestrator.py
```

Should see ✅ SUCCESS messages. Happy coding!
