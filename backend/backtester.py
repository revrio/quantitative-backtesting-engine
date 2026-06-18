import pandas as pd
import vectorbt as vbt
import numpy as np
def run_backtest(df):
    print("[*] Pivoting matrices for vectorbt...")
    price_matrix = df.pivot(index='Date', columns='Ticker', values='Close')
    signal_matrix = df.pivot(index='Date', columns='Ticker', values='Signal')
    entries = signal_matrix == 1
    exits = signal_matrix == -1
    print("[*] Running Vectorized Backtest Simulation...")
    portfolio = vbt.Portfolio.from_signals(
        price_matrix,
        entries,
        exits,
        init_cash=100000,      
        fees=0.001,            
        sl_stop=0.08,          
        tp_stop=0.24,          
        freq='1D',              
        group_by=True,
        size=0.1,
        cash_sharing=True,
        size_type='percent'
    )
    print("\n" + "="*40)
    print("      QUANTITATIVE TEAR SHEET")
    print("="*40)
    print(f"Total Return:       {portfolio.total_return() * 100:.2f}%")
    print(f"Win Rate:           {portfolio.trades.win_rate() * 100:.2f}%")
    print(f"Sharpe Ratio:       {portfolio.sharpe_ratio():.2f}")
    print(f"Max Drawdown:       {portfolio.max_drawdown() * 100:.2f}%")
    print(f"Total Trades:       {len(portfolio.trades)}")
    print("="*40)
    portfolio.plot().show()
    return portfolio
def run_api_backtest(df, initial_capital=100000, ticker=None):
    """API-friendly wrapper: returns JSON-serializable dict instead of printing."""
    if ticker and ticker.lower() != "all":
        df = df[df["Ticker"] == ticker].copy()
    price_matrix = df.pivot(index='Date', columns='Ticker', values='Close')
    signal_matrix = df.pivot(index='Date', columns='Ticker', values='Signal')
    entries = signal_matrix == 1
    exits = signal_matrix == -1
    is_portfolio = (ticker is None or ticker.lower() == "all")
    portfolio = vbt.Portfolio.from_signals(
        price_matrix, entries, exits,
        init_cash=initial_capital,
        fees=0.001,
        sl_stop=0.08,
        tp_stop=0.24,
        freq='1D',
        group_by=True if is_portfolio else False,
        size=0.1,
        cash_sharing=True if is_portfolio else False,
        size_type='percent'
    )
    equity = portfolio.value()
    if isinstance(equity, pd.DataFrame):
        equity_series = equity.sum(axis=1) if is_portfolio else equity.iloc[:, 0]
    else:
        equity_series = equity
    drawdown_series = (equity_series / equity_series.cummax()) - 1.0
    daily_rets = equity_series.pct_change()
    roll_mean = daily_rets.rolling(126).mean()
    roll_std = daily_rets.rolling(126).std()
    rolling_sharpe_series = (roll_mean / roll_std) * np.sqrt(252)
    curve_data = []
    total_points = len(equity_series)
    step = max(1, total_points // 500)
    for i in range(0, total_points, step):
        idx = equity_series.index[i]
        val = equity_series.iloc[i]
        dd = drawdown_series.iloc[i]
        rs = rolling_sharpe_series.iloc[i]
        date_str = str(idx.date()) if hasattr(idx, 'date') else str(idx)
        curve_data.append({
            "date": date_str, 
            "value": round(float(val), 2),
            "drawdown": round(float(dd * 100), 2) if pd.notna(dd) else 0.0,
            "rolling_sharpe": round(float(rs), 2) if pd.notna(rs) else 0.0
        })
    last_idx = equity_series.index[-1]
    last_date = str(last_idx.date()) if hasattr(last_idx, 'date') else str(last_idx)
    if not curve_data or curve_data[-1]["date"] != last_date:
        last_dd = drawdown_series.iloc[-1]
        last_rs = rolling_sharpe_series.iloc[-1]
        curve_data.append({
            "date": last_date, 
            "value": round(float(equity_series.iloc[-1]), 2),
            "drawdown": round(float(last_dd * 100), 2) if pd.notna(last_dd) else 0.0,
            "rolling_sharpe": round(float(last_rs), 2) if pd.notna(last_rs) else 0.0
        })
    total_ret = portfolio.total_return()
    win_r = portfolio.trades.win_rate()
    sharpe = portfolio.sharpe_ratio()
    max_dd = portfolio.max_drawdown()
    n_trades = portfolio.trades.count()
    if not is_portfolio:
        total_ret = total_ret.iloc[0] if isinstance(total_ret, pd.Series) else total_ret
        win_r = win_r.iloc[0] if isinstance(win_r, pd.Series) else win_r
        sharpe = sharpe.iloc[0] if isinstance(sharpe, pd.Series) else sharpe
        max_dd = max_dd.iloc[0] if isinstance(max_dd, pd.Series) else max_dd
        n_trades = n_trades.iloc[0] if isinstance(n_trades, pd.Series) else n_trades
    heatmap_data = []
    try:
        monthly_equity = equity_series.resample('ME').last()
        monthly_rets = monthly_equity.pct_change().dropna()
        for year, group in monthly_rets.groupby(monthly_rets.index.year):
            year_data = {"year": int(year)}
            for i in range(1, 13):
                month_ret = group[group.index.month == i]
                year_data[str(i)] = round(float(month_ret.iloc[0] * 100), 2) if not month_ret.empty else None
            heatmap_data.append(year_data)
    except Exception as e:
        print("Heatmap generation error:", e)
    try:
        if portfolio.trades.count() > 0:
            records = portfolio.trades.records_readable
            if 'Return' in records.columns:
                trade_returns = [round(float(x * 100), 2) for x in records['Return'].dropna().values]
            else:
                trade_returns = []
        else:
            trade_returns = []
    except Exception as e:
        print("Trade returns error:", e)
        trade_returns = []
    return {
        "total_return": round(float(total_ret * 100), 2) if pd.notna(total_ret) else 0.0,
        "win_rate": round(float(win_r * 100), 2) if pd.notna(win_r) else 0.0,
        "sharpe_ratio": round(float(sharpe), 2) if pd.notna(sharpe) else 0.0,
        "max_drawdown": round(float(max_dd * 100), 2) if pd.notna(max_dd) else 0.0,
        "total_trades": int(n_trades) if pd.notna(n_trades) else 0,
        "final_value": round(float(equity_series.iloc[-1]), 2),
        "initial_capital": initial_capital,
        "ticker": ticker if ticker else "Portfolio (All Stocks)",
        "equity_curve": curve_data,
        "heatmap_data": heatmap_data,
        "trade_returns": trade_returns,
    }
if __name__ == "__main__":
    from strategy_engine import load_data, calculate_indicators, calculate_patterns, generate_signals
    df = load_data()
    df = calculate_indicators(df)
    df = calculate_patterns(df)
    df = generate_signals(df)
    portfolio = run_backtest(df)