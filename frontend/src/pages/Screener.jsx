import React, { useState, useEffect } from 'react';
import { Search, Download, Play, Star, StarOff, X } from 'lucide-react';
import { scanMarket, refreshData, checkDownloadStatus } from '../lib/api';
export default function Screener() {
  const [universe, setUniverse] = useState('nifty500');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [volFilter, setVolFilter] = useState(false);
  const [trendFilter, setTrendFilter] = useState(false);
  const [activeTab, setActiveTab] = useState('screener');
  const [watchlist, setWatchlist] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('qbe_watchlist')) || [];
    } catch {
      return [];
    }
  });
  const [chartSymbol, setChartSymbol] = useState(null);
  useEffect(() => {
    localStorage.setItem('qbe_watchlist', JSON.stringify(watchlist));
  }, [watchlist]);
  const handleScan = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await scanMarket(universe);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshData(universe);
      
      let status = 'downloading';
      while (status === 'downloading') {
        await new Promise(r => setTimeout(r, 2000));
        const data = await checkDownloadStatus(universe);
        status = data.status;
      }
      
      await handleScan();
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
    }
  };
  const toggleWatchlist = (item) => {
    const exists = watchlist.find(w => w.ticker === item.ticker && w.pattern === item.pattern);
    if (exists) {
      setWatchlist(watchlist.filter(w => !(w.ticker === item.ticker && w.pattern === item.pattern)));
    } else {
      setWatchlist([...watchlist, item]);
    }
  };
  const formatCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);
  let displayData = activeTab === 'screener' ? (results?.results || []) : watchlist;
  if (search) {
    const q = search.toLowerCase();
    displayData = displayData.filter(r => r.ticker.toLowerCase().includes(q) || r.pattern.toLowerCase().includes(q));
  }
  if (volFilter) {
    displayData = displayData.filter(r => r.is_volume_high);
  }
  if (trendFilter) {
    displayData = displayData.filter(r => r.trend_aligned);
  }
  return (
    <div className="flex flex-col gap-6">
      {}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-semibold text-text-primary mb-2">Market Screener</h1>
          <p className="text-text-secondary">Candlestick pattern scanner powered by vectorbt</p>
        </div>
        <div className="flex gap-4 items-center">
          <select 
            className="bg-bg-surface border border-border-subtle rounded-md px-4 py-2 text-text-primary focus:outline-none focus:border-border-medium"
            value={universe} onChange={e => setUniverse(e.target.value)}
          >
            <option value="nifty50">Nifty 50</option>
            <option value="nifty500">Nifty 500</option>
            <option value="sp500">S&P 500</option>
          </select>
          <button 
            onClick={handleRefresh} disabled={refreshing || loading}
            className="flex items-center gap-2 px-4 py-2 border border-border-subtle rounded-md hover:bg-bg-hover transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Refresh Data
          </button>
          <button 
            onClick={handleScan} disabled={refreshing || loading}
            className="flex items-center gap-2 px-4 py-2 bg-accent-cyan text-bg-app font-medium rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            Quick Scan
          </button>
        </div>
      </div>
      {refreshing && (
        <div className="p-4 bg-accent-cyanDim border border-accent-cyan rounded-md text-accent-cyan flex items-center justify-center">
          <div className="animate-pulse flex items-center gap-3">
            <Download className="w-5 h-5 animate-bounce" />
            <span className="font-medium">Downloading 5-year data for {universe} and rebuilding Parquet... This might take a minute.</span>
          </div>
        </div>
      )}
      {error && (
        <div className="p-4 bg-status-bearishDim border border-status-bearish rounded-md text-status-bearish">
          {error}
        </div>
      )}
      {}
      {results && activeTab === 'screener' && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-bg-surface border border-border-subtle rounded-md p-4">
            <div className="text-text-secondary mb-1">Universe</div>
            <div className="text-2xl font-semibold text-text-primary">{results.universe}</div>
          </div>
          <div className="bg-bg-surface border border-border-subtle rounded-md p-4">
            <div className="text-text-secondary mb-1">Stocks Scanned</div>
            <div className="text-2xl font-semibold text-text-primary">{results.scanned_count}</div>
          </div>
          <div className="bg-bg-surface border border-border-subtle rounded-md p-4">
            <div className="text-text-secondary mb-1">Shortlisted Stocks</div>
            <div className="text-2xl font-semibold text-text-primary">{results.shortlisted_count}</div>
          </div>
          <div className="bg-bg-surface border border-border-subtle rounded-md p-4">
            <div className="text-text-secondary mb-1">Total Pattern Matches</div>
            <div className="text-2xl font-semibold text-text-primary">{results.match_count}</div>
          </div>
        </div>
      )}
      {}
      <div className="flex justify-between items-center bg-bg-surface border border-border-subtle rounded-md p-2">
        <div className="flex gap-2">
          <button 
            className={`px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'screener' ? 'bg-bg-elevated text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            onClick={() => setActiveTab('screener')}
          >
            Screener Results
          </button>
          <button 
            className={`px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'watchlist' ? 'bg-bg-elevated text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            onClick={() => setActiveTab('watchlist')}
          >
            Watchlist ({watchlist.length})
          </button>
        </div>
        <div className="flex gap-4 items-center pr-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input 
              type="text" placeholder="Filter ticker or pattern..."
              className="pl-9 pr-4 py-1.5 bg-bg-elevated border border-border-subtle rounded-md text-text-primary focus:outline-none focus:border-border-medium"
              value={search} onChange={e => setSearch(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 cursor-pointer text-text-secondary hover:text-text-primary transition-colors">
            <input type="checkbox" className="rounded bg-bg-elevated border-border-subtle text-accent-cyan focus:ring-accent-cyan focus:ring-offset-bg-app" checked={volFilter} onChange={e => setVolFilter(e.target.checked)} />
            High Volume
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-text-secondary hover:text-text-primary transition-colors">
            <input type="checkbox" className="rounded bg-bg-elevated border-border-subtle text-accent-cyan focus:ring-accent-cyan focus:ring-offset-bg-app" checked={trendFilter} onChange={e => setTrendFilter(e.target.checked)} />
            Trend Aligned
          </label>
        </div>
      </div>
      {}
      <div className="bg-bg-surface border border-border-subtle rounded-md overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-border-subtle bg-bg-elevated">
              <th className="px-4 py-3 font-medium text-text-secondary">Ticker</th>
              <th className="px-4 py-3 font-medium text-text-secondary">Pattern</th>
              <th className="px-4 py-3 font-medium text-text-secondary">Direction</th>
              <th className="px-4 py-3 font-medium text-text-secondary text-right">Close Price</th>
              <th className="px-4 py-3 font-medium text-text-secondary">Volume</th>
              <th className="px-4 py-3 font-medium text-text-secondary">RSI (14)</th>
              <th className="px-4 py-3 font-medium text-text-secondary">MACD</th>
              <th className="px-4 py-3 font-medium text-text-secondary">Trend</th>
              <th className="px-4 py-3 font-medium text-text-secondary text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan="9" className="text-center py-12 text-text-muted">Scanning patterns...</td></tr>}
            {!loading && displayData.length === 0 && (
              <tr><td colSpan="9" className="text-center py-12 text-text-muted">No matches found for the current filters.</td></tr>
            )}
            {!loading && displayData.map((row, i) => {
              const isSaved = watchlist.some(w => w.ticker === row.ticker && w.pattern === row.pattern);
              return (
                <tr key={`${row.ticker}-${row.pattern}-${i}`} className="border-b border-border-subtle hover:bg-bg-hover transition-colors">
                  <td className="px-4 py-3 font-mono">
                    <button 
                      onClick={() => setChartSymbol(row.ticker)}
                      className="text-accent-cyan hover:underline font-semibold"
                    >
                      {row.ticker}
                    </button>
                  </td>
                  <td className="px-4 py-3">{row.pattern}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${row.direction === 'Bullish' ? 'bg-status-bullishDim text-status-bullish' : row.direction === 'Bearish' ? 'bg-status-bearishDim text-status-bearish' : 'bg-bg-elevated text-text-secondary'}`}>
                      {row.direction}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-right">{formatCurrency(row.close)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${row.is_volume_high ? 'bg-status-bullishDim text-status-bullish' : 'bg-bg-elevated text-text-secondary'}`}>
                      {row.is_volume_high ? 'High' : 'Low'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">
                    <span className={`${row.rsi_14 < 30 ? 'text-status-bullish font-semibold' : row.rsi_14 > 70 ? 'text-status-bearish font-semibold' : 'text-text-primary'}`}>
                      {row.rsi_14}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${row.macd_state === 'Bullish' ? 'bg-status-bullishDim text-status-bullish' : 'bg-status-bearishDim text-status-bearish'}`}>
                      {row.macd_state}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${row.trend_state === 1 ? 'bg-status-bullishDim text-status-bullish' : row.trend_state === -1 ? 'bg-status-bearishDim text-status-bearish' : 'bg-bg-elevated text-text-secondary'}`}>
                      {row.trend_state === 1 ? 'Uptrend' : row.trend_state === -1 ? 'Downtrend' : 'Neutral'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button 
                      onClick={() => toggleWatchlist(row)}
                      className={`p-1.5 rounded-full transition-colors ${isSaved ? 'text-status-warning bg-status-warningDim' : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'}`}
                      title={isSaved ? "Remove from watchlist" : "Add to watchlist"}
                    >
                      {isSaved ? <Star className="w-4 h-4 fill-current" /> : <StarOff className="w-4 h-4" />}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {}
      {chartSymbol && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="bg-bg-surface border border-border-subtle rounded-xl w-full max-w-[1200px] h-[80vh] flex flex-col shadow-2xl">
            <div className="flex justify-between items-center p-4 border-b border-border-subtle">
              <h3 className="font-semibold text-lg">{chartSymbol} Chart</h3>
              <button onClick={() => setChartSymbol(null)} className="p-1.5 hover:bg-bg-hover rounded-md text-text-secondary hover:text-text-primary transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 bg-[#131722] rounded-b-xl overflow-hidden relative">
              <iframe 
                src={`https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=${chartSymbol.replace('.NS', '')}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&style=1&timezone=Asia%2FKolkata&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=in`}
                className="absolute inset-0 w-full h-full border-none"
                title="TradingView Chart"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}