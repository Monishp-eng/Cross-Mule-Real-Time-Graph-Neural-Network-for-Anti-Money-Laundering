# MuleGuard AI - Backend API Specification

## Base URL
```
Development: http://localhost:8000/api
Production:  https://api.muleguard.ai/api
```

## Authentication

All requests except `/auth/login` and `/auth/signup` require JWT authentication.

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## 🔐 Authentication Endpoints

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@muleguard.ai",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "USR001",
    "email": "admin@muleguard.ai",
    "name": "Admin User",
    "role": "admin"
  }
}
```

### Signup
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "newuser@muleguard.ai",
  "password": "SecurePassword123",
  "name": "New User"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 📊 Accounts Endpoints

### Get All Accounts
```http
GET /accounts
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "ACC001",
    "name": "Account 1",
    "riskScore": 92,
    "type": "high-risk",
    "channels": ["UPI", "ATM", "Wallet"],
    "balance": 50000,
    "clusterId": "CLU001",
    "jurisdiction": "India",
    "owner": "John Doe",
    "confidenceScore": 0.95,
    "sanctionsMatch": true
  }
]
```

### Get Account by ID
```http
GET /accounts/:id
Authorization: Bearer <token>
```

---

## 💰 Transactions Endpoints

### Get All Transactions
```http
GET /transactions?page=1&limit=50&status=flagged
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50)
- `status` (optional): Filter by status (completed, pending, flagged)

**Response:**
```json
{
  "data": [
    {
      "id": "TXN001",
      "fromAccount": "ACC001",
      "toAccount": "ACC002",
      "amount": 15000,
      "channel": "UPI",
      "timestamp": "2026-03-29T10:30:00Z",
      "riskScore": 88,
      "status": "flagged",
      "pattern": "structuring",
      "complexity": 3,
      "sanctionsFlag": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "totalPages": 3
  }
}
```

### Get Live Transactions (for polling)
```http
GET /transactions/live
Authorization: Bearer <token>
```

Returns most recent transactions (last 5 minutes)

---

## 🔴 Clusters Endpoints

### Get All Clusters
```http
GET /clusters
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "CLU001",
    "name": "Mule Ring Alpha",
    "accountCount": 4,
    "totalAmount": 385000,
    "riskScore": 92,
    "detectedAt": "2026-03-28T10:00:00Z",
    "pattern": "structuring",
    "jurisdictions": ["India", "Singapore"],
    "confidenceScore": 0.94
  }
]
```

### Get Cluster Details
```http
GET /clusters/:id
Authorization: Bearer <token>
```

---

## 🚨 Alerts Endpoints

