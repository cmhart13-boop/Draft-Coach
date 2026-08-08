from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote

import pandas as pd
import streamlit as st

from mock_draft_engine import (
    DEFAULT_ROSTER, advance_cpu_until_user, build_player_pool, full_draft_context,
    get_player, initialize_draft, make_pick, pause_draft, queue_add, queue_remove,
    resume_draft, roster_slots, start_draft, timer_remaining, undo_last_pick,
)
from player_profile import player_link_html, player_profile_href

STATE_KEY="mock_draft_state_v2"
POOL_KEY="mock_draft_original_pool_v2"
POS_STYLE={"QB":("#d5232b","#8a1017"),"RB":("#ff7a00","#a94300"),"WR":("#138dd8","#075688"),"TE":("#42a92d","#205f17"),"FLEX":("#9341d2","#58217f"),"K":("#58636e","#303941"),"D/ST":("#8d5008","#52300a")}


def _css():
    st.markdown("""
<style>
.mock-head{display:grid;grid-template-columns:34px 1fr 34px;align-items:start;margin:0 0 3px}.mock-head a{color:#fff!important;text-decoration:none!important;font-size:30px;line-height:1}.mock-title{text-align:center;font-size:22px;font-weight:1000;line-height:1}.mock-sub{text-align:center;font-size:12px;color:#fff;margin-top:4px}.mock-gear{text-align:right!important;font-size:22px!important}.mock-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #27323b;margin:5px 0 8px}.mock-tab{text-align:center;color:#fff!important;text-decoration:none!important;font-size:10px;font-weight:900;padding:10px 1px}.mock-tab.active{color:#dfff00!important;border-bottom:2px solid #dfff00}.draft-view-toggle{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:5px 0 8px}.draft-view{background:#09141d;border:1px solid #203646;border-radius:7px;text-align:center;padding:6px;color:#cbd3da!important;text-decoration:none!important;font-size:9px;font-weight:900}.draft-view.active{background:#102436;color:#fff!important;border-color:#228ed1}.mock-filter-button{height:38px;border-radius:7px;background:#08141e;border:1px solid #1d3446;display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff!important;text-decoration:none!important}.mock-poschips{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin:7px 0 8px}.mock-chip{border-radius:6px;text-align:center;padding:6px 1px;font-size:10px;font-weight:1000;color:#fff!important;text-decoration:none!important;border:1px solid transparent}.mock-chip.active{border-color:#fff;box-shadow:0 0 0 1px rgba(255,255,255,.25)}.mock-list-head{display:grid;grid-template-columns:31px minmax(0,1fr) 32px 34px 38px 28px 38px;gap:2px;padding:5px;color:#c4cbd2;font-size:8px;font-weight:900;background:#091017;border-radius:6px 6px 0 0}.mock-player{display:grid;grid-template-columns:31px minmax(0,1fr) 32px 34px 38px 28px 38px;gap:2px;align-items:center;border-radius:6px;padding:5px;margin:2px 0;border:1px solid rgba(255,255,255,.10)}.mock-rank{width:23px;height:23px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.18);font-size:10px;font-weight:1000}.mock-name{font-size:11px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}.mock-cell{font-size:8.5px;font-weight:900;text-align:center;white-space:nowrap}.mock-adp{font-size:8.5px;font-weight:1000;text-align:right}.mock-q,.mock-pick{height:23px;border-radius:5px;display:flex;align-items:center;justify-content:center;text-decoration:none!important;font-size:8px;font-weight:1000}.mock-q{color:#fff!important;background:rgba(0,0,0,.20);border:1px solid rgba(255,255,255,.20)}.mock-q.on,.mock-pick.on{background:#dfff00;color:#061006!important;border:1px solid #dfff00}.mock-pick{color:#b8c0c7!important;background:#071018;border:1px solid rgba(255,255,255,.20)}.draft-status{position:fixed;left:50%;bottom:67px;transform:translateX(-50%);width:min(500px,calc(100vw - 20px));z-index:9998;display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;background:#050b10;border:1px solid #25394a;border-radius:9px;padding:8px 9px;box-shadow:0 -5px 20px rgba(0,0,0,.42)}.clock-label{font-size:10px}.clock-pick{font-size:13px;font-weight:1000;color:#dfff00}.clock-team{font-size:11px;font-weight:900}.clock-timer{background:#dfff00;color:#061006;border-radius:6px;padding:6px 8px;font-size:14px;font-weight:1000}.board-top{display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;margin:3px 0 4px}.board-title{text-align:center;font-size:17px;font-weight:1000}.board-round{text-align:center;font-size:9px;color:#fff}.board-meta{text-align:right;font-size:8px}.board-legend{display:flex;justify-content:center;gap:7px;flex-wrap:wrap;margin:4px 0 7px;font-size:7px;font-weight:900}.legend-dot{display:inline-block;width:7px;height:7px;border-radius:1px;margin-right:2px}.board-wrap{background:#020609;border:1px solid #1c2b36;border-radius:7px;padding:3px;overflow:hidden}.draft-board{display:grid;gap:2px;width:100%}.team-head{background:#071018;border:1px solid #26313a;border-radius:3px;padding:4px 0;font-size:6px;font-weight:1000;text-align:center;overflow:hidden}.pick-card{min-height:45px;border-radius:3px;padding:2px 1px;border:1px solid rgba(255,255,255,.12);overflow:hidden}.pick-no{font-size:6px;color:#fff9}.pick-name{font-size:6px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;display:block;line-height:1.05;overflow-wrap:anywhere}.pick-pos{font-size:6px;text-align:center;font-weight:900;margin-top:2px}.queue-row,.team-row,.result-row{display:grid;grid-template-columns:45px 1fr 40px;gap:6px;align-items:center;padding:7px;border-bottom:1px solid #1d2a34}.slot{color:#dfff00;font-size:10px;font-weight:1000}.section-title{font-size:14px;font-weight:1000;margin:10px 0 5px}.mock-name-plain{font-size:12px!important;font-weight:900!important;color:#fff!important;text-decoration:none!important}.mock-spacer{height:68px}.settings-card{background:#07121b;border:1px solid #24405a;border-radius:9px;padding:8px;margin:5px 0 8px}.settings-line{font-size:10px;color:#cbd4db}@media(max-width:390px){.mock-player,.mock-list-head{grid-template-columns:29px minmax(0,1fr) 29px 31px 34px 26px 35px}.mock-name{font-size:10px!important}.mock-cell,.mock-adp{font-size:7.5px}.mock-poschips{gap:3px}.mock-chip{font-size:9px}.pick-card{min-height:41px}.pick-name{font-size:5.5px!important}.team-head{font-size:5.5px}}
</style>""",unsafe_allow_html=True)


