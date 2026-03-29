import os
from urllib.parse import urlparse

import streamlit as st


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
LOCAL_API_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


def get_api_base_url():
    secret_value = None
    try:
        secret_value = st.secrets.get("API_BASE_URL")
    except Exception:
        secret_value = None

    raw_value = secret_value or os.getenv("API_BASE_URL") or DEFAULT_API_BASE_URL
    raw_value = str(raw_value).strip()

    # Small convenience for deployed domains entered without a scheme.
    if raw_value and "://" not in raw_value and " " not in raw_value and "." in raw_value:
        raw_value = f"https://{raw_value}"

    return raw_value.rstrip("/")


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
