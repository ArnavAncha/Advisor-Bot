from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="Advisor Bot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STOCKS: List[Dict[str, str]] = [
    {"symbol": "JPM", "exchange": "NYSE", "name": "JPMorgan Chase", "tradingViewSymbol": "NYSE:JPM"},
    {"symbol": "MSFT", "exchange": "NASDAQ", "name": "Microsoft", "tradingViewSymbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "exchange": "NASDAQ", "name": "NVIDIA", "tradingViewSymbol": "NASDAQ:NVDA"},
    {"symbol": "AAPL", "exchange": "NASDAQ", "name": "Apple", "tradingViewSymbol": "NASDAQ:AAPL"},
    {"symbol": "AMZN", "exchange": "NASDAQ", "name": "Amazon", "tradingViewSymbol": "NASDAQ:AMZN"},
    {"symbol": "GOOGL", "exchange": "NASDAQ", "name": "Alphabet", "tradingViewSymbol": "NASDAQ:GOOGL"},
    {"symbol": "META", "exchange": "NASDAQ", "name": "Meta Platforms", "tradingViewSymbol": "NASDAQ:META"},
    {"symbol": "TSLA", "exchange": "NASDAQ", "name": "Tesla", "tradingViewSymbol": "NASDAQ:TSLA"},
    {"symbol": "BAC", "exchange": "NYSE", "name": "Bank of America", "tradingViewSymbol": "NYSE:BAC"},
    {"symbol": "GS", "exchange": "NYSE", "name": "Goldman Sachs", "tradingViewSymbol": "NYSE:GS"},
    {"symbol": "SPY", "exchange": "NYSEARCA", "name": "SPDR S&P 500 ETF", "tradingViewSymbol": "AMEX:SPY"},
    {"symbol": "QQQ", "exchange": "NASDAQ", "name": "Invesco QQQ Trust", "tradingViewSymbol": "NASDAQ:QQQ"},
]

QUESTIONNAIRE: List[Dict[str, Any]] = [
    {
        "id": "timeline",
        "label": "Investment timeline",
        "default": "medium",
        "options": [
            {"value": "short", "label": "Under 2 years", "score": 1},
            {"value": "medium", "label": "2 to 5 years", "score": 2},
            {"value": "long", "label": "5+ years", "score": 3},
        ],
    },
    {
        "id": "drawdown",
        "label": "Comfort with temporary losses",
        "default": "moderate",
        "options": [
            {"value": "low", "label": "Avoid big drops", "score": 1},
            {"value": "moderate", "label": "Can handle some volatility", "score": 2},
            {"value": "high", "label": "Comfortable with volatility", "score": 3},
        ],
    },
    {
        "id": "goal",
        "label": "Primary objective",
        "default": "balanced",
        "options": [
            {"value": "preserve", "label": "Preserve capital", "score": 1},
            {"value": "balanced", "label": "Balanced growth", "score": 2},
            {"value": "maximize", "label": "Maximize growth", "score": 3},
        ],
    },
    {
        "id": "liquidity",
        "label": "Need for cash access",
        "default": "medium",
        "options": [
            {"value": "high", "label": "Need cash soon", "score": 1},
            {"value": "medium", "label": "Some cash needed", "score": 2},
            {"value": "low", "label": "Can stay invested", "score": 3},
        ],
    },
    {
        "id": "experience",
        "label": "Investing experience",
        "default": "some",
        "options": [
            {"value": "new", "label": "New investor", "score": 1},
            {"value": "some", "label": "Some experience", "score": 2},
            {"value": "advanced", "label": "Advanced investor", "score": 3},
        ],
    },
]

_HISTORY_CACHE: Dict[str, Tuple[datetime, pd.DataFrame, str]] = {}
_CACHE_TTL = timedelta(minutes=10)


class AdvisorRequest(BaseModel):
    symbol: str = "JPM"
    answers: Dict[str, str] = Field(default_factory=dict)


