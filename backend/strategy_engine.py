import pandas as pd
import numpy as np
import time
from indicators import calculate_indicators
from patterns import calculate_patterns
from signals import generate_signals
def load_data(filepath="nifty500_5yr.parquet"):
    print("[*] Loading historical database into memory...")
    start = time.time()
    df = pd.read_parquet(filepath)
    print(f"[*] Loaded {len(df)} rows in {round(time.time() - start, 2)} seconds.")
    return df
if __name__ == "__main__":
    df = load_data()
    print("[*] Vectorizing indicators across 500 stocks...")
    df = calculate_indicators(df)
    print("[*] Vectorizing patterns across 500 stocks...")
    df = calculate_patterns(df)
    print("[*] Generating alpha signals...")
    df = generate_signals(df)
    print("\n" + "=" * 50)
    print("SIGNAL MATRIX SUMMARY")
    print("=" * 50)
    print(df["Signal"].value_counts().to_string())
    print(f"\nTotal rows:   {len(df)}")
    print(f"Long  (1):    {(df['Signal'] == 1).sum()}")
    print(f"Short (-1):   {(df['Signal'] == -1).sum()}")
    print(f"Neutral (0):  {(df['Signal'] == 0).sum()}")
    print(f"Signal rate:  {(df['Signal'] != 0).mean():.4%}")
    reliance = df[df["Ticker"] == "RELIANCE.NS"]
    print(f"\nRELIANCE.NS — last 20 rows:")
    print(reliance[["Date", "Close", "RSI_14", "Trend_State", "Bullish_Engulfing", "Bearish_Engulfing", "Hammer", "Signal"]].tail(20).to_string(index=False))
    print("\n\n")
    print(df.head(40))