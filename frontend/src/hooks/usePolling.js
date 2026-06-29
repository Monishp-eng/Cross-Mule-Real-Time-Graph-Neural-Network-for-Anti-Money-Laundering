import { useEffect } from "react";

export function usePolling(callback, intervalMs = 10000, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined;
    const id = setInterval(() => {
      callback();
    }, intervalMs);

    return () => clearInterval(id);
  }, [callback, enabled, intervalMs]);
}
