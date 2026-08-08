from __future__ import annotations

import streamlit as st


def apply_mobile_bottom_nav_fix() -> None:
    """Force the app's existing stateful bottom navigation into a native-style mobile row."""
    st.markdown(
        r"""
<style>
/* Keep the existing functional Streamlit buttons, but force a 5-across mobile dock. */
.st-key-app_bottom_nav {
    position: fixed !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    transform: none !important;
    width: 100vw !important;
    max-width: none !important;
    min-height: 92px !important;
    z-index: 2147483000 !important;
    background: #060b0f !important;
    border-top: 1px solid #263540 !important;
    padding: 7px 5px max(8px, env(safe-area-inset-bottom)) !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

.st-key-app_bottom_nav > div,
.st-key-app_bottom_nav [data-testid="stVerticalBlock"] {
    width: 100% !important;
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
}

.st-key-app_bottom_nav div[data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    align-items: stretch !important;
    gap: 3px !important;
    width: 100% !important;
    min-width: 0 !important;
    flex-wrap: nowrap !important;
}

.st-key-app_bottom_nav div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.st-key-app_bottom_nav [data-testid="stButton"] {
    width: 100% !important;
}

.st-key-app_bottom_nav button {
    width: 100% !important;
    min-width: 0 !important;
    height: 72px !important;
    min-height: 72px !important;
    padding: 3px 1px !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 9px !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #c8cdd5 !important;
    overflow: hidden !important;
}

.st-key-app_bottom_nav button[kind="primary"] {
    background: #101820 !important;
}

/* Replace the original emoji+text string with a much larger icon and clean label. */
.st-key-app_bottom_nav button p {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 2px !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    font-size: 0 !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    overflow: visible !important;
}

.st-key-app_bottom_nav button p::before {
    display: block !important;
    font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
    font-size: 29px !important;
    line-height: 31px !important;
    font-weight: 400 !important;
}

.st-key-app_bottom_nav button p::after {
    display: block !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
    font-size: 11px !important;
    line-height: 14px !important;
    font-weight: 750 !important;
    color: #c8cdd5 !important;
}

.st-key-bottom_Home button p::before { content: "🏠"; }
.st-key-bottom_Home button p::after { content: "Home"; }
.st-key-bottom_Mock_Draft button p::before { content: "🏈"; }
.st-key-bottom_Mock_Draft button p::after { content: "Draft"; }
.st-key-bottom_Players button p::before { content: "👤"; }
.st-key-bottom_Players button p::after { content: "Players"; }
.st-key-bottom_League_History button p::before { content: "👥"; }
.st-key-bottom_League_History button p::after { content: "Team IQ"; }
.st-key-bottom_Draft_Coach button p::before {
    content: "•••";
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    font-size: 28px !important;
    letter-spacing: 2px !important;
}
.st-key-bottom_Draft_Coach button p::after { content: "Coach"; }

/* Active tab keeps the existing stateful button behavior but gets a bright visual treatment. */
.st-key-app_bottom_nav button[kind="primary"] p::after {
    color: #dfff00 !important;
}
.st-key-app_bottom_nav button[kind="primary"] p::before {
    filter: saturate(1.15) brightness(1.15) !important;
}

/* Ensure page content clears the fixed navigation on iPhone. */
[data-testid="stAppViewBlockContainer"],
.block-container {
    padding-bottom: 112px !important;
}

@media (max-width: 430px) {
    .st-key-app_bottom_nav {
        min-height: 88px !important;
        padding-left: 3px !important;
        padding-right: 3px !important;
    }
    .st-key-app_bottom_nav button {
        height: 68px !important;
        min-height: 68px !important;
    }
    .st-key-app_bottom_nav button p::before {
        font-size: 27px !important;
        line-height: 29px !important;
    }
    .st-key-app_bottom_nav button p::after {
        font-size: 10.5px !important;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )
