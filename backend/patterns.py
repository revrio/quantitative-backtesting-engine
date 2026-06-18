"""Vectorized candlestick pattern detection for the backtesting engine.
Every computation uses **only** ``groupby('Ticker')`` + vectorized Pandas
column math — no Python-level ``for`` loops and no ``.apply()`` on rows.
Tolerances and thresholds are translated directly from the original
``patterns.py`` strict/flexible logic.
"""
from __future__ import annotations
import pandas as pd
STRICT_TOL = 0.05
FLEXIBLE_TOL = 0.12
def calculate_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Add boolean (1/0) candlestick-pattern columns to a flat OHLCV DataFrame.
    Added columns
    -------------
    Single-candle : ``Doji``, ``Spinning_Top``, ``Bullish_Marubozu``,
                    ``Bearish_Marubozu``, ``Hammer``, ``Hanging_Man``,
                    ``Shooting_Star``
    Two-candle    : ``Bullish_Engulfing``, ``Bearish_Engulfing``,
                    ``Piercing_Pattern``, ``Dark_Cloud_Cover``,
                    ``Bullish_Harami``, ``Bearish_Harami``
    Three-candle  : ``Morning_Star``, ``Evening_Star``
    Each column is **1** when the pattern matches under *either* the
    strict (tol = 0.05) or flexible (tol = 0.12) tolerance from the
    original codebase, and **0** otherwise.
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: ``Date``, ``Ticker``, ``Open``, ``High``,
        ``Low``, ``Close``, ``Volume``.  Rows should be sorted by
        ``[Ticker, Date]``.
    Returns
    -------
    pd.DataFrame
        The input DataFrame with the new pattern columns appended.
    """
    out = df.copy()
    out = out.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    out["_Body"] = (out["Close"] - out["Open"]).abs()
    out["_Range"] = out["High"] - out["Low"]
    out["_Midpoint"] = (out["Open"] + out["Close"]) / 2
    out["_Upper_Shadow"] = out["High"] - out[["Open", "Close"]].max(axis=1)
    out["_Lower_Shadow"] = out[["Open", "Close"]].min(axis=1) - out["Low"]
    g = out.groupby("Ticker", sort=False)
    prev_open   = g["Open"].shift(1)
    prev_close  = g["Close"].shift(1)
    prev_body   = g["_Body"].shift(1)
    prev_range  = g["_Range"].shift(1)
    prev_midpoint = g["_Midpoint"].shift(1)
    prev_long_body = (prev_body >= 0.45 * prev_range)
    prev_oc_max = pd.concat([prev_open, prev_close], axis=1).max(axis=1)
    prev_oc_min = pd.concat([prev_open, prev_close], axis=1).min(axis=1)
    prev2_open     = g["Open"].shift(2)
    prev2_close    = g["Close"].shift(2)
    prev2_body     = g["_Body"].shift(2)
    prev2_range    = g["_Range"].shift(2)
    prev2_midpoint = g["_Midpoint"].shift(2)
    prev2_long_body = (prev2_body >= 0.45 * prev2_range)
    close_1 = g["Close"].shift(1)
    close_3 = g["Close"].shift(3)
    valid_current = (
        out[["Open", "High", "Low", "Close", "_Body", "_Range"]].notna().all(axis=1)
        & (out["_Range"] > 0)
        & (out["High"] >= out[["Open", "Close"]].max(axis=1))
        & (out["Low"] <= out[["Open", "Close"]].min(axis=1))
    )
    out["_valid"] = valid_current
    valid_prev_1 = g["_valid"].shift(1).fillna(False).astype(bool)
    valid_prev_2 = g["_valid"].shift(2).fillna(False).astype(bool)
    valid_prev_3 = g["_valid"].shift(3).fillna(False).astype(bool)
    def _umbrella_shape(tol: float) -> pd.Series:
        """Small body, long lower shadow, tiny upper shadow."""
        return (
            valid_current
            & (out["_Body"] > 0.05 * out["_Range"])
            & (out["_Body"] <= 0.35 * out["_Range"])
            & (out["_Lower_Shadow"] >= 2 * out["_Body"])
            & (out["_Upper_Shadow"] <= tol * out["_Range"])
        )
    def _inverted_umbrella_shape(tol: float) -> pd.Series:
        """Small body, long upper shadow, tiny lower shadow."""
        return (
            valid_current
            & (out["_Body"] > 0.05 * out["_Range"])
            & (out["_Body"] <= 0.35 * out["_Range"])
            & (out["_Upper_Shadow"] >= 2 * out["_Body"])
            & (out["_Lower_Shadow"] <= tol * out["_Range"])
        )
    def _prior_downtrend(tol: float) -> pd.Series:
        return close_1 < close_3 * (1 - tol)
    def _prior_uptrend(tol: float) -> pd.Series:
        return close_1 > close_3 * (1 + tol)
    def _strict_or_flex(strict_mask: pd.Series, flex_mask: pd.Series) -> pd.Series:
        return (strict_mask | flex_mask).astype(int)
    def _bullish_engulfing(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close < prev_open)
            & (out["Close"] > out["Open"])
            & (out["_Body"] >= prev_body * (1 - tol))
            & (out["Open"] <= prev_close + tol * prev_body)
            & (out["Close"] >= prev_open - tol * prev_body)
        )
    out["Bullish_Engulfing"] = _strict_or_flex(
        _bullish_engulfing(STRICT_TOL), _bullish_engulfing(FLEXIBLE_TOL),
    )
    def _bearish_engulfing(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close > prev_open)
            & (out["Close"] < out["Open"])
            & (out["_Body"] >= prev_body * (1 - tol))
            & (out["Open"] >= prev_close - tol * prev_body)
            & (out["Close"] <= prev_open + tol * prev_body)
        )
    out["Bearish_Engulfing"] = _strict_or_flex(
        _bearish_engulfing(STRICT_TOL), _bearish_engulfing(FLEXIBLE_TOL),
    )
    def _piercing(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close < prev_open)                                  
            & (out["Close"] > out["Open"])                              
            & (out["Open"] <= prev_close + tol * prev_body)             
            & (out["Close"] > prev_midpoint)                            
            & (out["Close"] <= prev_open + tol * prev_body)             
        )
    out["Piercing_Pattern"] = _strict_or_flex(
        _piercing(STRICT_TOL), _piercing(FLEXIBLE_TOL),
    )
    def _dark_cloud(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close > prev_open)                                  
            & (out["Close"] < out["Open"])                              
            & (out["Open"] >= prev_close - tol * prev_body)             
            & (out["Close"] < prev_midpoint)                            
            & (out["Close"] >= prev_open - tol * prev_body)             
        )
    out["Dark_Cloud_Cover"] = _strict_or_flex(
        _dark_cloud(STRICT_TOL), _dark_cloud(FLEXIBLE_TOL),
    )
    def _bullish_harami(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close < prev_open)                                  
            & (out["Close"] > out["Open"])                              
            & prev_long_body                                            
            & (out["Open"] >= prev_close - tol * prev_body)             
            & (out["Close"] <= prev_open + tol * prev_body)             
            & (out["_Body"] <= 0.65 * prev_body + tol * prev_body)      
        )
    out["Bullish_Harami"] = _strict_or_flex(
        _bullish_harami(STRICT_TOL), _bullish_harami(FLEXIBLE_TOL),
    )
    def _bearish_harami(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1
            & (prev_close > prev_open)                                  
            & (out["Close"] < out["Open"])                              
            & prev_long_body                                            
            & (out["Open"] <= prev_close + tol * prev_body)             
            & (out["Close"] >= prev_open - tol * prev_body)             
            & (out["_Body"] <= 0.65 * prev_body + tol * prev_body)      
        )
    out["Bearish_Harami"] = _strict_or_flex(
        _bearish_harami(STRICT_TOL), _bearish_harami(FLEXIBLE_TOL),
    )
    def _morning_star(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1 & valid_prev_2
            & (prev2_close < prev2_open)                                
            & prev2_long_body                                           
            & (prev_body <= 0.30 * prev_range)                          
            & (prev_oc_max <= prev2_close + tol * prev2_body)           
            & (out["Close"] > out["Open"])                              
            & (out["Open"] >= prev_oc_max - tol * prev_range)           
            & (out["Close"] > prev2_midpoint)                           
        )
    out["Morning_Star"] = _strict_or_flex(
        _morning_star(STRICT_TOL), _morning_star(FLEXIBLE_TOL),
    )
    def _evening_star(tol: float) -> pd.Series:
        return (
            valid_current & valid_prev_1 & valid_prev_2
            & (prev2_close > prev2_open)                                
            & prev2_long_body                                           
            & (prev_body <= 0.30 * prev_range)                          
            & (prev_oc_min >= prev2_close - tol * prev2_body)           
            & (out["Close"] < out["Open"])                              
            & (out["Open"] <= prev_oc_min + tol * prev_range)           
            & (out["Close"] < prev2_midpoint)                           
        )
    out["Evening_Star"] = _strict_or_flex(
        _evening_star(STRICT_TOL), _evening_star(FLEXIBLE_TOL),
    )
    def _bullish_marubozu(tol: float) -> pd.Series:
        return (
            valid_current
            & (out["Close"] > out["Open"])
            & (out["_Body"] >= 0.80 * out["_Range"])
            & (out["_Upper_Shadow"] <= tol * out["_Range"])
            & (out["_Lower_Shadow"] <= tol * out["_Range"])
        )
    out["Bullish_Marubozu"] = _strict_or_flex(
        _bullish_marubozu(STRICT_TOL), _bullish_marubozu(FLEXIBLE_TOL),
    )
    def _bearish_marubozu(tol: float) -> pd.Series:
        return (
            valid_current
            & (out["Open"] > out["Close"])
            & (out["_Body"] >= 0.80 * out["_Range"])
            & (out["_Upper_Shadow"] <= tol * out["_Range"])
            & (out["_Lower_Shadow"] <= tol * out["_Range"])
        )
    out["Bearish_Marubozu"] = _strict_or_flex(
        _bearish_marubozu(STRICT_TOL), _bearish_marubozu(FLEXIBLE_TOL),
    )
    def _spinning_top(tol: float) -> pd.Series:
        return (
            valid_current
            & (out["_Body"] > tol * out["_Range"])
            & (out["_Body"] <= 0.25 * out["_Range"])
            & (out["_Upper_Shadow"] >= 0.75 * out["_Body"])
            & (out["_Lower_Shadow"] >= 0.75 * out["_Body"])
            & ((out["_Upper_Shadow"] - out["_Lower_Shadow"]).abs() <= tol * out["_Range"])
        )
    out["Spinning_Top"] = _strict_or_flex(
        _spinning_top(STRICT_TOL), _spinning_top(FLEXIBLE_TOL),
    )
    def _doji(tol: float) -> pd.Series:
        return valid_current & (out["_Body"] <= tol * out["_Range"])
    out["Doji"] = _strict_or_flex(_doji(STRICT_TOL), _doji(FLEXIBLE_TOL))
    def _hammer(tol: float) -> pd.Series:
        return _umbrella_shape(tol) & valid_prev_3 & _prior_downtrend(tol)
    out["Hammer"] = _strict_or_flex(_hammer(STRICT_TOL), _hammer(FLEXIBLE_TOL))
    def _hanging_man(tol: float) -> pd.Series:
        return _umbrella_shape(tol) & valid_prev_3 & _prior_uptrend(tol)
    out["Hanging_Man"] = _strict_or_flex(
        _hanging_man(STRICT_TOL), _hanging_man(FLEXIBLE_TOL),
    )
    def _shooting_star(tol: float) -> pd.Series:
        return _inverted_umbrella_shape(tol) & valid_prev_3 & _prior_uptrend(tol)
    out["Shooting_Star"] = _strict_or_flex(
        _shooting_star(STRICT_TOL), _shooting_star(FLEXIBLE_TOL),
    )
    out.drop(
        columns=["_Body", "_Range", "_Midpoint", "_Upper_Shadow", "_Lower_Shadow", "_valid"],
        inplace=True,
    )
    return out