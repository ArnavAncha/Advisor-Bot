from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    portfolio_name = Column(String(255), default="My Portfolio")
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    total_invested = Column(Float, default=0.0)
    unrealized_gain_loss = Column(Float, default=0.0)
    realized_gain_loss = Column(Float, default=0.0)
    
    # Performance metrics
    ytd_return = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio {self.portfolio_name} - ${self.total_value}>"

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255))
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    unrealized_gain_loss = Column(Float, default=0.0)
    gain_loss_percentage = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    def __repr__(self):
        return f"<PortfolioHolding {self.symbol} - {self.quantity} shares>"
