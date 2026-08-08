from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st


HOME_CSS = r"""
<style>
:root{
  --shiva-bg:#05080b;
  --shiva-panel:#09131c;
  --shiva-panel-2:#0d1822;
  --shiva-line:#193248;
  --shiva-neon:#d8ff00;
  --shiva-green:#3cff51;
  --shiva-blue:#00a8ff;
  --shiva-cyan:#27d9ff;
  --shiva-purple:#a855f7;
  --shiva-orange:#ff9f0a;
  --shiva-red:#ff375f;
  --shiva-text:#f8fbff;
  --shiva-muted:#a6b3bf;
}
html,body,.stApp{background:radial-gradient(circle at 50% -10%,#07162a 0,#05080b 34%,#05080b 100%)!important;color:var(--shiva-text)!important}
.block-container{max-width:520px!important;padding:12px 12px 92px!important}
.shiva-mobile-head{display:grid;grid-template-columns:40px minmax(0,1fr) 74px;align-items:center;gap:8px;margin:1px 0 14px}
.shiva-head-title{text-align:center;font-size:20px;font-weight:1000;letter-spacing:.03em;color:#fff}
.shiva-head-sub{text-align:center;color:#d9e5ee;font-size:12px;margin-top:2px}.shiva-head-icon{font-size:20px;color:#fff;text-align:center}
.home-brand{color:var(--shiva-neon);font-size:16px;font-style:italic;font-weight:1000;letter-spacing:.12em;margin:10px 0 3px}.home-sub{color:#fff;font-size:13px;font-weight:800;margin-bottom:13px}
.home-grid-label{color:#8795a2;font-size:10px;font-weight:1000;letter-spacing:.12em;text-transform:uppercase;margin:10px 0 8px}
.home-tile button{min-height:112px!important;border-radius:14px!important;border:1px solid #28435a!important;background:linear-gradient(145deg,#0d1a24,#081018)!important;box-shadow:0 9px 24px rgba(0,0,0,.28)!important;padding:10px 5px!important}
.home-tile button p{white-space:pre-line!important;font-size:13px!important;line-height:1.18!important;font-weight:1000!important;color:#fff!important}.home-tile button p::first-line{font-size:31px!important;line-height:1.35!important}
.st-key-home_board button{border-color:#8d6600!important;box-shadow:inset 0 0 34px rgba(255,171,0,.08)!important}.st-key-home_mock button{border-color:#5d2d91!important;box-shadow:inset 0 0 34px rgba(168,85,247,.09)!important}.st-key-home_profiles button{border-color:#006c9c!important;box-shadow:inset 0 0 34px rgba(0,168,255,.1)!important}.st-key-home_team button{border-color:#2f6b1f!important;box-shadow:inset 0 0 34px rgba(60,255,81,.08)!important}.st-key-home_sleepers button{border-color:#795400!important}.st-key-home_cheats button{border-color:#7c1730!important}
.st-key-home_ask button{min-height:76px!important;border-radius:14px!important;background:linear-gradient(135deg,#073a68,#091d36)!important;border:1px solid #0b6eaa!important;text-align:left!important;padding:12px 18px!important;box-shadow:0 9px 24px rgba(0,104,180,.18)!important}.st-key-home_ask button p{white-space:pre-line!important;font-size:13px!important;line-height:1.35!important}.st-key-home_ask button p::first-line{font-size:17px!important;font-weight:1000!important}
.league-card{margin-top:12px;background:linear-gradient(145deg,#07141f,#081019);border:1px solid #17334a;border-radius:14px;padding:14px}.league-kicker{color:#8e9aa7;font-size:10px;text-transform:uppercase}.league-name{font-size:17px;font-weight:1000;margin-top:5px}.league-meta{font-size:12px;color:#d1d9e1;margin-top:3px}
.st-key-home_league button{background:linear-gradient(135deg,#7a00d9,#9c00ff)!important;border-color:#b34aff!important;color:white!important}
.st-key-shiva_bottom_nav{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:min(520px,100vw)!important;z-index:9999!important;background:rgba(4,8,12,.97)!important;border-top:1px solid #173148!important;padding:5px 8px 8px!important;backdrop-filter:blur(18px)}
.st-key-shiva_bottom_nav [data-testid="stHorizontalBlock"]{gap:2px!important}.st-key-shiva_bottom_nav button{min-height:54px!important;border:0!important;background:transparent!important;box-shadow:none!important;border-radius:9px!important;padding:2px!important}.st-key-shiva_bottom_nav button p{white-space:pre-line!important;font-size:9px!important;line-height:1.1!important;color:#d7e0e8!important}.st-key-shiva_bottom_nav button p::first-line{font-size:20px!important;line-height:1.25!important}.st-key-shiva_bottom_nav button[kind="primary"] p{color:var(--shiva-neon)!important}.st-key-shiva_bottom_nav button[kind="primary"]{background:rgba(216,255,0,.06)!important}
@media(max-width:360px){.home-tile button{min-height:102px!important}.home-tile button p{font-size:11px!important}.home-tile button p::first-line{font-size:27px!important}}
</style>
"""


