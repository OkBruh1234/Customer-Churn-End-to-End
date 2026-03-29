import os

import pandas as pd
import requests
import streamlit as st

from ui_theme import apply_theme, render_page_header, render_sidebar_block, render_soft_panel


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USER_HISTORY_LIMIT = 50
ADMIN_SUMMARY_KEY = "admin_summary_cache"
ADMIN_USERS_KEY = "admin_users_cache"
ADMIN_HISTORY_KEY = "admin_history_cache"
ADMIN_MESSAGE_KEY = "admin_feedback_message"


@st.cache_resource
def get_http_session():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def build_error_message(error):
    default_message = (
        "Could not reach the backend. Start FastAPI with "
        "uvicorn backend.main:app --reload and try again."
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
        "timeout": 30,
    }
    if payload is not None:
        request_kwargs["json"] = payload

    response = get_http_session().request(**request_kwargs)
    response.raise_for_status()
    return response.json()


def get_json(path):
    return request_json("GET", path)


def patch_json(path, payload):
    return request_json("PATCH", path, payload=payload)


def invalidate_admin_cache():
    st.session_state.pop(ADMIN_SUMMARY_KEY, None)
    st.session_state.pop(ADMIN_USERS_KEY, None)
    st.session_state.pop(ADMIN_HISTORY_KEY, None)


def get_admin_summary(force_refresh=False):
    if force_refresh or ADMIN_SUMMARY_KEY not in st.session_state:
        st.session_state[ADMIN_SUMMARY_KEY] = get_json("/admin/summary")
    return st.session_state[ADMIN_SUMMARY_KEY]


def get_admin_users(force_refresh=False):
    if force_refresh or ADMIN_USERS_KEY not in st.session_state:
        st.session_state[ADMIN_USERS_KEY] = get_json("/admin/users")
    return st.session_state[ADMIN_USERS_KEY]


def get_user_history(user_id, force_refresh=False):
    history_cache = st.session_state.setdefault(ADMIN_HISTORY_KEY, {})
    if force_refresh or user_id not in history_cache:
        history_cache[user_id] = get_json(f"/users/{user_id}/predictions?limit={USER_HISTORY_LIMIT}")
    return history_cache[user_id]


def replace_history_item(history_data, updated_item):
    updated_predictions = []
    for item in history_data.get("predictions", []):
        if item["prediction_id"] == updated_item["prediction_id"]:
            updated_predictions.append(updated_item)
        else:
            updated_predictions.append(item)

    return {
        **history_data,
        "predictions": updated_predictions,
    }


def update_summary_cache(previous_item, updated_item):
    summary_data = st.session_state.get(ADMIN_SUMMARY_KEY)
    if not summary_data:
        return

    previous_recorded = previous_item.get("actual_outcome") is not None
    updated_recorded = updated_item.get("actual_outcome") is not None
    previous_matched = previous_item.get("comparison_status") == "Matched"
    updated_matched = updated_item.get("comparison_status") == "Matched"

    outcomes_recorded = summary_data["outcomes_recorded"]
    matched_predictions = summary_data["matched_predictions"]

    if not previous_recorded and updated_recorded:
        outcomes_recorded += 1
    if previous_recorded and not updated_recorded:
        outcomes_recorded -= 1

    if previous_matched and not updated_matched:
        matched_predictions -= 1
    elif not previous_matched and updated_matched:
        matched_predictions += 1

    prediction_accuracy = None
    if outcomes_recorded > 0:
        prediction_accuracy = round((matched_predictions / outcomes_recorded) * 100, 2)

    summary_data["outcomes_recorded"] = outcomes_recorded
    summary_data["matched_predictions"] = matched_predictions
    summary_data["prediction_accuracy"] = prediction_accuracy


