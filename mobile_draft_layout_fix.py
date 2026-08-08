from __future__ import annotations

import streamlit as st


def apply_mobile_draft_layout_fix() -> None:
    """Final mobile-only layout correction for Draft Coach.

    Keeps all existing Streamlit buttons/callbacks/state intact; this module only
    prevents Streamlit's narrow-screen column stacking from destroying the draft
    room and removes duplicate bottom-nav label rendering.
    """
    st.markdown(
        r"""
<style>
@media (max-width: 520px) {
  /* Draft room header: back | title | settings, always one compact row. */
  div[data-testid="stHorizontalBlock"]:has(.mock-title) {
    display: grid !important;
    grid-template-columns: 38px minmax(0,1fr) 38px !important;
    gap: 8px !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 0 8px !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.mock-title) > div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
    padding: 0 !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.mock-title) button {
    width: 38px !important;
    height: 38px !important;
    min-height: 38px !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    font-size: 22px !important;
  }
  .mock-title { font-size: 22px !important; line-height: 1.05 !important; }
  .mock-sub { font-size: 11px !important; line-height: 1.2 !important; margin-top: 4px !important; }

  /* Players / Queue / Draft Board / Roster: one ESPN-style tab row. */
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) {
    display: grid !important;
    grid-template-columns: repeat(4,minmax(0,1fr)) !important;
    gap: 0 !important;
    align-items: stretch !important;
    width: 100% !important;
    border-bottom: 1px solid #31363b !important;
    margin: 6px 0 10px !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) > div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
    padding: 0 !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button {
    width: 100% !important;
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 2px !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button p,
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button p * {
    font-size: 9px !important;
    line-height: 11px !important;
    font-weight: 950 !important;
    white-space: normal !important;
    text-align: center !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button[kind="primary"] {
    border-bottom: 3px solid #dfff00 !important;
  }

  /* Player-list controls stay in a compact four-column toolbar. */
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_reset_filters) {
    display: grid !important;
    grid-template-columns: minmax(0,1.25fr) minmax(0,1.15fr) 62px 42px !important;
    gap: 7px !important;
    align-items: center !important;
    width: 100% !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_reset_filters) > div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
    padding: 0 !important;
  }
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] > div,
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) button {
    min-height: 42px !important;
    height: 42px !important;
  }
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] > div {
    border-radius: 12px !important;
    padding: 0 10px !important;
  }
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] span,
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] div,
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) button p,
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) button p * {
    font-size: 12px !important;
  }

  /* Never let any mock-draft player row columns stack vertically. */
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: 9% 39% 9% 13% 15% 15% !important;
    gap: 0 !important;
    align-items: center !important;
  }
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
  }

  /* Bottom nav: exactly one icon + one label. Hide original emoji/text nodes. */
  .st-key-app_bottom_nav {
    min-height: 72px !important;
    height: auto !important;
    padding: 4px 4px max(5px, env(safe-area-inset-bottom)) !important;
  }
  .st-key-app_bottom_nav button {
    height: 58px !important;
    min-height: 58px !important;
  }
  .st-key-app_bottom_nav button p {
    font-size: 0 !important;
    color: transparent !important;
    overflow: visible !important;
  }
  .st-key-app_bottom_nav button p > *,
  .st-key-app_bottom_nav button [data-testid="stMarkdownContainer"] *,
  .st-key-app_bottom_nav button span {
    font-size: 0 !important;
    color: transparent !important;
    line-height: 0 !important;
  }
  .st-key-app_bottom_nav button p::before {
    font-size: 23px !important;
    line-height: 25px !important;
    color: #b7bec5 !important;
  }
  .st-key-app_bottom_nav button p::after {
    font-size: 9px !important;
    line-height: 11px !important;
    color: #b7bec5 !important;
  }
  .st-key-app_bottom_nav button[kind="primary"] p::before,
  .st-key-app_bottom_nav button[kind="primary"] p::after {
    color: #dfff00 !important;
  }

  /* Make room for nav + live clock without covering player controls. */
  [data-testid="stAppViewBlockContainer"], .block-container {
    padding-bottom: 150px !important;
  }
  .draft-status {
    bottom: 72px !important;
    width: calc(100vw - 16px) !important;
    max-width: 504px !important;
  }
}

@media (max-width: 390px) {
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button p,
  div[data-testid="stHorizontalBlock"]:has(.st-key-mock_tab_PLAYERS_AVAILABLE) button p * {
    font-size: 7.5px !important;
    line-height: 9px !important;
  }
  .mock-title { font-size: 20px !important; }
}
</style>
""",
        unsafe_allow_html=True,
    )
