import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { BacktestResult } from "../types";

interface ResultsPanelProps {
  result: BacktestResult;
}

function MetricCard({ label, value, color = "text-gray-100" }: { label: string; value: string; color?: string }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${color}`}>{value}</div>
    </div>
  );
}

export default function ResultsPanel({ result }: ResultsPanelProps) {
  const {
    total_return_pct,
    total_return,
    sharpe_ratio,
    max_drawdown_pct,
    win_rate,
    total_trades,
    profit_factor,
    equity_curve,
    trades,
    final_value,
    initial_capital,
  } = result;

  const isPositive = total_return >= 0;

  const chartData = equity_curve.map((p) => ({
    date: new Date(p.time * 1000).toLocaleDateString(),
    value: p.value,
  }));

  return (
    <div className="flex flex-col gap-4">
      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <MetricCard
          label="Total Return"
          value={`${isPositive ? "+" : ""}${total_return_pct.toFixed(2)}%`}
          color={isPositive ? "text-green-400" : "text-red-400"}
        />
        <MetricCard
          label="Net P&L"
          value={`$${isPositive ? "+" : ""}${total_return.toFixed(2)}`}
          color={isPositive ? "text-green-400" : "text-red-400"}
        />
        <MetricCard
          label="Final Value"
          value={`$${final_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        />
        <MetricCard label="Initial Capital" value={`$${initial_capital.toLocaleString()}`} />
        <MetricCard
          label="Sharpe Ratio"
          value={sharpe_ratio.toFixed(3)}
          color={sharpe_ratio >= 1 ? "text-green-400" : sharpe_ratio >= 0 ? "text-yellow-400" : "text-red-400"}
        />
        <MetricCard
          label="Max Drawdown"
          value={`${max_drawdown_pct.toFixed(2)}%`}
          color={max_drawdown_pct < -20 ? "text-red-400" : "text-yellow-400"}
        />
        <MetricCard
          label="Win Rate"
          value={`${win_rate.toFixed(1)}%`}
          color={win_rate >= 50 ? "text-green-400" : "text-red-400"}
        />
        <MetricCard label="Profit Factor" value={profit_factor != null ? profit_factor.toFixed(2) : "—"} />
        <MetricCard label="Total Trades" value={String(total_trades)} />
      </div>

      {/* Equity Curve */}
      <div className="panel p-3">
        <div className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-3">Equity Curve</div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3f54" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#9ca3af", fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#1b2838", border: "1px solid #2a3f54", color: "#f3f4f6" }}
              formatter={(v) => [`$${Number(v).toFixed(2)}`, "Portfolio Value"]}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={isPositive ? "#26a69a" : "#ef5350"}
              fill={isPositive ? "rgba(38,166,154,0.15)" : "rgba(239,83,80,0.15)"}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Trades table */}
      {trades.length > 0 && (
        <div className="panel p-3">
          <div className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-3">
            Trades ({trades.length})
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-dark-500">
                  <th className="text-left py-1 pr-3">Entry</th>
                  <th className="text-left py-1 pr-3">Exit</th>
                  <th className="text-right py-1 pr-3">Entry $</th>
                  <th className="text-right py-1 pr-3">Exit $</th>
                  <th className="text-right py-1 pr-3">P&L</th>
                  <th className="text-right py-1">Return %</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice(0, 50).map((t, i) => (
                  <tr key={i} className="border-b border-dark-500/50 hover:bg-dark-300/50">
                    <td className="py-1 pr-3 text-gray-300">
                      {new Date(t.entry_time * 1000).toLocaleDateString()}
                    </td>
                    <td className="py-1 pr-3 text-gray-300">
                      {new Date(t.exit_time * 1000).toLocaleDateString()}
                    </td>
                    <td className="py-1 pr-3 text-right">${t.entry_price.toFixed(2)}</td>
                    <td className="py-1 pr-3 text-right">${t.exit_price.toFixed(2)}</td>
                    <td className={`py-1 pr-3 text-right ${t.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}
                    </td>
                    <td className={`py-1 text-right ${t.pnl_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {t.pnl_pct >= 0 ? "+" : ""}{t.pnl_pct.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {trades.length > 50 && (
              <div className="text-xs text-gray-500 mt-2 text-center">
                Showing 50 of {trades.length} trades
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