def normalize_symbol(symbol: str) -> str:
    raw_symbol = (symbol or "JPM").strip().upper()
    if ":" in raw_symbol:
        raw_symbol = raw_symbol.split(":", 1)[1]
    return raw_symbol.replace(".", "-")


def stock_info(symbol: str) -> Dict[str, str]:
    normalized = normalize_symbol(symbol)
    for stock in STOCKS:
        if stock["symbol"] == normalized:
            return stock
    exchange = "NASDAQ" if normalized in {"MSFT", "NVDA", "AAPL", "AMZN", "GOOGL", "META", "TSLA"} else "NYSE"
    return {
        "symbol": normalized,
        "exchange": exchange,
        "name": normalized,
        "tradingViewSymbol": f"{exchange}:{normalized}",
    }


def money(value: float) -> str:
    return f"${value:,.0f}"


def percent(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def number(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return fallback
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return fallback
        return result
    except (TypeError, ValueError):
        return fallback


def latest(series: pd.Series, fallback: float = 0.0) -> float:
    clean = series.dropna()
    if clean.empty:
        return fallback
    return safe_float(clean.iloc[-1], fallback)


def fetch_history(symbol: str) -> Tuple[pd.DataFrame, str]:
    normalized = normalize_symbol(symbol)
    cached = _HISTORY_CACHE.get(normalized)
    if cached and datetime.utcnow() - cached[0] < _CACHE_TTL:
        return cached[1].copy(), cached[2]

    try:
        history = yf.Ticker(normalized).history(period="1y", interval="1d", auto_adjust=True)
        if history.empty or "Close" not in history:
            raise ValueError("Yahoo Finance returned no price history.")
        history = history.dropna(subset=["Close"]).copy()
        source = "Yahoo Finance via yfinance"
    except Exception:
        history = fallback_history(normalized)
        source = "Generated fallback because Yahoo Finance was unavailable"

    if history.empty or len(history) < 35:
        raise HTTPException(status_code=502, detail=f"Not enough market data for {normalized}.")

    _HISTORY_CACHE[normalized] = (datetime.utcnow(), history.copy(), source)
    return history, source


def fallback_history(symbol: str) -> pd.DataFrame:
    seed = sum(ord(char) for char in symbol)
    rng = random.Random(seed)
    dates = pd.bdate_range(end=datetime.utcnow().date(), periods=252)
    price = 70 + (seed % 140)
    rows = []

    for date in dates:
        drift = 0.0004 + (seed % 7) * 0.00008
        shock = rng.gauss(0, 0.016)
        price = max(5, price * (1 + drift + shock))
        open_price = price * (1 + rng.gauss(0, 0.004))
        high_price = max(open_price, price) * (1 + abs(rng.gauss(0, 0.006)))
        low_price = min(open_price, price) * (1 - abs(rng.gauss(0, 0.006)))
        volume = int(4_000_000 + rng.random() * 18_000_000)
        rows.append(
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": price,
                "Volume": volume,
            }
        )

    return pd.DataFrame(rows, index=dates)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean().replace(0, 1e-9)
    return 100 - (100 / (1 + gains / losses))


def with_indicators(history: pd.DataFrame) -> pd.DataFrame:
    data = history.copy()
    close = data["Close"]
    data["return"] = close.pct_change()
    data["sma20"] = close.rolling(20).mean()
    data["sma50"] = close.rolling(50).mean()
    data["sma200"] = close.rolling(200).mean()
    data["rsi"] = rsi(close)
    data["ema12"] = close.ewm(span=12, adjust=False).mean()
    data["ema26"] = close.ewm(span=26, adjust=False).mean()
    data["macd"] = data["ema12"] - data["ema26"]
    data["macdSignal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["momentum20"] = close.pct_change(20) * 100
    data["volatility30"] = data["return"].rolling(30).std() * math.sqrt(252) * 100
    if "Volume" in data:
        rolling_volume = data["Volume"].rolling(20).mean().replace(0, pd.NA)
        data["volumeChange"] = (data["Volume"] / rolling_volume - 1) * 100
    else:
        data["volumeChange"] = 0
    return data


def signal_from_row(row: pd.Series) -> Tuple[str, float]:
    price = safe_float(row.get("Close"))
    sma20 = safe_float(row.get("sma20"), price)
    sma50 = safe_float(row.get("sma50"), price)
    rsi_value = safe_float(row.get("rsi"), 50)
    macd_delta = safe_float(row.get("macd")) - safe_float(row.get("macdSignal"))
    momentum = safe_float(row.get("momentum20"))

    score = 0.0
    score += 1.0 if price > sma20 else -1.0
    score += 1.0 if price > sma50 else -1.0
    score += 0.8 if macd_delta > 0 else -0.8
    score += 0.6 if momentum > 0 else -0.6

    if 45 <= rsi_value <= 70:
        score += 0.5
    elif rsi_value < 35:
        score += 0.4
    elif rsi_value > 75:
        score -= 1.0

    if score >= 1.5:
        return "BUY", score
    if score <= -1.5:
        return "SELL", score
    return "HOLD", score


def risk_profile_from_answers(answers: Dict[str, str]) -> Dict[str, Any]:
    score_total = 0
    min_total = 0
    max_total = 0
    normalized_answers: Dict[str, str] = {}

    for question in QUESTIONNAIRE:
        options = question["options"]
        scores_by_value = {option["value"]: int(option["score"]) for option in options}
        selected = answers.get(question["id"], question["default"])
        if selected not in scores_by_value:
            selected = question["default"]

        normalized_answers[question["id"]] = selected
        score_total += scores_by_value[selected]
        min_total += min(scores_by_value.values())
        max_total += max(scores_by_value.values())

    risk_score = round(((score_total - min_total) / (max_total - min_total)) * 100)
    if risk_score < 40:
        profile = "Conservative"
    elif risk_score < 70:
        profile = "Balanced"
    else:
        profile = "Growth"

    return {"riskProfile": profile, "riskScore": risk_score, "answers": normalized_answers}


def recommendation(profile: str, prediction: str, confidence: int, metrics: Dict[str, float]) -> Dict[str, Any]:
    rsi_value = metrics["rsi"]
    volatility = metrics["volatility30"]
    momentum = metrics["momentum20"]

    if prediction == "BUY":
        action_by_profile = {
            "Conservative": "Add gradually, keep a larger cash buffer, and use a tight review threshold.",
            "Balanced": "Rebalance into the position in stages while keeping diversification intact.",
            "Growth": "Increase exposure more actively, but set a stop-loss and position limit.",
        }
        base = "Trend and momentum are supportive"
    elif prediction == "SELL":
        action_by_profile = {
            "Conservative": "Reduce exposure and protect capital until the trend improves.",
            "Balanced": "Trim the position and wait for a stronger technical setup.",
            "Growth": "Avoid adding now; only keep exposure if it fits a high-volatility plan.",
        }
        base = "The setup is weak"
    else:
        action_by_profile = {
            "Conservative": "Hold current exposure and keep cash available.",
            "Balanced": "Hold and rebalance only if the position drifts from target allocation.",
            "Growth": "Watch for a breakout before increasing exposure.",
        }
        base = "Signals are mixed"

    note = (
        f"{base}: RSI is {rsi_value:.1f}, 20-day momentum is {momentum:.1f}%, "
        f"and 30-day annualized volatility is {volatility:.1f}%. "
        f"For a {profile.lower()} profile, the model confidence is {confidence}%."
    )

    return {
        "riskProfile": profile,
        "advisorNote": note,
        "suggestedAction": action_by_profile.get(profile, action_by_profile["Balanced"]),
    }


def simulate_strategy(data: pd.DataFrame) -> Dict[str, Any]:
    initial_cash = 100_000.0
    cash = initial_cash
    shares = 0
    trades: List[Dict[str, Any]] = []
    last_trade_index = -10

    for index_position in range(50, len(data)):
        row = data.iloc[index_position]
        price = safe_float(row["Close"])
        if price <= 0:
            continue

        signal, _score = signal_from_row(row)
        if index_position - last_trade_index < 7:
            continue

        date_value = data.index[index_position]
        date_label = date_value.date().isoformat() if hasattr(date_value, "date") else str(date_value)

        if signal == "BUY" and cash > 1000:
            quantity = math.floor((cash * 0.92) / price)
            if quantity <= 0:
                continue
            cash -= quantity * price
            shares += quantity
            last_trade_index = index_position
            trades.append(
                {
                    "date": date_label,
                    "action": "BUY",
                    "shares": quantity,
                    "price": round(price, 2),
                    "portfolio": round(cash + shares * price, 2),
                }
            )
        elif signal == "SELL" and shares > 0:
            cash += shares * price
            sold_shares = shares
            shares = 0
            last_trade_index = index_position
            trades.append(
                {
                    "date": date_label,
                    "action": "SELL",
                    "shares": sold_shares,
                    "price": round(price, 2),
                    "portfolio": round(cash, 2),
                }
            )

    final_price = safe_float(data["Close"].iloc[-1])
    portfolio_value = cash + shares * final_price

    first_price = safe_float(data["Close"].iloc[0], final_price)
    buy_hold_shares = initial_cash / first_price if first_price > 0 else 0
    buy_hold_value = buy_hold_shares * final_price

    return {
        "portfolioValue": portfolio_value,
        "portfolioReturn": ((portfolio_value / initial_cash) - 1) * 100,
        "buyHoldValue": buy_hold_value,
        "buyHoldReturn": ((buy_hold_value / initial_cash) - 1) * 100,
        "trades": list(reversed(trades[-25:])),
    }


def signal_accuracy(data: pd.DataFrame) -> float:
    correct = 0
    total = 0

    for index_position in range(50, len(data) - 1):
        signal, _score = signal_from_row(data.iloc[index_position])
        if signal == "HOLD":
            continue
        next_return = safe_float(data["Close"].iloc[index_position + 1] / data["Close"].iloc[index_position] - 1)
        predicted_up = signal == "BUY"
        actual_up = next_return > 0
        correct += int(predicted_up == actual_up)
        total += 1

    if total == 0:
        return 50.0
    return (correct / total) * 100


def build_dashboard(symbol: str, risk_profile: str) -> Dict[str, Any]:
    stock = stock_info(symbol)
    history, source = fetch_history(stock["symbol"])
    data = with_indicators(history)

    close = data["Close"].dropna()
    if len(close) < 2:
        raise HTTPException(status_code=502, detail=f"Not enough close-price data for {stock['symbol']}.")

    price = safe_float(close.iloc[-1])
    previous_price = safe_float(close.iloc[-2], price)
    change = price - previous_price
    change_percent = (change / previous_price) * 100 if previous_price else 0
    latest_row = data.iloc[-1]
    prediction, model_score = signal_from_row(latest_row)
    confidence = int(max(52, min(94, 56 + abs(model_score) * 11)))

    metrics = {
        "rsi": latest(data["rsi"], 50),
        "sma20": latest(data["sma20"], price),
        "sma50": latest(data["sma50"], price),
        "sma200": latest(data["sma200"], price),
        "momentum20": latest(data["momentum20"]),
        "volatility30": latest(data["volatility30"]),
        "volumeChange": latest(data["volumeChange"]),
        "macdDelta": latest(data["macd"] - data["macdSignal"]),
    }

    backtest = simulate_strategy(data)
    accuracy = signal_accuracy(data)
    relative_return = backtest["portfolioReturn"] - backtest["buyHoldReturn"]
    advisor = recommendation(risk_profile, prediction, confidence, metrics)

    return {
        "market": {
            **stock,
            "price": round(price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "updatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "dataSource": source,
        },
        "kpis": [
            {
                "title": "Model Portfolio Value",
                "value": money(backtest["portfolioValue"]),
                "change": percent(backtest["portfolioReturn"]),
                "updated": "SMA/RSI/MACD strategy",
            },
            {
                "title": "Buy-and-Hold Value",
                "value": money(backtest["buyHoldValue"]),
                "change": percent(backtest["buyHoldReturn"]),
                "updated": f"{stock['symbol']} 1-year baseline",
            },
            {
                "title": "ROI vs Hold",
                "value": percent(relative_return),
                "change": "strategy spread",
                "updated": "model vs asset hold",
            },
            {
                "title": "Signal Accuracy",
                "value": f"{accuracy:.0f}%",
                "change": f"{confidence}% conf.",
                "updated": "next-day direction",
            },
        ],
        "insights": [
            {"label": "RSI (14-day)", "value": number(metrics["rsi"], 1)},
            {"label": "MACD spread", "value": number(metrics["macdDelta"], 2)},
            {"label": "20-day momentum", "value": percent(metrics["momentum20"])},
            {"label": "30-day volatility", "value": percent(metrics["volatility30"])},
            {"label": "Price vs 50-day SMA", "value": percent(((price / metrics["sma50"]) - 1) * 100 if metrics["sma50"] else 0)},
            {"label": "Volume vs 20-day avg", "value": percent(metrics["volumeChange"])},
        ],
        "prediction": {
            "action": prediction,
            "confidence": confidence,
            "note": (
                f"Signal score {model_score:.1f}; price is {percent(((price / metrics['sma50']) - 1) * 100 if metrics['sma50'] else 0)} "
                "versus the 50-day moving average."
            ),
        },
        "advisor": advisor,
        "trades": backtest["trades"],
        "disclaimer": "Educational demo only. This is not financial advice.",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stocks")
def stocks(q: str = Query("", alias="query")) -> Dict[str, List[Dict[str, str]]]:
    query = q.strip().lower()
    if not query:
        return {"stocks": STOCKS}

    matches = [
        stock
        for stock in STOCKS
        if query in stock["symbol"].lower()
        or query in stock["name"].lower()
        or query in stock["exchange"].lower()
    ]
    return {"stocks": matches[:12]}


@app.get("/api/advisor/questions")
def advisor_questions() -> Dict[str, List[Dict[str, Any]]]:
    return {"questions": QUESTIONNAIRE}


@app.post("/api/advisor")
def advisor(request: AdvisorRequest) -> Dict[str, Any]:
    risk = risk_profile_from_answers(request.answers)
    stock = stock_info(request.symbol)
    profile = risk["riskProfile"]
    template_note = {
        "Conservative": "This profile prioritizes capital protection, lower drawdowns, and smaller position sizes.",
        "Balanced": "This profile balances growth opportunities with diversification and risk controls.",
        "Growth": "This profile accepts higher volatility in exchange for stronger upside potential.",
    }[profile]
    action = {
        "Conservative": "Keep a larger cash buffer and add only when the signal is strong.",
        "Balanced": "Use staged rebalancing and keep sector exposure diversified.",
        "Growth": "Allow more equity exposure, but define a stop-loss before adding.",
    }[profile]

    return {
        **risk,
        "symbol": stock["symbol"],
        "name": stock["name"],
        "advisorNote": template_note,
        "suggestedAction": action,
        "questions": QUESTIONNAIRE,
    }


@app.get("/api/dashboard")
def dashboard(
    symbol: str = Query("JPM"),
    risk_profile: str = Query("Balanced", pattern="^(Conservative|Balanced|Growth)$"),
) -> Dict[str, Any]:
    return build_dashboard(symbol, risk_profile)
