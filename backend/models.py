from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


def utcnow():
    """Naive UTC timestamp.

    datetime.utcnow() is deprecated from Python 3.12 and emits a warning on
    every insert. This keeps the existing naive-UTC storage format so rows
    written before and after the change stay directly comparable.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    predictions = relationship("PredictionLog", back_populates="user", cascade="all, delete-orphan")


class PredictionLog(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    churn_probability = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)
    input_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    actual_outcome = Column(String(20), nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="predictions")
