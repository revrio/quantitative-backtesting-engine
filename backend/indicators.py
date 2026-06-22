"""Vectorized technical indicators for the backtesting engine.
Every function operates on a flat DataFrame with a ``Ticker`` column
(as produced by :func:`data_pipeline.flatten_multiindex`) and uses
**only** ``groupby('Ticker')`` + vectorized Pandas operations — no
Python-level ``for`` loops.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator columns to a flat OHLCV + Ticker DataFrame.
    All computations are fully vectorized globally — avoiding memory-heavy pandas groupby.
    """
    out = df.copy()
    out = out.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    
    same_t1 = out["Ticker"] == out["Ticker"].shift(1)
    same_t10 = out["Ticker"] == out["Ticker"].shift(10)
    
    # RSI (14)
    delta = out["Close"].diff().where(same_t1)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.mask(avg_loss == 0)
    rsi = 100 - (100 / (1 + rs))
    out["RSI_14"] = rsi.mask(avg_loss == 0, 100)
    
    # MACD
    ema_12 = out["Close"].ewm(span=12, adjust=False, min_periods=12).mean()
    ema_26 = out["Close"].ewm(span=26, adjust=False, min_periods=26).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False, min_periods=9).mean()
    out["MACD"] = macd_line
    out["MACD_Signal"] = macd_signal
    
    # Volume SMA 10
    out["Volume_SMA_10"] = out["Volume"].rolling(window=10, min_periods=10).mean().where(same_t10)
    
    # Trend State
    ema_fast = out["Close"].ewm(span=9, adjust=False).mean()
    ema_slow = out["Close"].ewm(span=21, adjust=False).mean()
    out["Trend_State"] = np.where(ema_fast > ema_slow, 1, np.where(ema_fast < ema_slow, -1, 0)).astype("int8")
    
    return out