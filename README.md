# StockPulse

StockPulse is a complete, unified Quantitative Backtesting and Screening Platform built with Python (FastAPI + vectorbt) and React (Vite + TailwindCSS + Recharts).

## Architecture

The project is structured into two main applications:

- **`backend/`**: A high-performance Python FastAPI server acting as the central intelligence hub. It uses `vectorbt` for vectorized backtesting, handles real-time market data ingestion with Timezone-Aware safeguards, and stores 5-year historical series as compressed Parquet files for near-instant reads.
- **`frontend/`**: A modern React 19 application built with Vite. It features a stunning premium dark-mode UI with complex quantitative charts (Drawdown, Rolling Sharpe, Trade Distribution) rendered beautifully via Recharts.

## Getting Started

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Features
- **Vectorized Backtesting**: Test strategies on 500+ stocks simultaneously in milliseconds.
- **Advanced Tear Sheet**: Generate Institutional-grade visualizations (Drawdown curves, Rolling Sharpe, Monthly Returns Heatmap, Trade Distribution).
- **Market Guard**: Safe, timezone-aware daily data updates.
- **Dynamic Screener**: Instantly filter thousands of tickers matching specific technical patterns, trends, and volume parameters.
