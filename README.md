# Gold & Crypto Backtest Dashboard

A self-hosted trading dashboard for backtesting strategies on **Gold (XAUUSD)** and **Bitcoin (BTC-USD)** with Pine Script support.

---

## Quick Start

```bash
# One command to launch everything
./start.sh
```

Then open your browser:
- **Dashboard:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

---

## Manual Start

```bash
# Terminal 1 — Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
pnpm dev
```

---

## Features

| Feature | Description |
|---|---|
| **Multi-symbol** | Gold (GC=F), Bitcoin (BTC-USD), Silver, Crude Oil, Ethereum |
| **Timeframes** | 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w |
| **13+ Indicators** | SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic, OBV, CCI, Williams %R, ADX, Momentum, ROC |
| **Backtesting** | Write Python strategies, get equity curve + full metrics |
| **Python Runtime** | Execute arbitrary Python scripts with market data injected |
| **Pine Script** | Paste TradingView Pine Script — auto-transpiled to Python and executed |
| **Charts** | TradingView Lightweight Charts — candlesticks + indicator overlays + trade markers |
| **Real-time** | WebSocket price stream for live updates |

---

## How to Use

### 1. Load a Chart

1. Select a symbol from the **top-left dropdown** (Gold XAUUSD is default)
2. Click a **timeframe button** (1D, 4H, 1H, etc.)
3. Set a **date range** with the date pickers
4. The chart loads automatically

### 2. Add Indicators

In the **left sidebar**:
1. Select an indicator from the dropdown (SMA, RSI, MACD, etc.)
2. Click **Add**
3. Adjust parameters (e.g. length, period) — the chart updates automatically
4. Click **X** to remove an indicator

**Main panel indicators** (overlaid on candles): SMA, EMA, Bollinger Bands
**Sub-panel indicators** (below chart): RSI, MACD, ATR, Stochastic, etc.

### 3. Run a Backtest

Click the **Backtest** tab:

1. Set **Initial Capital** and **Commission** (e.g. 0.001 = 0.1%)
2. Write your strategy in the **Strategy Code** box
3. Click **Run Backtest**

**Strategy template:**
```python
# Variables available: close, open_, high, low, volume, df, pd, np, ta (TA-Lib)

# Example: Simple Moving Average Crossover
fast_ma = close.rolling(10).mean()
slow_ma = close.rolling(30).mean()

# REQUIRED: define entries and exits as boolean Series
entries = fast_ma > slow_ma   # buy when fast crosses above slow
exits = fast_ma < slow_ma     # sell when fast crosses below slow
```

**More strategy examples:**
```python
# RSI-based strategy
rsi = ta.RSI(close.values, timeperiod=14)
rsi = pd.Series(rsi, index=close.index)

entries = rsi < 30   # buy when oversold
exits = rsi > 70     # sell when overbought
```

```python
# Bollinger Band breakout
upper, mid, lower = ta.BBANDS(close.values, timeperiod=20)
upper = pd.Series(upper, index=close.index)
lower = pd.Series(lower, index=close.index)

entries = close < lower   # buy at lower band touch
exits = close > upper     # sell at upper band touch
```

**Results shown:**
- Total Return, Net P&L
- Sharpe Ratio
- Max Drawdown
- Win Rate, Profit Factor
- Total Trades
- Equity Curve chart
- Full trades table (with entry/exit prices, P&L per trade)
- Trade markers on the main chart

### 4. Execute Python Scripts

Click the **Python Script** tab:

Write and run any Python code with market data available:
```python
# Explore data, compute indicators, print analysis
print(f"Bars: {len(close)}")
print(f"Latest Gold price: ${close.iloc[-1]:.2f}")

rsi = pd.Series(ta.RSI(close.values, timeperiod=14), index=close.index)
print(f"RSI(14): {rsi.iloc[-1]:.2f}")

atr = pd.Series(ta.ATR(high.values, low.values, close.values, timeperiod=14), index=close.index)
print(f"ATR(14): {atr.iloc[-1]:.2f}")
```

