import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

/**
 * Custom hook to safely fetch dashboard telemetry JSONs from `/data` dynamically.
 * Handles loading states, errors, auto-cache fallback, and refetching.
 */
export function useDashboardData<T>(fileName: string, fallbackData: T) {
  const [data, setData] = useState<T>(fallbackData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/data/${fileName}`);
      if (!response.ok) {
        throw new Error(`Server returned status ${response.status} (${response.statusText})`);
      }
      const jsonData = await response.json();
      
      // Merge with fallback data to ensure missing fields do not crash the UI
      if (typeof fallbackData === "object" && fallbackData !== null) {
        setData({ ...fallbackData, ...jsonData });
      } else {
        setData(jsonData);
      }
    } catch (err: any) {
      console.error(`[Telemetry Ingestion Alert] failed to fetch '${fileName}':`, err);
      setError(err.message || "Failed to load static telemetry.");
      toast.error(`Ingestion Warning`, {
        description: `Failed to fetch telemetry node '${fileName}'. Reverting to offline cached profile.`,
        duration: 4000,
      });
      setData(fallbackData);
    } finally {
      setLoading(false);
    }
  }, [fileName, fallbackData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
