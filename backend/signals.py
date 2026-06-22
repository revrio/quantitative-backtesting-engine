"""Alpha generation layer for the backtesting engine.
Two-tier architecture:
  1. **Strategy Layer** – ``get_pattern_signals(df)`` combines individual
     pattern columns into master bullish / bearish sentiment masks.
  2. **Engine Layer** – ``generate_signals(df)`` intersects sentiment with
     trend regime and RSI filters to produce a final ``Signal`` column.
All operations are pure Pandas vectorized boolean logic — no loops,
no ``.apply()``.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
def get_pattern_signals(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Combine individual pattern columns into master sentiment masks.
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: ``Bullish_Engulfing``, ``Hammer``,
        ``Bearish_Engulfing``.
    Returns
    -------
    tuple[pd.Series, pd.Series]
        ``(bullish_patterns, bearish_patterns)`` — boolean Series.
    """
    bullish_patterns = (
        (df['Bullish_Engulfing'] == 1) | 
        (df['Hammer'] == 1) |
        (df['Morning_Star'] == 1) |
        (df['Bullish_Harami'] == 1) |
        (df['Piercing_Pattern'] == 1) |
        (df['Bullish_Marubozu'] == 1)
    )
    bearish_patterns = (
        (df['Bearish_Engulfing'] == 1) | 
        (df['Shooting_Star'] == 1) |
        (df['Evening_Star'] == 1) |
        (df['Dark_Cloud_Cover'] == 1) |
        (df['Hanging_Man'] == 1) |
        (df['Bearish_Harami'] == 1) |
        (df['Bearish_Marubozu'] == 1)
    )
    return bullish_patterns, bearish_patterns
def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Create the final ``Signal`` column on the DataFrame.
    Signal values:
      -  **1** → Long  (uptrend + bullish pattern + RSI < 60)
      - **-1** → Short (downtrend + bearish pattern + RSI > 40)
      -  **0** → No signal
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: ``Trend_State``, ``RSI_14``,
        ``Bullish_Engulfing``, ``Hammer``, ``Bearish_Engulfing``.
    Returns
    -------
    pd.DataFrame
        The input DataFrame with a ``Signal`` column appended.
    """
    out = df.copy()
    bullish_patterns, bearish_patterns = get_pattern_signals(out)
    high_volume = out['Volume'] > out['Volume_SMA_10']
    long_mask = (
       (( (out["Trend_State"] == 1)
        & bullish_patterns
        & (out["RSI_14"] < 70)) | (out['Bullish_Marubozu'] == 1)) & 
        high_volume
    )
    short_mask = (
        (((out["Trend_State"] == -1)
        & bearish_patterns
        & (out["RSI_14"] > 30)) | (out['Bearish_Marubozu'] == 1)) & 
        high_volume
    )
    out["Signal"] = np.select(
        condlist=[long_mask, short_mask],
        choicelist=[1, -1],
        default=0,
    ).astype("int8")
    return out
def generate_signals2(df):
    """
    Master Alpha Generator: Bollinger Band + MACD Confluence
    """
    sma = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(window=20).mean())
    std = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(window=20).std())
    df['BB_Upper'] = sma + (2 * std)
    df['BB_Lower'] = sma - (2 * std)
    macd_bull_cross = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
    macd_bear_cross = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
    touched_lower_bb = (df['Low'] <= df['BB_Lower']) | (df['Low'].shift(1) <= df['BB_Lower'].shift(1))
    touched_upper_bb = (df['High'] >= df['BB_Upper']) | (df['High'].shift(1) >= df['BB_Upper'].shift(1))
    long_mask = touched_lower_bb & macd_bull_cross
    short_mask = touched_upper_bb & macd_bear_cross
    df['Signal'] = 0
    df.loc[long_mask, 'Signal'] = 1
    df.loc[short_mask, 'Signal'] = -1
    return df