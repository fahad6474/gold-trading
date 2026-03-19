"""
Data fetcher for Gold (GC=F) and BTC-USD using yfinance.
Results are cached locally to avoid repeated API calls.
"""
import os
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

CACHE_DIR = Path("/tmp/gold-trading-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Supported symbols
SYMBOLS = {
    "GC=F": "Gold Futures (XAUUSD)",
    "BTC-USD": "Bitcoin / USD",
    "SI=F": "Silver Futures",
    "CL=F": "Crude Oil Futures",
    "ETH-USD": "Ethereum / USD",
}

# yfinance interval mapping
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h",   # yfinance doesn't have 4h natively; we resample
    "1d": "1d",
    "1w": "1wk",
}

# Cache TTL in minutes
CACHE_TTL = {
    "1m": 2,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 60,
    "1d": 360,
    "1w": 1440,
}


def _cache_key(symbol: str, timeframe: str, start: str, end: str) -> str:
    key = f"{symbol}_{timeframe}_{start}_{end}"
    return hashlib.md5(key.encode()).hexdigest()


def _load_cache(cache_path: Path, ttl_minutes: int) -> Optional[pd.DataFrame]:
    if not cache_path.exists():
        return None
    age = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).total_seconds() / 60
    if age > ttl_minutes:
        return None
    try:
        df = pd.read_parquet(cache_path)
        return df
    except Exception:
        return None


def _save_cache(cache_path: Path, df: pd.DataFrame) -> None:
    try:
        df.to_parquet(cache_path)
    except Exception:
        pass


def fetch_ohlcv(
    symbol: str,
    timeframe: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a symbol. Returns a DataFrame with columns:
    [open, high, low, close, volume] indexed by datetime.
    """
    if symbol not in SYMBOLS:
        raise ValueError(f"Unsupported symbol: {symbol}. Choose from: {list(SYMBOLS.keys())}")
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Choose from: {list(TIMEFRAME_MAP.keys())}")

    # Default date range
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    if start is None:
        start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    cache_path = CACHE_DIR / f"{_cache_key(symbol, timeframe, start, end)}.parquet"
    ttl = CACHE_TTL.get(timeframe, 60)

    cached = _load_cache(cache_path, ttl)
    if cached is not None:
        return cached

    interval = TIMEFRAME_MAP[timeframe]
    ticker = yf.Ticker(symbol)

    df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data returned for {symbol} with interval {interval}")

    # Standardize column names
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume"
    })
    df = df[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # Resample 4h from 1h data
    if timeframe == "4h":
        df = df.resample("4h").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum"
        }).dropna()

    _save_cache(cache_path, df)
    return df


def get_latest_price(symbol: str) -> dict:
    """Get the latest price tick for a symbol."""
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    return {
        "symbol": symbol,
        "price": float(info.last_price) if info.last_price else None,
        "timestamp": int(datetime.now().timestamp()),
    }


def list_symbols() -> list:
    return [{"symbol": k, "name": v} for k, v in SYMBOLS.items()]
