from __future__ import annotations

import streamlit as st


def apply_mobile_nav_override() -> None:
    """Match the reference mobile bottom nav and suppress Streamlit floating chrome."""
    st.markdown(
        r"""
        <style>
        /* Reference-style bottom navigation */
        .bottom-nav {
            position: fixed !important;
            left: 50% !important;
            bottom: 0 !important;
            transform: translateX(-50%) !important;
            width: min(520px, 100vw) !important;
            min-height: 92px !important;
            z-index: 2147483000 !important;
            background: #02060a !important;
            border-top: 1px solid #20364d !important;
            display: grid !important;
            grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
            align-items: center !important;
            padding: 10px 2px max(10px, env(safe-area-inset-bottom)) !important;
            box-sizing: border-box !important;
            backdrop-filter: none !important;
        }
        .bottom-item {
            min-width: 0 !important;
            text-align: center !important;
            text-decoration: none !important;
            color: #c8cdd5 !important;
            font-size: 14px !important;
            line-height: 1.1 !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
        }
        .bottom-item.active {
            color: #dfff00 !important;
            font-weight: 800 !important;
        }
        .bottom-icon {
            display: block !important;
            height: 38px !important;
            margin: 0 0 4px !important;
            font-size: 0 !important;
            line-height: 38px !important;
            filter: none !important;
        }
        .bottom-icon::before {
            display: block !important;
            font-size: 31px !important;
            line-height: 38px !important;
            font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
        }
        .bottom-item:nth-child(1) .bottom-icon::before { content: "🏠"; }
        .bottom-item:nth-child(2) .bottom-icon::before { content: "🏈"; }
        .bottom-item:nth-child(3) .bottom-icon::before { content: "👤"; }
        .bottom-item:nth-child(4) .bottom-icon::before { content: "👥"; }
        .bottom-item:nth-child(5) .bottom-icon::before {
            content: "•••";
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            font-size: 29px !important;
            letter-spacing: 3px !important;
            color: #c8cdd5 !important;
        }
        [data-testid="stAppViewBlockContainer"], .block-container {
            padding-bottom: 118px !important;
        }

        /* Hide Streamlit / Community Cloud floating controls and badges. */
        header,
        footer,
        #MainMenu,
        #stDecoration,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stStatusWidget"] *,
        [data-testid="stAppDeployButton"],
        [data-testid="stMainMenu"],
        [data-testid="stBaseButton-header"],
        [data-testid="stBaseButton-headerNoPadding"],
        [data-testid*="viewerBadge"],
        [class*="viewerBadge"],
        [class*="ViewerBadge"],
        [class*="hostedWithStreamlit"],
        [class*="HostedWithStreamlit"],
        [class*="stDeployButton"],
        [aria-label*="Hosted with Streamlit"],
        [aria-label*="Streamlit Community Cloud"],
        [title*="Hosted with Streamlit"],
        [title*="Streamlit Community Cloud"],
        a[href*="streamlit.io/cloud"],
        a[href*="share.streamlit.io"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        @media (max-width: 390px) {
            .bottom-nav { min-height: 86px !important; padding-top: 8px !important; }
            .bottom-item { font-size: 13px !important; }
            .bottom-icon { height: 35px !important; line-height: 35px !important; }
            .bottom-icon::before { font-size: 28px !important; line-height: 35px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
