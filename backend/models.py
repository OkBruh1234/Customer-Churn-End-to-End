from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    predictions = relationship("PredictionLog", back_populates="user", cascade="all, delete-orphan")


class PredictionLog(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    churn_probability = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)
    input_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    actual_outcome = Column(String(20), nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="predictions")
