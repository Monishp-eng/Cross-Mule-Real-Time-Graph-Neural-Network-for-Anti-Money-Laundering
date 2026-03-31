# MuleGuard AI - Backend Integration Guide

## Overview

The MuleGuard AI dashboard is now fully prepared for backend integration. The application supports both **mock data mode** (for development) and **real API mode** (for production).

---

## Quick Start

### 1. Configuration

Create a `.env` file in the root directory (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` to configure your backend:

```env
# Your backend API URL
VITE_API_BASE_URL=http://localhost:8000/api

# Enable mock data (set to false for production)
VITE_ENABLE_MOCK_DATA=true

# Enable live updates
VITE_ENABLE_LIVE_UPDATES=true
```

### 2. Switch to Real API Mode

To connect to your backend, update `.env`:

```env
VITE_API_BASE_URL=https://your-backend-api.com/api
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_LIVE_UPDATES=true
```

---

## Architecture

### File Structure

```
src/app/
├── config/
│   ├── api.config.ts       # API endpoints configuration
│   └── config.ts           # Feature flags and environment config
├── services/
│   ├── api.service.ts      # Axios HTTP client with interceptors
│   └── data.service.ts     # Smart service (switches between mock/real)
├── hooks/
│   ├── useApi.ts           # Generic API hooks (loading, error states)
│   └── useData.ts          # Domain-specific data hooks
├── components/
│   └── ui/
│       ├── loading.tsx     # Loading spinners and skeletons
│       └── error.tsx       # Error display components
```

---

## Backend API Endpoints

Your backend should implement the following REST endpoints:

### Authentication
```
POST   /api/auth/login
POST   /api/auth/signup
POST   /api/auth/logout
POST   /api/auth/refresh
```

### Accounts
```
GET    /api/accounts
GET    /api/accounts/:id
```

### Transactions
```
GET    /api/transactions
GET    /api/transactions/:id
GET    /api/transactions/live
```

### Clusters (Mule Rings)
```
GET    /api/clusters
GET    /api/clusters/:id
```

### Alerts
```
GET    /api/alerts
GET    /api/alerts/:id
PATCH  /api/alerts/:id/status
POST   /api/alerts/:id/dismiss
```

### Graph Data
```
GET    /api/graph/nodes
GET    /api/graph/links
GET    /api/graph              # Returns { nodes, links }
```

### Risk Scoring
```
GET    /api/risk/distribution
GET    /api/risk/jurisdictions
GET    /api/risk/ownership
```

### Channel Flow
```
GET    /api/channels/flow
GET    /api/channels/velocity
```

### Reports
```
GET    /api/reports/risk-trend
GET    /api/reports/complexity
POST   /api/reports/generate
GET    /api/reports/export
```

### Intelligence Sharing
```
GET    /api/intelligence/sharing
POST   /api/intelligence/partnerships
```

### Statistics
```
GET    /api/stats/dashboard
```

---

## API Response Formats

### Account
```json
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
  "sanctionsMatch": false
}
```

### Transaction
```json
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
```

### Cluster
```json
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
```

### Alert
```json
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
```

### Graph Data
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

---

## Authentication

The API client automatically handles JWT tokens:

### Login Flow
```typescript
// User logs in
const response = await apiService.login({
  email: 'user@example.com',
  password: 'password123'
});

// Tokens are automatically stored
// All subsequent requests include Bearer token
```

### Token Storage
- **Access Token**: `localStorage.getItem('auth_token')`
- **Refresh Token**: `localStorage.getItem('refresh_token')`

### Auto-Refresh
The API client automatically refreshes expired tokens and retries failed requests.

---

## Using Data Hooks in Components

### Basic Data Fetching
```typescript
import { useAccounts } from '../hooks/useData';
import { LoadingSpinner } from './ui/loading';
import { ErrorCard } from './ui/error';

function AccountsList() {
  const { data: accounts, loading, error, refetch } = useAccounts();

  if (loading) return <LoadingSpinner message="Loading accounts..." />;
  if (error) return <ErrorCard error={error} onRetry={refetch} />;
  
  return (
    <div>
      {accounts?.map(account => (
        <div key={account.id}>{account.name}</div>
      ))}
    </div>
  );
}
```

### Live Data with Polling
```typescript
import { useLiveTransactions } from '../hooks/useData';

