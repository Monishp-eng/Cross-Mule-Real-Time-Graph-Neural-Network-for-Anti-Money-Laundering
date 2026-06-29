import { useCallback, useEffect, useRef, useState } from "react";

export function useAsync(asyncFn, deps = [], immediate = true) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(Boolean(immediate));
  const inFlightRef = useRef(null);
  const hasDataRef = useRef(false);

  useEffect(() => {
    hasDataRef.current = data !== null;
  }, [data]);

  const execute = useCallback(async () => {
    if (inFlightRef.current) {
      return inFlightRef.current;
    }

    // Keep existing content visible during background refreshes.
    if (!hasDataRef.current) {
      setLoading(true);
    }
    setError(null);

    const request = (async () => {
      try {
        const result = await asyncFn();
        setData(result);
        return result;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        inFlightRef.current = null;
        setLoading(false);
      }
    })();

    inFlightRef.current = request;
    return request;
  }, deps);

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {});
    }
  }, [execute, immediate]);

  return { data, error, loading, execute, setData };
}
