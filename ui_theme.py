import html

import streamlit as st


APP_THEME_CSS = """
<style>
:root {
    --page-bg: #f4f8fd;
    --page-glow: rgba(64, 122, 209, 0.1);
    --page-glow-soft: rgba(158, 193, 248, 0.2);
    --card-bg: rgba(255, 255, 255, 0.9);
    --card-border: rgba(66, 105, 166, 0.13);
    --card-border-strong: rgba(66, 105, 166, 0.26);
    --ink: #203047;
    --muted: #617289;
    --accent: #2f6fdd;
    --accent-deep: #1e4fa8;
    --accent-soft: #e8f0ff;
    --sidebar-top: #203b64;
    --sidebar-bottom: #1b2f4d;
    --shadow: 0 14px 28px rgba(33, 58, 96, 0.09);
    --focus-ring: rgba(47, 111, 221, 0.2);
}

html, body, [class*="css"] {
    font-family: "Segoe UI", "Trebuchet MS", "Gill Sans", sans-serif;
    color: var(--ink);
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, var(--page-glow), transparent 34%),
        radial-gradient(circle at bottom right, var(--page-glow-soft), transparent 28%),
        linear-gradient(180deg, #f8fbff 0%, var(--page-bg) 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--sidebar-top) 0%, var(--sidebar-bottom) 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    color: #f5f9ff;
}

[data-testid="stSidebar"] * {
    color: #f5f9ff;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 2.5rem;
}

.hero-card {
    background: linear-gradient(
        135deg,
        rgba(30, 79, 168, 0.96) 0%,
        rgba(47, 111, 221, 0.94) 58%,
        rgba(109, 154, 226, 0.9) 100%
    );
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 24px;
    box-shadow: var(--shadow);
    color: #f8fbff;
    margin-bottom: 1.2rem;
    overflow: hidden;
    padding: 1.35rem 1.55rem;
    position: relative;
}

.hero-card::after {
    background: radial-gradient(circle, rgba(255, 255, 255, 0.18) 0%, transparent 65%);
    content: "";
    height: 220px;
    position: absolute;
    right: -60px;
    top: -85px;
    width: 220px;
}

.hero-kicker {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    opacity: 0.86;
    text-transform: uppercase;
}

.hero-title {
    font-size: 2.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.06;
    margin: 0.35rem 0 0.5rem 0;
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 0.98rem;
    line-height: 1.5;
    margin: 0;
    max-width: 760px;
    opacity: 0.94;
    position: relative;
    z-index: 1;
}

.soft-panel {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    box-shadow: var(--shadow);
    margin-bottom: 0.9rem;
    padding: 1rem 1.05rem;
}

.soft-panel h3 {
    color: var(--ink);
    font-size: 1.02rem;
    font-weight: 700;
    margin: 0 0 0.35rem 0;
}

.soft-panel p {
    color: var(--muted);
    line-height: 1.55;
    margin: 0;
}

div[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    box-shadow: var(--shadow);
    padding: 0.55rem 0.85rem;
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

div[data-testid="stMetricValue"] {
    color: var(--ink);
    font-size: 1.7rem;
    font-weight: 700;
}

.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
    border: 1px solid rgba(30, 79, 168, 0.2);
    border-radius: 14px;
    box-shadow: 0 10px 18px rgba(30, 79, 168, 0.16);
    color: #f8fbff;
    font-weight: 700;
    min-height: 2.55rem;
    transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    box-shadow: 0 12px 22px rgba(30, 79, 168, 0.18);
    transform: translateY(-1px);
}

.stButton > button:focus,
.stFormSubmitButton > button:focus {
    box-shadow: 0 0 0 3px var(--focus-ring);
    outline: none;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--card-border) !important;
    border-radius: 14px;
    box-shadow: none !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

div[data-baseweb="input"] > div:hover,
div[data-baseweb="select"] > div:hover,
div[data-baseweb="textarea"] > div:hover {
    border-color: var(--card-border-strong) !important;
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--focus-ring) !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] span {
    color: var(--ink) !important;
}

div[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    overflow: hidden;
}

div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.84);
    border: 1px solid var(--card-border);
    border-radius: 18px;
}

[data-testid="stMarkdownContainer"] code,
[data-testid="stCaptionContainer"] code {
    background: transparent !important;
    border: none !important;
    color: var(--accent-deep) !important;
    font-size: inherit !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] code {
    background: transparent;
    border: none;
    color: #f5f9ff;
    padding: 0;
}

[data-testid="stSidebar"] .sidebar-card {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 18px;
    margin-bottom: 0.95rem;
    padding: 0.9rem 0.95rem 0.7rem 0.95rem;
}

[data-testid="stSidebar"] .sidebar-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
}

[data-testid="stSidebar"] .sidebar-row {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    flex-direction: column;
    gap: 0.16rem;
    padding: 0.48rem 0;
}

[data-testid="stSidebar"] .sidebar-row:last-child {
    border-bottom: none;
}

[data-testid="stSidebar"] .sidebar-label {
    color: rgba(232, 241, 255, 0.72);
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

[data-testid="stSidebar"] .sidebar-value {
    color: #f7fbff;
    font-size: 0.96rem;
    font-weight: 600;
    line-height: 1.35;
    word-break: break-word;
}

[data-testid="stSidebar"] .sidebar-note {
    color: rgba(229, 240, 255, 0.74);
    font-size: 0.82rem;
    line-height: 1.4;
    margin-top: 0.2rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid var(--card-border);
    border-radius: 14px 14px 0 0;
    color: var(--muted);
    padding: 0.5rem 0.9rem;
}

.stTabs [aria-selected="true"] {
    background: rgba(255, 255, 255, 0.96);
    border-color: var(--card-border-strong);
    color: var(--accent-deep);
}

.tiny-note {
    color: var(--muted);
    font-size: 0.92rem;
    margin-top: 0.35rem;
}
</style>
"""


def apply_theme():
    st.markdown(APP_THEME_CSS, unsafe_allow_html=True)


def render_page_header(title, subtitle, kicker):
    st.markdown(
        f"""
        <section class="hero-card">
            <div class="hero-kicker">{html.escape(str(kicker))}</div>
            <div class="hero-title">{html.escape(str(title))}</div>
            <p class="hero-subtitle">{html.escape(str(subtitle))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_soft_panel(title, description):
    st.markdown(
        f"""
        <section class="soft-panel">
            <h3>{html.escape(str(title))}</h3>
            <p>{html.escape(str(description))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_block(title, rows, note=None):
    row_markup = "".join(
        (
            f'<div class="sidebar-row">'
            f'<div class="sidebar-label">{html.escape(str(label))}</div>'
            f'<div class="sidebar-value">{html.escape(str(value))}</div>'
            f"</div>"
        )
        for label, value in rows
    )

    note_markup = (
        f'<div class="sidebar-note">{html.escape(str(note))}</div>'
        if note
        else ""
    )

    st.markdown(
        (
            f'<div class="sidebar-card">'
            f'<div class="sidebar-title">{html.escape(str(title))}</div>'
            f"{row_markup}"
            f"{note_markup}"
            f"</div>"
        ),
        unsafe_allow_html=True,
    )
