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

To re-run the notebook or retrain the model, also install the training extras
(`matplotlib`, `seaborn`, `shap`, `xgboost`), which the deployed services
deliberately do not carry:

```bash
pip install -r requirements-dev.txt   # or: uv sync --group dev
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

## Deployment

The backend runs as a Render web service and the UI on Streamlit Community Cloud.

### Render (backend)

| Setting | Value |
| --- | --- |
| Build Command | `pip install -r requirements-backend.txt` |
| Start Command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Python version | from `.python-version` (3.13.4) |

`requirements-backend.txt` is the slim, API-only dependency set. The repo-root
`requirements.txt` is a superset that also works, so an existing service keeps
building if the command is not updated — switching just makes the image
noticeably smaller by dropping Streamlit and its pyarrow tree.

Do **not** add `--reload` to the start command: it runs a file-watching
supervisor process and roughly doubles memory on a 512 MB instance.

### Streamlit Community Cloud (frontend)

Installs the repo-root `requirements.txt` automatically. Set the backend URL in
**Settings → Secrets**:

```toml
API_BASE_URL = "https://your-backend-service.onrender.com"
```

### Keep-alive

`.github/workflows/keep-alive.yml` pings `/health` on a schedule so the free
instance does not sit spun down. One-time setup: add a repository **variable**
named `BACKEND_URL` (Settings → Secrets and variables → Actions → Variables)
containing the Render base URL. The workflow fails with instructions if it is
missing.

Two caveats worth knowing:

- Free instance time is capped at **750 hours/month per workspace** and a month
  is ~730 hours. The default schedule keeps the service awake ~20h/day (~608
  h/month) rather than 24/7, so the cap is not the thing that takes the service
  down. Going 24/7 leaves almost no headroom and no room for a second free
  service.
- GitHub disables scheduled workflows after 60 days without repository activity,
  and the scheduler can run late under load. An external monitor such as
  UptimeRobot or cron-job.org pointed at `/health` is a good backup.

## Cold Start Notes

Cold start is dominated by container boot, not by the model:

| Stage | Cost |
| --- | --- |
| `import pandas` + `import sklearn` | ~1.0 s |
| `joblib.load(churn_model.pkl)` | ~0.2 s |
| First `predict_proba` | ~0.04 s |
| Warm `predict_proba` | ~0.035 s |

What the code does about the rest:

- **The port binds before the model loads.** Uvicorn runs lifespan startup
  *before* opening the listening socket, so blocking work there delays the point
  at which the platform sees a live service. `init_db()` still runs inline
  (milliseconds, and required before the first request); the model warm-up is
  handed to a background thread.
- **Warm-up runs a real prediction**, not just `joblib.load`. The first
  `predict_proba` is what pays for pandas frame construction, the
  ColumnTransformer/OneHotEncoder paths and numpy's BLAS init, so it belongs in
  warm-up rather than on the first user request.
- **`/health` never touches the model** and stays `200` while warming, so an
  uptime monitor does not flap on every deploy. Its `model_ready` flag tells a
  warm instance from one that just booted.
- **The UI wakes the backend on page load**, before the user types anything, and
  shows elapsed time while it boots instead of freezing. Backend calls retry
  through a cold start rather than surfacing it as a dead backend.
- **scikit-learn is pinned to 1.8.0**, the version that wrote `churn_model.pkl`.
  Unpinned, a fresh build installs a newer minor and unpickles with
  `InconsistentVersionWarning`, which risks silently different predictions.

### Known limitation: prediction history is not durable

`DATABASE_URL` defaults to SQLite on the instance's local disk, which Render
does not persist across restarts. Every cold start therefore begins with an
empty database, and stored users and prediction history are lost.

The UI handles the visible symptom: when the backend returns
`404 User not found` for a session it still holds, it re-registers the same name
and continues instead of dead-ending. It cannot recover the lost rows. Pointing
`DATABASE_URL` at a managed Postgres instance is the actual fix and needs no
code change beyond adding a driver.

## Notes
- Streamlit reuses one pooled HTTP session for backend calls, with a separate
  no-retry session for liveness probes so they fail fast.
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
