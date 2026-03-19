import { useState, useCallback } from "react";
import { runBacktest } from "../services/api";
import type { BacktestResult } from "../types";

export function useBacktest() {
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (payload: {
    symbol: string;
    timeframe: string;
    strategy_code: string;
    start?: string;
    end?: string;
    initial_capital?: number;
    commission?: number;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBacktest(payload);
      setResult(res);
      return res;
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail || (e as { message?: string })?.message || "Backtest failed";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = () => { setResult(null); setError(null); };

  return { result, loading, error, run, clear };
}
