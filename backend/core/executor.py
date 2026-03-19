"""
Safe Python script execution sandbox.
Restricts dangerous builtins and injects trading data + libraries.
"""
import io
import sys
import threading
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional

import numpy as np
import pandas as pd
import talib as ta


# Safe builtins whitelist
SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "isinstance": isinstance,
    "type": type,
    "hasattr": hasattr,
    "getattr": getattr,
    "any": any,
    "all": all,
    "None": None,
    "True": True,
    "False": False,
    "__build_class__": __build_class__,
    "__name__": "__main__",
}


def run_strategy_code(
    code: str,
    df: pd.DataFrame,
    timeout_seconds: int = 30,
) -> dict:
    """
    Execute strategy code with OHLCV data injected.
    The code has access to: close, open_, high, low, volume, df, pd, np, ta
    It should set `entries` and `exits` as boolean pandas Series.
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Inject context
    exec_globals = {
        "__builtins__": SAFE_BUILTINS,
        "pd": pd,
        "np": np,
        "ta": ta,
        "df": df,
        "close": df["close"].copy(),
        "open_": df["open"].copy(),
        "high": df["high"].copy(),
        "low": df["low"].copy(),
        "volume": df["volume"].copy(),
        "index": df.index,
    }

    result = {"success": False, "stdout": "", "stderr": "", "entries": None, "exits": None}
    exception_holder = [None]

    def _exec():
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compile(code, "<strategy>", "exec"), exec_globals)  # noqa: S102
            result["entries"] = exec_globals.get("entries")
            result["exits"] = exec_globals.get("exits")
            result["success"] = True
        except Exception:
            exception_holder[0] = traceback.format_exc()

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        result["stderr"] = "Execution timed out (30s limit)"
        return result

    result["stdout"] = stdout_capture.getvalue()
    result["stderr"] = stderr_capture.getvalue()

    if exception_holder[0]:
        result["stderr"] += exception_holder[0]
        result["success"] = False

    return result


def run_free_code(
    code: str,
    df: Optional[pd.DataFrame] = None,
    timeout_seconds: int = 30,
) -> dict:
    """
    Execute arbitrary Python code (for the Execute tab, not just strategy backtest).
    Returns stdout, stderr, and any named variables.
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    exec_globals = {
        "__builtins__": SAFE_BUILTINS,
        "pd": pd,
        "np": np,
        "ta": ta,
    }

    if df is not None:
        exec_globals.update({
            "df": df,
            "close": df["close"].copy(),
            "open_": df["open"].copy(),
            "high": df["high"].copy(),
            "low": df["low"].copy(),
            "volume": df["volume"].copy(),
            "index": df.index,
        })

    result = {"success": False, "stdout": "", "stderr": ""}
    exception_holder = [None]

    def _exec():
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compile(code, "<script>", "exec"), exec_globals)  # noqa: S102
            result["success"] = True
            # Capture any user-defined variables (non-internal, non-module)
            user_vars = {}
            for k, v in exec_globals.items():
                if k.startswith("_") or k in ("pd", "np", "ta", "df", "close", "open_", "high", "low", "volume", "index"):
                    continue
                try:
                    if isinstance(v, (int, float, str, bool, list, dict)):
                        user_vars[k] = v
                    elif isinstance(v, pd.Series):
                        user_vars[k] = {"type": "Series", "length": len(v), "last": float(v.iloc[-1]) if len(v) > 0 else None}
                    elif isinstance(v, pd.DataFrame):
                        user_vars[k] = {"type": "DataFrame", "shape": list(v.shape)}
                except Exception:
                    pass
            result["variables"] = user_vars
        except Exception:
            exception_holder[0] = traceback.format_exc()

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        result["stderr"] = "Execution timed out (30s limit)"
        return result

    result["stdout"] = stdout_capture.getvalue()
    result["stderr"] += stderr_capture.getvalue()

    if exception_holder[0]:
        result["stderr"] += exception_holder[0]
        result["success"] = False

    return result
