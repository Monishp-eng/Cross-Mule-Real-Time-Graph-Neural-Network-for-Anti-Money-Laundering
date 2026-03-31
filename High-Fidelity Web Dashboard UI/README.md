# MuleGuard AI Dashboard

A modern, high-fidelity web dashboard for Cross-Channel Mule Account Detection using Graph Neural Networks (GNN).

## 🎯 Features

- **Real-Time Detection**: GNN-powered entity graph with relationship analysis
- **Pattern Detection**: Structuring, fragmentation, nesting, and rapid movement detection
- **Risk Scoring**: Jurisdiction-based analysis with confidence scores
- **Ownership Correlation**: Identify suspicious patterns across linked accounts
- **Sanctions Screening**: Behavior-based signals instead of simple list matching
- **Intelligence Sharing**: Privacy-safe collaboration with partner institutions
- **Compliance Reporting**: Regulator-ready reports with confidence scores
- **Cross-Channel Integration**: Unified view across UPI, ATM, Wallet, App, Web

## 🚀 Quick Start

### Development Mode (Current - Mock Data)
```bash
npm install
npm run dev
```

### Connect Your Backend (3 Steps)
1. Create `.env` file: `cp .env.example .env`
2. Configure: `VITE_API_BASE_URL=http://your-backend-url/api`
3. Enable API: `VITE_ENABLE_MOCK_DATA=false`
4. Restart: `npm run dev`

**That's it!** See [QUICKSTART.md](./QUICKSTART.md) for details.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](./QUICKSTART.md) | Connect backend in 3 steps |
| [BACKEND_READY.md](./BACKEND_READY.md) | Quick reference guide |
| [BACKEND_INTEGRATION.md](./BACKEND_INTEGRATION.md) | Complete integration guide |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | Full API specification |
| [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md) | Step-by-step checklist |

## 🏗️ Architecture

```
src/app/
├── config/          # API endpoints & feature flags
├── services/        # HTTP client & data layer
├── hooks/           # Custom React hooks for API calls
├── components/      # UI components & views
│   ├── dashboard/   # Dashboard widgets
│   └── ui/          # Reusable UI components
└── types.ts         # TypeScript types
```

## 🔌 Backend Requirements

Your backend needs to implement these core endpoints:

- `POST /api/auth/login` - Authentication
- `GET /api/accounts` - Account list
- `GET /api/transactions` - Transactions
- `GET /api/clusters` - Mule ring clusters
- `GET /api/alerts` - Alerts
- `GET /api/graph` - Network graph data

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete spec.

## 🎨 Technology Stack

- **Frontend**: React 18, TypeScript
- **Routing**: React Router 7
- **Styling**: Tailwind CSS v4
- **UI Components**: Radix UI, shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **State Management**: React Hooks

## 🔧 Configuration

### Environment Variables
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_ENABLE_MOCK_DATA=true
VITE_ENABLE_LIVE_UPDATES=true
VITE_TRANSACTION_POLL_INTERVAL=3000
VITE_DASHBOARD_POLL_INTERVAL=10000
```

See [.env.example](./.env.example) for all options.

## 📦 Installation

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing

### With Mock Data (Default)
```bash
npm run dev
# Dashboard runs with mock data
```

### With Real Backend
```bash
# Update .env
VITE_ENABLE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost:8000/api

# Restart
npm run dev
```

## 🎯 Key Features Implemented

### Dashboard Analytics
- ✅ Real-time metrics cards
- ✅ Interactive GNN entity graph
- ✅ Live transaction stream
- ✅ Cross-channel flow visualization (Sankey)
- ✅ Alert monitoring panel

### Risk Scoring
- ✅ Jurisdiction-based risk analysis
- ✅ Ownership correlation detection
- ✅ Confidence score tracking
- ✅ Multi-jurisdiction tracking

### Pattern Detection
- ✅ **Structuring**: Breaking large amounts into smaller transactions
- ✅ **Fragmentation**: Splitting funds across multiple accounts
- ✅ **Nesting**: Layered transactions through intermediaries
- ✅ **Rapid Movement**: High-velocity fund transfers

### Compliance & Reporting
- ✅ Behavior-based sanctions screening
- ✅ Transaction complexity metrics
- ✅ Privacy-safe intelligence sharing
- ✅ Regulator-ready reports with confidence scores
- ✅ Exportable data (PDF/CSV)

## 🔐 Security

- JWT token authentication with auto-refresh
- Secure token storage in localStorage
- CORS protection
- Request retry with exponential backoff
- Rate limiting support

## 📱 Responsive Design

- Desktop-optimized (primary)
- Tablet-friendly layouts
- Mobile-responsive components
- Dark/Light theme support

## 🚀 Production Deployment

```bash
# Build for production
npm run build

# Deploy dist/ folder to your hosting
# (Netlify, Vercel, AWS S3, etc.)
```

### Production Environment
```env
VITE_API_BASE_URL=https://api.muleguard.ai/api
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_LIVE_UPDATES=true
VITE_ENV=production
```

## 🤝 Backend Integration Status

✅ **Frontend**: 100% Complete  
✅ **API Layer**: 100% Ready  
⏳ **Backend**: Waiting for your API implementation  

See [BACKEND_READY.md](./BACKEND_READY.md) for integration guide.

## 📄 License

Proprietary - MuleGuard AI

## 🆘 Support

For backend integration help:
1. Read [QUICKSTART.md](./QUICKSTART.md)
2. Check [BACKEND_INTEGRATION.md](./BACKEND_INTEGRATION.md)
3. Review [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md)

---

**Dashboard Status**: ✅ Production-Ready | 🔌 Backend-Ready | 🚀 Deploy-Ready