def _state(): return st.session_state.get(STATE_KEY)
def _colors(pos): return POS_STYLE.get(str(pos).upper(),("#52606c","#29313a"))
def _return_query(view): return f"draft_tab=DRAFT_BOARD&draft_view={view}"


def _handle_actions(state):
    qid=st.query_params.get("queue"); did=st.query_params.get("draft")
    if qid:
        pid=str(qid); queue_remove(state,pid) if pid in state.get("queue",[]) else queue_add(state,pid); del st.query_params["queue"]; st.rerun()
    if did:
        pid=str(did); on=state.get("status")=="active" and not state.get("paused") and state.get("currentTeam")==state.get("userTeamId")
        if on and get_player(state,pid): make_pick(state,pid,source="user"); advance_cpu_until_user(state); st.session_state.pop("mock2_shiva_answer",None)
        del st.query_params["draft"]; st.rerun()


def _position_chips(selected):
    bits=[]
    for pos in ("QB","RB","WR","TE","FLEX","K","D/ST"):
        c1,c2=_colors(pos); label="DEF" if pos=="D/ST" else pos; active=" active" if selected==pos else ""; href=f'?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=LIST&pos={quote(pos)}'
        bits.append(f'<a class="mock-chip{active}" href="{href}" target="_self" style="background:linear-gradient(135deg,{c1},{c2})">{label}</a>')
    st.markdown('<div class="mock-poschips">'+''.join(bits)+'</div>',unsafe_allow_html=True)


