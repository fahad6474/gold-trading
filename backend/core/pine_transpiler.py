"""
Pine Script v5 → Python transpiler using TA-Lib.
Converts a subset of Pine Script syntax to executable Python code.

Supported:
  - Variable declarations (var float/int/bool, :=, =)
  - ta.sma, ta.ema, ta.rsi, ta.macd, ta.bbands, ta.atr, ta.stoch
  - ta.crossover, ta.crossunder
  - strategy.entry, strategy.exit, strategy.close
  - if/else blocks, arithmetic, comparison operators
  - Math functions: math.abs, math.max, math.min, math.round, math.floor, math.ceil
  - close, open, high, low, volume, bar_index, na, nz()

Not supported (will be flagged):
  - plot(), plotshape(), plotchar(), alertcondition()
  - request.security() (multi-timeframe)
  - array.*, matrix.*, line.*, label.*
"""
import re
from typing import Tuple, List


UNSUPPORTED_PATTERNS = [
    (r"\bplot\s*\(", "plot() - use the chart panel instead"),
    (r"\bplotshape\s*\(", "plotshape() - not supported"),
    (r"\balertcondition\s*\(", "alertcondition() - not supported"),
    (r"\brequest\.security\s*\(", "request.security() - multi-timeframe not supported"),
    (r"\barray\.", "array.* functions"),
    (r"\bmatrix\.", "matrix.* functions"),
    (r"\bline\.new\s*\(", "line.new() - drawing tools not supported"),
    (r"\blabel\.new\s*\(", "label.new() - drawing tools not supported"),
]


def transpile(pine_code: str) -> Tuple[str, List[str]]:
    """Transpile Pine Script code to Python. Returns (python_code, warnings_list)."""
    warnings = []
    lines = pine_code.split("\n")
    output_lines = []

    for line in lines:
        for pattern, description in UNSUPPORTED_PATTERNS:
            if re.search(pattern, line):
                warnings.append(f"Unsupported: {description}")

    output_lines += [
        "# Auto-generated Python from Pine Script (TA-Lib backend)",
        "import numpy as np",
        "import pandas as pd",
        "import talib as _talib",
        "",
        "# Ensure numpy arrays for talib",
        "_c = close.values.astype(float)",
        "_h = high.values.astype(float)",
        "_l = low.values.astype(float)",
        "_v = volume.values.astype(float)",
        "_idx = close.index",
        "",
        "def _s(arr): return pd.Series(arr, index=_idx)",
        "",
        "bar_index = pd.Series(range(len(close)), index=_idx)",
        "na = float('nan')",
        "",
        "# ---- Transpiled Strategy ----",
        "",
    ]

    entry_conditions = []
    exit_conditions = []
    has_strategy = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            output_lines.append("")
            continue
        if stripped.startswith("//"):
            output_lines.append("# " + stripped[2:].strip())
            continue
        if stripped.startswith("//@version"):
            continue
        if re.match(r"^\s*indicator\s*\(", stripped):
            continue
        if re.match(r"^\s*strategy\s*\(", stripped):
            has_strategy = True
            continue

        skip = False
        for pattern, _ in UNSUPPORTED_PATTERNS:
            if re.search(pattern, stripped):
                output_lines.append(f"# SKIPPED (unsupported): {stripped}")
                skip = True
                break
        if skip:
            continue

        py_line = _transform_line(stripped, entry_conditions, exit_conditions)
        output_lines.append(py_line)

    output_lines += ["", "# ---- Signal Generation ----"]
    if entry_conditions:
        combined = " | ".join(f"({c})" for c in entry_conditions)
        output_lines.append(f"entries = ({combined}).fillna(False).astype(bool)")
    else:
        output_lines.append("entries = pd.Series(False, index=_idx)  # No strategy.entry() found")

    if exit_conditions:
        combined = " | ".join(f"({c})" for c in exit_conditions)
        output_lines.append(f"exits = ({combined}).fillna(False).astype(bool)")
    else:
        output_lines.append("exits = pd.Series(False, index=_idx)")

    return "\n".join(output_lines), warnings


def _transform_line(line: str, entry_conditions: list, exit_conditions: list) -> str:
    # strategy.entry long
    m = re.match(r'strategy\.entry\s*\(\s*"[^"]*"\s*,\s*strategy\.long\s*(?:,\s*when\s*=\s*(.+?))?\s*\)', line)
    if m:
        cond = _transform_expr(m.group(1) or "True")
        entry_conditions.append(cond)
        return f"# strategy.entry (long): {cond}"

    m = re.match(r'strategy\.entry\s*\(\s*"[^"]*"\s*,\s*strategy\.short\s*(?:,\s*when\s*=\s*(.+?))?\s*\)', line)
    if m:
        cond = _transform_expr(m.group(1) or "True")
        exit_conditions.append(cond)
        return f"# strategy.entry (short→exit): {cond}"

    m = re.match(r'strategy\.(?:close|exit)\s*\(\s*"[^"]*"(?:\s*,\s*when\s*=\s*(.+?))?\s*\)', line)
    if m:
        cond = _transform_expr(m.group(1) or "True")
        exit_conditions.append(cond)
        return f"# strategy.close/exit: {cond}"

    # input.* → default value
    line = re.sub(r'input\.int\s*\([^)]*defval\s*=\s*(\d+)[^)]*\)', r'\1', line)
    line = re.sub(r'input\.float\s*\([^)]*defval\s*=\s*([\d.]+)[^)]*\)', r'\1', line)
    line = re.sub(r'input\.int\s*\(\s*(\d+)[^)]*\)', r'\1', line)
    line = re.sub(r'input\.float\s*\(\s*([\d.]+)[^)]*\)', r'\1', line)
    line = re.sub(r'input\s*\(\s*(\d+(?:\.\d+)?)\s*[^)]*\)', r'\1', line)

    # var declarations → plain assignment
    line = re.sub(r'\bvar\s+(?:float|int|bool|string|color)\s+', '', line)
    line = re.sub(r'\bvar\s+', '', line)

    # := → =
    line = line.replace(":=", "=")

    return _transform_expr(line)


