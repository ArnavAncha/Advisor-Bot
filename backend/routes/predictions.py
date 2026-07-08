from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import AuthService
from services.ml_model import MLModelService
from pydantic import BaseModel

router = APIRouter()
auth_service = AuthService()
ml_service = MLModelService()

class PredictionRequest(BaseModel):
    symbol: str
    lookback_days: int = 30

class PredictionResponse(BaseModel):
    symbol: str
    prediction: str  # BUY, SELL, HOLD
    confidence: float
    technical_indicators: dict
    recommendation: str

@router.post("/predict", response_model=PredictionResponse)
async def get_prediction(
    request: PredictionRequest,
    current_user = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI prediction for a stock symbol"""
    try:
        prediction = await ml_service.predict(request.symbol, request.lookback_days)
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

@router.websocket("/ws/{symbol}")
async def websocket_predictions(websocket: WebSocket, symbol: str):
    """WebSocket for real-time stock predictions and market data"""
    await websocket.accept()
    try:
        while True:
            # Simulate real-time data stream
            data = await ml_service.get_real_time_data(symbol)
            await websocket.send_json(data)
    except Exception as e:
        await websocket.close(code=status.WS_1011_SERVER_ERROR)