def _status_inner(state):
    if state.get("status")!="active": return
    overall=int(state.get("currentOverallPick",1)); teams=int(state["settings"]["teamsCount"]); rnd=int(state.get("currentRound",1)); pir=(overall-1)%teams+1; rem=timer_remaining(state); mins,secs=divmod(max(0,rem),60); team_num=int(str(state.get("currentTeam","t1")).lstrip("t") or 1); label="You're on the clock!" if state.get("currentTeam")==state.get("userTeamId") else "Draft in progress"
    st.markdown(f'<div class="draft-status"><div><div class="clock-label">{label}</div><div class="clock-pick">Pick {rnd}.{pir:02d}</div></div><div class="clock-team">Team {team_num}</div><div class="clock-timer">{mins:02d}:{secs:02d}</div></div><div class="mock-spacer"></div>',unsafe_allow_html=True)


def _status_bar(state):
    frag=getattr(st,"fragment",None)
    if frag is None: _status_inner(state); return
    @frag(run_every=1.0)
    def live_status(): _status_inner(state)
    live_status()


def _run_shiva(state,history,roi,rankings,weekly,ask_shiva_func,api_key):
    if not api_key: st.warning("Ask Shiva requires the configured OpenAI API key."); return
    with st.spinner("Shiva is reading your roster and the live board..."):
        st.session_state["mock2_shiva_answer"]=ask_shiva_func(question="Who should I pick right now?",history=history,roi=roi,rankings=rankings,weekly=weekly,api_key=api_key,draft_context=full_draft_context(state)); st.session_state["mock2_shiva_pick"]=int(state["currentOverallPick"])