### Get All Alerts
```http
GET /alerts?status=new&severity=critical
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): Filter by status (new, investigating, resolved)
- `severity` (optional): Filter by severity (critical, high, medium, low)

**Response:**
```json
[
  {
    "id": "ALT001",
    "title": "High-Velocity Transaction Pattern",
    "description": "Cluster CLU001 showing rapid cross-channel transfers",
    "severity": "critical",
    "clusterId": "CLU001",
    "timestamp": "2026-03-29T10:00:00Z",
    "status": "new",
    "pattern": "structuring",
    "confidenceScore": 0.94,
    "sanctionsRelated": false
  }
]
```

### Update Alert Status
```http
PATCH /alerts/:id/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "investigating"
}
```

### Dismiss Alert
```http
POST /alerts/:id/dismiss
Authorization: Bearer <token>
```

---

## 🕸️ Graph Data Endpoints

### Get Complete Graph
```http
GET /graph
Authorization: Bearer <token>
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "ACC001",
      "label": "Account 1",
      "riskScore": 92,
      "size": 20,
      "color": "#ef4444",
      "clusterId": "CLU001"
    }
  ],
  "links": [
    {
      "source": "ACC001",
      "target": "ACC002",
      "value": 15,
      "animated": true
    }
  ]
}
```

### Get Nodes Only
```http
GET /graph/nodes
Authorization: Bearer <token>
```

### Get Links Only
```http
GET /graph/links
Authorization: Bearer <token>
```

---

## 📈 Risk Scoring Endpoints

### Get Risk Distribution
```http
GET /risk/distribution
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "range": "0-20",
    "count": 3,
    "severity": "Low"
  },
  {
    "range": "81-100",
    "count": 7,
    "severity": "Critical"
  }
]
```

### Get Jurisdiction Risks
```http
GET /risk/jurisdictions
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "jurisdiction": "India",
    "avgRisk": 72,
    "accounts": 8,
    "highRisk": 4
  },
  {
    "jurisdiction": "UAE",
    "avgRisk": 65,
    "accounts": 3,
    "highRisk": 2
  }
]
```

### Get Ownership Correlation
```http
GET /risk/ownership
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "owner": "John Doe",
    "accountCount": 3,
    "avgRisk": 88,
    "totalBalance": 145000,
    "jurisdictions": ["India", "Singapore"]
  }
]
```

---

## 🔄 Channel Flow Endpoints

### Get Channel Flow Data
```http
GET /channels/flow
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "from": "App",
    "to": "UPI",
    "value": 450000
  },
  {
    "from": "UPI",
    "to": "ATM",
    "value": 320000
  }
]
```

### Get Velocity Trend
```http
GET /channels/velocity
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "time": "00:00",
    "velocity": 42
  },
  {
    "time": "04:00",
    "velocity": 28
  }
]
```

---

## 📄 Reports Endpoints

### Get Risk Trend
```http
GET /reports/risk-trend?period=week
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` (optional): week, month, year

**Response:**
```json
[
  {
    "date": "Mon",
    "score": 68
  },
  {
    "date": "Tue",
    "score": 72
  }
]
```

### Get Complexity Data
```http
GET /reports/complexity
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "month": "Jan",
    "complexity": 45
  },
  {
    "month": "Feb",
    "complexity": 52
  }
]
```

### Generate Report
```http
POST /reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "reportType": "weekly",
  "startDate": "2026-03-01",
  "endDate": "2026-03-29",
  "clusters": ["CLU001", "CLU002"]
}
```

**Response:**
```json
{
  "reportId": "RPT001",
  "status": "generated",
  "downloadUrl": "/reports/export?reportId=RPT001&format=pdf"
}
```

### Export Report
```http
GET /reports/export?reportId=RPT001&format=pdf
Authorization: Bearer <token>
```

**Query Parameters:**
- `reportId`: Report ID from generate endpoint
- `format`: pdf or csv

**Response:** Binary file (PDF or CSV)

---

## 🤝 Intelligence Sharing Endpoints

### Get Sharing Partnerships
```http
GET /intelligence/sharing
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "INT001",
    "partner": "National Payment Corporation",
    "sharedAt": "2026-03-29T08:00:00Z",
    "clusterIds": ["CLU001", "CLU003"],
    "accountsShared": 7,
    "confidenceScore": 0.94,
    "status": "active"
  }
]
```

### Create Sharing Partnership
```http
POST /intelligence/partnerships
Authorization: Bearer <token>
Content-Type: application/json

{
  "partnerName": "Financial Intelligence Unit",
  "dataTypes": ["clusters", "transactions"],
  "jurisdictions": ["India", "UAE"]
}
```

---

## 📊 Statistics Endpoints

### Get Dashboard Stats
```http
GET /stats/dashboard
Authorization: Bearer <token>
```

**Response:**
```json
{
  "totalAccounts": 15,
  "totalTransactions": 12,
  "totalClusters": 3,
  "totalAlerts": 6,
  "highRiskAccounts": 7,
  "flaggedTransactions": 8,
  "sanctionsMatches": 1,
  "avgRiskScore": 62
}
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request parameters",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## 🔧 Rate Limiting

All endpoints are rate-limited:
- **Limit:** 1000 requests per hour per IP
- **Headers:**
  - `X-RateLimit-Limit`: 1000
  - `X-RateLimit-Remaining`: 945
  - `X-RateLimit-Reset`: 1711699200

When limit exceeded:
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Try again in 10 minutes.",
  "retryAfter": 600
}
```

---

## 🧪 Testing

### Using curl
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"test123"}'

# Get accounts
curl http://localhost:8000/api/accounts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman
Import collection: `/docs/MuleGuard_API.postman_collection.json` (to be provided)

---

## 📝 Notes

1. All timestamps are in ISO 8601 format (UTC)
2. All amounts are in INR (Indian Rupees)
3. Pagination uses 1-based indexing
4. Date formats: `YYYY-MM-DD` or `YYYY-MM-DDTHH:mm:ssZ`
5. Boolean values: `true` or `false` (lowercase)

---

## 🆘 Support

- API Documentation: https://docs.muleguard.ai
- Status Page: https://status.muleguard.ai
- Support Email: support@muleguard.ai
