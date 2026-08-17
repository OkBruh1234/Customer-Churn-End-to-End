# Changelog

Running log of changes to this project. Newest first. Update this file as part
of each change rather than after the fact.

---

## Unreleased — Render cold-start fix + Postgres persistence

Branch: `claude/render-cold-start-fix-ckkk6a`

### Problem

The backend took 2+ minutes to become usable after Render's free-tier spin-down.
The Streamlit UI froze on the name-registration step with no feedback while it
waited.

### Measurement first

Benchmarked the serving path before changing anything. `churn_model.pkl` is a
scikit-learn `Pipeline[ColumnTransformer -> RandomForestClassifier]`
(400 trees, depth 6, ~44k nodes):

| Stage | Cost |
| --- | --- |
| `import pandas` | 0.280 s |
| `import sklearn` | 0.749 s |
| `joblib.load(churn_model.pkl)` | 0.190 s |
| First `predict_proba` | 0.043 s |
| Warm `predict_proba` | 0.035 s |
| **Total cold model path** | **1.264 s** |

Inference was never the bottleneck. The time went to container boot, install
bloat, and a port-binding stall.

### Changed

**Backend — cold start**

- Replaced the blocking `@app.on_event("startup")` with a `lifespan` handler
  that starts model warm-up on a background thread. Uvicorn runs lifespan
  startup *before* opening the listening socket, so the old code delayed the
  point at which Render's port detection saw a live service. `init_db()` stays
  inline (milliseconds, required before the first request).
  Measured A/B on identical hardware: **port accepts at 0.897 s instead of
  1.894 s**. The gap equals the warm-up cost and scales up on a throttled
  instance.
- Warm-up now runs a real throwaway prediction, not just `joblib.load`. The
  first `predict_proba` is what pays for pandas frame construction, the
  ColumnTransformer/OneHotEncoder paths, and numpy BLAS init.
- `load_model()` uses double-checked locking instead of `lru_cache`, so the
  warm-up thread and an early request cannot both trigger a load.
- `/health` never touches the model and stays `200` while warming, so uptime
  monitors do not flap on deploys. Added `model_ready` and `warm_duration_ms`.
- Model version is computed lazily; a missing model file previously crashed the
  service at import with an unhelpful `OSError`.
- Replaced deprecated `datetime.utcnow` / `utcfromtimestamp`, silenced pydantic
  protected-namespace warnings, and removed `reload=True` from the `__main__`
  entrypoint (it spawns a file-watching supervisor and roughly doubles memory).

**Backend — persistence**

- `backend/database.py` normalizes the legacy `postgres://` scheme Render hands
  out to `postgresql+psycopg://`, which SQLAlchemy 2.x requires, and factors
  engine creation into `create_db_engine()` so migrations can target an explicit
  engine.
- Added `psycopg[binary]~=3.3` to the runtime dependency sets.
- `scripts/migrate_sqlite_backup.py` moves existing SQLite rows into Postgres.
- Fixed a data-safety hole in that script's same-location guard. It compared raw
  URL strings, but the source engine is built from an absolute path while an
  unset `DATABASE_URL` falls back to the relative default
  `sqlite:///./churn_app.db`. Those strings differ while naming the same file,
  so the guard passed and the script would migrate a database onto itself.
  Identity now resolves SQLite paths before comparing, and the script refuses
  outright when `DATABASE_URL` is unset.

**Dependencies**

- Dropped `matplotlib`, `seaborn`, `shap`, and `xgboost` from the runtime set.
  The served model imports none of them; they only inflated the deploy image
  and the cold start. Moved to `requirements-dev.txt`.
- Pinned `scikit-learn==1.8.0`, the version that wrote `churn_model.pkl`.
  Unpinned, a fresh build installed 1.9.0 and unpickled with
  `InconsistentVersionWarning` on all six estimators — a documented risk of
  silently different predictions. Verified the pin loads warning-free with
  warnings-as-errors.
- Added `requirements-backend.txt` (API-only, no streamlit/pyarrow).
  `requirements.txt` remains a working superset so an existing Render build
  command keeps succeeding.
- Relaxed `requires-python` from `">=3.14"` to `">=3.11"`. Local development
  stays on 3.14 (`.python-version`); every pinned dependency ships cp311-cp314
  manylinux wheels, so the lower floor costs nothing and leaves the deploy
  target free to move if a host does not yet offer 3.14.

**Frontend**

