from fastapi import APIRouter
from .auth import router as auth_router
from .portfolio import router as portfolio_router
from .trades import router as trades_router
from .predictions import router as predictions_router

router = APIRouter()

router.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
router.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
router.include_router(trades_router, prefix="/api/trades", tags=["trades"])
router.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])

__all__ = ["router"]
