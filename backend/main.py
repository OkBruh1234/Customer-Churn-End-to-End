import json
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend.identifiers import (
    format_prediction_id,
    format_user_id,
    parse_prediction_id,
    parse_user_id,
)
from backend.models import PredictionLog, User
from backend.prediction_service import (
    get_comparison_status,
    get_model_version,
    get_predicted_outcome,
    model_to_dict,
    predict_churn,
    warm_prediction_resources,
)
from backend.schemas import (
    AdminSummaryResponse,
    AdminUserSummaryItem,
    AdminUsersResponse,
    HealthResponse,
    PredictionHistoryItem,
    PredictionHistoryResponse,
    PredictionOutcomeUpdateRequest,
    PredictionRequest,
    PredictionResponse,
    UserCreateRequest,
    UserCreateResponse,
)
from backend.validation import validate_user_name

app = FastAPI(title="Customer Churn Backend", version="1.0.0")


@app.on_event("startup")
def startup_event():
    init_db()
    warm_prediction_resources()


@app.get("/")
def root():
    return {
        "message": "Customer Churn Backend is running.",
        "health": "/health",
        "docs": "/docs",
        "model_version": get_model_version(),
    }


def build_prediction_history_item(prediction_log):
    payload = {}
    if prediction_log.input_payload:
        try:
            payload = json.loads(prediction_log.input_payload)
        except json.JSONDecodeError:
            payload = {}

    result_payload = payload.get("result", {})
    predicted_outcome = get_predicted_outcome(prediction_log.churn_probability)

    return PredictionHistoryItem(
        prediction_id=format_prediction_id(prediction_log.id),
        created_at=prediction_log.created_at,
        churn_probability=prediction_log.churn_probability,
        confidence=float(result_payload.get("confidence", 0.0)),
        risk_level=prediction_log.risk_level,
        reasons=result_payload.get("reasons", []),
        model_version=result_payload.get("model_version", get_model_version()),
        processing_time_ms=float(result_payload.get("processing_time_ms", 0.0)),
        predicted_outcome=predicted_outcome,
        actual_outcome=prediction_log.actual_outcome,
        comparison_status=get_comparison_status(
            prediction_log.churn_probability,
            prediction_log.actual_outcome,
        ),
        outcome_recorded_at=prediction_log.outcome_recorded_at,
    )


def build_admin_summary(db: Session):
    total_users = int(db.query(func.count(User.id)).scalar() or 0)
    total_predictions = int(db.query(func.count(PredictionLog.id)).scalar() or 0)
    avg_churn_probability = float(
        db.query(func.avg(PredictionLog.churn_probability)).scalar() or 0.0
    )

    predictions_with_outcomes = (
        db.query(PredictionLog)
        .filter(PredictionLog.actual_outcome.is_not(None))
        .all()
    )

    outcomes_recorded = len(predictions_with_outcomes)
    matched_predictions = sum(
        get_comparison_status(prediction.churn_probability, prediction.actual_outcome) == "Matched"
        for prediction in predictions_with_outcomes
    )

    prediction_accuracy = None
    if outcomes_recorded:
        prediction_accuracy = round((matched_predictions / outcomes_recorded) * 100, 2)

    return AdminSummaryResponse(
        total_users=total_users,
        total_predictions=total_predictions,
        avg_churn_probability=avg_churn_probability,
        outcomes_recorded=outcomes_recorded,
        matched_predictions=matched_predictions,
        prediction_accuracy=prediction_accuracy,
    )


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", model_version=get_model_version())


@app.post("/users/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    try:
        cleaned_name = validate_user_name(payload.name)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    user = User(name=cleaned_name)
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserCreateResponse(
        user_id=format_user_id(user.id),
        name=user.name,
        created_at=user.created_at,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    try:
        internal_user_id = parse_user_id(request.user_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    user = db.get(User, internal_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    prediction_result = predict_churn(request.customer)

    prediction_log = PredictionLog(
        user_id=user.id,
        churn_probability=prediction_result["churn_probability"],
        risk_level=prediction_result["risk_level"],
        input_payload=json.dumps(
            {
                "user_id": format_user_id(user.id),
                "customer": model_to_dict(request.customer),
                "result": prediction_result,
            }
        ),
    )

    db.add(prediction_log)
    db.commit()
    db.refresh(prediction_log)

    return PredictionResponse(
        user_id=format_user_id(user.id),
        prediction_id=format_prediction_id(prediction_log.id),
        churn_probability=prediction_result["churn_probability"],
        confidence=prediction_result["confidence"],
        risk_level=prediction_result["risk_level"],
        reasons=prediction_result["reasons"],
        input_summary=prediction_result["input_summary"],
        model_version=prediction_result["model_version"],
        processing_time_ms=prediction_result["processing_time_ms"],
        created_at=prediction_log.created_at,
        predicted_outcome=prediction_result["predicted_outcome"],
        actual_outcome=prediction_log.actual_outcome,
        comparison_status=get_comparison_status(
            prediction_log.churn_probability,
            prediction_log.actual_outcome,
        ),
        outcome_recorded_at=prediction_log.outcome_recorded_at,
    )


@app.get("/users/{user_id}/predictions", response_model=PredictionHistoryResponse)
def get_prediction_history(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        internal_user_id = parse_user_id(user_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    user = db.get(User, internal_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    prediction_logs = (
        db.query(PredictionLog)
        .filter(PredictionLog.user_id == user.id)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
        .all()
    )

    total_predictions = (
        db.query(func.count(PredictionLog.id))
        .filter(PredictionLog.user_id == user.id)
        .scalar()
    )

    return PredictionHistoryResponse(
        user_id=format_user_id(user.id),
        name=user.name,
        total_predictions=int(total_predictions or 0),
        predictions=[build_prediction_history_item(log) for log in prediction_logs],
    )


@app.patch("/predictions/{prediction_id}/outcome", response_model=PredictionHistoryItem)
def update_prediction_outcome(
    prediction_id: str,
    payload: PredictionOutcomeUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        internal_prediction_id = parse_prediction_id(prediction_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    prediction_log = db.get(PredictionLog, internal_prediction_id)
    if prediction_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found.")

    prediction_log.actual_outcome = payload.actual_outcome
    prediction_log.outcome_recorded_at = datetime.utcnow()

    db.commit()
    db.refresh(prediction_log)

    return build_prediction_history_item(prediction_log)


@app.get("/admin/summary", response_model=AdminSummaryResponse)
def get_admin_summary(db: Session = Depends(get_db)):
    return build_admin_summary(db)


@app.get("/admin/users", response_model=AdminUsersResponse)
def get_admin_users(db: Session = Depends(get_db)):
    user_rows = (
        db.query(
            User.id.label("id"),
            User.name.label("name"),
            User.created_at.label("created_at"),
            func.count(PredictionLog.id).label("total_predictions"),
            func.avg(PredictionLog.churn_probability).label("avg_churn_probability"),
            func.max(PredictionLog.created_at).label("last_prediction_at"),
        )
        .outerjoin(PredictionLog, PredictionLog.user_id == User.id)
        .group_by(User.id, User.name, User.created_at)
        .order_by(func.count(PredictionLog.id).desc(), User.created_at.desc())
        .all()
    )

    return AdminUsersResponse(
        users=[
            AdminUserSummaryItem(
                user_id=format_user_id(row.id),
                name=row.name,
                created_at=row.created_at,
                total_predictions=int(row.total_predictions or 0),
                avg_churn_probability=float(row.avg_churn_probability or 0.0),
                last_prediction_at=row.last_prediction_at,
            )
            for row in user_rows
        ]
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
