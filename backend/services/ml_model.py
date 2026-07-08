import numpy as np
from typing import Dict, Optional
import asyncio
import logging
from .market_data import MarketDataService

logger = logging.getLogger(__name__)

class MLModelService:
    def __init__(self):
        self.market_data_service = MarketDataService()
        self.model = None  # Load pretrained LSTM model here
        self.scaler = None  # Load fitted scaler for normalization
    
    async def predict(self, symbol: str, lookback_days: int = 30) -> Dict:
        """
        Make prediction for a stock symbol using LSTM model
        Returns: {symbol, prediction (BUY/SELL/HOLD), confidence, technical_indicators, recommendation}
        """
        try:
            # Fetch market data
            historical_data = await self.market_data_service.get_historical_data(symbol)
            technical_indicators = await self.market_data_service.get_technical_indicators(symbol)
            
            # Prepare features for model
            features = self._prepare_features(historical_data, technical_indicators)
            
            # Get model prediction (mock for now)
            prediction_result = self._get_model_prediction(features)
            
            return {
                "symbol": symbol,
                "prediction": prediction_result["prediction"],
                "confidence": prediction_result["confidence"],
                "technical_indicators": technical_indicators,
                "recommendation": prediction_result["recommendation"]
            }
        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            raise
    
    async def get_real_time_data(self, symbol: str) -> Dict:
        """Stream real-time market data via WebSocket"""
        quote = await self.market_data_service.get_stock_quote(symbol)
        indicators = await self.market_data_service.get_technical_indicators(symbol)
        
        return {
            "symbol": symbol,
            "timestamp": str(np.datetime64('now')),
            "quote": quote,
            "indicators": indicators
        }
    
    def _prepare_features(self, historical_data: Dict, indicators: Dict) -> np.ndarray:
        """Prepare feature vector for model prediction"""
        # Extract relevant features and normalize
        features = np.array([
            indicators.get("rsi", 50) / 100,
            indicators.get("macd", 0),
            indicators.get("macd_signal", 0),
        ])
        return features
    
    def _get_model_prediction(self, features: np.ndarray) -> Dict:
        """Get prediction from trained model"""
        # Mock prediction logic - replace with actual model inference
        confidence = np.random.random()
        prediction = "BUY" if confidence > 0.6 else "HOLD"
        
        recommendation = f"Model suggests {prediction} with {confidence*100:.1f}% confidence"
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "recommendation": recommendation
        }
