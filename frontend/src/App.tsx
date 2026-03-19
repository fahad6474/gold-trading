import { useState, useEffect, useCallback } from "react";
import { RefreshCw, BarChart2, TrendingUp, Terminal, Activity, Loader2, AlertCircle } from "lucide-react";
import Chart from "./components/Chart";
import IndicatorPanel from "./components/IndicatorPanel";
import BacktestPanel from "./components/BacktestPanel";
import ResultsPanel from "./components/ResultsPanel";
import StrategyEditor from "./components/StrategyEditor";
import PineScriptEditor from "./components/PineScriptEditor";
import { useMarketData } from "./hooks/useMarketData";
import { calculateIndicators } from "./services/api";
import type { IndicatorConfig, IndicatorSeries, BacktestResult } from "./types";

const SYMBOLS = [
  { value: "GC=F", label: "Gold (XAUUSD)" },
  { value: "BTC-USD", label: "Bitcoin (BTC-USD)" },
  { value: "SI=F", label: "Silver (XAGUSD)" },
  { value: "CL=F", label: "Crude Oil (WTI)" },
  { value: "ETH-USD", label: "Ethereum (ETH-USD)" },
];

const TIMEFRAMES = [
  { value: "1d", label: "1D" },
  { value: "4h", label: "4H" },
  { value: "1h", label: "1H" },
  { value: "30m", label: "30M" },
  { value: "15m", label: "15M" },
  { value: "5m", label: "5M" },
  { value: "1w", label: "1W" },
];

type TabType = "backtest" | "python" | "pine";

const today = new Date().toISOString().split("T")[0];
const oneYearAgo = new Date(Date.now() - 365 * 86400 * 1000).toISOString().split("T")[0];

