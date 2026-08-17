"""HTTP client shared by the Streamlit pages.

Extracted from app.py / pages/Admin_Dashboard.py, which each carried their own
copy of the session + error-message logic.

The important behaviour here is cold-start handling. The backend runs on a
Render free instance, which spins down after ~15 minutes idle. Waking it means a
full container boot, and while that happens Render's edge answers 502/503 rather
than holding the connection. A single request with one long timeout therefore
fails in a way that looks like a dead backend, which is exactly what the UI used
to report. Instead we retry across the wake-up and show progress while it runs.
"""

import time

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from runtime_config import get_api_base_url_config, get_api_base_url_issue


API_BASE_URL, API_BASE_URL_SOURCE = get_api_base_url_config()
API_BASE_URL_ISSUE = get_api_base_url_issue(API_BASE_URL)

# (connect, read). Splitting these matters: a sleeping instance refuses or
# blackholes the connection, and we want to find that out in seconds rather than
# sitting on one 75s read timeout.
FAST_TIMEOUT = (5, 8)
NORMAL_TIMEOUT = (10, 45)

# Render free-tier cold starts are routinely 50-90s and can exceed two minutes
# when the image is large. Budget generously; we exit as soon as it answers.
WAKE_BUDGET_SECONDS = 210
WAKE_PROBE_INTERVAL_SECONDS = 3

BACKEND_AWAKE_KEY = "backend_awake"

# Statuses Render's edge returns while the instance is booting.
COLD_START_STATUSES = frozenset({502, 503, 504})


def _build_session(retry_policy):
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    adapter = HTTPAdapter(max_retries=retry_policy, pool_connections=4, pool_maxsize=8)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


@st.cache_resource
def get_http_session():
    """Session for real API calls. Short transport retries for transient blips.

    Deliberately modest: long cold-start waiting is the job of wake_backend(),
    not of urllib3 backoff. Stacking a long retry policy underneath the wake
    loop would multiply the two and let a single click hang for many minutes.
    """
    return _build_session(
        Retry(
            total=2,
            connect=2,
            read=1,
            status=2,
            backoff_factor=0.5,
            status_forcelist=sorted(COLD_START_STATUSES),
            allowed_methods=frozenset({"GET", "POST", "PATCH"}),
            raise_on_status=False,
        )
    )


@st.cache_resource
def get_probe_session():
    """Session for liveness probes: no retries, so a probe fails fast.

    probe_health must return within its timeout for the wake-up progress display
    to tick at a sensible rate; transport-level retries would silently stretch a
    5s probe into tens of seconds.
    """
    return _build_session(Retry(total=0, read=0, connect=0, redirect=0, status=0))


def request_json(method, path, payload=None, timeout=NORMAL_TIMEOUT, session=None):
    request_kwargs = {
        "method": method,
        "url": f"{API_BASE_URL}{path}",
        "timeout": timeout,
    }
    if payload is not None:
        request_kwargs["json"] = payload

    response = (session or get_http_session()).request(**request_kwargs)
    response.raise_for_status()
    return response.json()


def get_json(path, timeout=NORMAL_TIMEOUT, session=None):
    return request_json("GET", path, timeout=timeout, session=session)


def post_json(path, payload, timeout=NORMAL_TIMEOUT):
    return request_json("POST", path, payload=payload, timeout=timeout)


def patch_json(path, payload, timeout=NORMAL_TIMEOUT):
    return request_json("PATCH", path, payload=payload, timeout=timeout)


def probe_health(timeout=FAST_TIMEOUT):
    """Single cheap liveness check. Returns the payload, or None if unreachable."""
    try:
        return get_json("/health", timeout=timeout, session=get_probe_session())
    except requests.RequestException:
        return None


def is_backend_cold(error):
    """True when the failure looks like a sleeping instance rather than a real bug."""
    if isinstance(error, (requests.ConnectionError, requests.Timeout)):
        return True

    response = getattr(error, "response", None)
    return response is not None and response.status_code in COLD_START_STATUSES


def wake_backend(status_callback=None, budget_seconds=WAKE_BUDGET_SECONDS):
    """Poll /health until the instance answers or the budget runs out.

    Returns the health payload on success, otherwise None. status_callback gets
    a human-readable progress line so the page can show elapsed time instead of
    appearing frozen.
    """
    started_at = time.monotonic()
    attempt = 0

    while True:
        elapsed = time.monotonic() - started_at
        if elapsed >= budget_seconds:
            return None

        attempt += 1
        if status_callback:
            status_callback(
                f"Waking the backend on Render free tier… {int(elapsed)}s elapsed "
                f"(attempt {attempt})."
            )

        health = probe_health()
        if health is not None:
            st.session_state[BACKEND_AWAKE_KEY] = True
            return health

        time.sleep(WAKE_PROBE_INTERVAL_SECONDS)


def ensure_backend_awake(status_callback=None):
    """Wake the instance if needed. Cached per Streamlit session after success."""
    if st.session_state.get(BACKEND_AWAKE_KEY):
        return True

    if probe_health() is not None:
        st.session_state[BACKEND_AWAKE_KEY] = True
        return True

    return wake_backend(status_callback=status_callback) is not None


def call_with_wake(operation, status_callback=None):
    """Run a backend call, transparently waking a cold instance and retrying once.

    `operation` is a zero-arg callable performing the request.
    """
    try:
        return operation()
    except requests.RequestException as error:
        if not is_backend_cold(error):
            raise

        st.session_state.pop(BACKEND_AWAKE_KEY, None)
        if not ensure_backend_awake(status_callback=status_callback):
            raise

        return operation()


def is_missing_user_error(error):
    """True for the 404 the backend returns when its user row no longer exists.

    The backend stores users in SQLite on Render's ephemeral disk, so every cold
    start starts from an empty database while the browser session still holds
    the old user id. Callers use this to re-register instead of dead-ending.
    """
    response = getattr(error, "response", None)
    if response is None or response.status_code != 404:
        return False

    try:
        detail = response.json().get("detail", "")
    except ValueError:
        return False

    return "user not found" in str(detail).lower()


def build_error_message(error):
    if API_BASE_URL_ISSUE:
        return API_BASE_URL_ISSUE

    if is_backend_cold(error):
        return (
            f"The backend at {API_BASE_URL} did not wake up in time. "
            "It runs on Render's free tier, which spins the instance down after "
            "15 minutes idle. Wait a moment and try again — the next attempt is "
            "usually fast because the instance is already booting."
        )

    default_message = (
        f"Could not reach the backend at {API_BASE_URL}. "
        "Make sure your public FastAPI URL is set in API_BASE_URL."
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
