# 🚀 MuleGuard AI - Connect Your Backend in 3 Steps

## Current Status
✅ Dashboard fully functional with mock data  
✅ All features implemented and working  
✅ Backend integration ready to go  

---

## 🎯 Connect Your Backend (3 Steps)

### Step 1: Create `.env` File
```bash
cp .env.example .env
```

### Step 2: Configure Your Backend URL
Edit `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_ENABLE_MOCK_DATA=false
```

### Step 3: Restart Dev Server
```bash
npm run dev
```

**That's it!** Your dashboard now talks to your backend. 🎉

---

## 📋 What You Get

### ✅ Complete API Integration Layer
- HTTP client with automatic retries
- JWT token management
- Request/response interceptors
- Error handling
- Loading states

### ✅ Smart Data Service
- Switches between mock and real data
- No code changes needed
- Works exactly the same

### ✅ Ready-to-Use Hooks
```typescript
// Use in any component
import { useAccounts } from './hooks/useData';

function MyComponent() {
  const { data, loading, error } = useAccounts();
  // data automatically comes from your backend!
}
```

### ✅ UI Components
- Loading spinners
- Error messages
- Skeleton screens
- Network error handling

---

## 📚 Documentation

| File | Description |
|------|-------------|
| `BACKEND_READY.md` | Quick reference guide |
| `BACKEND_INTEGRATION.md` | Complete integration guide |
| `API_DOCUMENTATION.md` | Full API specification |
| `INTEGRATION_CHECKLIST.md` | Step-by-step checklist |
| `.env.example` | Environment configuration |

---

## 🔌 Backend API Requirements

Your backend needs these endpoints:

### Core Endpoints (Priority 1)
```
POST   /api/auth/login          # Authentication
GET    /api/accounts            # Account list
GET    /api/transactions        # Transaction list
GET    /api/clusters            # Mule ring clusters
GET    /api/alerts              # Alert list
GET    /api/graph               # Network graph data
```

### Extended Endpoints (Priority 2)
```
GET    /api/risk/jurisdictions  # Jurisdiction analysis
GET    /api/risk/ownership      # Ownership correlation
GET    /api/channels/flow       # Channel flow data
GET    /api/reports/risk-trend  # Risk trend data
GET    /api/intelligence/sharing # Intel sharing
```

See `API_DOCUMENTATION.md` for complete specification.

---

## 🧪 Testing

### 1. Test with Mock Data (Already Working)
```bash
npm run dev
# Dashboard works with mock data
```

### 2. Test with Your Backend
```bash
# Edit .env
VITE_ENABLE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost:8000/api

# Restart
npm run dev
```

### 3. Check Network Tab
- Open DevTools → Network
- Look for API calls to your backend
- Verify responses match expected format

---

## 🎨 Features Included

### Dashboard Analytics
- Real-time metrics
- GNN-based entity graph
- Live transaction stream
- Cross-channel flow visualization
- Alert monitoring

### Risk Scoring
- Jurisdiction-based analysis
- Ownership correlation
- Confidence scores
- Pattern detection

### Pattern Detection
- **Structuring**: Breaking large amounts
- **Fragmentation**: Splitting across accounts
- **Nesting**: Layered transactions
- **Rapid Movement**: High-velocity transfers

### Intelligence Sharing
- Privacy-safe sharing
- Partner collaboration
- Zero-knowledge protocols

### Compliance Reporting
- Regulator-ready reports
- Confidence scores
- Exportable data (PDF/CSV)

---

## 🔧 Configuration Options

### Environment Variables

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_MOCK_DATA=false      # false = use real API
VITE_ENABLE_LIVE_UPDATES=true    # Enable polling

# Polling Intervals
VITE_TRANSACTION_POLL_INTERVAL=3000   # 3 seconds
VITE_DASHBOARD_POLL_INTERVAL=10000    # 10 seconds

# API Behavior
VITE_API_TIMEOUT=30000            # 30 seconds
VITE_MAX_RETRY_ATTEMPTS=3         # Retry 3 times
```

---

## 💡 Usage Example

### Before (Mock Data)
```typescript
// Component automatically uses mock data
function Dashboard() {
  const { data: accounts } = useAccounts();
  // data comes from mockData.ts
}
```

### After (Real API)
```typescript
// Same code, but now uses real API!
function Dashboard() {
  const { data: accounts } = useAccounts();
  // data comes from your backend API
}
```

**No code changes needed!** Just flip the config. 🚀

---

## 🛠️ Troubleshooting

### Mock data still showing?
```bash
# Clear cache and restart
rm -rf node_modules/.vite
npm run dev
```

### CORS errors?
Add CORS middleware to your backend:
```python
# FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True
)
```

### 401 Unauthorized?
- Check backend is running
- Verify API URL is correct
- Test login endpoint first

---

## 📦 What's Included

### Files Created
```
src/app/
├── config/
│   ├── api.config.ts         ✅ API endpoints
│   └── config.ts             ✅ Feature flags
├── services/
│   ├── api.service.ts        ✅ HTTP client
│   └── data.service.ts       ✅ Data layer
├── hooks/
│   ├── useApi.ts             ✅ API hooks
│   └── useData.ts            ✅ Data hooks
└── components/ui/
    ├── loading.tsx           ✅ Loading states
    └── error.tsx             ✅ Error handling

Documentation/
├── BACKEND_READY.md          ✅ Quick start
├── BACKEND_INTEGRATION.md    ✅ Full guide
├── API_DOCUMENTATION.md      ✅ API spec
└── INTEGRATION_CHECKLIST.md  ✅ Checklist
```

### Packages Installed
```json
{
  "axios": "^1.14.0"  // HTTP client
}
```

---

## 🎯 Next Steps

1. **✅ Review Documentation**
   - Read `BACKEND_READY.md` for quick overview
   - Check `API_DOCUMENTATION.md` for API spec

2. **⏭️ Implement Backend**
   - Create required endpoints
   - Match response formats
   - Enable CORS

3. **⏭️ Configure & Test**
   - Create `.env` file
   - Set `VITE_ENABLE_MOCK_DATA=false`
   - Test integration

4. **⏭️ Deploy**
   - Build frontend: `npm run build`
   - Deploy `dist/` folder
   - Update production `.env`

---

## 🆘 Need Help?

1. Check `/BACKEND_INTEGRATION.md` for detailed guide
2. Review `/API_DOCUMENTATION.md` for endpoint specs
3. Use `/INTEGRATION_CHECKLIST.md` for step-by-step
4. Check browser console for error messages
5. Test API with curl/Postman first

---

## 🎉 You're Ready!

Everything is set up and waiting for your backend. The dashboard:

✅ Has all UI features implemented  
✅ Includes complete API integration layer  
✅ Handles loading and error states  
✅ Supports real-time updates  
✅ Works with mock data (current)  
✅ **Ready to connect to real API (3 steps above)** 🚀

---

**Made with ⚡ by Figma Make**
