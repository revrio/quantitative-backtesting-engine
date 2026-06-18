"""Data pipeline for downloading and managing historical market data."""
from __future__ import annotations
import logging
from datetime import datetime as _dt
from pathlib import Path
import pandas as pd
import pytz
import yfinance as yf
from universe import get_universe
logger = logging.getLogger(__name__)
def download_historical_data(
    universe: str = "sp500",
    period: str | None = "2y",
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Download historical OHLCV data for an entire universe of tickers.
    Uses ``yfinance.download`` with ``threads=True`` for parallel fetching
    and ``group_by="ticker"`` so the returned DataFrame is indexed as
    ``data[ticker][column]``.
    Parameters
    ----------
    universe:
        Name of the universe to fetch (``"sp500"``, ``"nifty500"``,
        ``"nifty50"``).  Passed directly to :func:`universe.get_universe`.
    period:
        yfinance period string (e.g. ``"1y"``, ``"2y"``, ``"max"``).
        Ignored when *start* is provided.
    start:
        Download start date as ``"YYYY-MM-DD"``.  When provided, *period*
        is ignored.
    end:
        Download end date as ``"YYYY-MM-DD"``.  Defaults to today.
    interval:
        Bar size — ``"1d"``, ``"1h"``, ``"5m"``, etc.
    Returns
    -------
    tuple[pd.DataFrame, list[str], list[str]]
        ``(data, successful_tickers, failed_tickers)``
        *data* is a MultiIndex DataFrame whose first column level is the
        ticker symbol and second level is the OHLCV field.
    """
    tickers = get_universe(universe)
    logger.info("Downloading %d tickers for universe '%s' …", len(tickers), universe)
    download_kwargs: dict = {
        "tickers": tickers,
        "interval": interval,
        "threads": True,
        "group_by": "ticker",
        "progress": True,
    }
    if start is not None:
        download_kwargs["start"] = start
        if end is not None:
            download_kwargs["end"] = end
    else:
        download_kwargs["period"] = period or "2y"
    data: pd.DataFrame = yf.download(**download_kwargs)
    if isinstance(data.columns, pd.MultiIndex):
        downloaded = data.columns.get_level_values(0).unique().tolist()
    else:
        downloaded = list(data.columns)
    successful = [t for t in tickers if t in downloaded]
    failed = [t for t in tickers if t not in downloaded]
    if failed:
        logger.warning(
            "%d / %d tickers failed to download: %s",
            len(failed),
            len(tickers),
            failed,
        )
    else:
        logger.info("All %d tickers downloaded successfully.", len(tickers))
    return data, successful, failed
def flatten_multiindex(data: pd.DataFrame) -> pd.DataFrame:
    """Reshape a yfinance MultiIndex DataFrame into a flat table.
    Converts the ``(Ticker, Field)`` MultiIndex columns returned by
    ``yf.download(group_by="ticker")`` into a regular DataFrame with
    columns: ``Date, Open, High, Low, Close, Volume, Ticker``.
    Parameters
    ----------
    data:
        MultiIndex DataFrame from :func:`download_historical_data`.
    Returns
    -------
    pd.DataFrame
        Flat DataFrame with a ``Ticker`` column and single-level
        OHLCV columns.
    """
    if not isinstance(data.columns, pd.MultiIndex):
        raise ValueError("DataFrame does not have MultiIndex columns — nothing to flatten.")
    flat = data.stack(level=0, future_stack=True)
    flat.index.names = ["Date", "Ticker"]
    flat = flat.reset_index()
    flat.columns.name = None
    keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume", "Ticker"] if c in flat.columns]
    flat = flat[keep]
    flat = flat.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    return flat
def save_to_parquet(data: pd.DataFrame, path: str | Path = "historical_data.parquet") -> Path:
    """Persist the downloaded DataFrame to a Parquet file.
    Parameters
    ----------
    data:
        The MultiIndex DataFrame returned by :func:`download_historical_data`.
    path:
        Destination file path.
    Returns
    -------
    Path
        Resolved path of the written file.
    """
    dest = Path(path)
    data.to_parquet(dest, engine="pyarrow")
    logger.info("Saved data to %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest
def load_from_parquet(path: str | Path = "historical_data.parquet") -> pd.DataFrame:
    """Load a previously saved Parquet file back into a MultiIndex DataFrame."""
    return pd.read_parquet(path, engine="pyarrow")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    data, ok, bad = download_historical_data(universe="nifty500", period="5y")
    print(f"\nDownloaded {len(ok)} tickers  |  Failed {len(bad)} tickers")
    print(f"MultiIndex DataFrame shape: {data.shape}")
    flat = flatten_multiindex(data)
    print(f"Flat DataFrame shape:       {flat.shape}")
    print(f"Columns: {list(flat.columns)}")
    print(f"\nSample rows:")
    print(flat.head(10))
    save_to_parquet(flat, path="nifty500_5yr.parquet")
def is_market_open(universe: str) -> bool:
    """Timezone-aware market guard. Returns True if market is currently in session."""
    now_utc = _dt.now(pytz.utc)
    if universe in ("nifty50", "nifty500"):
        ist = pytz.timezone("Asia/Kolkata")
        now = now_utc.astimezone(ist)
        if now.weekday() >= 5:
            return False
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=45, second=0, microsecond=0)
        return market_open <= now <= market_close
    elif universe == "sp500":
        eastern = pytz.timezone("US/Eastern")
        now = now_utc.astimezone(eastern)
        if now.weekday() >= 5:
            return False
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close
    return False
def apply_market_guard(df: pd.DataFrame, universe: str) -> tuple[pd.DataFrame, bool]:
    """Drop last row per ticker if market is currently open (partial candle)."""
    if is_market_open(universe):
        cleaned = df.groupby("Ticker", group_keys=False).apply(lambda g: g.iloc[:-1])
        return cleaned.reset_index(drop=True), True
    return df, False
def refresh_and_save(universe: str, parquet_path) -> dict:
    """Download fresh 5yr data, apply market guard, save to parquet."""
    from pathlib import Path
    Path(parquet_path).parent.mkdir(parents=True, exist_ok=True)
    data, ok, bad = download_historical_data(universe, period="5y")
    flat = flatten_multiindex(data)
    flat, guard_applied = apply_market_guard(flat, universe)
    save_to_parquet(flat, parquet_path)
    return {
        "status": "success",
        "universe": universe,
        "tickers_downloaded": len(ok),
        "tickers_failed": len(bad),
        "rows_saved": len(flat),
        "market_guard_applied": guard_applied,
        "partial_candle_dropped": guard_applied,
    }