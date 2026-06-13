import { useState, useEffect, useCallback } from "react";

const HEALTH_ENDPOINT = "/api/v1/end-point-health/";
const POLL_INTERVAL_MS = 30_000;

export interface ServerStatus {
  isOnline: boolean | null;
  lastChecked: Date | null;
  latencyMs: number | null;
  retry: () => void;
}

/**
 * Polls the backend health endpoint every 30 seconds.
 * Returns the global server connection status.
 */
export function useServerStatus(): ServerStatus {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const check = useCallback(async () => {
    const start = performance.now();
    try {
      const res = await fetch(HEALTH_ENDPOINT, { signal: AbortSignal.timeout(5000) });
      const elapsed = Math.round(performance.now() - start);
      setIsOnline(res.ok);
      setLatencyMs(elapsed);
    } catch {
      setIsOnline(false);
      setLatencyMs(null);
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [check]);

  return { isOnline, lastChecked, latencyMs, retry: check };
}
