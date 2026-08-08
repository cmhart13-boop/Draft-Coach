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


# IMPORTANT: do not block the Streamlit event loop with time.sleep here.
# The splash is a browser-side fixed overlay so the image actually paints
# immediately, stays visible for ~2.5 seconds, then fades away while the Home
# screen is already rendered underneath it.
if not st.session_state.get("_shiva_splash_seen", False):
    st.session_state["_shiva_splash_seen"] = True
    st.session_state["page"] = "Home"
    st.markdown(
        f"""
        <style>
        @keyframes shivaSplashExit {{
            0%, 88% {{ opacity:1; visibility:visible; }}
            100% {{ opacity:0; visibility:hidden; }}
        }}
        .shiva-startup-splash {{
            position:fixed !important;
            inset:0 !important;
            width:100vw !important;
            height:100dvh !important;
            z-index:2147483647 !important;
            background:#050b58 url("data:image/webp;base64,{SPLASH_WEBP_BASE64}") center center / contain no-repeat !important;
            pointer-events:none !important;
            opacity:1;
            visibility:visible;
            animation:shivaSplashExit 2.5s ease-out forwards;
        }}
        @media (max-width:600px) {{
            .shiva-startup-splash {{
                background-size:cover !important;
                background-position:center top !important;
            }}
        }}
        </style>
        <div class="shiva-startup-splash" aria-label="Shiva Intelligence loading screen"></div>
        """,
        unsafe_allow_html=True,
    )

# shiva_app_v2 still owns the main application renderer and currently contains
# a legacy set_page_config call. Suppress only that duplicate call while it runs.
_original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
try:
    run()
finally:
    st.set_page_config = _original_set_page_config

# Run the branding suppression after the app renders so Community Cloud chrome
# inserted late in the DOM is removed too.
hide_streamlit_branding()
