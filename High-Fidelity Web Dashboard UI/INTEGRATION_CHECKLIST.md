# ✅ Backend Integration Checklist

## Pre-Integration Setup

- [x] **API Service Layer Created**
  - `src/app/services/api.service.ts` - Axios HTTP client
  - Automatic token management
  - Request/response interceptors
  - Auto-retry on failure

- [x] **Data Service Layer Created**
  - `src/app/services/data.service.ts` - Mock/Real data switcher
  - Simulates API delays in mock mode
  - Zero code changes to switch modes

- [x] **Custom Hooks Created**
  - `src/app/hooks/useApi.ts` - Generic API hooks
  - `src/app/hooks/useData.ts` - Domain-specific hooks
  - Loading states
  - Error handling
  - Polling support

- [x] **UI Components Created**
  - `src/app/components/ui/loading.tsx` - Spinners, skeletons
  - `src/app/components/ui/error.tsx` - Error displays
  - Network error handling

- [x] **Configuration Files Created**
  - `src/app/config/api.config.ts` - API endpoints
  - `src/app/config/config.ts` - Feature flags
  - `.env.example` - Environment template
  - `.env.local.example` - Local config example

- [x] **Documentation Created**
  - `BACKEND_INTEGRATION.md` - Complete integration guide
  - `BACKEND_READY.md` - Quick reference
  - `API_DOCUMENTATION.md` - Full API spec

---

## Backend Requirements

### Must Implement

- [ ] **Authentication Endpoints**
  - `POST /api/auth/login`
  - `POST /api/auth/signup`
  - `POST /api/auth/refresh`

- [ ] **Core Data Endpoints**
  - `GET /api/accounts`
  - `GET /api/transactions`
  - `GET /api/clusters`
  - `GET /api/alerts`
  - `GET /api/graph`

- [ ] **Risk Analysis Endpoints**
  - `GET /api/risk/distribution`
  - `GET /api/risk/jurisdictions`
  - `GET /api/risk/ownership`

- [ ] **Channel & Reports**
  - `GET /api/channels/flow`
  - `GET /api/reports/risk-trend`
  - `GET /api/intelligence/sharing`

### Backend Configuration

- [ ] **CORS Enabled**
  ```
  Allow-Origin: http://localhost:5173 (dev)
  Allow-Credentials: true
  Allow-Methods: GET, POST, PATCH, DELETE
  Allow-Headers: Authorization, Content-Type
  ```

- [ ] **JWT Authentication**
  - Issue JWT tokens on login
  - Accept `Authorization: Bearer <token>` header
  - Return 401 when token expired

- [ ] **Response Format**
  - Return data as JSON
  - Use ISO 8601 for dates
  - Include error messages

- [ ] **Status Codes**
  - 200: Success
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized
  - 404: Not Found
  - 500: Server Error

---

## Frontend Configuration

### Development Mode (Mock Data)

- [x] **Current Configuration**
  ```env
  VITE_ENABLE_MOCK_DATA=true
  VITE_API_BASE_URL=http://localhost:8000/api
  ```

- [x] **Testing**
  - Dashboard loads successfully
  - All views display mock data
  - No API calls made

### Production Mode (Real API)

- [ ] **Update Environment**
  1. Create `.env` file in project root
  2. Copy from `.env.example`
  3. Set values:
     ```env
     VITE_API_BASE_URL=http://localhost:8000/api
     VITE_ENABLE_MOCK_DATA=false
     VITE_ENABLE_LIVE_UPDATES=true
     ```
  4. Restart dev server: `npm run dev`

- [ ] **Verify Configuration**
  - [ ] Check browser console for API calls
  - [ ] Verify correct base URL in Network tab
  - [ ] Confirm Authorization headers present

---

## Integration Testing

### Step 1: Backend Health Check

- [ ] Backend server running
- [ ] Can access `/api/health` or root endpoint
- [ ] CORS headers present in response

### Step 2: Authentication

- [ ] Login endpoint returns JWT token
- [ ] Token stored in localStorage
- [ ] Subsequent requests include Bearer token
- [ ] Token refresh works on expiry

### Step 3: Data Endpoints

- [ ] `/api/accounts` returns array of accounts
- [ ] `/api/transactions` returns transaction list
- [ ] `/api/clusters` returns mule ring clusters
- [ ] `/api/alerts` returns alert list
- [ ] `/api/graph` returns nodes and links

