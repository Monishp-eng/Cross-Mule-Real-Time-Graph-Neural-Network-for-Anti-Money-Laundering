// API Configuration
export const API_CONFIG = {
  // Update this with your actual backend URL
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  
  // API Endpoints
  ENDPOINTS: {
    // Authentication
    LOGIN: '/auth/login',
    SIGNUP: '/auth/signup',
    LOGOUT: '/auth/logout',
    REFRESH_TOKEN: '/auth/refresh',
    
    // Accounts
    GET_ACCOUNTS: '/accounts',
    GET_ACCOUNT_BY_ID: '/accounts/:id',
    
    // Transactions
    GET_TRANSACTIONS: '/transactions',
    GET_TRANSACTION_BY_ID: '/transactions/:id',
    GET_LIVE_TRANSACTIONS: '/transactions/live',
    
    // Clusters
    GET_CLUSTERS: '/clusters',
    GET_CLUSTER_BY_ID: '/clusters/:id',
    
    // Alerts
    GET_ALERTS: '/alerts',
    GET_ALERT_BY_ID: '/alerts/:id',
    UPDATE_ALERT_STATUS: '/alerts/:id/status',
    DISMISS_ALERT: '/alerts/:id/dismiss',
    
    // Graph Data
    GET_GRAPH_NODES: '/graph/nodes',
    GET_GRAPH_LINKS: '/graph/links',
    GET_GRAPH_DATA: '/graph',
    
    // Risk Scoring
    GET_RISK_DISTRIBUTION: '/risk/distribution',
    GET_JURISDICTION_RISKS: '/risk/jurisdictions',
    GET_OWNERSHIP_CORRELATION: '/risk/ownership',
    
    // Channel Flow
    GET_CHANNEL_FLOW: '/channels/flow',
    GET_VELOCITY_TREND: '/channels/velocity',
    
    // Reports
    GET_RISK_TREND: '/reports/risk-trend',
    GET_COMPLEXITY_DATA: '/reports/complexity',
    GENERATE_REPORT: '/reports/generate',
    EXPORT_REPORT: '/reports/export',
    
    // Intelligence Sharing
    GET_INTELLIGENCE_SHARING: '/intelligence/sharing',
    CREATE_SHARING_PARTNERSHIP: '/intelligence/partnerships',
    
    // Statistics
    GET_DASHBOARD_STATS: '/stats/dashboard',
  },
  
  // Request timeout in milliseconds
  TIMEOUT: 30000,
  
  // Retry configuration
  RETRY: {
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
  },
};

// Helper function to build endpoint with params
export function buildEndpoint(endpoint: string, params?: Record<string, string>): string {
  let url = endpoint;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`:${key}`, value);
    });
  }
  return url;
}