function LiveTransactionFeed() {
  const { data: transactions, loading, start, stop } = useLiveTransactions();
  
  return (
    <div>
      <button onClick={start}>Start Live Updates</button>
      <button onClick={stop}>Stop Live Updates</button>
      {/* Render transactions */}
    </div>
  );
}
```

### Mutations (Create, Update, Delete)
```typescript
import { useUpdateAlertStatus } from '../hooks/useData';
import { toast } from 'sonner';

function AlertCard({ alert }) {
  const { mutate, loading } = useUpdateAlertStatus();

  const handleResolve = async () => {
    await mutate(
      { id: alert.id, status: 'resolved' },
      {
        onSuccess: () => toast.success('Alert resolved'),
        onError: (error) => toast.error(error.message)
      }
    );
  };

  return (
    <div>
      <button onClick={handleResolve} disabled={loading}>
        {loading ? 'Resolving...' : 'Resolve Alert'}
      </button>
    </div>
  );
}
```

---

## Error Handling

### Automatic Retry
Failed requests are automatically retried up to 3 times for:
- Network errors
- 5xx server errors
- Timeout errors

### Error Display
```typescript
import { ErrorBanner, ErrorCard, NetworkError } from './ui/error';

// Inline error banner
{error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

// Full error card
{error && <ErrorCard error={error} onRetry={refetch} />}

// Network-specific error
{isNetworkError && <NetworkError onRetry={refetch} />}
```

---

## Loading States

### Spinners
```typescript
import { LoadingSpinner, LoadingCard, LoadingOverlay } from './ui/loading';

// Small inline spinner
<LoadingSpinner size="sm" />

// Card with loading state
<LoadingCard message="Loading data..." />

// Full-screen overlay
<LoadingOverlay message="Processing..." />
```

### Skeletons
```typescript
import { Skeleton, TableSkeleton, CardSkeleton } from './ui/loading';

// Custom skeleton
<Skeleton className="h-8 w-32" />

// Table skeleton
{loading && <TableSkeleton rows={10} />}

// Card skeleton
{loading && <CardSkeleton />}
```

---

## CORS Configuration

Your backend must allow CORS requests from the frontend:

```python
# Python/FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```javascript
// Node.js/Express example
const cors = require('cors');

app.use(cors({
  origin: ['http://localhost:5173', 'https://your-frontend.com'],
  credentials: true
}));
```

---

## WebSocket Support (Optional)

For real-time updates, implement WebSocket endpoints:

```
WS /ws/transactions    # Live transaction stream
WS /ws/alerts          # Real-time alert notifications
WS /ws/graph           # Graph updates
```

Update `.env`:
```env
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Testing Backend Integration

### 1. Start with Mock Data
```env
VITE_ENABLE_MOCK_DATA=true
```
Test UI functionality without backend dependency.

### 2. Switch to API Mode
```env
VITE_ENABLE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. Monitor Network Requests
Open browser DevTools → Network tab to inspect API calls.

### 4. Check Console for Errors
All API errors are logged to the console with full details.

---

## Production Deployment

### Environment Variables
```env
VITE_API_BASE_URL=https://api.mule guard.ai/v1
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_LIVE_UPDATES=true
VITE_ENV=production
```

### Build
```bash
npm run build
```

The build output will be in the `dist/` directory.

---

## Troubleshooting

### API calls fail with CORS error
- Ensure backend CORS is configured correctly
- Check `allow_credentials` is set to `true`

### Tokens not persisting
- Check localStorage is accessible
- Verify JWT tokens are valid format

### Mock data still showing after switching to API mode
- Clear browser cache
- Restart dev server
- Check `.env` file is loaded correctly

### Polling not working
- Set `VITE_ENABLE_LIVE_UPDATES=true` in `.env`
- Check network tab for periodic requests

---

## Support

For questions or issues:
1. Check browser console for error messages
2. Verify API endpoints match expected format
3. Test API endpoints with Postman/curl first
4. Enable verbose logging in development mode

---

**The dashboard is now 100% ready for backend integration!** 🚀

Simply update your `.env` file with the backend URL and set `VITE_ENABLE_MOCK_DATA=false` to connect.
