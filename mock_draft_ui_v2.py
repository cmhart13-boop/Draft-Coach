from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote

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
    roster_slots,
    start_draft,
    undo_last_pick,
)
from player_profile import player_profile_href

STATE_KEY = "mock_draft_state_v2"
POOL_KEY = "mock_draft_original_pool_v2"

POS_STYLE = {
    "QB": ("#d5232b", "#8a1017"),
    "RB": ("#ff7a00", "#b34400"),
    "WR": ("#138dd8", "#075688"),
    "TE": ("#42a92d", "#205f17"),
    "FLEX": ("#9341d2", "#58217f"),
    "K": ("#58636e", "#303941"),
    "D/ST": ("#8d5008", "#52300a"),
}

def _css() -> None:
    st.markdown("""
<style>
.mock2-title{text-align:center;font-size:26px;font-weight:1000;margin:2px 0 0;letter-spacing:.01em}
.mock2-sub{text-align:center;font-size:14px;color:#fff;margin:1px 0 8px}
.mock2-tabs{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-bottom:1px solid #23303a;margin:4px 0 12px}
.mock2-tab{padding:10px 2px;text-align:center;font-size:12px;font-weight:900;color:#fff;text-decoration:none!important}
.mock2-tab.active{color:#dfff00;border-bottom:3px solid #dfff00}
.mock2-filters{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,.9fr) minmax(0,.9fr) 44px;gap:8px;margin:8px 0}
.mock2-poschips{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:7px;margin:10px 0 10px}
.mock2-chip{border-radius:7px;text-align:center;padding:8px 1px;font-size:12px;font-weight:1000;color:#fff}
.mock2-head{display:grid;grid-template-columns:34px minmax(0,1fr) 42px 42px 45px 34px 44px;gap:4px;padding:6px 7px;color:#b7c0c8;font-size:9px;font-weight:900;background:#0a1117;border-radius:8px 8px 0 0}
.mock2-player-row{display:grid;grid-template-columns:34px minmax(0,1fr) 42px 42px 45px 34px 44px;gap:4px;align-items:center;border-radius:7px;padding:7px 7px;margin:3px 0;border:1px solid rgba(255,255,255,.11);box-shadow:inset 0 1px rgba(255,255,255,.04)}
.mock2-rank{width:27px;height:27px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.18);font-size:12px;font-weight:1000}
.mock2-name{font-size:13px;font-weight:1000;color:#fff!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}
.mock2-cell{font-size:11px;font-weight:900;text-align:center;white-space:nowrap}
.mock2-adp{font-size:11px;font-weight:1000;text-align:right}
.mock2-q,.mock2-draft{display:flex;align-items:center;justify-content:center;text-decoration:none!important;color:#fff!important;font-size:11px;font-weight:1000;border-radius:6px;height:28px}
.mock2-q{background:rgba(0,0,0,.22);border:1px solid rgba(255,255,255,.24)}
.mock2-q.on{background:#dfff00;color:#071006!important;border-color:#dfff00}
.mock2-draft{background:#071018;border:1px solid rgba(255,255,255,.28)}
.mock2-draft.on{background:#dfff00;color:#071006!important;border-color:#dfff00}
.mock2-onclock{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;background:#071018;border:1px solid #263b4e;border-radius:11px;padding:10px;margin:10px 0}
.mock2-clock-label{font-size:12px;color:#fff}.mock2-clock-pick{font-size:16px;color:#dfff00;font-weight:1000}
.mock2-timer{background:#dfff00;color:#081006;border-radius:7px;padding:8px 11px;font-size:17px;font-weight:1000}
.mock2-board-wrap{border:1px solid #25313a;border-radius:10px;background:#020609;padding:4px;overflow:hidden}
.mock2-board{display:grid;gap:2px;width:100%}
.mock2-teamhead{background:#071018;border:1px solid #26313a;border-radius:4px;padding:5px 1px;font-size:7px;font-weight:1000;text-align:center;overflow:hidden}
.mock2-boardcell{min-height:53px;border-radius:4px;padding:3px 2px;border:1px solid rgba(255,255,255,.12);overflow:hidden}
.mock2-pickno{font-size:7px;color:#fff9}.mock2-boardname{font-size:7px;font-weight:1000;line-height:1.12;color:#fff!important;text-decoration:none!important;display:block;margin-top:2px;overflow-wrap:anywhere}
.mock2-boardpos{font-size:7px;color:#fff;margin-top:2px;text-align:center;font-weight:900}
.mock2-section{font-size:17px;font-weight:1000;margin:13px 0 8px}
.mock2-roster-row{display:grid;grid-template-columns:45px 1fr;gap:8px;padding:10px;border-bottom:1px solid #24303a}
.mock2-slot{color:#dfff00;font-weight:1000;font-size:12px}.mock2-roster-player{font-size:14px;font-weight:900;color:#fff!important;text-decoration:none!important}
.mock2-shiva{background:linear-gradient(135deg,#08334e,#061a2a);border:1px solid #1272aa;border-radius:13px;padding:12px;margin:10px 0}
.mock2-shiva-title{font-size:12px;color:#6ed4ff;font-weight:1000}.mock2-shiva-answer{font-size:19px;font-weight:1000;color:#dfff00;margin-top:6px}
@media(max-width:430px){
  .mock2-title{font-size:24px}.mock2-poschips{gap:4px}.mock2-chip{padding:7px 1px;font-size:10px}
  .mock2-head,.mock2-player-row{grid-template-columns:31px minmax(0,1fr) 34px 34px 38px 31px 39px;gap:2px;padding-left:4px;padding-right:4px}
  .mock2-name{font-size:12px}.mock2-cell,.mock2-adp{font-size:9px}.mock2-rank{width:24px;height:24px;font-size:11px}.mock2-q,.mock2-draft{font-size:9px;height:25px}
  .mock2-boardcell{min-height:48px}.mock2-boardname{font-size:6.5px}.mock2-teamhead{font-size:6.5px}
}
</style>
""", unsafe_allow_html=True)

