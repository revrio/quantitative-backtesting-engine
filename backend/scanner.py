"""Stock screener / candlestick pattern scanner.
Loads parquet data, runs the vectorized indicators + patterns engine,
and returns structured scan results for the API layer.
"""
from __future__ import annotations
from datetime import datetime, timezone
import pandas as pd
from indicators import calculate_indicators
from patterns import calculate_patterns
PATTERN_META: dict[str, tuple[str, str]] = {
    "Bullish_Engulfing":  ("Bullish Engulfing",  "Bullish"),
    "Bearish_Engulfing":  ("Bearish Engulfing",  "Bearish"),
    "Piercing_Pattern":   ("Piercing Pattern",   "Bullish"),
    "Dark_Cloud_Cover":   ("Dark Cloud Cover",   "Bearish"),
    "Bullish_Harami":     ("Bullish Harami",     "Bullish"),
    "Bearish_Harami":     ("Bearish Harami",     "Bearish"),
    "Morning_Star":       ("Morning Star",       "Bullish"),
    "Evening_Star":       ("Evening Star",       "Bearish"),
    "Bullish_Marubozu":   ("Bullish Marubozu",   "Bullish"),
    "Bearish_Marubozu":   ("Bearish Marubozu",   "Bearish"),
    "Spinning_Top":       ("Spinning Top",       "Neutral"),
    "Doji":               ("Doji",               "Neutral"),
    "Hammer":             ("Hammer",             "Bullish"),
    "Hanging_Man":        ("Hanging Man",        "Bearish"),
    "Shooting_Star":      ("Shooting Star",      "Bearish"),
}
def run_scan(parquet_path: str, universe: str, tickers: list[str]) -> dict:
    """Run the candlestick pattern scanner on the latest data.
    Parameters
    ----------
    parquet_path:
        Path to the parquet file containing OHLCV + Ticker data.
    universe:
        Name of the universe being scanned (e.g. ``"nifty50"``).
    tickers:
        List of ticker symbols to scan.
    Returns
    -------
    dict
        JSON-serializable scan results including matched patterns,
        indicator values, and trend alignment information.
    """
    df = pd.read_parquet(parquet_path)
    df = df[df["Ticker"].isin(tickers)].copy()
    df = (
        df.sort_values(["Ticker", "Date"])
        .groupby("Ticker", group_keys=False)
        .tail(100)
        .reset_index(drop=True)
    )
    df = calculate_indicators(df)
    df = calculate_patterns(df)
    df = df.dropna(subset=["RSI_14", "MACD", "MACD_Signal", "Volume_SMA_10"])
    last_rows = df.groupby("Ticker", group_keys=False).tail(1).reset_index(drop=True)
    results: list[dict] = []
    pattern_columns = list(PATTERN_META.keys())
    for _, row in last_rows.iterrows():
        for col in pattern_columns:
            if row.get(col, 0) == 1:
                display_name, direction = PATTERN_META[col]
                trend_state = int(row["Trend_State"])
                is_marubozu = "Marubozu" in col
                trend_aligned = (
                    (direction == "Bullish" and trend_state == 1)
                    or (direction == "Bearish" and trend_state == -1)
                    or is_marubozu
                )
                results.append({
                    "ticker": row["Ticker"],
                    "pattern": display_name,
                    "direction": direction,
                    "close": round(float(row["Close"]), 2),
                    "current_volume": int(row["Volume"]),
                    "volume_sma_10": round(float(row["Volume_SMA_10"]), 2),
                    "is_volume_high": bool(row["Volume"] > row["Volume_SMA_10"]),
                    "rsi_14": round(float(row["RSI_14"]), 2),
                    "macd_state": "Bullish" if row["MACD"] > row["MACD_Signal"] else "Bearish",
                    "trend_state": trend_state,
                    "trend_aligned": trend_aligned,
                })
    shortlisted_tickers = set(r["ticker"] for r in results)
    return {
        "universe": universe,
        "scanned_count": len(last_rows),
        "shortlisted_count": len(shortlisted_tickers),
        "match_count": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }