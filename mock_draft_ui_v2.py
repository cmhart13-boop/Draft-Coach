from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from mock_draft_engine import (
    DEFAULT_ROSTER,
    advance_cpu_until_user,
    build_player_pool,
    full_draft_context,
    get_player,
    initialize_draft,
    make_pick,
    queue_add,
    queue_remove,
    recommendation_groups,
    roster_slots,
    start_draft,
    team_by_id,
    undo_last_pick,
)
from player_profile import open_player_profile, player_profile_href

STATE_KEY = "mock_draft_state_v2"
POOL_KEY = "mock_draft_original_pool_v2"

POS_STYLE = {
    "QB": ("#d9252a", "#7a1115"),
    "RB": ("#ff8a00", "#9a4300"),
    "WR": ("#1598f2", "#075b9a"),
    "TE": ("#48b72c", "#236d16"),
    "FLEX": ("#9a43d5", "#55207e"),
    "K": ("#68727c", "#353b41"),
    "D/ST": ("#995600", "#563000"),
}


def _css() -> None:
    st.markdown("""
<style>
.mock2-shell{background:#05090d;color:#fff}.mock2-title{text-align:center;font-size:27px;font-weight:1000;margin:4px 0 1px}.mock2-sub{text-align:center;font-size:14px;color:#d8dde2;margin-bottom:10px}.mock2-tabs{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;border-bottom:1px solid #24303a;margin:4px 0 12px}.mock2-tab{padding:10px 3px;text-align:center;font-size:12px;font-weight:900;color:#cfd5da}.mock2-tab.active{color:#dcff00;border-bottom:3px solid #dcff00}.mock2-filterbar{display:grid;grid-template-columns:1.55fr 1fr;gap:8px;margin:7px 0}.mock2-poschips{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin:8px 0 12px}.mock2-chip{border-radius:8px;text-align:center;padding:7px 2px;font-size:11px;font-weight:1000;color:#fff}.mock2-head{display:grid;grid-template-columns:38px minmax(0,1fr) 46px 44px 52px;gap:5px;padding:7px 9px;color:#aeb7bf;font-size:10px;font-weight:900;border-top:1px solid #26313a;border-bottom:1px solid #26313a}.mock2-player-row{display:grid;grid-template-columns:38px minmax(0,1fr) 46px 44px 52px;gap:5px;align-items:center;border-radius:9px;padding:8px 8px;margin:4px 0;border:1px solid rgba(255,255,255,.13);box-shadow:inset 0 1px rgba(255,255,255,.05)}.mock2-rank{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.22);font-size:13px;font-weight:1000}.mock2-name{font-size:15px;font-weight:1000;color:#fff!important;text-decoration:none!important}.mock2-meta{font-size:10px;color:#e1e6ea;margin-top:2px}.mock2-cell{font-size:12px;font-weight:900;text-align:center}.mock2-adp{font-size:12px;font-weight:1000;text-align:right}.mock2-onclock{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;background:#071018;border:1px solid #263b4e;border-radius:12px;padding:10px;margin:10px 0}.mock2-clock-label{font-size:12px;color:#dbe1e6}.mock2-clock-pick{font-size:16px;color:#dcff00;font-weight:1000}.mock2-timer{background:#dcff00;color:#081006;border-radius:9px;padding:8px 12px;font-size:18px;font-weight:1000}.mock2-shiva{background:linear-gradient(135deg,#08334e,#061a2a);border:1px solid #1272aa;border-radius:14px;padding:12px;margin:10px 0}.mock2-shiva-title{font-size:13px;color:#6ed4ff;font-weight:1000}.mock2-shiva-answer{font-size:20px;font-weight:1000;color:#dcff00;margin-top:7px}.mock2-board-wrap{overflow-x:auto;border:1px solid #25313a;border-radius:12px;background:#03070a}.mock2-board{display:grid;min-width:920px;gap:3px;padding:5px}.mock2-teamhead{background:#071018;border:1px solid #26313a;border-radius:6px;padding:7px 3px;font-size:10px;font-weight:1000;text-align:center}.mock2-boardcell{min-height:58px;border-radius:6px;padding:5px;border:1px solid rgba(255,255,255,.14)}.mock2-pickno{font-size:8px;color:#fff9}.mock2-boardname{font-size:9px;font-weight:1000;line-height:1.1;color:#fff!important;text-decoration:none!important;display:block;margin-top:3px}.mock2-boardpos{font-size:8px;color:#fffbd;margin-top:3px}.mock2-section{font-size:17px;font-weight:1000;margin:14px 0 8px}.mock2-roster-row{display:grid;grid-template-columns:45px 1fr;gap:8px;padding:10px;border-bottom:1px solid #24303a}.mock2-slot{color:#dcff00;font-weight:1000;font-size:12px}.mock2-roster-player{font-size:14px;font-weight:900;color:#fff!important;text-decoration:none!important}
@media(max-width:430px){.mock2-title{font-size:25px}.mock2-poschips{grid-template-columns:repeat(4,1fr)}.mock2-player-row{grid-template-columns:34px minmax(0,1fr) 42px 39px 47px;padding:8px 6px}.mock2-head{grid-template-columns:34px minmax(0,1fr) 42px 39px 47px;padding:7px 6px}.mock2-name{font-size:14px}}
</style>
""", unsafe_allow_html=True)


