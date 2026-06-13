import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { useServerStatusContext } from "@/contexts/ServerStatusContext";

const API_UI_BASE = "/api/v1/ui";

/**
 * Maps the static snapshot filename to the corresponding live API route.
 * e.g. "command-center.json" → "/api/v1/ui/command-center"
 */
function snapshotToLiveEndpoint(fileName: string): string | null {
  const stem = fileName.replace(/\.json$/, "");
  const knownRoutes = [
    "command-center",
    "alerts-table",
    "incident-response",
    "threat-intel-center",
    "asset-intelligence",
    "ai-operations",
    "it-hygiene",
    "playbooks-automation",
    "reporting-audit",
    "admin-health",
  ];
  if (knownRoutes.includes(stem)) {
    return `${API_UI_BASE}/${stem}`;
  }
  return null; // no live route for this file → always use snapshot
}

/**
 * Custom hook to fetch dashboard telemetry data.
 *
 * Behaviour:
 * - ONLINE  → fetches the matching live backend endpoint (/api/v1/ui/<name>)
 * - OFFLINE → serves the pre-generated dataset pipeline snapshot from /data/<name>
 * - If the live fetch fails mid-session → falls back to snapshot automatically
 *
 * Both sources share identical JSON shapes from the dataset pipeline.
 */
export function useDashboardData<T>(fileName: string, fallbackData: T) {
  const { isOnline } = useServerStatusContext();
  const [data, setData] = useState<T>(fallbackData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const snapshotUrl = `/data/${fileName}`;
  const liveUrl = snapshotToLiveEndpoint(fileName);

  const loadFromUrl = useCallback(
    async (url: string, mock: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(
            `Server returned status ${response.status} (${response.statusText})`
          );
        }
        const jsonData = await response.json();
        if (typeof fallbackData === "object" && fallbackData !== null) {
          setData({ ...fallbackData, ...jsonData });
        } else {
          setData(jsonData);
        }
        setIsMock(mock);
      } catch (err: any) {
        console.error(`[useDashboardData] Failed to fetch '${url}':`, err);
        setError(err.message || "Failed to load data.");
        // If live fetch failed, try snapshot as emergency fallback
        if (!mock) {
          try {
            const snapRes = await fetch(snapshotUrl);
            if (snapRes.ok) {
              const snapJson = await snapRes.json();
              if (typeof fallbackData === "object" && fallbackData !== null) {
                setData({ ...fallbackData, ...snapJson });
              } else {
                setData(snapJson);
              }
              setIsMock(true);
              toast.warning("Live data unavailable", {
                description: `Showing pipeline snapshot for '${fileName}'.`,
                duration: 3000,
              });
              return;
            }
          } catch {}
          toast.error(`Data Warning`, {
            description: `Failed to load '${fileName}'. Reverting to offline cached profile.`,
            duration: 4000,
          });
          setData(fallbackData);
          setIsMock(true);
        } else {
          setData(fallbackData);
          setIsMock(true);
        }
      } finally {
        setLoading(false);
      }
    },
    [fileName, snapshotUrl, fallbackData] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const fetchData = useCallback(async () => {
    if (isOnline === null) {
      // Still determining status — serve snapshot quietly
      loadFromUrl(snapshotUrl, true);
      return;
    }
    if (isOnline && liveUrl) {
      loadFromUrl(liveUrl, false);
    } else {
      loadFromUrl(snapshotUrl, true);
    }
  }, [isOnline, liveUrl, snapshotUrl, loadFromUrl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, isMock, refetch: fetchData };
}
