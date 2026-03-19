"""
Gold & BTC Backtest Dashboard — FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.data import router as data_router
from api.indicators import router as indicators_router
from api.backtest import router as backtest_router
from api.execute import router as execute_router
from core.data_fetcher import get_latest_price


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Gold & BTC Backtest Dashboard API started")
    print("Docs: http://localhost:8000/docs")
    yield
    print("Shutting down")


app = FastAPI(
    title="Gold & BTC Backtest Dashboard API",
    description="Backtest trading strategies for Gold (XAUUSD) and BTC with Pine Script support.",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(indicators_router)
app.include_router(backtest_router)
app.include_router(execute_router)


@app.get("/")
def root():
    return {
        "message": "Gold & BTC Backtest Dashboard API",
        "docs": "/docs",
        "endpoints": ["/api/symbols", "/api/data/{symbol}", "/api/indicators", "/api/backtest", "/api/execute"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- WebSocket: real-time price stream ----

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, symbol: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(symbol, []).append(ws)

    def disconnect(self, symbol: str, ws: WebSocket):
        if symbol in self.active:
            self.active[symbol] = [c for c in self.active[symbol] if c != ws]

    async def broadcast(self, symbol: str, data: dict):
        dead = []
        for ws in self.active.get(symbol, []):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(symbol, ws)


manager = ConnectionManager()


@app.websocket("/ws/price/{symbol}")
async def ws_price(websocket: WebSocket, symbol: str):
    """Stream live price updates every 3 seconds."""
    await manager.connect(symbol, websocket)
    try:
        while True:
            try:
                price_data = await asyncio.get_event_loop().run_in_executor(
                    None, get_latest_price, symbol
                )
                await websocket.send_json(price_data)
            except Exception as e:
                await websocket.send_json({"error": str(e), "symbol": symbol})
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(symbol, websocket)
