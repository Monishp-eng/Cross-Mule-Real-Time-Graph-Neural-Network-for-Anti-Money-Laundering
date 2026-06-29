import axios from "axios";

const isLocalHostName = (host) => ["localhost", "127.0.0.1"].includes(String(host || "").toLowerCase());

const normalizeBaseUrl = (url) => String(url || "").trim().replace(/\/$/, "");

const isLocalApiUrl = (url) => {
  const value = normalizeBaseUrl(url);
  return value.startsWith("http://localhost") || value.startsWith("http://127.0.0.1");
};

const sameOrigin = (left, right) => {
  try {
    return new URL(left).origin === new URL(right).origin;
  } catch {
    return false;
  }
};

const clearAuthState = () => {
  localStorage.removeItem("cmds_auth_token");
  localStorage.removeItem("cmds_auth_email");
  localStorage.removeItem("cmds_auth_role");
  localStorage.removeItem("cmds_auth_employee_id");
};

const buildApiBaseVariants = (base) => {
  const normalized = normalizeBaseUrl(base);
  if (!normalized) {
    return [];
  }

  const hasApiSuffix = normalized.endsWith("/api");
  return hasApiSuffix
    ? [normalized, normalized.slice(0, -4)]
    : [normalized, `${normalized}/api`];
};

const getDefaultBaseUrl = () => {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }

  const localDevHost = isLocalHostName(window.location.hostname) && ["5173", "3000"].includes(window.location.port);
  return localDevHost ? "http://127.0.0.1:8000" : window.location.origin;
};

const getConfiguredBaseUrl = () => {
  const envUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);

  if (typeof window === "undefined") {
    return envUrl || "";
  }

  const localStorageUrl = normalizeBaseUrl(localStorage.getItem("cmds_api_base"));
  const isHostedRuntime = !isLocalHostName(window.location.hostname);

  if (localStorageUrl) {
    // Ignore stale localhost override when app is opened from a hosted URL.
    if (!(isHostedRuntime && isLocalApiUrl(localStorageUrl))) {
      if (!isHostedRuntime || envUrl || sameOrigin(localStorageUrl, window.location.origin)) {
        return localStorageUrl;
      }
    }
  }

  return envUrl;
};

const getBaseUrl = () => getConfiguredBaseUrl() || getDefaultBaseUrl();
const getApiKey = () => localStorage.getItem("cmds_api_key") || import.meta.env.VITE_API_KEY || "";
const getAuthToken = () => localStorage.getItem("cmds_auth_token") || "";

const getCandidateBaseUrls = ({ includeLocalFallback = true } = {}) => {
  const configured = getConfiguredBaseUrl();
  const defaults = [];

  if (configured) {
    defaults.push(...buildApiBaseVariants(configured));
  } else {
    defaults.push(...buildApiBaseVariants(getDefaultBaseUrl()));
  }

  if (typeof window !== "undefined") {
    defaults.push(...buildApiBaseVariants(window.location.origin));
  }

  if (includeLocalFallback) {
    defaults.push("http://127.0.0.1:8000", "http://localhost:8000");
  }

  return [...new Set(defaults.map((value) => normalizeBaseUrl(value)).filter(Boolean))];
};

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 5000,
});

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function normalizeFraudScoreResponse(data, userId) {
  const score = Number(data?.risk_score || data?.fraud_score || 0);
  return {
    user_id: userId,
    fraud_score: score,
    risk_level: score >= 0.75 ? "High" : score >= 0.4 ? "Medium" : "Low",
    explanation: data?.reasons?.join(", ") || data?.explainability?.reasons?.join(", ") || "No explanation provided",
    raw: data,
  };
}

function withTimeout(promise, timeoutMs, timeoutMessage) {
  let timer;
  const timeoutPromise = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timer));
}

function isRetryableNetworkError(error) {
  const msg = String(error?.message || "").toLowerCase();
  const code = String(error?.code || "").toUpperCase();

  return (
    msg.includes("network error") ||
    msg.includes("failed to fetch") ||
    msg.includes("timeout") ||
    msg.includes("ecconnrefused") ||
    code === "ERR_NETWORK" ||
    code === "ECONNABORTED"
  );
}

function toErrorMessage(value) {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    const parts = value.map((item) => toErrorMessage(item)).filter(Boolean);
    return parts.join("; ");
  }
  if (typeof value === "object") {
    const candidate =
      toErrorMessage(value.detail) ||
      toErrorMessage(value.reason) ||
      toErrorMessage(value.message) ||
      toErrorMessage(value.error) ||
      toErrorMessage(value.msg) ||
      "";

    if (candidate) {
      return candidate;
    }

    const entries = Object.values(value)
      .map((item) => toErrorMessage(item))
      .filter(Boolean);
    return entries.join("; ");
  }
  return String(value);
}

