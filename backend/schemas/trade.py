from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class TradeCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    action: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    notes: Optional[str] = None

class TradeUpdate(BaseModel):
    status: Optional[str] = None
    execution_price: Optional[float] = None
    execution_time: Optional[datetime] = None
    notes: Optional[str] = None

class TradeResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    symbol: str
    action: str
    quantity: float
    price: float
    total_value: float
    model_prediction: Optional[str]
    confidence_score: float
    status: str
    execution_price: Optional[float]
    execution_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
