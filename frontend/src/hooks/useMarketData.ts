import { useState, useEffect, useCallback } from "react";
import { fetchOHLCV } from "../services/api";
import type { OHLCVBar } from "../types";

export function useMarketData(symbol: string, timeframe: string, start: string, end: string) {
  const [bars, setBars] = useState<OHLCVBar[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOHLCV(symbol, timeframe, start, end);
      setBars(data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail || (e as { message?: string })?.message || "Failed to load data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe, start, end]);

  useEffect(() => {
    load();
  }, [load]);

  return { bars, loading, error, reload: load };
}
