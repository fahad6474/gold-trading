import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import type { BacktestResult } from "../types";
import { runBacktest } from "../services/api";

const DEFAULT_STRATEGY = `# Moving Average Crossover Strategy
# Available: close, open_, high, low, volume, df, pd, np, ta

fast_ma = close.rolling(10).mean()
slow_ma = close.rolling(30).mean()

entries = fast_ma > slow_ma
exits = fast_ma < slow_ma
`;

interface BacktestPanelProps {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  onResult: (result: BacktestResult) => void;
  onError: (msg: string) => void;
}

export default function BacktestPanel({ symbol, timeframe, start, end, onResult, onError }: BacktestPanelProps) {
  const [code, setCode] = useState(DEFAULT_STRATEGY);
  const [capital, setCapital] = useState("10000");
  const [commission, setCommission] = useState("0.001");
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const result = await runBacktest({
        symbol,
        timeframe,
        strategy_code: code,
        start,
        end,
        initial_capital: parseFloat(capital),
        commission: parseFloat(commission),
      });
      onResult(result);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail || (e as { message?: string })?.message || "Unknown error";
      onError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel p-3 flex flex-col gap-3">
      <div className="text-xs font-bold text-gray-300 uppercase tracking-wider">Strategy (Python)</div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="label">Initial Capital ($)</label>
          <input
            type="number"
            className="input w-full"
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
          />
        </div>
        <div className="flex-1">
          <label className="label">Commission (e.g. 0.001 = 0.1%)</label>
          <input
            type="number"
            step="0.0001"
            className="input w-full"
            value={commission}
            onChange={(e) => setCommission(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="label">Strategy Code</label>
        <textarea
          className="input w-full font-mono text-xs"
          rows={10}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          style={{ resize: "vertical" }}
        />
        <div className="text-xs text-gray-500 mt-1">
          Variables: <code className="text-blue-400">close</code>, <code className="text-blue-400">open_</code>,{" "}
          <code className="text-blue-400">high</code>, <code className="text-blue-400">low</code>,{" "}
          <code className="text-blue-400">volume</code>, <code className="text-blue-400">pd</code>,{" "}
          <code className="text-blue-400">np</code>, <code className="text-blue-400">ta</code> (pandas_ta)
          <br />
          Must set: <code className="text-yellow-400">entries</code> and <code className="text-yellow-400">exits</code>{" "}
          (bool Series)
        </div>
      </div>

      <button className="btn-gold flex items-center justify-center gap-2" onClick={run} disabled={loading}>
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
        {loading ? "Running backtest..." : "Run Backtest"}
      </button>
    </div>
  );
}
