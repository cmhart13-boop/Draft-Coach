from __future__ import annotations

import streamlit as st


def hide_streamlit_branding() -> None:
    """Remove Streamlit/Community Cloud chrome that can overlap the mobile bottom nav."""
    st.markdown(
        r"""
        <style>
        /* Native Streamlit toolbar / status / deploy controls */
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
        .stAppDeployButton,
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        /* Community Cloud viewer / Hosted-with-Streamlit badge.
           Streamlit has changed these generated class names across releases,
           so target both known names and stable substring patterns. */
        .viewerBadge_container__1QSob,
        .styles_viewerBadge__1yB5_,
        .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK,
        [class*="viewerBadge"],
        [class*="ViewerBadge"],
        [class*="hostedWithStreamlit"],
        [class*="HostedWithStreamlit"],
        [aria-label*="Hosted with Streamlit"],
        [aria-label*="Streamlit Community Cloud"],
        [title*="Hosted with Streamlit"],
        [title*="Streamlit Community Cloud"],
        a[href*="streamlit.io/cloud"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        /* Prevent any hidden Streamlit chrome from reserving mobile space. */
        [data-testid="stAppViewContainer"] > header,
        [data-testid="stAppViewContainer"] > footer {
            display: none !important;
            height: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
