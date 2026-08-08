import time
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

st.set_page_config(
    page_title="Shiva Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

import shiva_app_v3
from mock_draft_players_espn import render_mock_draft_room_v2 as render_espn_players_available
from streamlit_branding_fix import hide_streamlit_branding

# Keep the existing app shell and mock-draft engine. Only replace the
# Players Available presentation layer used by the Draft Coach mock room.
shiva_app_v3.render_mock_draft_room_v2 = render_espn_players_available
run = shiva_app_v3.run

hide_streamlit_branding()

APP_ROOT = Path(__file__).resolve().parent
SPLASH_PATH = APP_ROOT / "assets" / "shiva_splash.jpg"


def valid_local_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


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
    if valid_local_image(SPLASH_PATH):
        try:
            st.image(str(SPLASH_PATH), use_container_width=True)
            time.sleep(2.5)
        except (UnidentifiedImageError, OSError, ValueError):
            pass

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
