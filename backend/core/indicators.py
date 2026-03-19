"""
Technical indicator library using TA-Lib.
Returns indicator values as lists of {time, value} dicts for the frontend.
"""
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import talib


INDICATOR_REGISTRY = {
    "SMA": {"description": "Simple Moving Average", "params": {"length": 20}, "panel": "main", "color": "#2196F3"},
    "EMA": {"description": "Exponential Moving Average", "params": {"length": 20}, "panel": "main", "color": "#FF9800"},
    "RSI": {"description": "Relative Strength Index", "params": {"length": 14}, "panel": "sub", "color": "#9C27B0"},
    "MACD": {"description": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}, "panel": "sub", "color": "#00BCD4"},
    "BBANDS": {"description": "Bollinger Bands", "params": {"length": 20, "std": 2}, "panel": "main", "color": "#607D8B"},
    "ATR": {"description": "Average True Range", "params": {"length": 14}, "panel": "sub", "color": "#F44336"},
    "STOCH": {"description": "Stochastic Oscillator", "params": {"k": 5, "d": 3}, "panel": "sub", "color": "#795548"},
    "OBV": {"description": "On-Balance Volume", "params": {}, "panel": "sub", "color": "#4CAF50"},
    "CCI": {"description": "Commodity Channel Index", "params": {"length": 20}, "panel": "sub", "color": "#FF5722"},
    "WILLIAMS": {"description": "Williams %R", "params": {"length": 14}, "panel": "sub", "color": "#673AB7"},
    "ADX": {"description": "Average Directional Index", "params": {"length": 14}, "panel": "sub", "color": "#009688"},
    "MOM": {"description": "Momentum", "params": {"length": 10}, "panel": "sub", "color": "#FF4081"},
    "ROC": {"description": "Rate of Change", "params": {"length": 10}, "panel": "sub", "color": "#8BC34A"},
}


def _to_series(arr: np.ndarray, index: pd.DatetimeIndex) -> List[Dict]:
    result = []
    for ts, val in zip(index, arr):
        if val is not None and not np.isnan(val):
            result.append({"time": int(ts.timestamp()), "value": round(float(val), 6)})
    return result


def compute_indicator(df: pd.DataFrame, name: str, params: Dict[str, Any]) -> List[Dict]:
    name_upper = name.upper()
    index = df.index
    c = df["close"].values.astype(float)
    h = df["high"].values.astype(float)
    l = df["low"].values.astype(float)
    v = df["volume"].values.astype(float)
    series_list = []

    if name_upper == "SMA":
        length = int(params.get("length", 20))
        result = talib.SMA(c, timeperiod=length)
        series_list.append({"name": f"SMA({length})", "data": _to_series(result, index), "panel": "main", "color": "#2196F3"})

    elif name_upper == "EMA":
        length = int(params.get("length", 20))
        result = talib.EMA(c, timeperiod=length)
        series_list.append({"name": f"EMA({length})", "data": _to_series(result, index), "panel": "main", "color": "#FF9800"})

    elif name_upper == "RSI":
        length = int(params.get("length", 14))
        result = talib.RSI(c, timeperiod=length)
        series_list.append({"name": f"RSI({length})", "data": _to_series(result, index), "panel": "sub", "color": "#9C27B0"})

    elif name_upper == "MACD":
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
        macd, signal_line, hist = talib.MACD(c, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        series_list.append({"name": "MACD", "data": _to_series(macd, index), "panel": "sub", "color": "#2196F3"})
        series_list.append({"name": "Signal", "data": _to_series(signal_line, index), "panel": "sub", "color": "#FF9800"})
        series_list.append({"name": "Histogram", "data": _to_series(hist, index), "panel": "sub", "color": "#4CAF50", "type": "histogram"})

    elif name_upper == "BBANDS":
        length = int(params.get("length", 20))
        std = float(params.get("std", 2.0))
        upper, mid, lower = talib.BBANDS(c, timeperiod=length, nbdevup=std, nbdevdn=std)
        color = "#607D8B"
        series_list.append({"name": "BB Upper", "data": _to_series(upper, index), "panel": "main", "color": color})
        series_list.append({"name": "BB Mid", "data": _to_series(mid, index), "panel": "main", "color": "#90A4AE"})
        series_list.append({"name": "BB Lower", "data": _to_series(lower, index), "panel": "main", "color": color})

    elif name_upper == "ATR":
        length = int(params.get("length", 14))
        result = talib.ATR(h, l, c, timeperiod=length)
        series_list.append({"name": f"ATR({length})", "data": _to_series(result, index), "panel": "sub", "color": "#F44336"})

    elif name_upper == "STOCH":
        k = int(params.get("k", 5))
        d = int(params.get("d", 3))
        slowk, slowd = talib.STOCH(h, l, c, fastk_period=k, slowk_period=3, slowd_period=d)
        series_list.append({"name": "%K", "data": _to_series(slowk, index), "panel": "sub", "color": "#795548"})
        series_list.append({"name": "%D", "data": _to_series(slowd, index), "panel": "sub", "color": "#FF9800"})

    elif name_upper == "OBV":
        result = talib.OBV(c, v)
        series_list.append({"name": "OBV", "data": _to_series(result, index), "panel": "sub", "color": "#4CAF50"})

    elif name_upper == "CCI":
        length = int(params.get("length", 20))
        result = talib.CCI(h, l, c, timeperiod=length)
        series_list.append({"name": f"CCI({length})", "data": _to_series(result, index), "panel": "sub", "color": "#FF5722"})

    elif name_upper == "WILLIAMS":
        length = int(params.get("length", 14))
        result = talib.WILLR(h, l, c, timeperiod=length)
        series_list.append({"name": f"Williams%R({length})", "data": _to_series(result, index), "panel": "sub", "color": "#673AB7"})

    elif name_upper == "ADX":
        length = int(params.get("length", 14))
        result = talib.ADX(h, l, c, timeperiod=length)
        series_list.append({"name": f"ADX({length})", "data": _to_series(result, index), "panel": "sub", "color": "#009688"})

    elif name_upper == "MOM":
        length = int(params.get("length", 10))
        result = talib.MOM(c, timeperiod=length)
        series_list.append({"name": f"MOM({length})", "data": _to_series(result, index), "panel": "sub", "color": "#FF4081"})

    elif name_upper == "ROC":
        length = int(params.get("length", 10))
        result = talib.ROC(c, timeperiod=length)
        series_list.append({"name": f"ROC({length})", "data": _to_series(result, index), "panel": "sub", "color": "#8BC34A"})

    else:
        raise ValueError(f"Unknown indicator: {name}. Available: {list(INDICATOR_REGISTRY.keys())}")

    return series_list


def list_indicators() -> List[Dict]:
    return [{"name": k, **v} for k, v in INDICATOR_REGISTRY.items()]
