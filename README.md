# Customer Churn Prediction System

End-to-end churn prediction project with a Streamlit frontend and a lightweight FastAPI backend.

## Overview
- Predicts customer churn from service, billing, and tenure inputs
- Registers each user before prediction and stores them in a SQLite database
- Serves the `.pkl` model through backend API endpoints
- Logs each prediction against the registered user ID
- Shows prediction history for each registered user
- Exposes model version metadata with each prediction
- Includes a Streamlit admin dashboard for overall usage metrics and user drill-down
- Lets admins record actual outcomes later to compare prediction vs real churn

## Tech Stack
- Python
- Streamlit
- FastAPI
- SQLAlchemy
- Scikit-learn
- SQLite

## Outputs
- Churn probability
- Risk classification
- Basic explanation of prediction
- User and prediction records stored in the backend database
- Formatted public user IDs such as `USR-000001`
- Prediction history with model version and latency
- Admin metrics such as total users, total predictions, and average churn probability
- Actual outcome tracking with prediction match or mismatch status

## Run Locally
1. Install dependencies into the same project environment used by Streamlit and FastAPI:

Using `uv`:

```bash
uv sync
```

Or using `pip` inside the project virtual environment:

```bash
pip install -r requirements.txt
```

2. Start the backend:

```bash
uvicorn backend.main:app --reload
```

3. Start the Streamlit UI in a second terminal:

```bash
streamlit run app.py
```

4. Open the Streamlit app, register the user name first, then submit prediction inputs.
5. Open the `Admin Dashboard` page from Streamlit's sidebar navigation to inspect all users, review user histories, and record actual outcomes.

## Notes
- The backend preloads the model at startup to reduce first-prediction delay.
- Streamlit reuses one HTTP session for backend calls to keep repeated requests a bit faster.
- Existing SQLite databases are upgraded at backend startup with the extra outcome-tracking columns.

## Why FastAPI Helps Here
- It gives the project a real backend boundary instead of keeping all logic inside Streamlit.
- The model can be served through clear API routes such as registration, prediction, history, and admin metrics.
- SQLAlchemy and database writes stay on the backend, so the UI remains thinner and easier to evolve.
- The same API can later be reused by another frontend, mobile app, or internal admin tool without changing the model-serving layer.

## Optional Configuration
- `API_BASE_URL`: Override the backend base URL used by Streamlit. Default: `http://127.0.0.1:8000`
- `DATABASE_URL`: Override the SQLAlchemy database URL. Default: `sqlite:///./churn_app.db`
- `MODEL_VERSION`: Override the model version label returned by the backend. By default it is derived from the model file name and last modified time.
