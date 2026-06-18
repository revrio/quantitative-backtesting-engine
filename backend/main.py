import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os
from data_pipeline import refresh_and_save
from scanner import run_scan
from indicators import calculate_indicators
from patterns import calculate_patterns
from signals import generate_signals
from backtester import run_api_backtest
from universe import get_universe
app = FastAPI(title="StockPulse API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ScanRequest(BaseModel):
    universe: str
class RefreshRequest(BaseModel):
    universe: str
class BacktestRequest(BaseModel):
    universe: str
    ticker: Optional[str] = None
    initial_capital: float = 100000.0
def get_parquet_path(universe: str) -> str:
    path = f"data/{universe}.parquet"
    if not os.path.exists(path) and universe == "nifty500":
        return "nifty500_5yr.parquet"
    return path
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/scan")
def scan_endpoint(req: ScanRequest):
    path = get_parquet_path(req.universe)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Data not found. Please refresh data first.")
    tickers = get_universe(req.universe)
    return run_scan(path, req.universe, tickers)
@app.post("/refresh")
def refresh_endpoint(req: RefreshRequest):
    path = f"data/{req.universe}.parquet"
    return refresh_and_save(req.universe, path)
@app.post("/backtest")
def backtest_endpoint(req: BacktestRequest):
    path = get_parquet_path(req.universe)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Data not found. Please refresh data first.")
    df = pd.read_parquet(path)
    if req.ticker and req.ticker.lower() != "all":
        df = df[df["Ticker"] == req.ticker].copy()
    df = calculate_indicators(df)
    df = calculate_patterns(df)
    df = generate_signals(df)
    return run_api_backtest(df, req.initial_capital, req.ticker)
@app.get("/symbols/{universe}")
def symbols_endpoint(universe: str):
    return get_universe(universe)
@app.get("/data-status")
def data_status():
    status = {}
    for uni in ["nifty50", "nifty500", "sp500"]:
        path = get_parquet_path(uni)
        if os.path.exists(path):
            df = pd.read_parquet(path)
            status[uni] = {
                "exists": True,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat(),
                "rows": len(df),
                "tickers": df["Ticker"].nunique()
            }
        else:
            status[uni] = {"exists": False}
    return status
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)