def _state() -> dict[str, Any] | None:
    return st.session_state.get(STATE_KEY)


def _position_color(pos: str) -> tuple[str, str]:
    return POS_STYLE.get(str(pos).upper(), ("#52606c", "#29313a"))


def _player_href(name: str) -> str:
    return html.escape(player_profile_href(name), quote=True)


def _run_shiva(state: dict[str, Any], history: pd.DataFrame, roi: pd.DataFrame, rankings: pd.DataFrame, weekly: pd.DataFrame, ask_shiva_func, api_key: str | None) -> None:
    if not api_key:
        st.warning("Ask Shiva requires the configured OpenAI API key.")
        return
    with st.spinner("Shiva is reading your roster and the live board..."):
        st.session_state["mock2_shiva_answer"] = ask_shiva_func(
            question="Who should I pick right now?",
            history=history,
            roi=roi,
            rankings=rankings,
            weekly=weekly,
            api_key=api_key,
            draft_context=full_draft_context(state),
        )
        st.session_state["mock2_shiva_pick"] = int(state["currentOverallPick"])


def _render_player_list(state: dict[str, Any], history: pd.DataFrame, roi: pd.DataFrame, rankings: pd.DataFrame, weekly: pd.DataFrame, ask_shiva_func, api_key: str | None) -> None:
    search = st.text_input("Search players", placeholder="⌕  Search players...", key="mock2_search", label_visibility="collapsed")
    positions = ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"]
    pos = st.selectbox("Position", positions, index=0, key="mock2_pos", label_visibility="collapsed")
    chips = []
    for p in ["QB", "RB", "WR", "TE", "FLEX", "K", "D/ST"]:
        c1, c2 = _position_color(p)
        label = "DEF" if p == "D/ST" else p
        chips.append(f'<div class="mock2-chip" style="background:linear-gradient(135deg,{c1},{c2})">{label}</div>')
    st.markdown('<div class="mock2-poschips">'+''.join(chips)+'</div>', unsafe_allow_html=True)

    pool = list(state.get("availablePlayers") or [])
    if search.strip():
        pool = [p for p in pool if search.strip().casefold() in str(p.get("name", "")).casefold()]
    if pos != "ALL":
        pool = [p for p in pool if p.get("position") == pos]
    pool = sorted(pool, key=lambda p: (p.get("rank", 9999), p.get("adp", 9999), p.get("name", "")))[:100]

    st.markdown('<div class="mock2-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div style="text-align:right">ADP</div></div>', unsafe_allow_html=True)
    on_clock = state.get("status") == "active" and not state.get("paused") and state.get("currentTeam") == state.get("userTeamId")
    for p in pool:
        c1, c2 = _position_color(str(p.get("position")))
        name = html.escape(str(p.get("name")))
        team = html.escape(str(p.get("team") or "—"))
        adp = float(p.get("adp") or 0)
        rank = int(p.get("rank") or 0)
        st.markdown(
            f'<div class="mock2-player-row" style="background:linear-gradient(90deg,{c2},{c1})"><div class="mock2-rank">{rank}</div><div><a class="mock2-name" href="{_player_href(str(p.get("name")))}" target="_self">{name}</a><div class="mock2-meta">Tap name for player profile</div></div><div class="mock2-cell">{html.escape(str(p.get("position")))}</div><div class="mock2-cell">{team}</div><div class="mock2-adp">{adp:.1f}</div></div>',
            unsafe_allow_html=True,
        )
        cqueue, cdraft = st.columns([1, 1])
        with cqueue:
            if st.button("＋ Queue", key=f"mock2_q_{p['id']}", use_container_width=True):
                queue_add(state, p["id"]); st.rerun()
        with cdraft:
            if st.button("DRAFT", key=f"mock2_d_{p['id']}", use_container_width=True, disabled=not on_clock, type="primary"):
                make_pick(state, p["id"], source="user")
                advance_cpu_until_user(state)
                st.session_state.pop("mock2_shiva_answer", None)
                st.rerun()

    if on_clock:
        st.markdown(f'<div class="mock2-onclock"><div><div class="mock2-clock-label">You\'re on the clock!</div><div class="mock2-clock-pick">Pick {state.get("currentRound")}.{((int(state.get("currentOverallPick",1))-1)%int(state["settings"]["teamsCount"]))+1:02d}</div></div><div class="mock2-timer">LIVE</div></div>', unsafe_allow_html=True)
        if st.button("🤖 WHO SHOULD I PICK?", key="mock2_shiva_btn", use_container_width=True, type="primary"):
            _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    ans = st.session_state.get("mock2_shiva_answer")
    if ans and st.session_state.get("mock2_shiva_pick") == int(state.get("currentOverallPick", 0)):
        st.markdown(f'<div class="mock2-shiva"><div class="mock2-shiva-title">ASK SHIVA GPT</div><div class="mock2-shiva-answer">{html.escape(str(ans.get("answer") or ""))}</div><div style="font-size:13px;color:#d4e0e8;margin-top:6px">{html.escape(str(ans.get("why") or ""))}</div></div>', unsafe_allow_html=True)


