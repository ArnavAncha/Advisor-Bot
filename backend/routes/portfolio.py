from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from services.auth_service import AuthService
from services.portfolio_service import PortfolioService
from models import Portfolio

router = APIRouter()
auth_service = AuthService()
portfolio_service = PortfolioService()

@router.post("/create", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new portfolio for the user"""
    portfolio = portfolio_service.create_portfolio(db, current_user.id, portfolio_data)
    return portfolio

@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all portfolios for the current user"""
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == current_user.id
    ).all()
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_data: PortfolioUpdate,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    portfolio = portfolio_service.update_portfolio(db, portfolio, portfolio_data)
    return portfolio