def render_user_table(users):
    if not users:
        st.info("No users registered yet.")
        return

    user_rows = []
    for user in users:
        user_rows.append(
            {
                "User ID": user["user_id"],
                "Name": user["name"],
                "Created At": pd.to_datetime(user["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "Predictions": user["total_predictions"],
                "Avg Churn Probability": f"{user['avg_churn_probability']:.2%}",
                "Last Prediction": (
                    pd.to_datetime(user["last_prediction_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    if user["last_prediction_at"]
                    else "No predictions yet"
                ),
            }
        )

    st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)


def render_user_history(history_data):
    predictions = history_data.get("predictions", [])
    if not predictions:
        st.info("This user has no predictions yet.")
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
                "Outcome Recorded At": (
                    pd.to_datetime(item["outcome_recorded_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    if item["outcome_recorded_at"]
                    else "Pending"
                ),
                "Reasons": ", ".join(item["reasons"]) if item["reasons"] else "No strong churn signals",
            }
        )

    st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)


st.set_page_config(page_title="Admin Dashboard", layout="wide")
apply_theme()
render_page_header(
    title="Admin Dashboard",
    subtitle=(
        "Monitor adoption, inspect every user trail, and record real retention outcomes "
        "without leaving the Streamlit workspace."
    ),
    kicker="Operations View",
)

force_refresh = False
with st.sidebar:
    render_sidebar_block(
        "Admin Controls",
        [("API Base URL", API_BASE_URL)],
        note="Refresh only when you want to pull the newest backend state.",
    )
    if st.button("Refresh Dashboard"):
        invalidate_admin_cache()
        force_refresh = True

try:
    summary = get_admin_summary(force_refresh=force_refresh)
    users_response = get_admin_users(force_refresh=force_refresh)
except requests.RequestException as error:
    st.error(build_error_message(error))
    st.stop()

users = users_response.get("users", [])
if not users:
    render_soft_panel(
        "Waiting for activity",
        "No users are registered yet. Once the main app creates users and predictions, this dashboard will populate automatically.",
    )
    st.stop()

control_col, notes_col = st.columns([1.4, 0.9])
with control_col:
    user_options = {
        f"{user['user_id']} | {user['name']}": user["user_id"]
        for user in users
    }
    selected_user_label = st.selectbox(
        "Select a user to inspect",
        options=list(user_options.keys()),
        key="admin_selected_user_label",
    )
    selected_user_id = user_options[selected_user_label]

with notes_col:
    render_soft_panel(
        "Why outcome tracking matters",
        "Predictions are useful, but recording the real outcome later is what lets you measure whether the model was actually right.",
    )

try:
    history_data = get_user_history(selected_user_id, force_refresh=force_refresh)
except requests.RequestException as error:
    st.error(build_error_message(error))
    st.stop()

feedback_message = st.session_state.pop(ADMIN_MESSAGE_KEY, None)
prediction_items = history_data.get("predictions", [])

if prediction_items:
    st.subheader("Record Actual Outcome")
    action_col, helper_col = st.columns([1.4, 0.9])

    with action_col:
        prediction_option_map = {
            (
                f"{item['prediction_id']} | Predicted {item['predicted_outcome']} | "
                f"Actual {item['actual_outcome'] or 'Not recorded'}"
            ): item["prediction_id"]
            for item in prediction_items
        }

        with st.form("record_actual_outcome_form", clear_on_submit=False):
            selected_prediction_label = st.selectbox(
                "Prediction",
                options=list(prediction_option_map.keys()),
            )
            actual_outcome = st.radio(
                "Actual Retention Outcome",
                options=["Retained", "Churned"],
                horizontal=True,
            )
            outcome_submitted = st.form_submit_button("Save Outcome")

        if outcome_submitted:
            prediction_id = prediction_option_map[selected_prediction_label]
            previous_item = next(
                item for item in prediction_items if item["prediction_id"] == prediction_id
            )
            try:
                updated_item = patch_json(
                    f"/predictions/{prediction_id}/outcome",
                    {"actual_outcome": actual_outcome},
                )
            except requests.RequestException as error:
                st.error(build_error_message(error))
            else:
                history_data = replace_history_item(history_data, updated_item)
                st.session_state.setdefault(ADMIN_HISTORY_KEY, {})[selected_user_id] = history_data
                update_summary_cache(previous_item, updated_item)
                st.session_state[ADMIN_MESSAGE_KEY] = (
                    f"Outcome saved for {prediction_id}. "
                    f"Status is now {updated_item['comparison_status'] or 'Pending'}."
                )
                st.rerun()

    with helper_col:
        render_soft_panel(
            "One-click update",
            "This form updates the selected prediction directly and refreshes the dashboard from cached state so the change feels much faster.",
        )

summary = st.session_state.get(ADMIN_SUMMARY_KEY, summary)
if feedback_message:
    st.success(feedback_message)

metric_col_1, metric_col_2, metric_col_3, metric_col_4, metric_col_5 = st.columns(5)
metric_col_1.metric("Total Users", summary["total_users"])
metric_col_2.metric("Total Predictions", summary["total_predictions"])
metric_col_3.metric("Avg Churn Probability", f"{summary['avg_churn_probability']:.2%}")
metric_col_4.metric("Outcomes Recorded", summary["outcomes_recorded"])
metric_col_5.metric(
    "Prediction Accuracy",
    f"{summary['prediction_accuracy']:.2f}%"
    if summary["prediction_accuracy"] is not None
    else "N/A",
)

users_tab, history_tab = st.tabs(["All Users", "Selected User History"])

with users_tab:
    st.subheader("All Users")
    render_user_table(users)

with history_tab:
    st.subheader(f"Prediction History for {history_data['name']}")
    st.caption(
        f"Showing up to {USER_HISTORY_LIMIT} stored predictions for {history_data['user_id']}."
    )
    render_user_history(history_data)
