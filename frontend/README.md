# Cross Mule Detection Frontend

Modern React frontend for the Cross Mule Detection System.

## 1. Project Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create env file:

```bash
cp .env.example .env
```

3. Update API URL in `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

4. Start dev server:

```bash
npm run dev
```

## 2. Pages Included

- Dashboard
- Transaction Monitor
- Fraud Analysis
- Graph Visualization
- Alerts
- Login (bonus)

## 3. Folder Structure

```text
src/
  components/
  hooks/
  pages/
  services/api.js
  utils/
```

## 4. Notes

- API integration is centralized in `src/services/api.js`
- Toast notifications are enabled with `react-hot-toast`
- Alerts page includes polling every 10 seconds