def _state() -> dict[str, Any] | None:
    return st.session_state.get(STATE_KEY)

def _position_color(pos: str) -> tuple[str, str]:
    return POS_STYLE.get(str(pos).upper(), ("#52606c", "#29313a"))

def _player_href(name: str) -> str:
    return html.escape(player_profile_href(name), quote=True)

def _handle_query_actions(state: dict[str, Any]) -> None:
    qid = st.query_params.get("queue")
    did = st.query_params.get("draft")
    if qid:
        pid = str(qid)
        if pid in list(state.get("queue") or []):
            queue_remove(state, pid)
        else:
            queue_add(state, pid)
        del st.query_params["queue"]
        st.rerun()
    if did:
        pid = str(did)
        on_clock = state.get("status") == "active" and not state.get("paused") and state.get("currentTeam") == state.get("userTeamId")
        if on_clock and get_player(state, pid):
            make_pick(state, pid, source="user")
            advance_cpu_until_user(state)
            st.session_state.pop("mock2_shiva_answer", None)
        del st.query_params["draft"]
        st.rerun()

def _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key):
    if not api_key:
        st.warning("Ask Shiva requires the configured OpenAI API key.")
        return
    with st.spinner("Shiva is reading your roster and the live board..."):
        st.session_state["mock2_shiva_answer"] = ask_shiva_func(
            question="Who should I pick right now?",
            history=history, roi=roi, rankings=rankings, weekly=weekly, api_key=api_key,
            draft_context=full_draft_context(state),
        )
        st.session_state["mock2_shiva_pick"] = int(state["currentOverallPick"])