def _render_board(state: dict[str, Any]) -> None:
    teams_count = int(state["settings"]["teamsCount"])
    rounds = int(state["settings"]["rounds"])
    cols_css = f"repeat({teams_count}, 88px)"
    picks = {int(p["pickNumber"]): p for p in state.get("picks", [])}
    parts = [f'<div class="mock2-board" style="grid-template-columns:{cols_css}">']
    for t in state["teams"]:
        parts.append(f'<div class="mock2-teamhead">{html.escape(t["name"])}</div>')
    for rnd in range(1, rounds + 1):
        for team_number in range(1, teams_count + 1):
            overall = (rnd - 1) * teams_count + (team_number if rnd % 2 else teams_count - team_number + 1)
            pick = picks.get(overall)
            if pick:
                c1, c2 = _position_color(pick.get("position"))
                name = html.escape(str(pick.get("playerName")))
                href = _player_href(str(pick.get("playerName")))
                body = f'<div class="mock2-boardcell" style="background:linear-gradient(145deg,{c1},{c2})"><div class="mock2-pickno">{overall}.</div><a class="mock2-boardname" href="{href}" target="_self">{name}</a><div class="mock2-boardpos">{html.escape(str(pick.get("position")))}</div></div>'
            else:
                body = f'<div class="mock2-boardcell" style="background:#081018"><div class="mock2-pickno">{overall}.</div></div>'
            parts.append(body)
    parts.append('</div>')
    st.markdown('<div class="mock2-board-wrap">'+''.join(parts)+'</div>', unsafe_allow_html=True)


