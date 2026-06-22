import React, { useState, useEffect } from 'react';
import { Play, Info, Download } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart, ReferenceLine, BarChart, Bar, Cell } from 'recharts';
import { runBacktest, getSymbols, refreshData, checkDownloadStatus } from '../lib/api';
export default function Backtester() {
  const [universe, setUniverse] = useState('nifty500');
  const [mode, setMode] = useState('portfolio');
  const [ticker, setTicker] = useState('');
  const [symbols, setSymbols] = useState([]);
  const [capital, setCapital] = useState(100000);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (mode === 'single') {
      getSymbols(universe).then(setSymbols).catch(console.error);
    }
  }, [universe, mode]);
  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runBacktest(universe, mode === 'portfolio' ? 'all' : ticker, capital);
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
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
    }
  };
  const formatCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  const calculateTradeDistribution = (returns) => {
    if (!returns || returns.length === 0) return [];
    const bins = [
      { name: '< -10%', min: -Infinity, max: -10, count: 0 },
      { name: '-10% to -5%', min: -10, max: -5, count: 0 },
      { name: '-5% to -2%', min: -5, max: -2, count: 0 },
      { name: '-2% to 0%', min: -2, max: 0, count: 0 },
      { name: '0% to +2%', min: 0, max: 2, count: 0 },
      { name: '+2% to +5%', min: 2, max: 5, count: 0 },
      { name: '+5% to +10%', min: 5, max: 10, count: 0 },
      { name: '+10% to +20%', min: 10, max: 20, count: 0 },
      { name: '> +20%', min: 20, max: Infinity, count: 0 }
    ];
    returns.forEach(r => {
      for (let bin of bins) {
        if (r > bin.min && r <= bin.max) {
          bin.count++;
          break;
        }
      }
    });
    return bins.filter(b => b.count > 0);
  };
  return (
    <div className="flex flex-col gap-6">
      {}
      <div>
        <h1 className="text-3xl font-semibold text-text-primary mb-2">Strategy Backtester</h1>
        <p className="text-text-secondary">Test the Pattern + Trend + Volume strategy on historical data</p>
      </div>
      {}
      <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
        <div className="grid grid-cols-4 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Universe</label>
            <select 
              className="w-full bg-bg-elevated border border-border-subtle rounded-md px-3 py-2 text-text-primary focus:outline-none focus:border-border-medium"
              value={universe} onChange={e => setUniverse(e.target.value)}
            >
              <option value="nifty50">Nifty 50</option>
              <option value="nifty500">Nifty 500</option>
              <option value="sp500">S&P 500</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Mode</label>
            <div className="flex gap-4 pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-text-primary">
                <input type="radio" name="mode" value="portfolio" checked={mode === 'portfolio'} onChange={() => setMode('portfolio')} className="text-accent-cyan focus:ring-accent-cyan" />
                Portfolio
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-text-primary">
                <input type="radio" name="mode" value="single" checked={mode === 'single'} onChange={() => setMode('single')} className="text-accent-cyan focus:ring-accent-cyan" />
                Single Stock
              </label>
            </div>
          </div>
          {mode === 'single' && (
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Ticker</label>
              <input 
                type="text" list="symbol-list"
                placeholder="e.g. RELIANCE.NS"
                className="w-full bg-bg-elevated border border-border-subtle rounded-md px-3 py-2 text-text-primary focus:outline-none focus:border-border-medium uppercase"
                value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())}
              />
              <datalist id="symbol-list">
                {symbols.map(s => <option key={s} value={s} />)}
              </datalist>
            </div>
          )}
          <div className={mode === 'portfolio' ? 'col-span-2' : ''}>
            <label className="block text-sm font-medium text-text-secondary mb-2">Initial Capital (₹)</label>
            <input 
              type="number" step="10000" min="10000"
              className="w-full bg-bg-elevated border border-border-subtle rounded-md px-3 py-2 text-text-primary focus:outline-none focus:border-border-medium font-mono"
              value={capital} onChange={e => setCapital(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="flex justify-between items-center pt-6 border-t border-border-subtle">
          <div className="flex items-center gap-2 text-text-secondary group cursor-help relative">
            <Info className="w-5 h-5 text-accent-cyan" />
            <span className="font-medium">Strategy: Pattern + Trend + RSI + Volume</span>
            <div className="absolute left-0 bottom-full mb-2 w-80 bg-bg-elevated border border-border-subtle rounded shadow-xl p-3 text-sm opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
              <strong>Long:</strong> Uptrend + Bullish Pattern + RSI&lt;70 + High Volume<br/>
              <strong>Short:</strong> Downtrend + Bearish Pattern + RSI&gt;30 + High Volume<br/>
              <strong>Exit:</strong> Inverse signal or Stop Loss (8%) / Take Profit (24%)
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={handleRefresh} disabled={refreshing || loading}
              className="flex items-center gap-2 px-4 py-2 border border-border-subtle rounded-md hover:bg-bg-hover transition-colors disabled:opacity-50 text-text-primary"
            >
              <Download className="w-4 h-4" />
              Refresh Data
            </button>
            <button 
              onClick={handleRun} disabled={loading || refreshing || (mode === 'single' && !ticker)}
              className="flex items-center gap-2 px-6 py-2.5 bg-accent-cyan text-bg-app font-semibold rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center gap-2"><div className="w-4 h-4 border-2 border-bg-app border-t-transparent rounded-full animate-spin"></div> Running...</span>
              ) : (
                <><Play className="w-4 h-4 fill-current" /> Run Backtest</>
              )}
            </button>
          </div>
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
      {results && !loading && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
          {}
          <div className="grid grid-cols-5 gap-4">
            {[
              { label: 'Total Return', value: `${results.total_return}%`, color: results.total_return >= 0 ? 'text-status-bullish' : 'text-status-bearish' },
              { label: 'Win Rate', value: `${results.win_rate}%`, color: 'text-text-primary' },
              { label: 'Sharpe Ratio', value: results.sharpe_ratio, color: results.sharpe_ratio > 1 ? 'text-status-bullish' : results.sharpe_ratio > 0 ? 'text-status-warning' : 'text-status-bearish' },
              { label: 'Max Drawdown', value: `${results.max_drawdown}%`, color: 'text-status-bearish' },
              { label: 'Total Trades', value: results.total_trades, color: 'text-text-primary' },
            ].map((metric, i) => (
              <div key={i} className="bg-bg-surface border border-border-subtle rounded-md p-5 flex flex-col justify-center items-center text-center">
                <div className={`text-3xl font-bold font-mono tracking-tight mb-2 ${metric.color}`}>
                  {metric.value}
                </div>
                <div className="text-sm font-medium text-text-secondary uppercase tracking-wider">{metric.label}</div>
              </div>
            ))}
          </div>
          {}
          <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
            <h3 className="font-semibold text-lg mb-6">Equity Curve</h3>
            <div className="w-full h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={results.equity_curve} margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a2232" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    stroke="#8b95a5" 
                    tick={{fill: '#8b95a5', fontSize: 12}}
                    tickMargin={10}
                    minTickGap={30}
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    stroke="#8b95a5" 
                    tick={{fill: '#8b95a5', fontSize: 12}}
                    tickFormatter={(val) => `₹${(val/1000).toFixed(0)}k`}
                    width={80}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111720', borderColor: '#243044', borderRadius: '6px', color: '#e8ecf2' }}
                    itemStyle={{ color: '#00d4ff', fontWeight: 600 }}
                    formatter={(value) => [formatCurrency(value), 'Portfolio Value']}
                    labelStyle={{ color: '#8b95a5', marginBottom: '4px' }}
                  />
                  <ReferenceLine 
                    y={results.initial_capital} 
                    stroke="#ffb347" 
                    strokeDasharray="3 3" 
                    strokeOpacity={0.5}
                    label={{ position: 'insideTopLeft', value: 'Initial Capital', fill: '#ffb347', fontSize: 12, dy: -10 }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#00d4ff" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorValue)" 
                    isAnimationActive={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          {}
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
              <h3 className="font-semibold text-lg mb-6 text-status-bearish">Drawdown Curve</h3>
              <div className="w-full h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={results.equity_curve} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a2232" vertical={false} />
                    <XAxis dataKey="date" stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 10}} minTickGap={30} />
                    <YAxis stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 10}} tickFormatter={(val) => `${val}%`} />
                    <Tooltip contentStyle={{ backgroundColor: '#111720', borderColor: '#243044', borderRadius: '6px', color: '#e8ecf2' }} formatter={(val) => [`${val}%`, 'Drawdown']} />
                    <Area type="monotone" dataKey="drawdown" stroke="#ff4757" strokeWidth={2} fillOpacity={0.2} fill="#ff4757" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
              <h3 className="font-semibold text-lg mb-6 text-status-warning">Rolling Sharpe (6-Month)</h3>
              <div className="w-full h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={results.equity_curve} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a2232" vertical={false} />
                    <XAxis dataKey="date" stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 10}} minTickGap={30} />
                    <YAxis stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 10}} domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#111720', borderColor: '#243044', borderRadius: '6px', color: '#e8ecf2' }} formatter={(val) => [val, 'Sharpe Ratio']} />
                    <Line type="monotone" dataKey="rolling_sharpe" stroke="#ffb347" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          {}
          <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
            <h3 className="font-semibold text-lg mb-6">Trade Return Distribution</h3>
            <div className="w-full h-[300px]">
              {(!results.trade_returns || results.trade_returns.length === 0) ? (
                <div className="h-full flex items-center justify-center text-text-muted">No trades recorded</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={calculateTradeDistribution(results.trade_returns)} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a2232" vertical={false} />
                    <XAxis dataKey="name" stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 11}} interval={0} angle={-45} textAnchor="end" />
                    <YAxis stroke="#8b95a5" tick={{fill: '#8b95a5', fontSize: 11}} allowDecimals={false} />
                    <Tooltip cursor={{fill: '#1a2232'}} contentStyle={{ backgroundColor: '#111720', borderColor: '#243044', borderRadius: '6px', color: '#e8ecf2' }} formatter={(val) => [val, 'Trades']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {calculateTradeDistribution(results.trade_returns).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.max <= 0 ? '#ff4757' : '#00e5a0'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          {}
          {results.heatmap_data && results.heatmap_data.length > 0 && (
            <div className="bg-bg-surface border border-border-subtle rounded-md p-6">
              <h3 className="font-semibold text-lg mb-4">Monthly Returns (%)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-text-secondary w-16">Year</th>
                      {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                        <th key={i} className="px-3 py-2 text-center font-medium text-text-secondary">{m}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.heatmap_data.map((row) => (
                      <tr key={row.year} className="border-t border-border-subtle">
                        <td className="px-3 py-2 font-medium text-text-primary">{row.year}</td>
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => {
                          const val = row[m.toString()];
                          if (val === null || val === undefined) {
                            return <td key={m} className="px-3 py-2 text-center text-text-muted">-</td>;
                          }
                          const isPositive = val > 0;
                          const opacity = Math.min(Math.abs(val) / 10, 1); 
                          const bgColor = isPositive ? `rgba(0, 229, 160, ${opacity * 0.5 + 0.1})` : `rgba(255, 71, 87, ${opacity * 0.5 + 0.1})`;
                          return (
                            <td key={m} className="px-3 py-2 text-center font-mono" style={{ backgroundColor: bgColor }}>
                              <span className={isPositive ? 'text-status-bullish font-semibold drop-shadow-sm' : 'text-status-bearish font-semibold drop-shadow-sm'}>
                                {val > 0 ? '+' : ''}{val.toFixed(1)}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {}
          <div className="bg-bg-surface border border-border-subtle rounded-md px-6 py-4 flex justify-between items-center text-sm font-medium">
            <div className="text-text-secondary">
              Target: <span className="text-text-primary px-2 py-1 bg-bg-elevated rounded ml-2 font-mono uppercase">{results.ticker}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-text-secondary">Initial: <span className="text-text-primary font-mono">{formatCurrency(results.initial_capital)}</span></span>
              <span className="text-text-muted">→</span>
              <span className="text-text-secondary">Final: <span className={`${results.final_value >= results.initial_capital ? 'text-status-bullish' : 'text-status-bearish'} font-mono`}>{formatCurrency(results.final_value)}</span></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}