api.interceptors.request.use((config) => {
  if (!config.baseURL) {
    config.baseURL = getBaseUrl();
  }
  const apiKey = getApiKey();
  const authToken = getAuthToken();
  if (apiKey) {
    config.headers = {
      ...(config.headers || {}),
      "x-api-key": apiKey,
    };
  }
  if (authToken) {
    config.headers = {
      ...(config.headers || {}),
      Authorization: `Bearer ${authToken}`,
    };
  }
  return config;
});

async function requestWithFallback(method, url, options = {}) {
  const { skipFallback = false, ...requestOptions } = options || {};
  const bases = getCandidateBaseUrls({ includeLocalFallback: !skipFallback });
  let lastError;

  for (const baseURL of bases) {
    try {
      const response = await api.request({
        method,
        url,
        baseURL,
        ...requestOptions,
      });
      return response;
    } catch (error) {
      lastError = error;
      if (!isRetryableNetworkError(error)) {
        throw error;
      }
    }
  }

  throw lastError || new Error("Unable to reach backend API. Verify API base URL and backend server status.");
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = Number(error?.response?.status || 0);
    const errorDetail = toErrorMessage(error?.response?.data?.detail) || "";
    const authExpired = statusCode === 401 && /token expired|invalid token|user not found/i.test(errorDetail);
    if (authExpired) {
      clearAuthState();
    }

    if (isRetryableNetworkError(error)) {
      const baseURL = error?.config?.baseURL || getBaseUrl();
      return Promise.reject(new Error(`Backend unreachable at ${baseURL}. Check server and API settings.`));
    }

    const message =
      toErrorMessage(error?.response?.data?.message) ||
      toErrorMessage(error?.response?.data?.detail) ||
      toErrorMessage(error?.response?.data) ||
      error?.message ||
      "Unexpected API error";
    return Promise.reject(new Error(message));
  }
);

