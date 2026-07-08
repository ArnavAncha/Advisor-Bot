from sqlalchemy import Column, String, DateTime, Boolean, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base
import enum

class RiskProfile(str, enum.Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    GROWTH = "Growth"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    # Risk Profile
    risk_profile = Column(String(50), default="Balanced")
    risk_score = Column(Float, default=50.0)  # 0-100 scale
    
    # Chase Bank Integration
    chase_customer_id = Column(String(255), unique=True, nullable=True)
    chase_access_token = Column(String(500), nullable=True)
    is_chase_linked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"
