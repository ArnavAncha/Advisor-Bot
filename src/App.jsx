import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X
} from 'lucide-react';
import { fetchJson } from './api';

const FALLBACK_STOCKS = [
  { symbol: 'JPM', exchange: 'NYSE', name: 'JPMorgan Chase', tradingViewSymbol: 'NYSE:JPM' },
  { symbol: 'MSFT', exchange: 'NASDAQ', name: 'Microsoft', tradingViewSymbol: 'NASDAQ:MSFT' },
  { symbol: 'NVDA', exchange: 'NASDAQ', name: 'NVIDIA', tradingViewSymbol: 'NASDAQ:NVDA' },
  { symbol: 'AAPL', exchange: 'NASDAQ', name: 'Apple', tradingViewSymbol: 'NASDAQ:AAPL' }
];

const DEFAULT_QUESTIONS = [
  {
    id: 'timeline',
    label: 'Investment timeline',
    default: 'medium',
    options: [
      { value: 'short', label: 'Under 2 years' },
      { value: 'medium', label: '2 to 5 years' },
      { value: 'long', label: '5+ years' }
    ]
  },
  {
    id: 'drawdown',
    label: 'Comfort with temporary losses',
    default: 'moderate',
    options: [
      { value: 'low', label: 'Avoid big drops' },
      { value: 'moderate', label: 'Can handle some volatility' },
      { value: 'high', label: 'Comfortable with volatility' }
    ]
  },
  {
    id: 'goal',
    label: 'Primary objective',
    default: 'balanced',
    options: [
      { value: 'preserve', label: 'Preserve capital' },
      { value: 'balanced', label: 'Balanced growth' },
      { value: 'maximize', label: 'Maximize growth' }
    ]
  }
];

const defaultAnswersFor = (questions) =>
  questions.reduce((answers, question) => {
    answers[question.id] = question.default;
    return answers;
  }, {});

const formatSigned = (value) => {
  if (typeof value !== 'number') return '';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
};

