# Advisor-Bot
JPMC Internship 2025 Advisor Bot

## What It Does

Advisor Bot is now a React + FastAPI demo that combines a risk questionnaire with market data from `yfinance`.

- React/Vite frontend dashboard
- FastAPI backend
- Stock search endpoint
- Risk scoring questionnaire
- Market indicators: RSI, MACD, moving averages, momentum, volatility, volume change
- Simulated strategy trades and KPI cards
- TradingView chart widget

## Run It Locally

Install frontend dependencies:

```bash
npm install
```

Install backend dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Start the backend API:

```bash
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:5173/
```

This is an educational demo only and is not financial advice.
