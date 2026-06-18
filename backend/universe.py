from __future__ import annotations
from functools import lru_cache
from io import StringIO
import pandas as pd
import requests
WIKI_HEADERS = {"User-Agent": "Mozilla/5.0 TradingScreener/1.0"}
UNIVERSE_URLS = {
    "nifty50": "https://en.wikipedia.org/wiki/NIFTY_50",
    "nifty500": "https://en.wikipedia.org/wiki/NIFTY_500",
    "sp500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
}
def _read_wikipedia_tables(url: str) -> list[pd.DataFrame]:
    response = requests.get(url, headers=WIKI_HEADERS, timeout=30)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))
def _clean_symbol(value: object) -> str:
    return str(value).strip().upper()
def _normalize_sp500_symbol(symbol: str) -> str:
    return symbol.replace(".", "-")
def _extract_symbol_table(tables: list[pd.DataFrame], expected_count: int) -> pd.DataFrame:
    for table in tables:
        if "Symbol" in table.columns and len(table) >= expected_count:
            return table
        first_row = table.iloc[0].astype(str).str.strip().tolist() if not table.empty else []
        if "Symbol" in first_row and len(table) >= expected_count:
            normalized = table.iloc[1:].copy()
            normalized.columns = first_row
            return normalized
    raise ValueError("Could not find a Wikipedia table with a Symbol column.")
@lru_cache(maxsize=3)
def get_universe(name: str = "nifty50") -> list[str]:
    normalized = name.lower().replace(" ", "").replace("&", "")
    if normalized in {"s&p500", "sandp500", "spx", "us500"}:
        normalized = "sp500"
    if normalized not in UNIVERSE_URLS:
        normalized = "nifty50"
    expected_count = 500 if normalized in {"nifty500", "sp500"} else 50
    table = _extract_symbol_table(_read_wikipedia_tables(UNIVERSE_URLS[normalized]), expected_count)
    symbols = [_clean_symbol(symbol) for symbol in table["Symbol"].dropna()]
    if normalized in {"nifty50", "nifty500"}:
        return [f"{symbol}.NS" for symbol in symbols]
    return [_normalize_sp500_symbol(symbol) for symbol in symbols]