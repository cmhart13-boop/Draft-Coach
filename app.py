import time

import streamlit as st

# Page configuration must be the first Streamlit command on every run.
st.set_page_config(
    page_title="Shiva Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from shiva_app_v2 import run
from splash_asset import SPLASH_WEBP_BASE64
from streamlit_branding_fix import hide_streamlit_branding


if not st.session_state.get("_shiva_splash_seen", False):
    # Mark immediately so any rerun during startup cannot loop the splash.
    st.session_state["_shiva_splash_seen"] = True
    st.markdown(
        f"""
        <style>
        header,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],#MainMenu,footer{{display:none!important;visibility:hidden!important}}
        [data-testid="stAppViewBlockContainer"],.block-container{{padding:0!important;margin:0!important;max-width:none!important}}
        .shiva-startup-splash{{
            position:fixed;
            inset:0;
            width:100vw;
            height:100dvh;
            z-index:2147483647;
            background-color:#050b58;
            background-image:url("data:image/webp;base64,{SPLASH_WEBP_BASE64}");
            background-repeat:no-repeat;
            background-position:center center;
            background-size:contain;
            pointer-events:none;
        }}
        </style>
        <div class="shiva-startup-splash" aria-label="Shiva Intelligence loading screen"></div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(2.35)
    st.session_state["page"] = "Home"
    st.query_params.clear()
    st.rerun()

# shiva_app_v2 also contains the legacy page-config call. Suppress only that
# duplicate call while rendering the app; restore Streamlit immediately after.
_original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
try:
    run()
finally:
    st.set_page_config = _original_set_page_config

hide_streamlit_branding()
