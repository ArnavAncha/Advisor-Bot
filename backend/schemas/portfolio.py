from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class PortfolioHoldingResponse(BaseModel):
    id: UUID
    symbol: str
    company_name: str
    quantity: float
    average_cost: float
    current_price: float
    total_value: float
    unrealized_gain_loss: float
    gain_loss_percentage: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioCreate(BaseModel):
    portfolio_name: str = Field(default="My Portfolio")
    cash_balance: float = Field(..., gt=0)

class PortfolioUpdate(BaseModel):
    portfolio_name: Optional[str] = None
    cash_balance: Optional[float] = None

class PortfolioResponse(BaseModel):
    id: UUID
    user_id: UUID
    portfolio_name: str
    total_value: float
    cash_balance: float
    total_invested: float
    unrealized_gain_loss: float
    realized_gain_loss: float
    ytd_return: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    holdings: List[PortfolioHoldingResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
