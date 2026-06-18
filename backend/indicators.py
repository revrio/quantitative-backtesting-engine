"""Vectorized technical indicators for the backtesting engine.
Every function operates on a flat DataFrame with a ``Ticker`` column
(as produced by :func:`data_pipeline.flatten_multiindex`) and uses
**only** ``groupby('Ticker')`` + vectorized Pandas operations — no
Python-level ``for`` loops.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-style RSI using exponential weighted moving average.
    Translated from the original ``indicators.py`` ``_rsi`` function.
    Uses ``ewm(alpha=1/period)`` which matches Wilder's smoothing.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.mask(avg_loss == 0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.mask(avg_loss == 0, 100)
def _macd(close: pd.Series) -> pd.DataFrame:
    """MACD line and Signal line.
    Translated from the original ``indicators.py``:
      - MACD  = EMA-12 − EMA-26
      - Signal = EMA-9 of MACD
    """
    ema_12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False, min_periods=9).mean()
    return pd.DataFrame({"MACD": macd_line, "MACD_Signal": macd_signal}, index=close.index)
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator columns to a flat OHLCV + Ticker DataFrame.
    All computations are fully vectorized via ``groupby("Ticker")`` —
    **no Python-level for loops**.
    Added columns
    -------------
    - ``RSI_14``       – 14-period Wilder RSI
    - ``MACD``         – 12/26 EMA difference
    - ``MACD_Signal``  – 9-period EMA of MACD
    - ``Volume_SMA_10``– 10-day simple moving average of Volume
    - ``Trend_Up``     – 1 if Close > previous day's 20-day rolling High, else 0
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: ``Close``, ``High``, ``Volume``, ``Ticker``.
        Rows should be sorted by ``[Ticker, Date]`` (as produced by
        :func:`data_pipeline.flatten_multiindex`).
    Returns
    -------
    pd.DataFrame
        The input DataFrame with the new indicator columns appended.
    """
    out = df.copy()
    out = out.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    g = out.groupby("Ticker", sort=False)
    out["RSI_14"] = g["Close"].transform(lambda s: _rsi(s, period=14))
    macd_df = g["Close"].apply(_macd)
    out["MACD"] = macd_df["MACD"].values
    out["MACD_Signal"] = macd_df["MACD_Signal"].values
    out["Volume_SMA_10"] = g["Volume"].transform(
        lambda s: s.rolling(window=10, min_periods=10).mean()
    )
    ema_fast = g["Close"].transform(lambda x: x.ewm(span=9, adjust=False).mean())
    ema_slow = g["Close"].transform(lambda x: x.ewm(span=21, adjust=False).mean())
    out["Trend_State"] = np.where(ema_fast > ema_slow, 1, np.where(ema_fast < ema_slow, -1, 0))
    return out