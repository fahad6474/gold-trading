export interface OHLCVBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSeries {
  name: string;
  data: { time: number; value: number }[];
  panel: "main" | "sub";
  color?: string;
  type?: "line" | "histogram";
}

export interface IndicatorConfig {
  id: string;
  name: string;
  params: Record<string, number | string>;
  panel: "main" | "sub";
  color?: string;
}

export interface TradeRecord {
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  side: string;
}

export interface BacktestResult {
  total_return: number;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  win_rate: number;
  total_trades: number;
  profit_factor: number | null;
  equity_curve: { time: number; value: number }[];
  trades: TradeRecord[];
  final_value: number;
  initial_capital: number;
}

export interface ExecuteResult {
  stdout: string;
  stderr: string;
  result: Record<string, unknown> | null;
  transpiled_code: string | null;
  success: boolean;
}

export type Symbol = "GC=F" | "BTC-USD" | "SI=F" | "CL=F" | "ETH-USD";
export type Timeframe = "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d" | "1w";

export interface SymbolInfo {
  symbol: string;
  name: string;
}
