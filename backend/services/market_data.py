import aiohttp
import asyncio
from typing import Dict, Optional
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MarketDataService:
    def __init__(self):
        self.alpha_vantage_url = "https://www.alphavantage.co/query"
        self.polygon_url = "https://api.polygon.io"
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.polygon_key = settings.POLYGON_API_KEY
    
    async def get_stock_quote(self, symbol: str) -> Dict:
        """Fetch current stock quote"""
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.alpha_vantage_url, params=params) as response:
                    data = await response.json()
                    quote = data.get("Global Quote", {})
                    return {
                        "symbol": symbol,
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent", "0%"),
                        "volume": quote.get("06. volume", 0)
                    }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, interval: str = "daily") -> Dict:
        """Fetch historical stock data for technical analysis"""
        try:
            function = "TIME_SERIES_DAILY" if interval == "daily" else "TIME_SERIES_INTRADAY"
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.alpha_vantage_url, params=params) as response:
                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_technical_indicators(self, symbol: str) -> Dict:
        """Calculate technical indicators (RSI, MACD, Bollinger Bands)"""
        # This would integrate with technical analysis libraries
        # like TA-Lib or pandas_ta
        return {
            "rsi": 65.5,
            "macd": 0.45,
            "macd_signal": 0.38,
            "bollinger_upper": 150.2,
            "bollinger_lower": 145.8,
            "bollinger_middle": 148.0
        }
