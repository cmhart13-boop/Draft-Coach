import time
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Shiva Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from shiva_app_v2 import run
from streamlit_branding_fix import hide_streamlit_branding

hide_streamlit_branding()

if not st.session_state.get("_shiva_splash_seen", False):
    st.markdown(
        """
        <style>
        [data-testid="stAppViewBlockContainer"], .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        .stImage img {
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100dvh !important;
            object-fit: cover !important;
            z-index: 999999 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.image(Path("assets/shiva_splash.jpg"), use_container_width=True)
    time.sleep(2.5)
    st.session_state["_shiva_splash_seen"] = True
    st.session_state["page"] = "Home"
    st.rerun()

_original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
try:
    run()
finally:
    st.set_page_config = _original_set_page_config

hide_streamlit_branding()