def _player_list(state,history,roi,rankings,weekly,ask_shiva_func,api_key):
    if str(st.query_params.get("reset_filters") or "")=="1":
        st.session_state["mock2_search"]=""; st.session_state["mock2_pos"]="ALL"; st.session_state["mock2_team"]="ALL"; del st.query_params["reset_filters"]
    qpos=str(st.query_params.get("pos") or "").upper()
    if qpos in {"QB","RB","WR","TE","FLEX","D/ST","K"}: st.session_state["mock2_pos"]=qpos
    c1,c2,c3,c4=st.columns([1.45,.9,.9,.35],gap="small")
    with c1: search=st.text_input("Search",placeholder="⌕ Search players...",key="mock2_search",label_visibility="collapsed")
    with c2: pos=st.selectbox("Position",["ALL","QB","RB","WR","TE","FLEX","D/ST","K"],key="mock2_pos",label_visibility="collapsed",format_func=lambda x:"All Positions" if x=="ALL" else x)
    teams=["ALL"]+sorted({str(p.get("team")) for p in state.get("availablePlayers",[]) if p.get("team")})
    with c3: team_filter=st.selectbox("Team",teams,key="mock2_team",label_visibility="collapsed",format_func=lambda x:"All Teams" if x=="ALL" else x)
    with c4: st.markdown('<a class="mock-filter-button" href="?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=LIST&reset_filters=1" target="_self" title="Reset filters">▽</a>',unsafe_allow_html=True)
    _position_chips(pos); pool=list(state.get("availablePlayers") or [])
    if search.strip(): pool=[p for p in pool if search.strip().casefold() in str(p.get("name","")).casefold()]
    if pos!="ALL": pool=[p for p in pool if (p.get("position") in {"RB","WR","TE"} if pos=="FLEX" else p.get("position")==pos)]
    if team_filter!="ALL": pool=[p for p in pool if str(p.get("team"))==team_filter]
    pool=sorted(pool,key=lambda p:(p.get("rank",9999),p.get("adp",9999),p.get("name","")))[:140]
    st.markdown('<div class="mock-list-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div style="text-align:right">ADP</div><div>Q</div><div></div></div>',unsafe_allow_html=True)
    on=state.get("status")=="active" and not state.get("paused") and state.get("currentTeam")==state.get("userTeamId"); queued=set(state.get("queue") or []); rq=_return_query("LIST")
    for p in pool:
        c1c,c2c=_colors(p.get("position")); pid=str(p["id"]); name=str(p.get("name")); team=html.escape(str(p.get("team") or "—")); pt=html.escape(str(p.get("position") or "—")); adp=float(p.get("adp") or 0); rank=int(p.get("rank") or 0); link=player_link_html(pid,name,css_class="mock-name",return_page="Mock Draft",return_query=rq); qc="mock-q on" if pid in queued else "mock-q"; qh=f'?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=LIST&queue={quote(pid)}'; pick=f'<a class="mock-pick on" href="?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=LIST&draft={quote(pid)}" target="_self">PICK</a>' if on else '<span class="mock-pick">PICK</span>'
        st.markdown(f'<div class="mock-player" style="background:linear-gradient(90deg,{c2c},{c1c})"><div class="mock-rank">{rank}</div><div>{link}</div><div class="mock-cell">{pt}</div><div class="mock-cell">{team}</div><div class="mock-adp">{adp:.1f}</div><a class="{qc}" href="{qh}" target="_self">Q</a>{pick}</div>',unsafe_allow_html=True)
    if on and st.button("🤖 WHO SHOULD I PICK?",key="mock2_shiva_btn",use_container_width=True,type="primary"): _run_shiva(state,history,roi,rankings,weekly,ask_shiva_func,api_key)
    ans=st.session_state.get("mock2_shiva_answer")
    if ans and st.session_state.get("mock2_shiva_pick")==int(state.get("currentOverallPick",0)): st.markdown(f'<div style="background:#072237;border:1px solid #126b9d;border-radius:9px;padding:9px;margin-top:7px"><div style="font-size:9px;color:#5ad0ff;font-weight:1000">ASK SHIVA GPT</div><div style="font-size:16px;color:#dfff00;font-weight:1000;margin-top:4px">{html.escape(str(ans.get("answer") or ""))}</div><div style="font-size:10px;margin-top:3px">{html.escape(str(ans.get("why") or ""))}</div></div>',unsafe_allow_html=True)


def _compact_name(name):
    p=str(name).replace("'","").split()
    return "—" if not p else (p[0][:9] if len(p)==1 else f"{p[0][0]}.{p[-1]}"[:10])


def _board(state):
    teams=int(state["settings"]["teamsCount"]); rounds=int(state["settings"]["rounds"]); cr=int(state.get("currentRound",1)); st.markdown(f'<div class="board-top"><div></div><div><div class="board-title">MOCK DRAFT BOARD</div><div class="board-round">Round {cr}⌄</div></div><div class="board-meta">{teams} Teams • {html.escape(str(state["settings"].get("scoring","PPR")))}</div></div>',unsafe_allow_html=True); legend=[]
    for pos in ("QB","RB","WR","TE","FLEX","K","D/ST"):
        c1,_=_colors(pos); label="DEF" if pos=="D/ST" else pos; legend.append(f'<span><i class="legend-dot" style="background:{c1}"></i>{label}</span>')
    st.markdown('<div class="board-legend">'+''.join(legend)+'</div>',unsafe_allow_html=True); picks={int(p["pickNumber"]):p for p in state.get("picks",[])}; parts=[f'<div class="draft-board" style="grid-template-columns:repeat({teams},minmax(0,1fr))">']
    for i in range(1,teams+1): parts.append(f'<div class="team-head">TEAM {i}</div>')
    for rnd in range(1,rounds+1):
        for col in range(1,teams+1):
            overall=(rnd-1)*teams+(col if rnd%2 else teams-col+1); pick=picks.get(overall); rp=(overall-1)%teams+1
            if pick:
                c1c,c2c=_colors(pick.get("position")); pid=str(pick.get("playerId")); pname=str(pick.get("playerName")); pos=str(pick.get("position")); href=player_profile_href(pname,pid,return_page="Mock Draft",return_query=_return_query("BOARD")); link=f'<a class="pick-name" href="{html.escape(href,quote=True)}" target="_self">{html.escape(_compact_name(pname))}</a>'; parts.append(f'<div class="pick-card" style="background:linear-gradient(145deg,{c1c},{c2c})"><div class="pick-no">{rnd}.{rp}</div>{link}<div class="pick-pos">{html.escape(pos)}</div></div>')
            else: parts.append(f'<div class="pick-card" style="background:#071018"><div class="pick-no">{rnd}.{rp}</div></div>')
    parts.append('</div>'); st.markdown('<div class="board-wrap">'+''.join(parts)+'</div>',unsafe_allow_html=True)


