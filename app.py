import pandas as pd
import requests
import streamlit as st

from backend.validation import validate_user_name
from runtime_config import get_api_base_url_config, get_api_base_url_issue
from ui_theme import apply_theme, render_page_header, render_sidebar_block, render_soft_panel


API_BASE_URL, API_BASE_URL_SOURCE = get_api_base_url_config()
API_BASE_URL_ISSUE = get_api_base_url_issue(API_BASE_URL)
BACKEND_TIMEOUT_SECONDS = 75
USER_SESSION_KEY = "registered_user"
LAST_PREDICTION_SESSION_KEY = "last_prediction"
PREDICTION_HISTORY_LIMIT = 10


@st.cache_resource
def get_http_session():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def build_error_message(error):
    if API_BASE_URL_ISSUE:
        return API_BASE_URL_ISSUE

    default_message = (
        f"Could not reach the backend at {API_BASE_URL}. "
        "Make sure your public FastAPI URL is set in API_BASE_URL. "
        "If you are using Render free tier, the first wake-up can take a little longer."
    )
    response = getattr(error, "response", None)
    if response is None:
        return default_message

    try:
        payload = response.json()
    except ValueError:
        return default_message

    detail = payload.get("detail")
    if detail:
        return f"Backend error: {detail}"

    return default_message


def request_json(method, path, payload=None):
    request_kwargs = {
        "method": method,
        "url": f"{API_BASE_URL}{path}",
        "timeout": BACKEND_TIMEOUT_SECONDS,
    }
    if payload is not None:
        request_kwargs["json"] = payload

    response = get_http_session().request(**request_kwargs)
    response.raise_for_status()
    return response.json()


def get_json(path):
    return request_json("GET", path)


def post_json(path, payload):
    return request_json("POST", path, payload=payload)


def reset_user_session():
    st.session_state.pop(USER_SESSION_KEY, None)
    st.session_state.pop(LAST_PREDICTION_SESSION_KEY, None)


def build_updated_history(history_data, prediction_result, user_name):
    new_history_item = {
        "prediction_id": prediction_result["prediction_id"],
        "created_at": prediction_result["created_at"],
        "churn_probability": prediction_result["churn_probability"],
        "confidence": prediction_result["confidence"],
        "risk_level": prediction_result["risk_level"],
        "reasons": prediction_result["reasons"],
        "model_version": prediction_result["model_version"],
        "processing_time_ms": prediction_result["processing_time_ms"],
        "predicted_outcome": prediction_result["predicted_outcome"],
        "actual_outcome": prediction_result.get("actual_outcome"),
        "comparison_status": prediction_result.get("comparison_status"),
        "outcome_recorded_at": prediction_result.get("outcome_recorded_at"),
    }

    if not history_data:
        return {
            "user_id": prediction_result["user_id"],
            "name": user_name,
            "total_predictions": 1,
            "predictions": [new_history_item],
        }

    existing_predictions = history_data.get("predictions", [])
    updated_predictions = [new_history_item] + existing_predictions

    return {
        "user_id": history_data["user_id"],
        "name": history_data["name"],
        "total_predictions": history_data.get("total_predictions", 0) + 1,
        "predictions": updated_predictions[:PREDICTION_HISTORY_LIMIT],
    }


def render_prediction_result(prediction_result):
    probability = prediction_result["churn_probability"]
    confidence = prediction_result["confidence"]
    reasons = prediction_result["reasons"]
    input_df = pd.DataFrame([prediction_result["input_summary"]])

    st.subheader("Latest Prediction")

    metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
    metric_col_1.metric("Churn Probability", f"{probability:.2%}")
    metric_col_2.metric("Confidence", f"{confidence:.2f}")
    metric_col_3.metric("Risk Level", prediction_result["risk_level"])
    metric_col_4.metric("Latency", f"{prediction_result['processing_time_ms']:.0f} ms")

    st.progress(probability)
    st.caption(
        f"Prediction ID: {prediction_result['prediction_id']} | "
        f"User ID: {prediction_result['user_id']} | "
        f"Model Version: {prediction_result['model_version']}"
    )
    st.write(f"Predicted outcome: **{prediction_result['predicted_outcome']}**")

    if prediction_result["risk_level"] == "Low Risk":
        st.success("Low Risk")
    elif prediction_result["risk_level"] == "Medium Risk":
        st.warning("Medium Risk")
    else:
        st.error("High Risk")
        st.write("Recommend a retention strategy such as discounting or proactive engagement.")

    st.write("### Why this prediction?")
    if reasons:
        for reason in reasons:
            st.write(f"- {reason}")
    else:
        st.write("No strong churn signals")

    with st.expander("Prediction Input Snapshot", expanded=False):
        st.dataframe(input_df, use_container_width=True)