export const apiService = {
  async getCurrentUser() {
    const { data } = await requestWithFallback("get", "/auth/me", { timeout: 7000, skipFallback: true });
    return data;
  },

  async signup(payload) {
    const { data } = await requestWithFallback("post", "/auth/signup", { data: payload, timeout: 8000 });
    return data;
  },

  async login(payload) {
    const identity = payload?.identity || payload?.email || "";
    const { data } = await requestWithFallback("post", "/login", {
      data: { identity, password: payload?.password || "" },
      timeout: 8000,
    });
    return data;
  },

  async getUsers(params = {}) {
    const { data } = await requestWithFallback("get", "/users", {
      params: { limit: params.limit || 200 },
      timeout: 7000,
      skipFallback: true,
    });
    return data;
  },

  async getUserProfile(userId, params = {}) {
    const { data } = await requestWithFallback("get", `/users/${encodeURIComponent(userId)}`, {
      params: { limit: params.limit || 200 },
      timeout: 9000,
      skipFallback: true,
    });
    return data;
  },

  async getRiskScore(userId) {
    const { data } = await requestWithFallback("get", "/risk-score", {
      params: { user_id: userId },
      timeout: 6000,
      skipFallback: true,
    });
    return data;
  },

  async getMyNotifications(params = {}) {
    const { data } = await requestWithFallback("get", "/v1/users/me/notifications", {
      params: { limit: params.limit || 100 },
      timeout: 5000,
      skipFallback: true,
    });
    return data;
  },

  async markNotificationRead(notificationId, read = true) {
    const { data } = await requestWithFallback(
      "patch",
      `/v1/users/me/notifications/${encodeURIComponent(notificationId)}/read`,
      { data: { read } }
    );
    return data;
  },

  async ingestEvent(payload) {
    const { data } = await requestWithFallback("post", "/v1/transactions/process", { data: payload });
    return data;
  },

  async ingestEventAsync(payload) {
    const { data } = await requestWithFallback("post", "/v1/transactions/process-async", { data: payload });
    return data;
  },

  async getAsyncAnalysisResult(requestId) {
    const { data } = await requestWithFallback("get", `/v1/transactions/result/${encodeURIComponent(requestId)}`);
    return data;
  },

  async getFraudScore(userId) {
    const payload = {
      channel: "MOBILE",
      raw_event: {
        user_id: userId,
        transfer_to_wallet: `wallet_${userId}`,
        transfer_amount: 1800,
        transfer_time: new Date().toISOString(),
        location: { latitude: 12.9716, longitude: 77.5946, country: "IN" },
      },
    };

    try {
      const { data } = await requestWithFallback("post", "/v1/transactions/process", { data: payload, timeout: 10000 });
      return normalizeFraudScoreResponse(data, userId);
    } catch (directError) {
      try {
        const queued = await requestWithFallback("post", "/v1/transactions/process-async", { data: payload, timeout: 10000 });
        const requestId = queued?.data?.request_id;
        if (!requestId) {
          throw new Error("Could not queue async fraud analysis request");
        }

        for (let attempt = 0; attempt < 8; attempt += 1) {
          await sleep(500 + attempt * 250);
          const poll = await requestWithFallback("get", `/v1/transactions/result/${encodeURIComponent(requestId)}`, { skipFallback: true });
          const state = String(poll?.data?.state || "").toLowerCase();
          if (state === "completed") {
            const result = poll?.data?.result?.result || poll?.data?.result || {};
            if (String(result?.status || "").toUpperCase() === "ERROR") {
              throw new Error(result?.reason || "Fraud analysis failed");
            }
            return normalizeFraudScoreResponse(result, userId);
          }
          if (state === "failed") {
            throw new Error(poll?.data?.error || "Fraud analysis failed in async processing");
          }
        }

        throw new Error("Fraud analysis timed out. Please try again.");
      } catch (fallbackError) {
        throw new Error(fallbackError?.message || directError?.message || "Fraud analysis failed");
      }
    }
  },

  async getTransactions(params = {}) {
    try {
      const { data } = await withTimeout(
        requestWithFallback("get", "/transactions", {
        params: { limit: params.limit || 100 },
        timeout: 3500,
        skipFallback: true,
        }),
        4500,
        "Timed out while fetching transactions"
      );
      const mapped = (data?.transactions || []).map((row, idx) => {
        const sourceIsFraud = ["BLOCK", "FLAG", "CONFIRMED_MULE", "FRAUD"].includes(String(row?.decision || row?.status || "").toUpperCase());
        const statusLabel = String(row?.status || row?.decision || "SAFE").toUpperCase();
        const amount = Number(row?.amount ?? 0);
        const currency = String(row?.currency || "INR").toUpperCase();
        const transactionId = row?.transaction_id || `TXN_${idx}`;
        return {
          id: transactionId,
          transaction_id: transactionId,
          user_id: row?.user_id || "unknown",
          source_account_id: row?.account_id || null,
            name: row?.name || null,
            mobile_number: row?.mobile_number || null,
            account_number: row?.account_number || row?.account_id || null,
            account_product_type: row?.account_product_type || null,
            narration: row?.narration || null,
            pincode: row?.pincode || null,
            receiver_id: row?.receiver_id || null,
          amount,
          currency,
          status: sourceIsFraud ? "FRAUD" : statusLabel,
          source_status: statusLabel,
          source_is_fraud: sourceIsFraud,
          source_fraud_reason: row?.detection_reason || row?.reason || null,
          timestamp: row?.timestamp,
          risk_score: Number(row?.risk_score || 0),
          channel: row?.channel || "APP",
          channels_involved: row?.channels_involved || [row?.channel || "APP"],
          confidence_score: Number(row?.confidence_score || 0),
          raw: row,
        };
      });
      const deduped = [];
      const seen = new Set();
      for (const row of mapped) {
        const key = `${row.transaction_id || row.id}|${row.timestamp || ""}`;
        if (seen.has(key)) continue;
        seen.add(key);
        deduped.push(row);
      }
      return { transactions: deduped };
    } catch (error) {
      return { transactions: [], _error: error?.message || "Unable to fetch transactions" };
    }
  },

  async getAlerts(params = {}) {
    try {
      const { data } = await withTimeout(
        requestWithFallback("get", "/alerts", {
        params: { limit: params.limit || 100 },
        timeout: 6500,
        skipFallback: true,
        }),
        7500,
        "Timed out while fetching alerts"
      );
      const alerts = (data?.alerts || []).map((item, idx) => ({
        id: item.alert_id || `ALT_${idx}`,
        alert_id: item.alert_id || `ALT_${idx}`,
        alert_type: String(item.alert_type || "decision").toLowerCase(),
        user_id: item.user_id || "unknown",
        account_id: item.account_id || item.user_id || "unknown",
        severity: String(item.risk_level || item.severity || "MEDIUM").toUpperCase(),
        reason: item.reason || "Suspicious activity detected",
        detection_reason: item.detection_reason || item.reason || "Suspicious activity detected",
        channels_involved: item.channels_involved || [item.channel || "APP"],
        confidence_score: Number(item.confidence_score || 0),
        case_id: item.case_id || `CASE-${item.alert_id || idx}`,
        timestamp: item.timestamp,
        status: String(item.status || "OPEN").toUpperCase(),
        risk_score: Number(item.risk_score || 0),
        risk_breakdown: item.risk_breakdown || {},
        pattern_signals: item.pattern_signals || {},
        reviewed: String(item.status || "OPEN").toUpperCase() === "CLOSED",
      }));

      return { alerts };
    } catch (error) {
      return { alerts: [], _error: error?.message || "Unable to fetch alerts" };
    }
  },

  async alertAction(alertId, action, note = "") {
    const { data } = await requestWithFallback("post", `/alerts/${encodeURIComponent(alertId)}/action`, {
      data: { action, note },
      timeout: 7000,
    });
    return data;
  },

  async seedDemoAlerts(count = 3) {
    const { data } = await requestWithFallback("post", "/alerts/demo-seed", {
      params: { count },
      timeout: 10000,
      skipFallback: true,
    });
    return data;
  },

  async markAlertReviewed(alertId) {
    try {
      const { data } = await requestWithFallback("patch", `/alerts/${encodeURIComponent(alertId)}/review`, {
        data: { reviewed: true },
      });
      return data;
    } catch {
      return { status: "ok", alert_id: alertId, reviewed: true };
    }
  },

  async getGraphData() {
    try {
      const { data } = await withTimeout(
        requestWithFallback("get", "/graph", {
          timeout: 10000,
          skipFallback: true,
        }),
        12000,
        "Timed out while fetching graph data"
      );
      return data;
    } catch (error) {
      return {
        nodes: [],
        links: [],
        clusters: [],
        explanations: [],
        flagged_paths: [],
        _error: error?.message || "Unable to fetch graph data",
      };
    }
  },

  async getStats() {
    try {
      const { data } = await withTimeout(
        requestWithFallback("get", "/v1/stats", {
          timeout: 3500,
          skipFallback: true,
        }),
        4500,
        "Timed out while fetching stats"
      );
      return data;
    } catch (error) {
      return {
        stats: {},
        observability: {},
        _error: error?.message || "Unable to fetch stats",
      };
    }
  },

  async trainModel(csvText, options = {}) {
    const { data } = await requestWithFallback("post", "/v1/train", {
      data: {
        csv_text: csvText,
        out_dir: options.outDir || "models",
        epochs: options.epochs || 40,
        hidden_dim: options.hiddenDim || 64,
        seed: options.seed || 42,
      },
      timeout: 10000,
    });
    return data;
  },

  async predictFromCsv(csvText) {
    const { data } = await requestWithFallback("post", "/v1/predict", {
      data: { csv_text: csvText },
      timeout: 120000,
    });
    return data;
  },

  async startMonitoring() {
    const { data } = await requestWithFallback("post", "/v1/stream/start");
    return data;
  },

  async getMonitoringStatus() {
    const { data } = await requestWithFallback("get", "/v1/stream/status");
    return data;
  },

  async generateReport(format = "csv") {
    const response = await requestWithFallback("get", "/v1/report", {
      params: { format },
      responseType: format === "csv" ? "blob" : "json",
    });
    return response;
  },

  async resetData() {
    const { data } = await requestWithFallback("post", "/v1/reset");
    return data;
  },

  async getIntelSummary() {
    const { data } = await requestWithFallback("get", "/v1/intel/summary");
    return data;
  },

  async getComplianceSar(limit = 50) {
    const { data } = await requestWithFallback("get", "/compliance/sar", {
      params: { limit },
      timeout: 10000,
      skipFallback: true,
    });
    return data;
  },

  async getComplianceRiskSummary(limit = 200) {
    const { data } = await requestWithFallback("get", "/compliance/risk-summary", {
      params: { limit },
      timeout: 10000,
      skipFallback: true,
    });
    return data;
  },

  async runDemoScenario(scenario, options = {}) {
    const { data } = await requestWithFallback("post", `/v1/demo/run/${encodeURIComponent(scenario)}`, {
      timeout: options.timeout || 120000,
      skipFallback: options.skipFallback ?? true,
    });
    return data;
  },
};

export default api;
