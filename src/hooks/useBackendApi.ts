import { useState, useCallback } from "react";
import { toast } from "sonner";

const API_BASE = "http://0.0.0.0:8000/api/v1";

interface RiskScoreResult {
  event_id: string;
  risk_score: number;
  priority: string;
  predicted_analyst_verdict: string;
  confidence: number;
  features: Record<string, number>;
}

interface HealthCheckResult {
  service: string;
  status: "healthy" | "degraded" | "offline";
  latency_ms: number;
  error?: string;
}

export function useRiskScoring() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RiskScoreResult | null>(null);

  const scoreAlert = useCallback(async (alertData: Record<string, unknown>) => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/ai-analysis/scoring`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(alertData),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
      return data as RiskScoreResult;
    } catch (err: any) {
      toast.error("Risk scoring failed", {
        description: err.message || "Could not reach scoring engine",
      });
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { scoreAlert, result, loading };
}

export function useHealthCheck() {
  const [results, setResults] = useState<HealthCheckResult[]>([]);
  const [loading, setLoading] = useState(false);

  const checkAll = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/end-point-health/`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data);
      return data as HealthCheckResult[];
    } catch (err: any) {
      toast.error("Health check failed", {
        description: err.message || "Could not reach health endpoint",
      });
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return { checkAll, results, loading };
}