- Extracted the duplicated HTTP layer from `app.py` and
  `pages/Admin_Dashboard.py` into `backend_client.py`, with pooled connections,
  bounded transport retries across Render's 502/503 wake window, and a separate
  no-retry session so liveness probes fail fast.
- The UI now wakes the backend on page load, before the user types, showing
  elapsed time instead of freezing. Registration previously ran bare, so a cold
  backend showed a motionless page for the full 75 s timeout and then an error.
- Added recovery for a reset backend database: a `404 User not found` for a
  session the browser still holds now re-registers the same name and continues.

**Keep-alive**

- Added `.github/workflows/keep-alive.yml` pinging `/health` on a schedule, with
  the URL from a repository variable rather than hardcoded.
- Runs every 10 minutes, 24/7, so the service is never cold for a visitor in any
  timezone. The budget constraint this accepts: Render's free tier allows
  **750 instance-hours per month per workspace** and a month is ~730 h, so this
  consumes ~97% of the allowance. Workable for a single service, but it leaves
  no room for a second free web service in the same workspace — adding one would
  exceed the cap, and exceeding it suspends the service outright. Narrow the
  cron back to `*/10 0-19 * * *` (~608 h/month) if another service is ever
  needed.
- Added `scripts/measure_cold_start.sh` to time a real deployment.

### Verified

Run against a live local backend, not mocked:

- Backend lifecycle: port bind 0.897 s, `/health` 0.015 s while
  `model_ready=false`, warm-up completed at 2.337 s
  (`warm_duration_ms=1440`), register 0.018 s, first `/predict` 0.044 s,
  warm `/predict` 0.040 s.
- Streamlit `AppTest` on `app.py`: registration form renders, register →
  `USR-000001`, predict → `PRED-000001`, stale `USR-009999` auto-recovers to
  `USR-000002` with an explanatory message.
- Streamlit `AppTest` on `pages/Admin_Dashboard.py`: metrics and seeded user
  render, no error widgets.
- Cold path against an unroutable host: wake status widget, error message, and
  retry button all appear; no unhandled exception.
- `scikit-learn==1.8.0` loads `churn_model.pkl` with warnings-as-errors passing.

### Verified in production

Measured against the deployed Render service after merging (2026-08-17):

| Signal | Value |
| --- | --- |
| `warm_duration_ms` reported by `/health` | **16703.61** |
| `/health` response time, warm | 0.60 – 1.04 s |
| `POST /predict` round trip | 0.78 s |
| Server-side `processing_time_ms` | 202.71 |
| `churn_probability` for the reference row | 0.7489 |

Two things this confirms:

- **Warm-up on Render's free tier takes 16.7 s.** Under the previous blocking
  startup, every one of those seconds delayed the listening socket and so
  delayed the platform seeing a live service. It now runs on a background
  thread while `/health` answers in under a second.
- **The scikit-learn pin holds across environments.** The reference row scores
  0.7489 in production, identical to the local benchmark, so the 1.8.0 pin
  reproduces predictions rather than merely silencing a warning.

Render built successfully with `.python-version` at `3.14`, so the fallback to
`3.13.4` is not needed.

The keep-alive workflow completed with conclusion `success` on its first
`workflow_dispatch` run.

### Not verified

- **A true cold start.** All timings above were taken against an already-running
  instance. To measure the spun-down path, leave the service idle for >15
  minutes with the keep-alive workflow disabled, or suspend and resume it in the
  Render dashboard, then run `scripts/measure_cold_start.sh <url>`.
- **The Postgres path end to end.** `DATABASE_URL` is not yet set on the Render
  service, so it is still running on ephemeral SQLite — a fresh registration
  returned `USR-000001`, confirming the database had been reset. The cold-start
  work was verified against SQLite only.

### Manual steps still required

These cannot be done from the repository alone:

1. Add repository **variable** `BACKEND_URL` (Settings → Secrets and variables →
   Actions → Variables) set to the Render base URL. The keep-alive workflow
   fails with instructions if it is missing.
2. Set the Render **Build Command** to `pip install -r requirements-backend.txt`.
   The existing command still works, so this is an optimization, not a
   prerequisite.
3. Confirm the Render **Start Command** is
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` with no `--reload`.
4. Set `DATABASE_URL` on the Render service to the Postgres connection string.
   Without it the service still runs, but on ephemeral SQLite that is wiped on
   every restart.
5. If a Render build fails with a Python version error, change `.python-version`
   from `3.14` to `3.13.4`. All pins have wheels for both.
