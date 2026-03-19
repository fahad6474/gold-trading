from fastapi import APIRouter, HTTPException
from typing import Optional

from core.data_fetcher import fetch_ohlcv
from core.executor import run_free_code
from core.pine_transpiler import transpile
from models.schemas import ExecuteRequest, ExecuteResponse

router = APIRouter(prefix="/api", tags=["execute"])


@router.post("/execute", response_model=ExecuteResponse)
def execute_script(request: ExecuteRequest):
    """
    Execute a Python or Pine Script at runtime.

    For Python: Code runs with close, open_, high, low, volume, pd, np, ta available.
    For Pine Script: Code is transpiled to Python first, then executed.

    The transpiled Python code is returned in `transpiled_code` for Pine Script.
    """
    # Fetch market data if symbol provided
    df = None
    if request.symbol:
        try:
            df = fetch_ohlcv(request.symbol, request.timeframe or "1d", request.start, request.end)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Data fetch failed: {str(e)}")

    transpiled_code = None
    warnings = []

    if request.language == "pine":
        try:
            transpiled_code, warnings = transpile(request.code)
            code_to_run = transpiled_code
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Pine Script transpilation failed: {str(e)}")
    else:
        code_to_run = request.code

    result = run_free_code(code_to_run, df)

    stderr = result.get("stderr", "")
    if warnings:
        stderr = "\n".join(f"[Warning] {w}" for w in warnings) + ("\n\n" + stderr if stderr else "")

    return ExecuteResponse(
        stdout=result.get("stdout", ""),
        stderr=stderr,
        result=result.get("variables"),
        transpiled_code=transpiled_code,
        success=result.get("success", False),
    )