Click **Execute** — output, errors, and any defined variables are shown below.

### 5. Run Pine Script

Click the **Pine Script** tab:

Paste your Pine Script strategy from TradingView:
```pine
//@version=5
strategy("Gold EMA Cross", overlay=true)

fast = ta.ema(close, 10)
slow = ta.ema(close, 30)

longCondition = ta.crossover(fast, slow)
shortCondition = ta.crossunder(fast, slow)

strategy.entry("Long", strategy.long, when=longCondition)
strategy.close("Long", when=shortCondition)
```

Click **Run Pine Script**. The transpiler converts it to Python and executes it.

Click **Show Python** to see the generated Python code.

**Supported Pine Script features:**
- `ta.sma()`, `ta.ema()`, `ta.wma()`, `ta.rsi()`, `ta.atr()`, `ta.cci()`, `ta.obv()`, `ta.macd()`
- `ta.crossover()`, `ta.crossunder()`
- `ta.highest()`, `ta.lowest()`, `ta.stdev()`
- `strategy.entry()`, `strategy.close()`, `strategy.exit()`
- `math.abs()`, `math.max()`, `math.min()`, `math.sqrt()`, `math.log()`
- `nz()`, `na()`, variable declarations, `if/else`, arithmetic
- `input.int()`, `input.float()` (converted to default values)

**Not supported (will be skipped with a warning):**
- `plot()`, `plotshape()`, `alertcondition()` — use the chart panel instead
- `request.security()` — multi-timeframe not available
- `array.*`, `matrix.*`, `line.*`, `label.*`

---

## Backtest Metrics Explained

| Metric | Meaning |
|---|---|
| **Total Return %** | Percentage gain/loss over the period |
| **Net P&L** | Dollar profit or loss |
| **Final Value** | Portfolio value at end of backtest |
| **Sharpe Ratio** | Risk-adjusted return (>1 is good, >2 is excellent) |
| **Max Drawdown %** | Largest peak-to-trough loss (lower is better) |
| **Win Rate %** | Percentage of trades that were profitable |
| **Profit Factor** | Gross profit / Gross loss (>1.5 is good) |
| **Total Trades** | Number of round-trip trades executed |

---

## Available Symbols

| Symbol | Name |
|---|---|
| `GC=F` | Gold Futures (XAUUSD equivalent) |
| `BTC-USD` | Bitcoin / US Dollar |
| `SI=F` | Silver Futures |
| `CL=F` | Crude Oil (WTI) Futures |
| `ETH-USD` | Ethereum / US Dollar |

---

## API Reference

The backend API is fully documented at **http://localhost:8000/docs**

| Endpoint | Method | Description |
|---|---|---|
| `/api/symbols` | GET | List supported symbols |
| `/api/data/{symbol}` | GET | Historical OHLCV data |
| `/api/indicators` | GET | List available indicators |
| `/api/indicators` | POST | Calculate indicators |
| `/api/backtest` | POST | Run a backtest |
| `/api/execute` | POST | Execute Python/Pine Script |
| `/ws/price/{symbol}` | WebSocket | Real-time price stream |

---

## Tech Stack

- **Backend:** Python 3.11 + FastAPI + uvicorn
- **Data:** Yahoo Finance (yfinance) — free, no API key needed
- **Backtesting:** vectorbt (vectorized, high performance)
- **Indicators:** TA-Lib (130+ indicators)
- **Frontend:** React + Vite + TypeScript + TailwindCSS
- **Charts:** TradingView Lightweight Charts
- **Editor:** Monaco Editor (VS Code engine)

---

## Tips

- **Cache:** Historical data is cached in `/tmp/gold-trading-cache/` — subsequent loads are instant
- **Timeframe limits:** Short timeframes (1m, 5m) only go back 7-60 days via yfinance
- **Strategy errors:** If your strategy has an error, it's shown in red — check variable names and syntax
- **Pine Script transpiler:** Some complex Pine Script won't transpile — check the warnings panel
- **Trade markers:** After a backtest, buy/sell arrows appear on the chart