def _render_player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key):
    c1, c2, c3 = st.columns([1.4, .85, .85])
    with c1:
        search = st.text_input("Search players", placeholder="⌕  Search players...", key="mock2_search", label_visibility="collapsed")
    with c2:
        pos = st.selectbox("Position", ["ALL","QB","RB","WR","TE","D/ST","K"], key="mock2_pos", label_visibility="collapsed")
    with c3:
        team_filter = st.selectbox("Team", ["ALL"] + sorted({str(p.get("team")) for p in state.get("availablePlayers",[]) if p.get("team")}), key="mock2_team", label_visibility="collapsed")

    chips=[]
    for p in ["QB","RB","WR","TE","FLEX","K","D/ST"]:
        c1c,c2c=_position_color(p); label="DEF" if p=="D/ST" else p
        chips.append(f'<div class="mock2-chip" style="background:linear-gradient(135deg,{c1c},{c2c})">{label}</div>')
    st.markdown('<div class="mock2-poschips">'+''.join(chips)+'</div>', unsafe_allow_html=True)

    pool=list(state.get("availablePlayers") or [])
    if search.strip():
        pool=[p for p in pool if search.strip().casefold() in str(p.get("name","")).casefold()]
    if pos!="ALL":
        pool=[p for p in pool if p.get("position")==pos]
    if team_filter!="ALL":
        pool=[p for p in pool if str(p.get("team"))==team_filter]
    pool=sorted(pool,key=lambda p:(p.get("rank",9999),p.get("adp",9999),p.get("name","")))[:120]

    st.markdown('<div class="mock2-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div style="text-align:right">ADP</div><div>Q</div><div></div></div>', unsafe_allow_html=True)
    on_clock = state.get("status")=="active" and not state.get("paused") and state.get("currentTeam")==state.get("userTeamId")
    queued=set(state.get("queue") or [])
    for p in pool:
        c1c,c2c=_position_color(str(p.get("position")))
        pid=str(p["id"]); name=html.escape(str(p.get("name"))); team=html.escape(str(p.get("team") or "—"))
        adp=float(p.get("adp") or 0); rank=int(p.get("rank") or 0); pos_txt=html.escape(str(p.get("position") or "—"))
        q_href=f'?page=Mock%20Draft&queue={quote(pid)}'
        q_cls='mock2-q on' if pid in queued else 'mock2-q'
        if on_clock:
            d_href=f'?page=Mock%20Draft&draft={quote(pid)}'; d_html=f'<a class="mock2-draft on" href="{d_href}" target="_self">PICK</a>'
        else:
            d_html='<span class="mock2-draft">PICK</span>'
        st.markdown(
            f'<div class="mock2-player-row" style="background:linear-gradient(90deg,{c2c},{c1c})">'
            f'<div class="mock2-rank">{rank}</div>'
            f'<div><a class="mock2-name" href="{_player_href(str(p.get("name")))}" target="_self">{name}</a></div>'
            f'<div class="mock2-cell">{pos_txt}</div><div class="mock2-cell">{team}</div><div class="mock2-adp">{adp:.1f}</div>'
            f'<a class="{q_cls}" href="{q_href}" target="_self">Q</a>{d_html}</div>',
            unsafe_allow_html=True
        )

    if on_clock:
        pick_num=((int(state.get("currentOverallPick",1))-1)%int(state["settings"]["teamsCount"]))+1
        st.markdown(f'<div class="mock2-onclock"><div><div class="mock2-clock-label">You’re on the clock!</div><div class="mock2-clock-pick">Pick {state.get("currentRound")}.{pick_num:02d}</div></div><div style="font-size:14px;font-weight:900">Team {state.get("userTeamId")}</div><div class="mock2-timer">01:30</div></div>', unsafe_allow_html=True)
        if st.button("🤖 WHO SHOULD I PICK?", key="mock2_shiva_btn", use_container_width=True, type="primary"):
            _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    ans=st.session_state.get("mock2_shiva_answer")
    if ans and st.session_state.get("mock2_shiva_pick")==int(state.get("currentOverallPick",0)):
        st.markdown(f'<div class="mock2-shiva"><div class="mock2-shiva-title">ASK SHIVA GPT</div><div class="mock2-shiva-answer">{html.escape(str(ans.get("answer") or ""))}</div><div style="font-size:13px;color:#d4e0e8;margin-top:6px">{html.escape(str(ans.get("why") or ""))}</div></div>', unsafe_allow_html=True)

def _render_board(state):
    teams_count=int(state["settings"]["teamsCount"]); rounds=int(state["settings"]["rounds"])
    picks={int(p["pickNumber"]):p for p in state.get("picks",[])}
    parts=[f'<div class="mock2-board" style="grid-template-columns:repeat({teams_count},minmax(0,1fr))">']
    for t in state["teams"]:
        parts.append(f'<div class="mock2-teamhead">{html.escape(t["name"])}</div>')
    for rnd in range(1,rounds+1):
        for team_number in range(1,teams_count+1):
            overall=(rnd-1)*teams_count+(team_number if rnd%2 else teams_count-team_number+1)
            pick=picks.get(overall)
            if pick:
                c1c,c2c=_position_color(pick.get("position")); pname=str(pick.get("playerName")); href=_player_href(pname)
                parts.append(f'<div class="mock2-boardcell" style="background:linear-gradient(145deg,{c1c},{c2c})"><div class="mock2-pickno">{overall}.</div><a class="mock2-boardname" href="{href}" target="_self">{html.escape(pname)}</a><div class="mock2-boardpos">{html.escape(str(pick.get("position")))}</div></div>')
            else:
                parts.append(f'<div class="mock2-boardcell" style="background:#081018"><div class="mock2-pickno">{overall}.</div></div>')
    parts.append('</div>')
    st.markdown('<div class="mock2-board-wrap">'+''.join(parts)+'</div>', unsafe_allow_html=True)