export default function App() {
  const [symbol, setSymbol] = useState("GC=F");
  const [timeframe, setTimeframe] = useState("1d");
  const [start, setStart] = useState(oneYearAgo);
  const [end, setEnd] = useState(today);
  const [tab, setTab] = useState<TabType>("backtest");
  const [indicators, setIndicators] = useState<IndicatorConfig[]>([]);
  const [indicatorData, setIndicatorData] = useState<IndicatorSeries[]>([]);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [indicatorLoading, setIndicatorLoading] = useState(false);

  const { bars, loading, error, reload } = useMarketData(symbol, timeframe, start, end);

  const loadIndicators = useCallback(async () => {
    if (indicators.length === 0 || bars.length === 0) {
      setIndicatorData([]);
      return;
    }
    setIndicatorLoading(true);
    try {
      const payload = indicators.map((ind) => ({ name: ind.name, params: ind.params }));
      const res = await calculateIndicators(symbol, timeframe, payload, start, end);
      setIndicatorData(res.indicators);
    } catch {
      // silently fail
    } finally {
      setIndicatorLoading(false);
    }
  }, [indicators, symbol, timeframe, start, end, bars.length]);

  useEffect(() => { loadIndicators(); }, [loadIndicators]);

  useEffect(() => {
    setBacktestResult(null);
    setBacktestError(null);
  }, [symbol, timeframe, start, end]);

  const latestBar = bars[bars.length - 1];
  const prevBar = bars[bars.length - 2];
  const priceChange = latestBar && prevBar ? latestBar.close - prevBar.close : 0;
  const pricePct = prevBar ? (priceChange / prevBar.close) * 100 : 0;

  return (
    <div className="min-h-screen bg-dark-200 flex flex-col">
      {/* Header */}
      <header className="bg-dark-400 border-b border-dark-500 px-4 py-2 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <BarChart2 className="text-yellow-500" size={20} />
            <span className="text-sm font-bold text-gray-100">Gold &amp; Crypto Backtest Dashboard</span>
          </div>
          {latestBar && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">{SYMBOLS.find((s) => s.value === symbol)?.label}</span>
              <span className="font-bold text-gray-100">
                ${latestBar.close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className={`text-xs ${priceChange >= 0 ? "text-green-400" : "text-red-400"}`}>
                {priceChange >= 0 ? "▲" : "▼"} {Math.abs(pricePct).toFixed(2)}%
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {SYMBOLS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <div className="flex gap-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setTimeframe(tf.value)}
                className={`btn text-xs px-2 py-1 ${timeframe === tf.value ? "bg-blue-600 text-white" : "btn-ghost"}`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <input type="date" className="input" value={start} onChange={(e) => setStart(e.target.value)} />
          <input type="date" className="input" value={end} onChange={(e) => setEnd(e.target.value)} />

          <button className="btn-ghost flex items-center gap-1" onClick={reload} title="Reload data">
            <RefreshCw size={14} />
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex-1 flex overflow-hidden" style={{ minHeight: 0 }}>
        {/* Left sidebar */}
        <aside className="w-64 border-r border-dark-500 p-3 overflow-y-auto flex-shrink-0">
          <IndicatorPanel active={indicators} onChange={setIndicators} />
        </aside>

        {/* Center content */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Chart area */}
          <div className="panel m-3 overflow-hidden flex-shrink-0">
            <div className="flex items-center justify-between px-3 py-2 border-b border-dark-500">
              <div className="flex items-center gap-2">
                <TrendingUp size={14} className="text-yellow-500" />
                <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                  {SYMBOLS.find((s) => s.value === symbol)?.label} &middot; {timeframe.toUpperCase()}
                </span>
                {indicatorLoading && <Loader2 size={12} className="animate-spin text-gray-400" />}
              </div>
              <span className="text-xs text-gray-500">{bars.length} bars</span>
            </div>

            {loading && (
              <div className="flex items-center justify-center h-64 text-gray-400">
                <Loader2 className="animate-spin mr-2" size={20} />
                Loading {symbol} data...
              </div>
            )}
            {error && (
              <div className="flex items-center justify-center h-64 text-red-400 gap-2">
                <AlertCircle size={20} />
                <span className="text-sm">{error}</span>
              </div>
            )}
            {!loading && !error && bars.length > 0 && (
              <Chart
                bars={bars}
                indicators={indicatorData}
                trades={backtestResult?.trades ?? []}
                height={360}
              />
            )}
          </div>

          {/* Tabs */}
          <div className="px-3 flex-1">
            <div className="flex gap-1 border-b border-dark-500 mb-3">
              {[
                { id: "backtest", label: "Backtest", icon: <BarChart2 size={14} /> },
                { id: "python", label: "Python Script", icon: <Terminal size={14} /> },
                { id: "pine", label: "Pine Script", icon: <Activity size={14} /> },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id as TabType)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
                    tab === t.id
                      ? "border-blue-500 text-blue-400"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}
                >
                  {t.icon}
                  {t.label}
                </button>
              ))}
            </div>

            <div className="pb-6">
              {tab === "backtest" && (
                <div className="flex flex-col gap-4">
                  <BacktestPanel
                    symbol={symbol}
                    timeframe={timeframe}
                    start={start}
                    end={end}
                    onResult={(r) => { setBacktestResult(r); setBacktestError(null); }}
                    onError={setBacktestError}
                  />
                  {backtestError && (
                    <div className="panel p-3 text-red-300 flex items-start gap-2">
                      <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                      <pre className="whitespace-pre-wrap text-xs">{backtestError}</pre>
                    </div>
                  )}
                  {backtestResult && <ResultsPanel result={backtestResult} />}
                </div>
              )}
              {tab === "python" && (
                <StrategyEditor symbol={symbol} timeframe={timeframe} start={start} end={end} />
              )}
              {tab === "pine" && (
                <PineScriptEditor symbol={symbol} timeframe={timeframe} start={start} end={end} />
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-dark-400 border-t border-dark-500 px-4 py-1.5 flex items-center justify-between text-xs text-gray-500">
        <span>Gold &amp; Crypto Backtest Dashboard</span>
        <span>Data: Yahoo Finance &middot; Engine: vectorbt &middot; Charts: TradingView Lightweight Charts</span>
      </footer>
    </div>
  );
}
