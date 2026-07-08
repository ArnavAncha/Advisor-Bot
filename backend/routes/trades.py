from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import TradeCreate, TradeUpdate, TradeResponse
from services.auth_service import AuthService
from models import Trade, Portfolio

router = APIRouter()
auth_service = AuthService()

@router.post("/create", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_data: TradeCreate,
    portfolio_id: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trade"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    trade = Trade(
        portfolio_id=portfolio.id,
        symbol=trade_data.symbol,
        action=trade_data.action,
        quantity=trade_data.quantity,
        price=trade_data.price,
        total_value=trade_data.quantity * trade_data.price,
        notes=trade_data.notes,
        status="PENDING"
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

@router.get("/{portfolio_id}", response_model=List[TradeResponse])
async def get_trades(
    portfolio_id: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trades for a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    trades = db.query(Trade).filter(Trade.portfolio_id == portfolio.id).all()
    return trades

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    trade_data: TradeUpdate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a trade status"""
    trade = db.query(Trade).join(Portfolio).filter(
        Trade.id == trade_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    if trade_data.status:
        trade.status = trade_data.status
    if trade_data.execution_price:
        trade.execution_price = trade_data.execution_price
    if trade_data.execution_time:
        trade.execution_time = trade_data.execution_time
    if trade_data.notes:
        trade.notes = trade_data.notes
    
    db.commit()
    db.refresh(trade)
    return trade
