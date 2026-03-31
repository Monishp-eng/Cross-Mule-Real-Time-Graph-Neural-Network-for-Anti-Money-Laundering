// Feature flags and configuration
export const config = {
  // Enable mock data instead of API calls
  useMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
  
  // Enable live updates/polling
  enableLiveUpdates: import.meta.env.VITE_ENABLE_LIVE_UPDATES === 'true' || false,
  
  // API Configuration
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),
    maxRetries: parseInt(import.meta.env.VITE_MAX_RETRY_ATTEMPTS || '3', 10),
  },
  
  // Polling intervals
  polling: {
    transactions: parseInt(import.meta.env.VITE_TRANSACTION_POLL_INTERVAL || '3000', 10),
    dashboard: parseInt(import.meta.env.VITE_DASHBOARD_POLL_INTERVAL || '10000', 10),
  },
  
  // Environment
  isDevelopment: import.meta.env.VITE_ENV === 'development' || import.meta.env.DEV,
  isProduction: import.meta.env.VITE_ENV === 'production' || import.meta.env.PROD,
};

export default config;
