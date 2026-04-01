import os
from urllib.parse import urlparse

import streamlit as st


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
LOCAL_API_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}
API_BASE_URL_SECRET_PATHS = (
    ("API_BASE_URL",),
    ("api_base_url",),
    ("general", "API_BASE_URL"),
    ("general", "api_base_url"),
    ("backend", "API_BASE_URL"),
    ("backend", "api_base_url"),
)
API_BASE_URL_ENV_KEYS = ("API_BASE_URL", "api_base_url")


def _read_streamlit_secret(path):
    try:
        value = st.secrets
    except Exception:
        return None

    for key in path:
        if value is None:
            return None

        try:
            value = value.get(key)
        except Exception:
            return None

    return value


def get_api_base_url_config():
    raw_value = None
    source = "default"

    for path in API_BASE_URL_SECRET_PATHS:
        secret_value = _read_streamlit_secret(path)
        if secret_value:
            raw_value = secret_value
            source = f"streamlit_secret:{'.'.join(path)}"
            break

    if not raw_value:
        for key in API_BASE_URL_ENV_KEYS:
            env_value = os.getenv(key)
            if env_value:
                raw_value = env_value
                source = f"environment:{key}"
                break

    if not raw_value:
        raw_value = DEFAULT_API_BASE_URL

    raw_value = str(raw_value).strip()

    # Small convenience for deployed domains entered without a scheme.
    if raw_value and "://" not in raw_value and " " not in raw_value and "." in raw_value:
        raw_value = f"https://{raw_value}"

    return raw_value.rstrip("/"), source


def get_api_base_url():
    return get_api_base_url_config()[0]


def get_api_base_url_issue(api_base_url):
    lowered = api_base_url.lower()

    if "uvicorn" in lowered or "backend.main:app" in lowered or " " in api_base_url:
        return (
            "API_BASE_URL looks like a uvicorn command, not a public backend URL. "
            "Use something like https://your-backend-service.com."
        )

    parsed = urlparse(api_base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return (
            "API_BASE_URL is not a valid URL. It should look like "
            "https://your-backend-service.com."
        )

    if parsed.hostname in LOCAL_API_HOSTS:
        return (
            "API_BASE_URL points to localhost. That only works on your own machine. "
            "In Streamlit Cloud, use your public backend URL."
        )

    return None
