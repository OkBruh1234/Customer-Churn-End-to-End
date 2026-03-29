from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

from backend.validation import MAX_USER_NAME_LENGTH


class HealthResponse(BaseModel):
    status: str
    model_version: str


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=MAX_USER_NAME_LENGTH)


class UserCreateResponse(BaseModel):
    user_id: str
    name: str
    created_at: datetime


class CustomerFeatures(BaseModel):
    gender: Literal["Male", "Female"]
    senior_citizen: Literal[0, 1]
    partner: Literal["Yes", "No"]
    dependents: Literal["Yes", "No"]
    phone_service: Literal["Yes", "No"]
    multiple_lines: Literal["Yes", "No", "No phone service"]
    internet_service: Literal["DSL", "Fiber optic", "No"]
    online_security: Literal["Yes", "No", "No internet service"]
    online_backup: Literal["Yes", "No", "No internet service"]
    device_protection: Literal["Yes", "No", "No internet service"]
    tech_support: Literal["Yes", "No", "No internet service"]
    streaming_tv: Literal["Yes", "No", "No internet service"]
    streaming_movies: Literal["Yes", "No", "No internet service"]
    contract: Literal["Month-to-month", "One year", "Two year"]
    paperless_billing: Literal["Yes", "No"]
    payment_method: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ]
    monthly_charges: float = Field(..., ge=0, le=200)
    tenure: int = Field(..., ge=0, le=72)


class PredictionRequest(BaseModel):
    user_id: str
    customer: CustomerFeatures


class PredictionResponse(BaseModel):
    user_id: str
    prediction_id: str
    churn_probability: float
    confidence: float
    risk_level: str
    reasons: List[str]
    input_summary: Dict[str, Any]
    model_version: str
    processing_time_ms: float
    created_at: datetime
    predicted_outcome: str
    actual_outcome: str | None = None
    comparison_status: str | None = None
    outcome_recorded_at: datetime | None = None


class PredictionHistoryItem(BaseModel):
    prediction_id: str
    created_at: datetime
    churn_probability: float
    confidence: float
    risk_level: str
    reasons: List[str]
    model_version: str
    processing_time_ms: float
    predicted_outcome: str
    actual_outcome: str | None = None
    comparison_status: str | None = None
    outcome_recorded_at: datetime | None = None


class PredictionHistoryResponse(BaseModel):
    user_id: str
    name: str
    total_predictions: int
    predictions: List[PredictionHistoryItem]


class PredictionOutcomeUpdateRequest(BaseModel):
    actual_outcome: Literal["Churned", "Retained"]


class AdminSummaryResponse(BaseModel):
    total_users: int
    total_predictions: int
    avg_churn_probability: float
    outcomes_recorded: int
    matched_predictions: int
    prediction_accuracy: float | None


class AdminUserSummaryItem(BaseModel):
    user_id: str
    name: str
    created_at: datetime
    total_predictions: int
    avg_churn_probability: float
    last_prediction_at: datetime | None = None


class AdminUsersResponse(BaseModel):
    users: List[AdminUserSummaryItem]