def _queue(state):
    st.markdown('<div class="section-title">QUEUE</div>',unsafe_allow_html=True)
    if not state.get("queue"): st.info("Your draft queue is empty.")
    for pid in list(state.get("queue") or []):
        p=get_player(state,pid)
        if p:
            link=player_link_html(str(p["id"]),str(p["name"]),css_class="mock-name-plain",return_page="Mock Draft",return_query="draft_tab=QUEUE"); st.markdown(f'<div class="queue-row"><div class="slot">{html.escape(str(p.get("position")))}</div><div>{link}</div><a class="mock-q on" href="?page=Mock%20Draft&draft_tab=QUEUE&queue={quote(str(pid))}" target="_self">×</a></div>',unsafe_allow_html=True)


def _team(state):
    st.markdown('<div class="section-title">MY TEAM</div>',unsafe_allow_html=True)
    for slot,p in roster_slots(state,state["userTeamId"]):
        body=player_link_html(str(p["id"]),str(p["name"]),css_class="mock-name-plain",return_page="Mock Draft",return_query="draft_tab=TEAM") if p else '<span style="color:#75808a">—</span>'; pos=html.escape(str(p.get("position"))) if p else ""; st.markdown(f'<div class="team-row"><div class="slot">{html.escape(slot)}</div><div>{body}</div><div class="mock-cell">{pos}</div></div>',unsafe_allow_html=True)


def _results(state):
    st.markdown('<div class="section-title">DRAFT RESULTS</div>',unsafe_allow_html=True)
    if not state.get("picks"): st.info("No picks have been made yet.")
    for pick in state.get("picks",[]):
        link=player_link_html(str(pick.get("playerId")),str(pick.get("playerName")),css_class="mock-name-plain",return_page="Mock Draft",return_query="draft_tab=RESULTS"); pir=((int(pick.get("pickNumber",1))-1)%int(state["settings"]["teamsCount"]))+1; st.markdown(f'<div class="result-row"><div class="slot">{int(pick.get("round",0))}.{pir:02d}</div><div>{link}</div><div class="mock-cell">{html.escape(str(pick.get("position")))}</div></div>',unsafe_allow_html=True)


def _settings(state):
    s=state["settings"]; st.markdown(f'<div class="settings-card"><div class="section-title">DRAFT SETTINGS</div><div class="settings-line">{int(s["teamsCount"])} Teams • {html.escape(str(s["scoring"]))} • Snake Draft • {int(s["rounds"])} Rounds • {int(s["secondsPerPick"])} sec/pick</div></div>',unsafe_allow_html=True); c1,c2=st.columns(2,gap="small")
    with c1:
        label="RESUME DRAFT" if state.get("paused") else "PAUSE DRAFT"
        if st.button(label,use_container_width=True,key="toggle_pause"): resume_draft(state) if state.get("paused") else pause_draft(state); st.rerun()
    with c2:
        if st.button("UNDO LAST PICK",use_container_width=True,key="undo_draft",disabled=not bool(state.get("picks"))): undo_last_pick(state); st.rerun()