### Step 4: Real-Time Features

- [ ] Live transactions polling works
- [ ] Dashboard stats update periodically
- [ ] New alerts appear automatically

### Step 5: Error Handling

- [ ] Network errors display error message
- [ ] Invalid token triggers login redirect
- [ ] 404 errors show "Not Found" message
- [ ] Retry button works on errors

### Step 6: Loading States

- [ ] Spinners show while loading
- [ ] Skeleton screens on initial load
- [ ] Loading indicators on mutations

---

## Common Issues & Solutions

### Issue: CORS Error

**Symptom:** 
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
```python
# Backend (FastAPI example)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Mock Data Still Showing

**Symptom:** Mock data displays even with `VITE_ENABLE_MOCK_DATA=false`

**Solution:**
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Restart dev server
4. Check `.env` file is in project root

### Issue: 401 Unauthorized

**Symptom:** All API requests return 401

**Solution:**
1. Check token in localStorage
2. Verify Authorization header format
3. Confirm token not expired
4. Test login endpoint first

### Issue: Endpoints Not Found

**Symptom:** 404 errors for all endpoints

**Solution:**
1. Verify `VITE_API_BASE_URL` is correct
2. Check backend routes match expected paths
3. Ensure backend server is running
4. Test with curl or Postman first

---

## Performance Optimization

### Recommended Settings

- [ ] **Enable Polling Selectively**
  ```env
  VITE_ENABLE_LIVE_UPDATES=true  # Only in production
  ```

- [ ] **Adjust Poll Intervals**
  ```env
  VITE_TRANSACTION_POLL_INTERVAL=5000  # 5 seconds
  VITE_DASHBOARD_POLL_INTERVAL=15000   # 15 seconds
  ```

- [ ] **Implement Caching**
  - Cache responses for 30 seconds
  - Use stale-while-revalidate strategy

- [ ] **Lazy Loading**
  - Load graph data on demand
  - Paginate large datasets
  - Defer non-critical requests

---

## Security Checklist

- [ ] **Environment Variables**
  - `.env` not committed to git
  - Secrets not hardcoded
  - Production keys separate from dev

- [ ] **Token Security**
  - JWT tokens in localStorage (XSS protected)
  - Refresh tokens secure
  - Tokens expire appropriately

- [ ] **API Security**
  - HTTPS in production
  - Rate limiting enabled
  - Input validation on backend

- [ ] **CORS Configuration**
  - Specific origins (not wildcard in prod)
  - Credentials allowed
  - Restricted methods

---

## Deployment Checklist

### Frontend Build

- [ ] Update production `.env`:
  ```env
  VITE_API_BASE_URL=https://api.muleguard.ai/api
  VITE_ENABLE_MOCK_DATA=false
  VITE_ENABLE_LIVE_UPDATES=true
  VITE_ENV=production
  ```

- [ ] Run production build:
  ```bash
  npm run build
  ```

- [ ] Test build locally:
  ```bash
  npm run preview
  ```

- [ ] Deploy `dist/` directory to hosting

### Backend Deployment

- [ ] Deploy backend API
- [ ] Configure CORS with frontend URL
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure rate limiting
- [ ] Set up logging

### Post-Deployment

- [ ] Test login flow
- [ ] Verify all endpoints work
- [ ] Check real-time updates
- [ ] Monitor error logs
- [ ] Test on multiple browsers
- [ ] Mobile responsiveness check

---

## Success Criteria

✅ **Integration Complete When:**

1. Dashboard loads without errors
2. Login authenticates successfully
3. All views display real data
4. Real-time updates work
5. Error handling graceful
6. Loading states smooth
7. Mobile responsive
8. Performance acceptable (<2s load time)

---

## Support Resources

- **Integration Guide**: `/BACKEND_INTEGRATION.md`
- **API Spec**: `/API_DOCUMENTATION.md`
- **Quick Reference**: `/BACKEND_READY.md`
- **Example Config**: `/.env.example`

---

## Next Steps

1. ✅ Review this checklist
2. ✅ Read `/BACKEND_INTEGRATION.md`
3. ⏭️ Implement backend endpoints
4. ⏭️ Configure `.env` file
5. ⏭️ Test integration
6. ⏭️ Deploy to production

---

**Status: 🟢 Frontend Ready for Backend Integration**

All infrastructure is in place. Just connect your backend API and you're live! 🚀
