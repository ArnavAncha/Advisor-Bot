from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "Advisor Bot API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/advisor_bot")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    TRADINGVIEW_API_KEY: str = os.getenv("TRADINGVIEW_API_KEY", "")
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    
    # Chase Bank Integration
    CHASE_API_BASE_URL: str = os.getenv("CHASE_API_BASE_URL", "https://api.chase.com")
    CHASE_CLIENT_ID: str = os.getenv("CHASE_CLIENT_ID", "")
    CHASE_CLIENT_SECRET: str = os.getenv("CHASE_CLIENT_SECRET", "")
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5000"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
