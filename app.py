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
from joel_smyth_ppr import enrich_rankings_with_joel_ppr, render_joel_ppr_panel
from mobile_bottom_nav_fix import apply_mobile_bottom_nav_fix
from mock_draft_players_espn import render_mock_draft_room_v2 as render_espn_players_available
from streamlit_branding_fix import hide_streamlit_branding

# Keep the existing app shell and mock-draft engine. Only replace the
# Players Available presentation layer used by the Draft Coach mock room.
shiva_app_v3.render_mock_draft_room_v2 = render_espn_players_available

# Inject Joel Smyth's 2026 FULL-PPR information into the app's existing ranking
# dataframe so Player Profiles, Ask Shiva, Mock Draft and Draft Coach can all
# consume the analyst fields without replacing the app's verified base data.
_original_load_rankings = shiva_app_v3.load_rankings


def _load_rankings_with_joel_ppr():
    return enrich_rankings_with_joel_ppr(_original_load_rankings())


shiva_app_v3.load_rankings = _load_rankings_with_joel_ppr

# Add a dedicated Joel PPR intelligence panel to Draft Coach while preserving
# every existing Draft Coach feature and live-draft behavior.
_original_draft_coach = shiva_app_v3._draft_coach


def _draft_coach_with_joel_ppr(rankings, weekly):
    _original_draft_coach(rankings, weekly)
    render_joel_ppr_panel(rankings, weekly, shiva_app_v3._player_rows)


shiva_app_v3._draft_coach = _draft_coach_with_joel_ppr
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

# Apply last so this targeted mobile override wins over older nav CSS.
apply_mobile_bottom_nav_fix()
hide_streamlit_branding()