def _render_queue(state):
    st.markdown('<div class="mock2-section">QUEUE</div>', unsafe_allow_html=True)
    if not state.get("queue"): st.info("Your draft queue is empty.")
    for pid in list(state.get("queue") or []):
        p=get_player(state,pid)
        if not p: continue
        c1c,c2c=_position_color(p.get("position"))
        st.markdown(f'<div class="mock2-player-row" style="grid-template-columns:minmax(0,1fr) 44px;background:linear-gradient(90deg,{c2c},{c1c})"><a class="mock2-name" href="{_player_href(p["name"])}" target="_self">{html.escape(p["name"])}</a><a class="mock2-q on" href="?page=Mock%20Draft&queue={quote(str(pid))}" target="_self">×</a></div>', unsafe_allow_html=True)

def _render_team(state):
    st.markdown('<div class="mock2-section">MY TEAM</div>', unsafe_allow_html=True)
    for slot,player in roster_slots(state,state["userTeamId"]):
        if player:
            body=f'<a class="mock2-roster-player" href="{_player_href(player["name"])}" target="_self">{html.escape(player["name"])}</a> <span style="color:#9eabb5">· {html.escape(player["position"])}</span>'
        else:
            body='<span style="color:#75808a">—</span>'
        st.markdown(f'<div class="mock2-roster-row"><div class="mock2-slot">{html.escape(slot)}</div><div>{body}</div></div>', unsafe_allow_html=True)

def render_mock_draft_room_v2(rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, roi: pd.DataFrame, db_path, ask_shiva_func, api_key: str | None) -> None:
    _css()
    st.markdown('<div class="mock2-title">MOCK DRAFT</div><div class="mock2-sub">10-Team PPR • Snake Draft</div>', unsafe_allow_html=True)

    if POOL_KEY not in st.session_state:
        st.session_state[POOL_KEY]=build_player_pool(rankings,weekly)
    pool=st.session_state[POOL_KEY]
    if not pool:
        st.error("No verified 2026 ranking rows are available for the mock draft."); return

    state=_state()
    if state is None:
        st.markdown('<div class="mock2-section">CREATE MOCK DRAFT</div>', unsafe_allow_html=True)
        with st.form("mock2_setup"):
            c1,c2=st.columns(2)
            with c1: teams=st.selectbox("Teams",[8,10,12],index=1)
            with c2: slot=st.number_input("Draft Position",1,int(teams),min(4,int(teams)),1)
            c3,c4=st.columns(2)
            with c3: scoring=st.selectbox("Scoring",["PPR","Half PPR","Standard"],index=0)
            with c4: rounds=st.number_input("Rounds",10,20,sum(DEFAULT_ROSTER.values()),1)
            if st.form_submit_button("START MOCK DRAFT",use_container_width=True,type="primary"):
                state=initialize_draft(pool,int(teams),int(slot),scoring,DEFAULT_ROSTER.copy(),int(rounds),90)
                start_draft(state); advance_cpu_until_user(state); st.session_state[STATE_KEY]=state; st.rerun()
        return

    if state.get("status")=="active" and not state.get("paused") and state.get("currentTeam")!=state.get("userTeamId"):
        advance_cpu_until_user(state)
    st.session_state[STATE_KEY]=state
    _handle_query_actions(state)

    tab=str(st.query_params.get("draft_tab") or st.session_state.get("mock2_tab","PLAYERS")).upper()
    if tab not in {"PLAYERS","BOARD","QUEUE","TEAM"}: tab="PLAYERS"
    st.session_state["mock2_tab"]=tab
    labels=[("BOARD","DRAFT BOARD"),("QUEUE","QUEUE"),("TEAM","TEAM"),("PLAYERS","PLAYERS")]
    st.markdown('<div class="mock2-tabs">'+''.join(f'<a class="mock2-tab{" active" if tab==key else ""}" href="?page=Mock%20Draft&draft_tab={key}" target="_self">{label}</a>' for key,label in labels)+'</div>', unsafe_allow_html=True)

    c1,c2=st.columns(2)
    with c1:
        if st.button("↶ UNDO PICK",key="mock2_undo",use_container_width=True,disabled=not state.get("picks")):
            undo_last_pick(state); st.rerun()
    with c2:
        if st.button("HOME",key="mock2_home",use_container_width=True):
            st.session_state["page"]="Home"; st.query_params.clear(); st.rerun()

    if tab=="PLAYERS": _render_player_list(state,history,roi,rankings,weekly,ask_shiva_func,api_key)
    elif tab=="BOARD": _render_board(state)
    elif tab=="QUEUE": _render_queue(state)
    else: _render_team(state)
