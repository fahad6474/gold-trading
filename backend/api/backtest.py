from fastapi import APIRouter, HTTPException

from core.backtester import run_backtest
from models.schemas import BacktestRequest

router = APIRouter(prefix="/api", tags=["backtest"])


@router.post("/backtest")
def backtest(request: BacktestRequest):
    """
    Run a backtest with a Python strategy.

    The strategy code receives these variables:
      - close, open_, high, low, volume  (pandas Series)
      - df  (full OHLCV DataFrame)
      - pd, np, ta  (pandas, numpy, pandas_ta)

    The strategy must set:
      - entries  (bool Series) — buy signals
      - exits    (bool Series) — sell signals

    Example strategy:
        fast = close.rolling(10).mean()
        slow = close.rolling(30).mean()
        entries = fast > slow
        exits = fast < slow
    """
    try:
        result = run_backtest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            strategy_code=request.strategy_code,
            start=request.start,
            end=request.end,
            initial_capital=request.initial_capital,
            commission=request.commission,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

    return result