def _render_queue(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock2-section">QUEUE</div>', unsafe_allow_html=True)
    if not state.get("queue"):
        st.info("Your draft queue is empty.")
    for pid in list(state.get("queue") or []):
        p = get_player(state, pid)
        if not p:
            continue
        c1, c2 = _position_color(p.get("position"))
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(f'<div class="mock2-player-row" style="grid-template-columns:1fr;background:linear-gradient(90deg,{c2},{c1})"><a class="mock2-name" href="{_player_href(p["name"])}" target="_self">{html.escape(p["name"])}</a></div>', unsafe_allow_html=True)
        with cols[1]:
            if st.button("×", key=f"mock2_qremove_{pid}", use_container_width=True):
                queue_remove(state, pid); st.rerun()


def _render_team(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock2-section">MY TEAM</div>', unsafe_allow_html=True)
    for slot, player in roster_slots(state, state["userTeamId"]):
        if player:
            name_html = f'<a class="mock2-roster-player" href="{_player_href(player["name"])}" target="_self">{html.escape(player["name"])}</a> <span style="color:#9eabb5">· {html.escape(player["position"])}</span>'
        else:
            name_html = '<span style="color:#75808a">—</span>'
        st.markdown(f'<div class="mock2-roster-row"><div class="mock2-slot">{html.escape(slot)}</div><div>{name_html}</div></div>', unsafe_allow_html=True)


def render_mock_draft_room_v2(rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, roi: pd.DataFrame, db_path, ask_shiva_func, api_key: str | None) -> None:
    _css()
    st.markdown('<div class="mock2-title">MOCK DRAFT</div>', unsafe_allow_html=True)
    st.markdown('<div class="mock2-sub">10-Team PPR • Snake Draft</div>', unsafe_allow_html=True)

    if POOL_KEY not in st.session_state:
        st.session_state[POOL_KEY] = build_player_pool(rankings, weekly)
    pool = st.session_state[POOL_KEY]
    if not pool:
        st.error("No verified 2026 ranking rows are available for the mock draft.")
        return

    state = _state()
    if state is None:
        st.markdown('<div class="mock2-section">CREATE MOCK DRAFT</div>', unsafe_allow_html=True)
        with st.form("mock2_setup"):
            c1, c2 = st.columns(2)
            with c1:
                teams = st.selectbox("Teams", [8, 10, 12], index=1)
            with c2:
                slot = st.number_input("Draft Position", 1, int(teams), min(4, int(teams)), 1)
            c3, c4 = st.columns(2)
            with c3:
                scoring = st.selectbox("Scoring", ["PPR", "Half PPR", "Standard"], index=0)
            with c4:
                rounds = st.number_input("Rounds", 10, 20, sum(DEFAULT_ROSTER.values()), 1)
            if st.form_submit_button("START MOCK DRAFT", use_container_width=True, type="primary"):
                state = initialize_draft(pool, int(teams), int(slot), scoring, DEFAULT_ROSTER.copy(), int(rounds), 90)
                start_draft(state)
                advance_cpu_until_user(state)
                st.session_state[STATE_KEY] = state
                st.rerun()
        return

    if state.get("status") == "active" and not state.get("paused") and state.get("currentTeam") != state.get("userTeamId"):
        advance_cpu_until_user(state)
    st.session_state[STATE_KEY] = state

    tabs = ["PLAYERS", "BOARD", "QUEUE", "TEAM"]
    if "mock2_tab" not in st.session_state:
        st.session_state["mock2_tab"] = "PLAYERS"
    cols = st.columns(4)
    for col, tab in zip(cols, tabs):
        with col:
            if st.button(tab, key=f"mock2_tab_{tab}", use_container_width=True, type="primary" if st.session_state["mock2_tab"] == tab else "secondary"):
                st.session_state["mock2_tab"] = tab
                st.rerun()

    ctrl1, ctrl2 = st.columns(2)
    with ctrl1:
        if st.button("↶ UNDO PICK", key="mock2_undo", use_container_width=True, disabled=not state.get("picks")):
            undo_last_pick(state); st.rerun()
    with ctrl2:
        if st.button("HOME", key="mock2_home", use_container_width=True):
            st.session_state["page"] = "Home"; st.rerun()

    tab = st.session_state["mock2_tab"]
    if tab == "PLAYERS":
        _render_player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    elif tab == "BOARD":
        _render_board(state)
    elif tab == "QUEUE":
        _render_queue(state)
    else:
        _render_team(state)