def apply_mobile_shell_css() -> None:
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def _go(page: str, mock_view: str | None = None) -> None:
    st.session_state.page = page
    if mock_view:
        st.session_state["mock_room_view"] = mock_view
    st.rerun()


def render_mobile_header(title: str = "SHIVA INTELLIGENCE", subtitle: str = "Your Draft Command Center", back_page: str | None = None) -> None:
    left = "‹" if back_page else "☰"
    cols = st.columns([0.7, 4.2, 1.2])
    with cols[0]:
        if st.button(left, key=f"mobile_head_left_{title}", use_container_width=True):
            _go(back_page or "Home")
    with cols[1]:
        st.markdown(f'<div class="shiva-head-title">{html.escape(title)}</div><div class="shiva-head-sub">{html.escape(subtitle)}</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="shiva-head-icon">↗ &nbsp; ♢</div>', unsafe_allow_html=True)


def render_home(rankings: pd.DataFrame, draft_state: dict[str, Any] | None = None) -> None:
    apply_mobile_shell_css()
    render_mobile_header()
    st.markdown('<div class="home-brand">SHIVA INTELLIGENCE</div><div class="home-sub">Your Draft Command Center</div>', unsafe_allow_html=True)

    row1 = st.columns(3, gap="small")
    with row1[0]:
        with st.container(key="home_board"):
            if st.button("🏆\nDRAFT BOARD\n2026 Rankings", key="home_board_btn", use_container_width=True):
                _go("Mock Draft", "BOARD")
    with row1[1]:
        with st.container(key="home_mock"):
            if st.button("👥\nMOCK DRAFT\nPractice & Plan", key="home_mock_btn", use_container_width=True):
                _go("Mock Draft", "PLAYERS")
    with row1[2]:
        with st.container(key="home_profiles"):
            if st.button("👤\nPLAYER PROFILES\nStats & Trends", key="home_profiles_btn", use_container_width=True):
                _go("Player Profiles")

    row2 = st.columns(3, gap="small")
    with row2[0]:
        with st.container(key="home_team"):
            if st.button("⭐\nMY TEAM HQ\nRoster & Lineup", key="home_team_btn", use_container_width=True):
                _go("Draft Coach")
    with row2[1]:
        with st.container(key="home_sleepers"):
            if st.button("🎭\nSLEEPERS\nHidden Gems", key="home_sleepers_btn", use_container_width=True):
                st.session_state["shiva_prompt_dynamic"] = "Show me the best current sleeper values supported by the loaded 2026 ADP and historical data."
                _go("Shiva Intelligence")
    with row2[2]:
        with st.container(key="home_cheats"):
            if st.button("📋\nCHEAT SHEETS\nKey Rankings", key="home_cheats_btn", use_container_width=True):
                _go("Draft Coach")

    with st.container(key="home_ask"):
        if st.button("🤖  ASK SHIVA GPT\nAsk questions, get advice, win your league.   →", key="home_ask_btn", use_container_width=True):
            _go("Shiva Intelligence")

    st.markdown('<div class="league-card"><div class="league-kicker">MY LEAGUE</div><div class="league-name">Shiva Champion League</div><div class="league-meta">10-Team PPR</div></div>', unsafe_allow_html=True)
    with st.container(key="home_league"):
        if st.button("VIEW LEAGUE", key="home_league_btn", use_container_width=True):
            _go("Shiva League History")


def render_bottom_navigation(current_page: str) -> None:
    apply_mobile_shell_css()
    with st.container(key="shiva_bottom_nav"):
        cols = st.columns(5)
        items = [
            ("Home", "⌂\nHome", None),
            ("Mock Draft", "◉\nDraft", "PLAYERS"),
            ("Player Profiles", "♙\nPlayers", None),
            ("Draft Coach", "♧\nTeam", None),
            ("Shiva League History", "•••\nMore", None),
        ]
        for col, (page, label, mock_view) in zip(cols, items):
            with col:
                active = current_page == page or (page == "Home" and current_page == "Home")
                if st.button(label, key=f"bottom_{page}_{mock_view or 'main'}", use_container_width=True, type="primary" if active else "secondary"):
                    _go(page, mock_view)
