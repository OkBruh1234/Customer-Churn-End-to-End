import os
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parent.parent / "churn_model.pkl"
DEFAULT_MODEL_VERSION = f"{MODEL_PATH.stem}:{datetime.utcfromtimestamp(MODEL_PATH.stat().st_mtime).strftime('%Y%m%d%H%M%S')}"


def model_to_dict(model_instance):
    if hasattr(model_instance, "model_dump"):
        return model_instance.model_dump()
    return model_instance.dict()


@lru_cache(maxsize=1)
def load_model():
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_model_version():
    return os.getenv("MODEL_VERSION", DEFAULT_MODEL_VERSION)


def warm_prediction_resources():
    load_model()
    get_model_version()


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
