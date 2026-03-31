# Cross Mule Backend (Node.js + Express)

This backend is designed to match the frontend API contract used in:

- `High-Fidelity Web Dashboard UI/src/app/config/api.config.ts`
- Base URL: `http://localhost:8000/api`

No frontend files were modified.

## Features

- Express REST API with route structure aligned to frontend API config
- MongoDB via Mongoose (schemas for users, accounts, transactions, clusters, alerts, reports, partnerships)
- JWT authentication with refresh token flow
- Validation via `express-validator`
- CORS enabled for frontend origin
- Error handling and request logging
- Seed data for immediate frontend-compatible responses

## Quick Start

1. Install dependencies:

```bash
npm install
```

2. Configure environment:

```bash
cp .env.example .env
```

3. Start MongoDB (local or remote) and set `MONGO_URI` in `.env`.

4. Run backend:

```bash
npm run dev
```

Server starts at `http://localhost:8000`.

## Testing

Default smoke tests:

```bash
npm test
```

In-memory Mongo integration suite (no local MongoDB required):

```bash
RUN_INTEGRATION_TESTS=true MONGOMS_VERSION=7.0.14 npm run test:integration
```

Notes:

- The integration suite is intentionally gated behind `RUN_INTEGRATION_TESTS=true`.
- On first run, `mongodb-memory-server-core` downloads a MongoDB binary for your platform.

CI-friendly integration run (uses external MongoDB URI and skips binary download):

```bash
RUN_INTEGRATION_TESTS=true MONGO_URI=mongodb://127.0.0.1:27017 npm run test:integration
```

## API Docs

OpenAPI spec file:

- `docs/openapi.yaml`

Swagger UI endpoints:

- `GET /api-docs`
- `GET /api-docs.json`

## Docker Compose

From repository root (`Cross Mule Detection`):

```bash
docker compose up --build
```

Services started:

- `backend` on `http://localhost:8000`
- `mongo` on `mongodb://localhost:27017`

The compose file is at `../docker-compose.yml` and backend image definition is in `Dockerfile`.

## GitHub Actions

Two split workflows are included under `.github/workflows`:

- `backend-smoke.yml`: runs on every push/PR that touches backend files.
- `backend-integration.yml`: manual trigger (`workflow_dispatch`) for full integration test run.

## Frontend Connection

Frontend already points to:

- `VITE_API_BASE_URL=http://localhost:8000/api`

Auth token behavior supported:

- Access token expected in `Authorization: Bearer <token>`
- Refresh endpoint accepts `{ "refresh_token": "..." }`
- Refresh response returns `{ "token": "..." }` (as expected by frontend interceptor)

## Implemented Endpoints

### Auth
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`

### Accounts
- `GET /api/accounts`
- `GET /api/accounts/:id`
- `POST /api/accounts`
- `PUT /api/accounts/:id`
- `DELETE /api/accounts/:id`

### Transactions
- `GET /api/transactions`
- `GET /api/transactions/:id`
- `GET /api/transactions/live`
- `POST /api/transactions`
- `PUT /api/transactions/:id`
- `DELETE /api/transactions/:id`

### Clusters
- `GET /api/clusters`
- `GET /api/clusters/:id`

### Alerts
- `GET /api/alerts`
- `GET /api/alerts/:id`
- `PATCH /api/alerts/:id/status`
- `POST /api/alerts/:id/dismiss`

### Graph
- `GET /api/graph/nodes`
- `GET /api/graph/links`
- `GET /api/graph`

### Risk
- `GET /api/risk/distribution`
- `GET /api/risk/jurisdictions`
- `GET /api/risk/ownership`

### Channels
- `GET /api/channels/flow`
- `GET /api/channels/velocity`

### Reports
- `GET /api/reports/risk-trend`
- `GET /api/reports/complexity`
- `POST /api/reports/generate`
- `GET /api/reports/export?reportId=...&format=csv|pdf`

### Intelligence
- `GET /api/intelligence/sharing`
- `POST /api/intelligence/partnerships`

### Stats
- `GET /api/stats/dashboard`

### Generic aliases requested
- `GET /api/data`
- `POST /api/submit`

## Sample Auth Flow

```bash
# Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"secret123","name":"AML Analyst"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"secret123"}'

# Use token for protected endpoint
curl http://localhost:8000/api/accounts \
  -H "Authorization: Bearer <access_token>"
```

## Notes

- Data is auto-seeded on first startup if collections are empty.
- Most endpoints are auth-protected to match expected production usage.
