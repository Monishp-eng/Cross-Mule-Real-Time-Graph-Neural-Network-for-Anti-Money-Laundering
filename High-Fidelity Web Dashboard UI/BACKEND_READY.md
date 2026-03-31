# Backend Integration - Quick Reference

## 🚀 Your Dashboard is Backend-Ready!

All components now support both **mock data** (current) and **real API** (production) modes.

---

## ⚙️ Configuration

### Step 1: Create `.env` file
```bash
cp .env.example .env
```

### Step 2: Configure Backend URL
```env
# Development - Use Mock Data
VITE_API_BASE_URL=http://localhost:8000/api
VITE_ENABLE_MOCK_DATA=true

# Production - Use Real API
VITE_API_BASE_URL=https://api.yourbackend.com
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_LIVE_UPDATES=true
```

---

## 📚 Key Files Created

### Configuration
- `/src/app/config/api.config.ts` - API endpoints
- `/src/app/config/config.ts` - Feature flags
- `/.env.example` - Environment template

### Services
- `/src/app/services/api.service.ts` - HTTP client (Axios)
- `/src/app/services/data.service.ts` - Smart data layer

### Hooks
- `/src/app/hooks/useApi.ts` - Generic API hooks
- `/src/app/hooks/useData.ts` - Domain-specific hooks

### UI Components
- `/src/app/components/ui/loading.tsx` - Loading states
- `/src/app/components/ui/error.tsx` - Error handling

### Documentation
- `/BACKEND_INTEGRATION.md` - Complete integration guide

---

## 🔌 How It Works

### Current Mode: Mock Data
```typescript
// src/app/config/config.ts
useMockData: true  // Returns mock data from mockData.ts
```

### Production Mode: Real API
```typescript
// .env
VITE_ENABLE_MOCK_DATA=false

// Automatically switches to real API calls
// All components work exactly the same!
```

---

## 💡 Example Usage

### In Any Component
```typescript
import { useAccounts, useTransactions } from '../hooks/useData';
import { LoadingSpinner } from './ui/loading';
import { ErrorCard } from './ui/error';

function MyComponent() {
  const { data: accounts, loading, error, refetch } = useAccounts();
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorCard error={error} onRetry={refetch} />;
  
  return <div>{/* Render accounts */}</div>;
}
```

### Live Data Polling
```typescript
import { useLiveTransactions } from '../hooks/useData';

function LiveFeed() {
  const { data, start, stop } = useLiveTransactions();
  // Auto-updates every 3 seconds!
}
```

---

## 🎯 Backend Requirements

Your backend needs to implement these endpoints:

### Core Endpoints
```
POST   /api/auth/login
GET    /api/accounts
GET    /api/transactions
GET    /api/clusters
GET    /api/alerts
GET    /api/graph
GET    /api/risk/jurisdictions
GET    /api/intelligence/sharing
GET    /api/reports/risk-trend
```

See `/BACKEND_INTEGRATION.md` for complete API specification.

---

## 🔄 Data Flow

```
Component → useData Hook → dataService → 
  ↓
  ├─ Mock Mode → mockData.ts (instant)
  └─ API Mode  → apiService → Backend API
```

---

## ✅ Features Included

- ✅ Automatic token management (JWT)
- ✅ Token refresh on expiry
- ✅ Request retry (3 attempts)
- ✅ Loading states
- ✅ Error handling
- ✅ Live data polling
- ✅ Request/response interceptors
- ✅ CORS support
- ✅ TypeScript types
- ✅ Mock data fallback

---

## 🧪 Testing

### Test with Mock Data (Current)
```bash
# Already working!
npm run dev
```

### Test with Backend
```bash
# 1. Update .env
VITE_ENABLE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost:8000/api

# 2. Start backend server
# 3. Refresh browser
```

---

## 🛠️ Troubleshooting

### Mock data not switching off?
```bash
# Clear cache and restart
rm -rf node_modules/.vite
npm run dev
```

### CORS errors?
Add to your backend:
```python
# FastAPI
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### Check API calls
Open DevTools → Network tab → Filter: XHR

---

## 📖 Full Documentation

Read `/BACKEND_INTEGRATION.md` for:
- Complete API specification
- Request/response formats
- Authentication flow
- WebSocket support
- Production deployment
- Advanced patterns

---

## 🎉 You're All Set!

**Current Status**: Dashboard runs with mock data
**To Connect Backend**: 
1. Create `.env` file
2. Set `VITE_ENABLE_MOCK_DATA=false`
3. Set `VITE_API_BASE_URL=your-api-url`
4. Restart dev server

**Zero code changes needed!** 🚀