def render_prediction_history(history_data):
    st.subheader("Prediction History")

    predictions = history_data.get("predictions", [])
    if not predictions:
        st.info("No predictions stored for this user yet.")
        return

    history_rows = []
    for item in predictions:
        history_rows.append(
            {
                "Prediction ID": item["prediction_id"],
                "Created At": pd.to_datetime(item["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "Risk Level": item["risk_level"],
                "Churn Probability": f"{item['churn_probability']:.2%}",
                "Confidence": f"{item['confidence']:.2f}",
                "Latency (ms)": round(item["processing_time_ms"], 2),
                "Model Version": item["model_version"],
                "Predicted Outcome": item["predicted_outcome"],
                "Actual Outcome": item["actual_outcome"] or "Not recorded",
                "Comparison": item["comparison_status"] or "Pending",
                "Reasons": ", ".join(item["reasons"]) if item["reasons"] else "No strong churn signals",
            }
        )

    history_df = pd.DataFrame(history_rows)
    st.dataframe(history_df, use_container_width=True, hide_index=True)


def render_registration_rules():
    st.markdown(
        """
        <div class="tiny-note">
            Name rules: start with a capital letter, use letters only with spaces, apostrophes, or hyphens,
            avoid numbers, and keep single-word names reasonably short.
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Customer Churn Prediction System", layout="wide")
apply_theme()
render_page_header(
    title="Customer Churn Prediction System",
    subtitle=(
        "Register a customer-facing session, route predictions through FastAPI, "
        "and keep a clean history of churn decisions in one place."
    ),
    kicker="Prediction Workspace",
)

registered_user = st.session_state.get(USER_SESSION_KEY)
last_prediction = st.session_state.get(LAST_PREDICTION_SESSION_KEY)
history_data = None
history_error = None

if registered_user:
    try:
        history_data = get_json(
            f"/users/{registered_user['user_id']}/predictions?limit={PREDICTION_HISTORY_LIMIT}"
        )
    except requests.RequestException as error:
        history_error = build_error_message(error)

with st.sidebar:
    sidebar_rows = [
        ("API Base URL", API_BASE_URL),
        ("Config Source", API_BASE_URL_SOURCE),
    ]
    if registered_user:
        sidebar_rows.extend(
            [
                ("Registered User", registered_user["name"]),
                ("User ID", registered_user["user_id"]),
            ]
        )
        if history_data and history_data.get("predictions"):
            sidebar_rows.extend(
                [
                    ("Stored Predictions", history_data["total_predictions"]),
                    ("Active Model", history_data["predictions"][0]["model_version"]),
                ]
            )
    render_sidebar_block(
        "Backend Session",
        sidebar_rows,
        note=(
            "Switch user any time to start a fresh session."
            if registered_user
            else "Register a user first to unlock the prediction workflow."
        ),
    )
    if API_BASE_URL_ISSUE:
        st.warning(API_BASE_URL_ISSUE)
    if registered_user:
        if st.button("Switch User"):
            reset_user_session()
            st.rerun()

if not registered_user:
    register_col, info_col = st.columns([1.25, 0.85])

    with register_col:
        st.subheader("Step 1: Register User")
        with st.form("register_user_form", clear_on_submit=False):
            user_name = st.text_input(
                "Enter your name",
                placeholder="Example: Rahul Sharma",
                help="Use a proper name format, for example Rahul Sharma or Maria Jones.",
            )
            register_submitted = st.form_submit_button("Continue")

        render_registration_rules()

        if register_submitted:
            try:
                cleaned_name = validate_user_name(user_name)
            except ValueError as error:
                st.error(str(error))
            else:
                try:
                    user_data = post_json("/users/register", {"name": cleaned_name})
                except requests.RequestException as error:
                    st.error(build_error_message(error))
                else:
                    st.session_state[USER_SESSION_KEY] = user_data
                    st.session_state.pop(LAST_PREDICTION_SESSION_KEY, None)
                    st.success(
                        f"Registration successful for {user_data['name']}. "
                        f"Assigned user ID: {user_data['user_id']}"
                    )
                    st.rerun()

    with info_col:
        render_soft_panel(
            "Why register first?",
            "Each prediction is linked to a real user session so the backend can track history, model version, and later actual outcomes.",
        )
        render_soft_panel(
            "Fast flow",
            "Once registration succeeds, the prediction form unlocks immediately and all future requests reuse the same session.",
        )
        render_soft_panel(
            "Admin ready",
            "The admin dashboard can later review who predicted what, when they did it, and whether the model matched reality.",
        )

    st.stop()

overview_col_1, overview_col_2, overview_col_3, overview_col_4 = st.columns(4)
overview_col_1.metric("User ID", registered_user["user_id"])
overview_col_2.metric(
    "Predictions Stored",
    history_data["total_predictions"] if history_data else 0,
)
overview_col_3.metric(
    "Latest Latency",
    (
        f"{history_data['predictions'][0]['processing_time_ms']:.0f} ms"
        if history_data and history_data.get("predictions")
        else "N/A"
    ),
)
overview_col_4.metric(
    "Current Model",
    history_data["predictions"][0]["model_version"].split(":")[0]
    if history_data and history_data.get("predictions")
    else "Pending",
)

st.write(f"Welcome back, **{registered_user['name']}**.")
if history_error:
    st.warning(history_error)
elif history_data and history_data.get("predictions"):
    st.caption(f"Current model version: {history_data['predictions'][0]['model_version']}")
else:
    st.caption("Current model version will appear after the first prediction is stored.")

form_col, context_col = st.columns([1.45, 0.85])

with form_col:
    st.subheader("Step 2: Customer Details")

    gender = st.selectbox("Gender", ["Male", "Female"], key="gender")
    senior = st.selectbox("Senior Citizen", [0, 1], key="senior")
    partner = st.selectbox("Partner", ["Yes", "No"], key="partner")
    dependents = st.selectbox("Dependents", ["Yes", "No"], key="dependents")

    phone = st.selectbox("Phone Service", ["Yes", "No"], key="phone")
    if phone == "No":
        multiple_lines = "No phone service"
        st.info("No phone service selected, so Multiple Lines is auto-set.")
    else:
        multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No"], key="multiple_lines")

    internet = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"], key="internet")
    if internet == "No":
        st.info("No internet selected, so all dependent internet services are auto-set.")
        online_security = "No internet service"
        online_backup = "No internet service"
        device_protection = "No internet service"
        tech_support = "No internet service"
        streaming_tv = "No internet service"
        streaming_movies = "No internet service"
    else:
        online_security = st.selectbox("Online Security", ["Yes", "No"], key="online_security")
        online_backup = st.selectbox("Online Backup", ["Yes", "No"], key="online_backup")
        device_protection = st.selectbox("Device Protection", ["Yes", "No"], key="device_protection")
        tech_support = st.selectbox("Tech Support", ["Yes", "No"], key="tech_support")
        streaming_tv = st.selectbox("Streaming TV", ["Yes", "No"], key="streaming_tv")
        streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No"], key="streaming_movies")

    contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"], key="contract")
    paperless = st.selectbox("Paperless Billing", ["Yes", "No"], key="paperless")
    payment = st.selectbox(
        "Payment Method",
        [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        ],
        key="payment",
    )
    monthly = st.number_input(
        "Monthly Charges",
        min_value=0.0,
        max_value=200.0,
        value=70.0,
        key="monthly",
    )
    tenure = st.slider("Tenure (months)", min_value=0, max_value=72, value=12, key="tenure")

    prediction_payload = {
        "user_id": registered_user["user_id"],
        "customer": {
            "gender": gender,
            "senior_citizen": senior,
            "partner": partner,
            "dependents": dependents,
            "phone_service": phone,
            "multiple_lines": multiple_lines,
            "internet_service": internet,
            "online_security": online_security,
            "online_backup": online_backup,
            "device_protection": device_protection,
            "tech_support": tech_support,
            "streaming_tv": streaming_tv,
            "streaming_movies": streaming_movies,
            "contract": contract,
            "paperless_billing": paperless,
            "payment_method": payment,
            "monthly_charges": monthly,
            "tenure": tenure,
        },
    }

    if st.button("Predict Churn", type="primary"):
        with st.spinner("Running churn prediction..."):
            try:
                prediction_result = post_json("/predict", prediction_payload)
            except requests.RequestException as error:
                st.error(build_error_message(error))
            else:
                st.session_state[LAST_PREDICTION_SESSION_KEY] = prediction_result
                last_prediction = prediction_result
                history_data = build_updated_history(
                    history_data=history_data,
                    prediction_result=prediction_result,
                    user_name=registered_user["name"],
                )

with context_col:
    render_soft_panel(
        "Current Session",
        f"User {registered_user['user_id']} is active. Every prediction is logged and can later be reviewed in the admin dashboard.",
    )
    render_soft_panel(
        "Latency Tip",
        "The backend preloads the model on startup, so later predictions should feel faster than the very first call after a restart.",
    )
    render_soft_panel(
        "What gets tracked",
        "Probability, risk level, model version, latency, predicted outcome, and later the actual retention result for comparison.",
    )

result_tab, history_tab = st.tabs(["Latest Prediction", "Prediction History"])

with result_tab:
    if last_prediction:
        render_prediction_result(last_prediction)
    else:
        st.info("Run a churn prediction to see the latest result here.")

with history_tab:
    if history_data:
        render_prediction_history(history_data)
    else:
        st.info("Prediction history will appear after the first stored result.")
