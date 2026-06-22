const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export async function scanMarket(universe) {
  const res = await fetch(`${API}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ universe }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Scan failed (${res.status})`);
  }
  return res.json();
}
export async function refreshData(universe) {
  const res = await fetch(`${API}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ universe }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Refresh failed (${res.status})`);
  }
  return res.json();
}
export async function runBacktest(universe, ticker, initialCapital) {
  const res = await fetch(`${API}/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      universe,
      ticker: ticker || null,
      initial_capital: initialCapital,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Backtest failed (${res.status})`);
  }
  return res.json();
}
export async function getSymbols(universe) {
  const res = await fetch(`${API}/symbols/${universe}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Failed to fetch symbols (${res.status})`);
  }
  return res.json();
}
export async function getDataStatus() {
  const res = await fetch(`${API}/data-status`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Failed to fetch data status (${res.status})`);
  }
  return res.json();
}

export async function checkDownloadStatus(universe) {
  const res = await fetch(`${API}/download-status/${universe}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Failed to check download status (${res.status})`);
  }
  return res.json();
}