import axios from "axios";
import type { BacktestResult, ExecuteResult, IndicatorSeries, OHLCVBar } from "../types";

const BASE = "http://localhost:8000";

const api = axios.create({ baseURL: BASE });

export const fetchOHLCV = async (
  symbol: string,
  timeframe: string,
  start?: string,
  end?: string
): Promise<OHLCVBar[]> => {
  const params: Record<string, string> = { timeframe };
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await api.get(`/api/data/${symbol}`, { params });
  return res.data.bars;
};

export const fetchSymbols = async () => {
  const res = await api.get("/api/symbols");
  return res.data.symbols;
};

export const fetchIndicatorList = async () => {
  const res = await api.get("/api/indicators");
  return res.data.indicators;
};

export const calculateIndicators = async (
  symbol: string,
  timeframe: string,
  indicators: { name: string; params: Record<string, number | string> }[],
  start?: string,
  end?: string
): Promise<{ indicators: IndicatorSeries[]; errors: { indicator: string; error: string }[] }> => {
  const res = await api.post("/api/indicators", { symbol, timeframe, indicators, start, end });
  return res.data;
};

export const runBacktest = async (payload: {
  symbol: string;
  timeframe: string;
  strategy_code: string;
  start?: string;
  end?: string;
  initial_capital?: number;
  commission?: number;
}): Promise<BacktestResult> => {
  const res = await api.post("/api/backtest", payload);
  return res.data;
};

export const executeScript = async (payload: {
  code: string;
  language: "python" | "pine";
  symbol?: string;
  timeframe?: string;
  start?: string;
  end?: string;
}): Promise<ExecuteResult> => {
  const res = await api.post("/api/execute", payload);
  return res.data;
};

export const wsPrice = (symbol: string, onMessage: (data: unknown) => void): WebSocket => {
  const ws = new WebSocket(`ws://localhost:8000/ws/price/${symbol}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
};