def render_mock_draft_room_v2(rankings:pd.DataFrame,weekly:pd.DataFrame,history:pd.DataFrame,roi:pd.DataFrame,db_path,ask_shiva_func,api_key:str|None)->None:
    _css(); settings_open=str(st.query_params.get("draft_settings") or "")=="1"; gear='?page=Mock%20Draft' if settings_open else '?page=Mock%20Draft&draft_settings=1'; state=_state(); subtitle="10-Team PPR • Snake Draft" if not state else f'{int(state["settings"]["teamsCount"])}-Team {html.escape(str(state["settings"]["scoring"]))} • Snake Draft'; st.markdown(f'<div class="mock-head"><a href="?page=Home" target="_self">‹</a><div><div class="mock-title">MOCK DRAFT</div><div class="mock-sub">{subtitle}</div></div><a class="mock-gear" href="{gear}" target="_self">⚙</a></div>',unsafe_allow_html=True)
    if POOL_KEY not in st.session_state: st.session_state[POOL_KEY]=build_player_pool(rankings,weekly)
    pool=st.session_state[POOL_KEY]
    if not pool: st.error("No verified 2026 ranking rows are available for the mock draft."); return
    if state is None:
        st.markdown('<div class="section-title">CREATE MOCK DRAFT</div>',unsafe_allow_html=True)
        with st.form("mock2_setup"):
            c1,c2=st.columns(2)
            with c1: teams=st.selectbox("Teams",[8,10,12],index=1)
            with c2: slot=st.number_input("Draft Position",1,int(teams),min(4,int(teams)),1)
            c3,c4=st.columns(2)
            with c3: scoring=st.selectbox("Scoring",["PPR","Half PPR","Standard"],index=0)
            with c4: rounds=st.number_input("Rounds",10,20,sum(DEFAULT_ROSTER.values()),1)
            if st.form_submit_button("START MOCK DRAFT",use_container_width=True,type="primary"): state=initialize_draft(pool,int(teams),int(slot),scoring,DEFAULT_ROSTER.copy(),int(rounds),90); start_draft(state); advance_cpu_until_user(state); st.session_state[STATE_KEY]=state; st.rerun()
        return
    if state.get("status")=="active" and not state.get("paused") and state.get("currentTeam")!=state.get("userTeamId"): advance_cpu_until_user(state)
    st.session_state[STATE_KEY]=state; _handle_actions(state)
    if settings_open: _settings(state)
    tab=str(st.query_params.get("draft_tab") or st.session_state.get("mock2_tab","DRAFT_BOARD")).upper(); tab=tab if tab in {"DRAFT_BOARD","QUEUE","TEAM","RESULTS"} else "DRAFT_BOARD"; st.session_state["mock2_tab"]=tab; labels=(("DRAFT_BOARD","DRAFT BOARD"),("QUEUE","QUEUE"),("TEAM","TEAM"),("RESULTS","RESULTS")); st.markdown('<div class="mock-tabs">'+''.join(f'<a class="mock-tab{" active" if tab==k else ""}" href="?page=Mock%20Draft&draft_tab={k}" target="_self">{v}</a>' for k,v in labels)+'</div>',unsafe_allow_html=True)
    if tab=="DRAFT_BOARD":
        view=str(st.query_params.get("draft_view") or st.session_state.get("mock2_view","LIST")).upper(); view=view if view in {"LIST","BOARD"} else "LIST"; st.session_state["mock2_view"]=view; st.markdown('<div class="draft-view-toggle"><a class="draft-view'+(' active' if view=='LIST' else '')+'" href="?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=LIST" target="_self">PLAYER LIST</a><a class="draft-view'+(' active' if view=='BOARD' else '')+'" href="?page=Mock%20Draft&draft_tab=DRAFT_BOARD&draft_view=BOARD" target="_self">BOARD VIEW</a></div>',unsafe_allow_html=True); _player_list(state,history,roi,rankings,weekly,ask_shiva_func,api_key) if view=="LIST" else _board(state)
    elif tab=="QUEUE": _queue(state)
    elif tab=="TEAM": _team(state)
    else: _results(state)
    _status_bar(state)