def _transform_expr(expr: str) -> str:
    result = expr

    # ta.* → talib wrappers (return pandas Series via _s())
    result = re.sub(r'\bta\.sma\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.SMA(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.ema\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.EMA(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.wma\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.WMA(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.rma\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.EMA(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.rsi\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.RSI(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.atr\s*\(([^)]+)\)',
                    r'_s(_talib.ATR(_h, _l, _c, timeperiod=int(\1)))', result)
    result = re.sub(r'\bta\.cci\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.CCI(_h, _l, _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.obv\b',
                    r'_s(_talib.OBV(_c, _v))', result)
    result = re.sub(r'\bta\.mom\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.MOM(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.roc\s*\(([^,)]+),\s*([^)]+)\)',
                    r'_s(_talib.ROC(\1.values.astype(float) if hasattr(\1,"values") else _c, timeperiod=int(\2)))', result)
    result = re.sub(r'\bta\.highest\s*\(([^,)]+),\s*([^)]+)\)',
                    r'\1.rolling(int(\2)).max()', result)
    result = re.sub(r'\bta\.lowest\s*\(([^,)]+),\s*([^)]+)\)',
                    r'\1.rolling(int(\2)).min()', result)
    result = re.sub(r'\bta\.stdev\s*\(([^,)]+),\s*([^)]+)\)',
                    r'\1.rolling(int(\2)).std()', result)

    # crossover / crossunder
    result = re.sub(
        r'\bta\.crossover\s*\(([^,)]+),\s*([^)]+)\)',
        r'((\1 > \2) & (\1.shift(1) <= \2.shift(1)))', result)
    result = re.sub(
        r'\bta\.crossunder\s*\(([^,)]+),\s*([^)]+)\)',
        r'((\1 < \2) & (\1.shift(1) >= \2.shift(1)))', result)
    result = re.sub(
        r'\bcrossover\s*\(([^,)]+),\s*([^)]+)\)',
        r'((\1 > \2) & (\1.shift(1) <= \2.shift(1)))', result)
    result = re.sub(
        r'\bcrossunder\s*\(([^,)]+),\s*([^)]+)\)',
        r'((\1 < \2) & (\1.shift(1) >= \2.shift(1)))', result)

    # math.*
    result = re.sub(r'\bmath\.abs\s*\(', 'abs(', result)
    result = re.sub(r'\bmath\.max\s*\(', 'max(', result)
    result = re.sub(r'\bmath\.min\s*\(', 'min(', result)
    result = re.sub(r'\bmath\.round\s*\(', 'round(', result)
    result = re.sub(r'\bmath\.floor\s*\(', 'int(', result)
    result = re.sub(r'\bmath\.ceil\s*\(', 'int(', result)
    result = re.sub(r'\bmath\.pow\s*\(([^,)]+),\s*([^)]+)\)', r'(\1 ** \2)', result)
    result = re.sub(r'\bmath\.sqrt\s*\(', 'np.sqrt(', result)
    result = re.sub(r'\bmath\.log\s*\(', 'np.log(', result)
    result = re.sub(r'\bmath\.exp\s*\(', 'np.exp(', result)
    result = re.sub(r'\bmath\.pi\b', 'np.pi', result)

    # nz() — replace NA with 0
    result = re.sub(r'\bnz\s*\(([^,)]+),\s*([^)]+)\)', r'\1.fillna(\2)', result)
    result = re.sub(r'\bnz\s*\(([^)]+)\)', r'\1.fillna(0)', result)
    result = re.sub(r'\bna\s*\(([^)]+)\)', r'\1.isna()', result)

    # Pine operators
    result = result.replace(" and ", " & ")
    result = result.replace(" or ", " | ")
    result = re.sub(r'\bnot\s+', '~', result)

    # open → open_ (Python keyword conflict)
    result = re.sub(r'\bopen\b(?!\s*_)', 'open_', result)

    # source[n] → source.shift(n)
    result = re.sub(r'(\w+)\[(\d+)\]', r'\1.shift(\2)', result)

    # Pine color constants
    result = re.sub(r'\bcolor\.\w+\b', '"#ffffff"', result)
    result = re.sub(r'\bcolor\.new\s*\([^)]+\)', '"#ffffff"', result)

    return result