const App = () => {
  const [symbol, setSymbol] = useState('NYSE:JPM');
  const [stocks, setStocks] = useState(FALLBACK_STOCKS);
  const [dashboard, setDashboard] = useState(null);
  const [questions, setQuestions] = useState(DEFAULT_QUESTIONS);
  const [answers, setAnswers] = useState(defaultAnswersFor(DEFAULT_QUESTIONS));
  const [advisor, setAdvisor] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [showAllTrades, setShowAllTrades] = useState(false);
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingAdvisor, setLoadingAdvisor] = useState(false);
  const [error, setError] = useState('');

  const answerKey = useMemo(() => JSON.stringify(answers), [answers]);
  const riskProfile = advisor?.riskProfile || 'Balanced';
  const advisorPanel = dashboard?.advisor || advisor;
  const selectedStock = stocks.find((stock) => stock.tradingViewSymbol === symbol) || dashboard?.market;
  const visibleTrades = dashboard?.trades
    ? showAllTrades ? dashboard.trades : dashboard.trades.slice(0, 5)
    : [];

  useEffect(() => {
    let ignore = false;

    async function loadStartupData() {
      try {
        const [stockResponse, questionResponse] = await Promise.all([
          fetchJson('/api/stocks'),
          fetchJson('/api/advisor/questions')
        ]);

        if (ignore) return;

        const nextStocks = stockResponse.stocks?.length ? stockResponse.stocks : FALLBACK_STOCKS;
        const nextQuestions = questionResponse.questions?.length ? questionResponse.questions : DEFAULT_QUESTIONS;
        setStocks(nextStocks);
        setQuestions(nextQuestions);
        setAnswers(defaultAnswersFor(nextQuestions));
      } catch (startupError) {
        if (!ignore) {
          setError(`Backend is not reachable yet: ${startupError.message}`);
        }
      }
    }

    loadStartupData();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadAdvice() {
      if (!Object.keys(answers).length) return;
      setLoadingAdvisor(true);
      try {
        const response = await fetchJson('/api/advisor', {
          method: 'POST',
          body: JSON.stringify({ symbol, answers })
        });
        if (!ignore) {
          setAdvisor(response);
        }
      } catch (adviceError) {
        if (!ignore) {
          setError(`Advisor scoring failed: ${adviceError.message}`);
        }
      } finally {
        if (!ignore) {
          setLoadingAdvisor(false);
        }
      }
    }

    loadAdvice();
    return () => {
      ignore = true;
    };
  }, [symbol, answerKey]);

  useEffect(() => {
    let ignore = false;

    async function loadDashboard() {
      setLoadingDashboard(true);
      setError('');
      try {
        const response = await fetchJson(
          `/api/dashboard?symbol=${encodeURIComponent(symbol)}&risk_profile=${encodeURIComponent(riskProfile)}`
        );
        if (!ignore) {
          setDashboard(response);
          setShowAllTrades(false);
        }
      } catch (dashboardError) {
        if (!ignore) {
          setError(`Market dashboard failed: ${dashboardError.message}`);
        }
      } finally {
        if (!ignore) {
          setLoadingDashboard(false);
        }
      }
    }

    loadDashboard();
    return () => {
      ignore = true;
    };
  }, [symbol, riskProfile]);

  useEffect(() => {
    let ignore = false;
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetchJson(`/api/stocks?query=${encodeURIComponent(searchQuery)}`);
        if (!ignore) {
          setSearchResults(response.stocks || []);
        }
      } catch {
        if (!ignore) {
          setSearchResults([]);
        }
      }
    }, 180);

    return () => {
      ignore = true;
      window.clearTimeout(timer);
    };
  }, [searchQuery]);

  const handleAnswerChange = (questionId, value) => {
    setAnswers((currentAnswers) => ({
      ...currentAnswers,
      [questionId]: value
    }));
  };

  const selectStock = (stock) => {
    setSymbol(stock.tradingViewSymbol);
    setSearchQuery('');
    setShowSearchResults(false);
    setTradeModalOpen(false);
  };

  const handleSearchKeyDown = (event) => {
    if (event.key === 'Enter' && searchResults.length) {
      event.preventDefault();
      selectStock(searchResults[0]);
    }
  };

  return (
    <>
      <main className="dashboard-content">
        <header className="dashboard-header">
          <div>
            <div className="dashboard-tag">
              <Bot size={14} /> JPMC Internship 2025
            </div>
            <h1>Advisor Bot Dashboard</h1>
            <p className="dashboard-subtitle">
              Data-backed portfolio monitoring, risk scoring, technical signals, and advisor-style action planning.
            </p>
          </div>

          <div className="search-shell">
            <Search className="search-icon" size={18} />
            <input
              type="search"
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.target.value);
                setShowSearchResults(true);
              }}
              onFocus={() => setShowSearchResults(true)}
              onBlur={() => window.setTimeout(() => setShowSearchResults(false), 120)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search ticker or company"
              aria-label="Search ticker or company"
            />
            {showSearchResults && (searchQuery || searchResults.length > 0) && (
              <div className="search-results">
                {searchResults.length ? (
                  searchResults.map((stock) => (
                    <button
                      type="button"
                      key={stock.tradingViewSymbol}
                      onMouseDown={() => selectStock(stock)}
                    >
                      <span>
                        <strong>{stock.symbol}</strong>
                        {stock.name}
                      </span>
                      <small>{stock.exchange}</small>
                    </button>
                  ))
                ) : (
                  <p>No matching tickers found.</p>
                )}
              </div>
            )}
          </div>
        </header>

        {error && (
          <div className="alert">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        <section className="advisor-hero-card">
          <div className="advisor-hero-copy">
            <div className="assistant-badge">
              <Sparkles size={14} /> AI Advisor
            </div>
            <h2>{selectedStock?.name || 'Selected asset'} plan</h2>
            <p>
              The recommendation now blends your questionnaire answers with live market data, momentum, RSI, volatility,
              and a simple model backtest.
            </p>
            <div className="advisor-actions">
              <div className="advisor-pill">
                <TrendingUp size={14} />
                {dashboard?.prediction?.action || 'Loading'} signal
              </div>
              <div className="advisor-pill">
                <ShieldCheck size={14} />
                {riskProfile} profile
              </div>
              {loadingAdvisor && (
                <div className="advisor-pill">
                  <Loader2 size={14} className="spin" />
                  scoring
                </div>
              )}
            </div>
          </div>

          <div className="advisor-hero-panel">
            <div className="advisor-score-row">
              <span className="advisor-label">Risk profile</span>
              <strong>{riskProfile}</strong>
              <small>{advisor?.riskScore ?? 50}/100</small>
            </div>

            <div className="question-grid">
              {questions.map((question) => (
                <label key={question.id}>
                  <span>{question.label}</span>
                  <select
                    value={answers[question.id] || question.default}
                    onChange={(event) => handleAnswerChange(question.id, event.target.value)}
                  >
                    {question.options.map((option) => (
                      <option value={option.value} key={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>

            <p className="advisor-response">
              {advisorPanel?.advisorNote || 'Answer the questions to generate a recommendation.'}
            </p>
            <div className="advisor-recommendations">
              <span>Suggested action</span>
              <strong>{advisorPanel?.suggestedAction || 'Loading...'}</strong>
            </div>
          </div>
        </section>

        <section className="market-strip">
          <div>
            <span className="advisor-label">Asset view</span>
            <select value={symbol} onChange={(event) => setSymbol(event.target.value)}>
              {stocks.map((stock) => (
                <option value={stock.tradingViewSymbol} key={stock.tradingViewSymbol}>
                  {stock.name} ({stock.symbol})
                </option>
              ))}
            </select>
          </div>
          <div className="market-price">
            <span>{dashboard?.market?.symbol || selectedStock?.symbol || 'JPM'}</span>
            <strong>{dashboard?.market ? `$${dashboard.market.price.toLocaleString()}` : '--'}</strong>
            <small className={dashboard?.market?.change >= 0 ? 'positive' : 'negative'}>
              {dashboard?.market
                ? `${formatSigned(dashboard.market.change)} (${formatSigned(dashboard.market.changePercent)}%)`
                : 'loading'}
            </small>
          </div>
          <div className="data-source">
            <CheckCircle2 size={16} />
            <span>{dashboard?.market?.dataSource || 'Waiting for backend data'}</span>
          </div>
        </section>

        <section className="kpi-cards">
          {(dashboard?.kpis || []).map((kpi) => (
            <Card key={kpi.title} {...kpi} />
          ))}
          {!dashboard?.kpis?.length && [1, 2, 3, 4].map((item) => <CardSkeleton key={item} />)}
        </section>

        <section className="performance-comparison">
          <div className="section-header">
            <div>
              <span className="advisor-label">Live chart</span>
              <h2>The Current Stock Market</h2>
            </div>
            {loadingDashboard && (
              <span className="loading-chip">
                <Loader2 size={14} className="spin" />
                loading data
              </span>
            )}
          </div>
          <div className="chart-frame">
            <StockWidget symbol={symbol} />
          </div>
        </section>

        <section className="dashboard-bottom-section">
          <div className="model-insights">
            <h2>Model Insights</h2>
            <ul>
              {(dashboard?.insights || []).map((insight) => (
                <li key={insight.label}>
                  {insight.label}
                  <span>{insight.value}</span>
                </li>
              ))}
              {!dashboard?.insights?.length && <li>Waiting for indicators <span>--</span></li>}
            </ul>
            <div className="latest-prediction">
              <h3>Latest Prediction</h3>
              <p className={`prediction-${(dashboard?.prediction?.action || 'hold').toLowerCase()}`}>
                {dashboard?.prediction?.action || 'HOLD'}
              </p>
              <p>Confidence: {dashboard?.prediction?.confidence ?? '--'}%</p>
              <small>{dashboard?.prediction?.note || 'Waiting for model signal.'}</small>
            </div>
          </div>

          <div className="trades-log">
            <div className="section-header">
              <div>
                <h2>Trades Log</h2>
                <p>Simulated trades from the technical signal strategy.</p>
              </div>
              <button type="button" className="ghost-btn" onClick={() => setTradeModalOpen(true)}>
                View full log
              </button>
            </div>

            <TradesTable trades={visibleTrades} />

            <button
              className="view-all-trades-btn"
              type="button"
              disabled={!dashboard?.trades?.length || dashboard.trades.length <= 5}
              onClick={() => setShowAllTrades((current) => !current)}
            >
              {showAllTrades ? 'Show recent trades' : `View all trades (${dashboard?.trades?.length || 0})`}
            </button>
          </div>
        </section>

        <p className="disclaimer">{dashboard?.disclaimer || 'Educational demo only. This is not financial advice.'}</p>
      </main>

      <footer className="footer">
        <p>&copy; 2025 AI Stock Dashboard. Data provided by TradingView and Yahoo Finance via yfinance.</p>
      </footer>

      {tradeModalOpen && (
        <TradeModal trades={dashboard?.trades || []} onClose={() => setTradeModalOpen(false)} />
      )}
    </>
  );
};

const Card = ({ title, value, change, updated }) => (
  <div className="card">
    <h3>{title}</h3>
    <p>
      <span className="value">{value}</span>
      {change && <span className={String(change).startsWith('-') ? 'negative' : 'positive'}>{change}</span>}
    </p>
    {updated && <span className="updated">{updated}</span>}
  </div>
);

const CardSkeleton = () => (
  <div className="card skeleton-card">
    <span />
    <strong />
    <small />
  </div>
);

const TradesTable = ({ trades }) => (
  <div className="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Action</th>
          <th>Shares</th>
          <th>Price ($)</th>
          <th>Portfolio ($)</th>
        </tr>
      </thead>
      <tbody>
        {trades.length ? (
          trades.map((trade) => (
            <tr key={`${trade.date}-${trade.action}-${trade.price}`}>
              <td>{trade.date}</td>
              <td>
                <span className={`trade-action action-${trade.action.toLowerCase()}`}>{trade.action}</span>
              </td>
              <td>{trade.shares.toLocaleString()}</td>
              <td>{trade.price.toLocaleString()}</td>
              <td>{trade.portfolio.toLocaleString()}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="5" className="empty-table">
              No strategy trades found for this asset yet.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
);

const TradeModal = ({ trades, onClose }) => (
  <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <section className="trade-modal" role="dialog" aria-modal="true" aria-label="Full trades log" onMouseDown={(event) => event.stopPropagation()}>
      <div className="section-header">
        <div>
          <span className="advisor-label">Full strategy history</span>
          <h2>Trades Log</h2>
        </div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close trades log">
          <X size={18} />
        </button>
      </div>
      <TradesTable trades={trades} />
    </section>
  </div>
);

const StockWidget = ({ symbol }) => {
  const containerRef = useRef(null);
  const widgetId = useMemo(
    () => `tradingview-chart-${symbol.replace(/[^a-z0-9]/gi, '-').toLowerCase()}`,
    [symbol]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.replaceChildren();

    const widget = document.createElement('div');
    widget.className = 'tradingview-widget-container__widget';
    container.appendChild(widget);

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.innerHTML = JSON.stringify({
      symbol,
      interval: 'D',
      timezone: 'Etc/UTC',
      theme: 'dark',
      style: '2',
      locale: 'en',
      withdateranges: true,
      allow_symbol_change: true,
      autosize: true,
      container_id: widgetId
    });
    container.appendChild(script);

    return () => {
      container.replaceChildren();
    };
  }, [symbol, widgetId]);

  return <div id={widgetId} ref={containerRef} className="stock-widget" />;
};

export default App;
