import logging
import os
import threading
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd


logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "churn_model.pkl"

# Model load and warm-up run on a background thread at startup so the HTTP port
# binds immediately. Everything that touches the model goes through these.
_model = None
_model_lock = threading.Lock()
_ready_event = threading.Event()
_warm_lock = threading.Lock()
_warm_started_at = time.perf_counter()
_warm_duration_ms = None


def model_to_dict(model_instance):
    if hasattr(model_instance, "model_dump"):
        return model_instance.model_dump()
    return model_instance.dict()


@lru_cache(maxsize=1)
def get_default_model_version():
    """Derive a version label from the model file, tolerating a missing file.

    Computed lazily: doing this at import time meant a missing or unreadable
    churn_model.pkl crashed the whole service on import with an OSError that
    said nothing useful about the real problem.
    """
    try:
        modified_at = datetime.fromtimestamp(MODEL_PATH.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return f"{MODEL_PATH.stem}:unknown"

    return f"{MODEL_PATH.stem}:{modified_at.strftime('%Y%m%d%H%M%S')}"


@lru_cache(maxsize=1)
def get_model_version():
    return os.getenv("MODEL_VERSION", get_default_model_version())


def load_model():
    """Return the cached model, loading it once under a lock.

    Double-checked locking rather than lru_cache: the background warm-up thread
    and an early request can call this concurrently, and lru_cache does not
    prevent the wrapped call from running twice on a cache miss.
    """
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            started_at = time.perf_counter()
            _model = joblib.load(MODEL_PATH)
            logger.info(
                "Loaded churn model in %.0f ms", (time.perf_counter() - started_at) * 1000
            )

    return _model


def is_model_ready():
    return _ready_event.is_set()


def get_warm_duration_ms():
    return _warm_duration_ms


def wait_until_ready(timeout_seconds):
    return _ready_event.wait(timeout_seconds)


def warm_prediction_resources():
    """Load the model and push one throwaway row through the full predict path.

    Loading the pickle alone is not enough. The first predict_proba is what
    actually pays for pandas frame construction, the ColumnTransformer /
    OneHotEncoder code paths and numpy's BLAS init, so the old warm-up left all
    of that on the first real user request.
    """
    global _warm_duration_ms

    with _warm_lock:
        if _ready_event.is_set():
            return

        started_at = time.perf_counter()
        try:
            load_model()
            get_model_version()
            _run_warmup_prediction()
        except Exception:
            logger.exception("Model warm-up failed; first request will load lazily")
            return

        _warm_duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        _ready_event.set()
        logger.info(
            "Model warm-up complete in %.0f ms (%.0f ms after process start)",
            _warm_duration_ms,
            (time.perf_counter() - _warm_started_at) * 1000,
        )


def start_background_warmup():
    """Kick off warm-up without blocking startup, so the port binds right away."""
    thread = threading.Thread(
        target=warm_prediction_resources,
        name="model-warmup",
        daemon=True,
    )
    thread.start()
    return thread


def _run_warmup_prediction():
    warmup_frame = pd.DataFrame(
        {
            "gender": ["Male"],
            "SeniorCitizen": [0],
            "Partner": ["Yes"],
            "Dependents": ["No"],
            "tenure": [12],
            "PhoneService": ["Yes"],
            "MultipleLines": ["No"],
            "InternetService": ["Fiber optic"],
            "OnlineSecurity": ["No"],
            "OnlineBackup": ["No"],
            "DeviceProtection": ["No"],
            "TechSupport": ["No"],
            "StreamingTV": ["No"],
            "StreamingMovies": ["No"],
            "Contract": ["Month-to-month"],
            "PaperlessBilling": ["Yes"],
            "PaymentMethod": ["Electronic check"],
            "MonthlyCharges": [70.0],
            "TotalCharges": [840.0],
            "tenure_bucket": ["0-1 year"],
            "service_count": [0],
            "charges_per_tenure": [70.0 / 13],
        }
    )
    load_model().predict_proba(warmup_frame)


def to_native_value(value):
    if hasattr(value, "item"):
        return value.item()
    return value


def build_feature_frame(customer):
    customer_data = model_to_dict(customer)
    total_charges = customer_data["monthly_charges"] * customer_data["tenure"]

    if customer_data["tenure"] <= 12:
        tenure_bucket = "0-1 year"
    elif customer_data["tenure"] <= 24:
        tenure_bucket = "1-2 years"
    elif customer_data["tenure"] <= 48:
        tenure_bucket = "2-4 years"
    else:
        tenure_bucket = "4+ years"

    services = [
        customer_data["online_security"],
        customer_data["online_backup"],
        customer_data["device_protection"],
        customer_data["tech_support"],
        customer_data["streaming_tv"],
        customer_data["streaming_movies"],
    ]

    service_count = sum(service == "Yes" for service in services)
    charges_per_tenure = customer_data["monthly_charges"] / (customer_data["tenure"] + 1)

    feature_frame = pd.DataFrame(
        {
            "gender": [customer_data["gender"]],
            "SeniorCitizen": [customer_data["senior_citizen"]],
            "Partner": [customer_data["partner"]],
            "Dependents": [customer_data["dependents"]],
            "tenure": [customer_data["tenure"]],
            "PhoneService": [customer_data["phone_service"]],
            "MultipleLines": [customer_data["multiple_lines"]],
            "InternetService": [customer_data["internet_service"]],
            "OnlineSecurity": [customer_data["online_security"]],
            "OnlineBackup": [customer_data["online_backup"]],
            "DeviceProtection": [customer_data["device_protection"]],
            "TechSupport": [customer_data["tech_support"]],
            "StreamingTV": [customer_data["streaming_tv"]],
            "StreamingMovies": [customer_data["streaming_movies"]],
            "Contract": [customer_data["contract"]],
            "PaperlessBilling": [customer_data["paperless_billing"]],
            "PaymentMethod": [customer_data["payment_method"]],
            "MonthlyCharges": [customer_data["monthly_charges"]],
            "TotalCharges": [total_charges],
            "tenure_bucket": [tenure_bucket],
            "service_count": [service_count],
            "charges_per_tenure": [charges_per_tenure],
        }
    )

    return feature_frame


def build_reasons(customer):
    customer_data = model_to_dict(customer)
    reasons = []

    if customer_data["tenure"] < 12:
        reasons.append("Low tenure")
    if customer_data["contract"] == "Month-to-month":
        reasons.append("Flexible contract")
    if customer_data["internet_service"] == "Fiber optic":
        reasons.append("Fiber users churn more")
    if customer_data["tech_support"] == "No":
        reasons.append("No tech support")
    if customer_data["monthly_charges"] > 80:
        reasons.append("High monthly charges")

    return reasons


def get_predicted_outcome(churn_probability):
    if churn_probability >= 0.5:
        return "Churned"
    return "Retained"


def get_comparison_status(churn_probability, actual_outcome):
    if actual_outcome is None:
        return None

    if get_predicted_outcome(churn_probability) == actual_outcome:
        return "Matched"
    return "Mismatched"


def predict_churn(customer):
    started_at = time.perf_counter()
    model = load_model()
    input_df = build_feature_frame(customer)
    probability = float(model.predict_proba(input_df)[0][1])
    confidence = abs(probability - 0.5) * 2

    if probability < 0.30:
        risk_level = "Low Risk"
    elif probability < 0.60:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    input_summary = {
        key: to_native_value(value) for key, value in input_df.iloc[0].to_dict().items()
    }

    return {
        "churn_probability": probability,
        "confidence": confidence,
        "risk_level": risk_level,
        "reasons": build_reasons(customer),
        "input_summary": input_summary,
        "model_version": get_model_version(),
        "processing_time_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "predicted_outcome": get_predicted_outcome(probability),
    }
