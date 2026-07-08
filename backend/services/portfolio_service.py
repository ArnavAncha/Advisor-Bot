from sqlalchemy.orm import Session
from models import Portfolio, PortfolioHolding
from schemas import PortfolioCreate, PortfolioUpdate
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PortfolioService:
    def create_portfolio(self, db: Session, user_id, portfolio_data: PortfolioCreate) -> Portfolio:
        """Create a new portfolio for a user"""
        portfolio = Portfolio(
            user_id=user_id,
            portfolio_name=portfolio_data.portfolio_name,
            cash_balance=portfolio_data.cash_balance,
            total_value=portfolio_data.cash_balance
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio
    
    def update_portfolio(self, db: Session, portfolio: Portfolio, portfolio_data: PortfolioUpdate) -> Portfolio:
        """Update portfolio information"""
        if portfolio_data.portfolio_name:
            portfolio.portfolio_name = portfolio_data.portfolio_name
        if portfolio_data.cash_balance:
            portfolio.cash_balance = portfolio_data.cash_balance
            # Recalculate total value
            total_holdings = sum(
                h.total_value for h in portfolio.holdings
            )
            portfolio.total_value = portfolio.cash_balance + total_holdings
        
        db.commit()
        db.refresh(portfolio)
        return portfolio
    
    def add_holding(self, db: Session, portfolio: Portfolio, symbol: str, quantity: float, price: float) -> PortfolioHolding:
        """Add a holding to portfolio"""
        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            symbol=symbol,
            quantity=quantity,
            average_cost=price,
            current_price=price,
            total_value=quantity * price
        )
        db.add(holding)
        
        # Update portfolio totals
        portfolio.total_invested += quantity * price
        portfolio.total_value = portfolio.cash_balance + portfolio.total_invested
        
        db.commit()
        db.refresh(holding)
        return holding
    
    def calculate_metrics(self, db: Session, portfolio: Portfolio) -> dict:
        """Calculate portfolio performance metrics"""
        total_value = portfolio.total_value
        total_invested = portfolio.total_invested
        
        total_return = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "total_value": total_value,
            "total_invested": total_invested,
            "total_return": total_return,
            "ytd_return": 0,  # Would need more data
            "sharpe_ratio": 0,  # Would need historical volatility
            "max_drawdown": 0  # Would need full historical data
        }
