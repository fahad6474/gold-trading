from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class OHLCVBar(BaseModel):
    time: int  # Unix timestamp seconds
    open: float
    high: float
    low: float
    close: float
    volume: float


class DataResponse(BaseModel):
    symbol: str
    timeframe: str
    bars: List[OHLCVBar]


class IndicatorRequest(BaseModel):
    symbol: str
    timeframe: str
    start: Optional[str] = None
    end: Optional[str] = None
    indicators: List[Dict[str, Any]]  # [{name: "SMA", params: {length: 20}}]


class IndicatorSeries(BaseModel):
    name: str
    data: List[Dict[str, Any]]  # [{time, value}]
    color: Optional[str] = None
    panel: str = "main"  # "main" or "sub"


class IndicatorResponse(BaseModel):
    indicators: List[IndicatorSeries]


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start: Optional[str] = "2022-01-01"
    end: Optional[str] = None
    strategy_code: str
    initial_capital: float = 10000.0
    commission: float = 0.001  # 0.1%


class TradeRecord(BaseModel):
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    side: str = "long"


class BacktestResult(BaseModel):
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    profit_factor: Optional[float]
    equity_curve: List[Dict[str, Any]]  # [{time, value}]
    trades: List[TradeRecord]
    final_value: float
    initial_capital: float


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"  # "python" or "pine"
    symbol: Optional[str] = "GC=F"
    timeframe: Optional[str] = "1d"
    start: Optional[str] = "2022-01-01"
    end: Optional[str] = None


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    result: Optional[Dict[str, Any]] = None
    transpiled_code: Optional[str] = None  # For Pine Script, show generated Python
    success: bool
