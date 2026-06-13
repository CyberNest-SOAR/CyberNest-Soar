import { useState, useEffect, useCallback } from "react";
import { useServerStatusContext } from "@/contexts/ServerStatusContext";
import { toast } from "sonner";

interface FetchWithFallbackResult<T> {
  data: T;
  loading: boolean;
  error: string | null;
  /** true when data is coming from the static pipeline snapshot (offline mode) */
  isMock: boolean;
  isOnline: boolean | null;
  refetch: () => void;
}

/**
 * Smart data-fetching hook with server-aware fallback.
 *
 * - ONLINE  → fetches `liveEndpoint` (e.g. /api/v1/ui/command-center)
 * - OFFLINE → fetches `snapshotPath` (e.g. /data/command-center.json)
 *             which is a pre-generated dataset pipeline snapshot
 *
 * Both sources share the exact same JSON shape, so the UI renders
 * identically in both modes.
 */
export function useFetchWithFallback<T>(
  liveEndpoint: string,
  snapshotPath: string,
  emptyFallback: T
): FetchWithFallbackResult<T> {
  const { isOnline } = useServerStatusContext();
  const [data, setData] = useState<T>(emptyFallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const fetchFromUrl = useCallback(async (url: string, mock: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (typeof emptyFallback === "object" && emptyFallback !== null && !Array.isArray(emptyFallback)) {
        setData({ ...emptyFallback, ...json });
      } else {
        setData(json);
      }
      setIsMock(mock);
    } catch (err: any) {
      console.error(`[useFetchWithFallback] Failed to fetch '${url}':`, err);
      setError(err.message);
      // If the live endpoint failed, try the snapshot as emergency fallback
      if (!mock) {
        try {
          const snapRes = await fetch(snapshotPath);
          if (snapRes.ok) {
            const snapJson = await snapRes.json();
            setData(snapJson);
            setIsMock(true);
            toast.warning("Live data unavailable", {
              description: "Showing pipeline snapshot data instead.",
              duration: 3000,
            });
            return;
          }
        } catch {}
      }
      setData(emptyFallback);
      setIsMock(true);
    } finally {
      setLoading(false);
    }
  }, [snapshotPath]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchData = useCallback(async () => {
    if (isOnline === null) {
      // Still checking — serve snapshot silently
      fetchFromUrl(snapshotPath, true);
      return;
    }
    if (isOnline) {
      fetchFromUrl(liveEndpoint, false);
    } else {
      fetchFromUrl(snapshotPath, true);
    }
  }, [isOnline, liveEndpoint, snapshotPath, fetchFromUrl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, isMock, isOnline, refetch: fetchData };
}
