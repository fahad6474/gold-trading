"""
Backtesting engine using vectorbt (vectorized, fast).
Strategies are written as Python code strings that produce `entries` and `exits` boolean Series.
"""
import traceback
from typing import Optional
import numpy as np
import pandas as pd

from .data_fetcher import fetch_ohlcv
from .executor import run_strategy_code


def run_backtest(
    symbol: str,
    timeframe: str,
    strategy_code: str,
    start: Optional[str] = "2022-01-01",
    end: Optional[str] = None,
    initial_capital: float = 10000.0,
    commission: float = 0.001,
) -> dict:
    """
    Run a backtest and return performance metrics + equity curve + trades.
    Strategy code must set `entries` and `exits` as boolean pandas Series.
    """
    # Fetch data
    df = fetch_ohlcv(symbol, timeframe, start, end)
    if df.empty:
        raise ValueError("No data available for the selected period")

    # Execute strategy to get entries/exits
    result = run_strategy_code(strategy_code, df)
    if not result["success"]:
        raise ValueError(f"Strategy error: {result['stderr']}")

    entries = result.get("entries")
    exits = result.get("exits")

    if entries is None or exits is None:
        raise ValueError(
            "Strategy must define `entries` (buy signals) and `exits` (sell signals) as boolean pandas Series.\n"
            "Example:\n"
            "  fast = close.rolling(10).mean()\n"
            "  slow = close.rolling(30).mean()\n"
            "  entries = fast > slow\n"
            "  exits = fast < slow"
        )

    # Align index
    entries = entries.reindex(df.index).fillna(False).astype(bool)
    exits = exits.reindex(df.index).fillna(False).astype(bool)

    # Run vectorbt backtest
    try:
        import vectorbt as vbt
        pf = vbt.Portfolio.from_signals(
            df["close"],
            entries,
            exits,
            init_cash=initial_capital,
            fees=commission,
            freq=_vbt_freq(timeframe),
        )
        return _extract_metrics(pf, df, initial_capital)
    except ImportError:
        # Fallback: simple manual backtest if vectorbt not available
        return _simple_backtest(df, entries, exits, initial_capital, commission)
    except Exception as e:
        # Fallback on vectorbt errors
        return _simple_backtest(df, entries, exits, initial_capital, commission)


def _vbt_freq(timeframe: str) -> str:
    freq_map = {
        "1m": "1T", "5m": "5T", "15m": "15T", "30m": "30T",
        "1h": "1H", "4h": "4H", "1d": "1D", "1w": "1W"
    }
    return freq_map.get(timeframe, "1D")


def _extract_metrics(pf, df: pd.DataFrame, initial_capital: float) -> dict:
    """Extract metrics from a vectorbt Portfolio object."""
    stats = pf.stats()

    total_return = float(pf.total_return())
    final_value = initial_capital * (1 + total_return)

    try:
        sharpe = float(pf.sharpe_ratio())
        if np.isnan(sharpe):
            sharpe = 0.0
    except Exception:
        sharpe = 0.0

    try:
        max_dd = float(pf.max_drawdown())
    except Exception:
        max_dd = 0.0

    # Equity curve
    equity = pf.value()
    equity_curve = [
        {"time": int(ts.timestamp()), "value": round(float(v), 2)}
        for ts, v in zip(equity.index, equity.values)
        if not np.isnan(v)
    ]

    # Trades
    trades_list = []
    try:
        trades = pf.trades.records_readable
        for _, row in trades.iterrows():
            entry_t = row.get("Entry Timestamp") or row.get("entry_time")
            exit_t = row.get("Exit Timestamp") or row.get("exit_time")
            entry_p = float(row.get("Avg Entry Price", row.get("entry_price", 0)))
            exit_p = float(row.get("Avg Exit Price", row.get("exit_price", 0)))
            pnl = float(row.get("PnL", 0))
            ret = float(row.get("Return", 0))
            trades_list.append({
                "entry_time": int(pd.Timestamp(entry_t).timestamp()) if entry_t else 0,
                "exit_time": int(pd.Timestamp(exit_t).timestamp()) if exit_t else 0,
                "entry_price": round(entry_p, 4),
                "exit_price": round(exit_p, 4),
                "pnl": round(pnl, 2),
                "pnl_pct": round(ret * 100, 2),
                "side": "long",
            })
    except Exception:
        pass

    win_rate = 0.0
    profit_factor = None
    if trades_list:
        winners = [t for t in trades_list if t["pnl"] > 0]
        losers = [t for t in trades_list if t["pnl"] < 0]
        win_rate = len(winners) / len(trades_list) * 100
        gross_profit = sum(t["pnl"] for t in winners)
        gross_loss = abs(sum(t["pnl"] for t in losers))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else None

    return {
        "total_return": round(total_return * initial_capital, 2),
        "total_return_pct": round(total_return * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown": round(max_dd * initial_capital, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(trades_list),
        "profit_factor": profit_factor,
        "equity_curve": equity_curve,
        "trades": trades_list,
        "final_value": round(final_value, 2),
        "initial_capital": initial_capital,
    }


def _simple_backtest(
    df: pd.DataFrame,
    entries: pd.Series,
    exits: pd.Series,
    initial_capital: float,
    commission: float,
) -> dict:
    """Simple fallback backtester (no vectorbt dependency)."""
    cash = initial_capital
    shares = 0.0
    in_position = False
    entry_price = 0.0
    entry_time = None
    trades = []
    equity_values = []

    for ts, row in df.iterrows():
        price = row["close"]
        is_entry = bool(entries.get(ts, False))
        is_exit = bool(exits.get(ts, False))

        if not in_position and is_entry:
            cost = cash * (1 - commission)
            shares = cost / price
            cash = 0.0
            entry_price = price
            entry_time = ts
            in_position = True
        elif in_position and is_exit:
            proceeds = shares * price * (1 - commission)
            pnl = proceeds - (shares * entry_price)
            trades.append({
                "entry_time": int(entry_time.timestamp()),
                "exit_time": int(ts.timestamp()),
                "entry_price": round(entry_price, 4),
                "exit_price": round(price, 4),
                "pnl": round(pnl, 2),
                "pnl_pct": round((price / entry_price - 1) * 100, 2),
                "side": "long",
            })
            cash = proceeds
            shares = 0.0
            in_position = False

        portfolio_value = cash + shares * price
        equity_values.append({"time": int(ts.timestamp()), "value": round(portfolio_value, 2)})

    final_value = equity_values[-1]["value"] if equity_values else initial_capital
    total_return = final_value - initial_capital
    total_return_pct = (final_value / initial_capital - 1) * 100

    # Compute max drawdown
    equity_series = pd.Series([e["value"] for e in equity_values])
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    max_dd_pct = float(drawdown.min() * 100) if not drawdown.empty else 0.0

    winners = [t for t in trades if t["pnl"] > 0]
    losers = [t for t in trades if t["pnl"] < 0]
    win_rate = len(winners) / len(trades) * 100 if trades else 0.0
    gross_profit = sum(t["pnl"] for t in winners)
    gross_loss = abs(sum(t["pnl"] for t in losers))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else None

    # Simple Sharpe (annualized)
    if len(equity_series) > 1:
        daily_returns = equity_series.pct_change().dropna()
        sharpe = float(daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0.0
    else:
        sharpe = 0.0

    return {
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown": round(max_dd_pct / 100 * initial_capital, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(trades),
        "profit_factor": profit_factor,
        "equity_curve": equity_values,
        "trades": trades,
        "final_value": round(final_value, 2),
        "initial_capital": initial_capital,
    }
