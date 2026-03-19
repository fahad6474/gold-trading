from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from core.data_fetcher import fetch_ohlcv
from core.indicators import compute_indicator, list_indicators
from models.schemas import IndicatorRequest

router = APIRouter(prefix="/api", tags=["indicators"])


@router.get("/indicators")
def get_indicator_list():
    """List all available indicators with their parameters."""
    return {"indicators": list_indicators()}


@router.post("/indicators")
def calculate_indicators(request: IndicatorRequest):
    """Calculate one or more indicators on a symbol's data."""
    try:
        df = fetch_ohlcv(request.symbol, request.timeframe, request.start, request.end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {str(e)}")

    result_series = []
    errors = []

    for ind_config in request.indicators:
        name = ind_config.get("name", "")
        params = ind_config.get("params", {})
        try:
            series = compute_indicator(df, name, params)
            result_series.extend(series)
        except Exception as e:
            errors.append({"indicator": name, "error": str(e)})

    return {"indicators": result_series, "errors": errors}
