import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { API_CONFIG } from '../config/api.config';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REFRESH_TOKEN}`, {
          refresh_token: refreshToken,
        });
        
        const { token } = response.data;
        localStorage.setItem('auth_token', token);
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Generic request handler with retry logic
async function request<T>(
  config: AxiosRequestConfig,
  retries = API_CONFIG.RETRY.MAX_RETRIES
): Promise<T> {
  try {
    const response = await apiClient.request<T>(config);
    return response.data;
  } catch (error) {
    if (retries > 0 && shouldRetry(error as AxiosError)) {
      await delay(API_CONFIG.RETRY.RETRY_DELAY);
      return request<T>(config, retries - 1);
    }
    throw error;
  }
}

// Check if request should be retried
function shouldRetry(error: AxiosError): boolean {
  return (
    !error.response ||
    error.response.status >= 500 ||
    error.code === 'ECONNABORTED'
  );
}

// Delay helper
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// API Service Methods
export const apiService = {
  // Authentication
  login: (credentials: { email: string; password: string }) =>
    request({ method: 'POST', url: API_CONFIG.ENDPOINTS.LOGIN, data: credentials }),

  signup: (userData: { email: string; password: string; name: string }) =>
    request({ method: 'POST', url: API_CONFIG.ENDPOINTS.SIGNUP, data: userData }),

  logout: () =>
    request({ method: 'POST', url: API_CONFIG.ENDPOINTS.LOGOUT }),

  // Accounts
  getAccounts: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_ACCOUNTS }),

  getAccountById: (id: string) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_ACCOUNT_BY_ID.replace(':id', id) }),

  // Transactions
  getTransactions: (params?: { page?: number; limit?: number; status?: string }) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_TRANSACTIONS, params }),

  getTransactionById: (id: string) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_TRANSACTION_BY_ID.replace(':id', id) }),

  getLiveTransactions: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_LIVE_TRANSACTIONS }),

  // Clusters
  getClusters: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_CLUSTERS }),

  getClusterById: (id: string) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_CLUSTER_BY_ID.replace(':id', id) }),

  // Alerts
  getAlerts: (params?: { status?: string; severity?: string }) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_ALERTS, params }),

  getAlertById: (id: string) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_ALERT_BY_ID.replace(':id', id) }),

  updateAlertStatus: (id: string, status: string) =>
    request({
      method: 'PATCH',
      url: API_CONFIG.ENDPOINTS.UPDATE_ALERT_STATUS.replace(':id', id),
      data: { status },
    }),

  dismissAlert: (id: string) =>
    request({ method: 'POST', url: API_CONFIG.ENDPOINTS.DISMISS_ALERT.replace(':id', id) }),

  // Graph Data
  getGraphNodes: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_GRAPH_NODES }),

  getGraphLinks: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_GRAPH_LINKS }),

  getGraphData: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_GRAPH_DATA }),

  // Risk Scoring
  getRiskDistribution: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_RISK_DISTRIBUTION }),

  getJurisdictionRisks: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_JURISDICTION_RISKS }),

  getOwnershipCorrelation: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_OWNERSHIP_CORRELATION }),

  // Channel Flow
  getChannelFlow: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_CHANNEL_FLOW }),

  getVelocityTrend: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_VELOCITY_TREND }),

  // Reports
  getRiskTrend: (params?: { period?: string }) =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_RISK_TREND, params }),

  getComplexityData: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_COMPLEXITY_DATA }),

  generateReport: (reportType: string, params?: any) =>
    request({
      method: 'POST',
      url: API_CONFIG.ENDPOINTS.GENERATE_REPORT,
      data: { reportType, ...params },
    }),

  exportReport: (reportId: string, format: 'pdf' | 'csv') =>
    request({
      method: 'GET',
      url: API_CONFIG.ENDPOINTS.EXPORT_REPORT,
      params: { reportId, format },
      responseType: 'blob',
    }),

  // Intelligence Sharing
  getIntelligenceSharing: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_INTELLIGENCE_SHARING }),

  createSharingPartnership: (data: any) =>
    request({
      method: 'POST',
      url: API_CONFIG.ENDPOINTS.CREATE_SHARING_PARTNERSHIP,
      data,
    }),

  // Statistics
  getDashboardStats: () =>
    request({ method: 'GET', url: API_CONFIG.ENDPOINTS.GET_DASHBOARD_STATS }),
};

export default apiService;
