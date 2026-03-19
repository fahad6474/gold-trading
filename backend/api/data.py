from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.data_fetcher import fetch_ohlcv, list_symbols, get_latest_price

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/symbols")
def get_symbols():
    """List all supported trading symbols."""
    return {"symbols": list_symbols()}


@router.get("/data/{symbol}")
def get_ohlcv(
    symbol: str,
    timeframe: str = Query("1d", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w"),
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """Fetch historical OHLCV data for a symbol."""
    try:
        df = fetch_ohlcv(symbol, timeframe, start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {str(e)}")

    bars = []
    for ts, row in df.iterrows():
        bars.append({
            "time": int(ts.timestamp()),
            "open": round(float(row["open"]), 4),
            "high": round(float(row["high"]), 4),
            "low": round(float(row["low"]), 4),
            "close": round(float(row["close"]), 4),
            "volume": round(float(row["volume"]), 2),
        })

    return {"symbol": symbol, "timeframe": timeframe, "bars": bars}


@router.get("/price/{symbol}")
def get_latest(symbol: str):
    """Get the latest price for a symbol."""
    try:
        return get_latest_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
