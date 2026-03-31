import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';

interface UseApiOptions<T> {
  initialData?: T;
  enabled?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for API calls with loading and error states
 */
export function useApi<T>(
  apiCall: () => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiResult<T> {
  const { initialData = null, enabled = true, onSuccess, onError } = options;
  
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    
    setLoading(true);
    setError(null);

    try {
      const result = await apiCall();
      setData(result);
      onSuccess?.(result);
    } catch (err) {
      const error = err as Error;
      setError(error);
      onError?.(error);
      console.error('API Error:', error);
    } finally {
      setLoading(false);
    }
  }, [apiCall, enabled, onSuccess, onError]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Custom hook for mutations (POST, PUT, PATCH, DELETE)
 */
interface UseMutationResult<T, V> {
  mutate: (variables: V) => Promise<T | null>;
  data: T | null;
  loading: boolean;
  error: Error | null;
  reset: () => void;
}

export function useMutation<T, V = void>(
  apiCall: (variables: V) => Promise<T>,
  options: {
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  } = {}
): UseMutationResult<T, V> {
  const { onSuccess, onError } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(
    async (variables: V): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiCall(variables);
        setData(result);
        onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err as Error;
        setError(error);
        onError?.(error);
        console.error('Mutation Error:', error);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiCall, onSuccess, onError]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { mutate, data, loading, error, reset };
}

/**
 * Custom hook for polling data at intervals
 */
export function usePolling<T>(
  apiCall: () => Promise<T>,
  interval: number = 5000,
  options: UseApiOptions<T> & { autoStart?: boolean } = {}
): UseApiResult<T> & { start: () => void; stop: () => void } {
  const { autoStart = true, ...apiOptions } = options;
  const [isPolling, setIsPolling] = useState(autoStart);

  const { data, loading, error, refetch } = useApi(apiCall, {
    ...apiOptions,
    enabled: isPolling,
  });

  useEffect(() => {
    if (!isPolling) return;

    const intervalId = setInterval(() => {
      refetch();
    }, interval);

    return () => clearInterval(intervalId);
  }, [isPolling, interval, refetch]);

  const start = useCallback(() => setIsPolling(true), []);
  const stop = useCallback(() => setIsPolling(false), []);

  return { data, loading, error, refetch, start, stop };
}

/**
 * Helper to format API errors
 */
export function formatApiError(error: Error | AxiosError): string {
  if ('response' in error && error.response) {
    const axiosError = error as AxiosError<{ message?: string; error?: string }>;
    return (
      axiosError.response?.data?.message ||
      axiosError.response?.data?.error ||
      'An error occurred while processing your request'
    );
  }
  return error.message || 'An unexpected error occurred';
}

/**
 * Hook for authentication state
 */
export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!localStorage.getItem('auth_token');
  });

  const login = useCallback((token: string, refreshToken?: string) => {
    localStorage.setItem('auth_token', token);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
  }, []);

  return { isAuthenticated, login, logout };
}
