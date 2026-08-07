from __future__ import annotations

import html
import math
import time
from typing import Any

import pandas as pd
import streamlit as st

from mock_draft_engine import (
    DEFAULT_ROSTER,
    advance_cpu_until_user,
    auto_pick_user,
    build_player_pool,
    full_draft_context,
    get_player,
    initialize_draft,
    list_saved_drafts,
    load_saved_draft,
    make_pick,
    pause_draft,
    queue_add,
    queue_move,
    queue_remove,
    recommendation_groups,
    restart_draft,
    resume_draft,
    roster_needs,
    roster_slots,
    save_completed_draft,
    snake_team_for_pick,
    start_draft,
    team_by_id,
    timer_remaining,
    undo_last_pick,
)

POSITION_CLASS = {
    "QB": "pos-qb", "RB": "pos-rb", "WR": "pos-wr", "TE": "pos-te", "D/ST": "pos-dst", "K": "pos-k"
}


def _css() -> None:
    st.markdown(
        """
<style>
.mock-shell{width:100%;max-width:100%;overflow-x:hidden}
.mock-topbar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:8px 0}
.mock-chip{background:#18191d;border:1px solid #30323a;border-radius:10px;padding:8px;min-width:0}
.mock-chip-label{color:#858790;font-size:8px;font-weight:1000;text-transform:uppercase;letter-spacing:.08em}
.mock-chip-value{color:#fff;font-size:15px;font-weight:1000;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mock-chip-value.you{color:#31f22f}
.mock-section-title{font-size:12px;font-weight:1000;color:#fff;margin:12px 0 6px}
.mock-subtle{font-size:10px;color:#929399;line-height:1.35}
.mock-list-head{display:grid;grid-template-columns:35px minmax(0,1fr) 48px 54px;gap:6px;align-items:center;padding:6px 8px;background:#15161a;border:1px solid #30323a;border-bottom:0;border-radius:12px 12px 0 0;color:#7f828b;font-size:8px;font-weight:1000;letter-spacing:.06em;text-transform:uppercase}
.mock-rank{font-size:11px;color:#a2a4ab;font-weight:900;text-align:center}
.mock-player-name{font-size:12px;color:#fff;font-weight:1000;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mock-player-meta{font-size:9px;color:#929399;line-height:1.25;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mock-pos{font-size:9px;font-weight:1000;border-radius:7px;padding:4px 5px;text-align:center;min-width:32px;display:inline-block}
.pos-qb{background:#5a2529;color:#ff9aa0}.pos-rb{background:#17472e;color:#65ff9e}.pos-wr{background:#283d78;color:#9bb2ff}.pos-te{background:#604515;color:#ffd16b}.pos-dst{background:#3b3d44;color:#e5e5e8}.pos-k{background:#4a2b5e;color:#e2afff}
.mock-rec{display:flex;gap:7px;overflow-x:auto;padding:2px 0 7px;scrollbar-width:none}.mock-rec::-webkit-scrollbar{display:none}
.mock-rec-card{flex:0 0 128px;background:#1b1c20;border:1px solid #333640;border-radius:11px;padding:8px}
.mock-board-wrap{width:100%;overflow-x:auto;overflow-y:hidden;border:1px solid #3a3c45;border-radius:14px;background:#0f1013;-webkit-overflow-scrolling:touch;box-shadow:0 8px 28px rgba(0,0,0,.22)}
.mock-board{display:grid;min-width:900px;gap:4px;padding:7px;background:linear-gradient(180deg,#111217,#0d0e11)}
.mock-board-head,.mock-board-cell{border:1px solid #30333b;border-radius:7px;min-height:68px;padding:6px;background:#181a1f}
.mock-board-head{min-height:38px;font-size:9px;font-weight:1000;text-align:center;display:flex;align-items:center;justify-content:center;background:#202229;color:#d5d6da}
.mock-board-head.mine{border-color:#31f22f;color:#31f22f;background:#152218;box-shadow:0 0 10px rgba(49,242,47,.15)}
.mock-board-cell.mine{outline:1px solid rgba(49,242,47,.45);outline-offset:-1px}
.mock-board-cell.current{box-shadow:inset 0 0 0 2px #31f22f,0 0 12px rgba(49,242,47,.32);animation:mockPulse 1.4s ease-in-out infinite}
.mock-board-cell.pos-qb{background:linear-gradient(145deg,#422126,#26171a);border-color:#6b3037}
.mock-board-cell.pos-rb{background:linear-gradient(145deg,#16442e,#11291f);border-color:#276544}
.mock-board-cell.pos-wr{background:linear-gradient(145deg,#263d76,#17244a);border-color:#3f5da4}
.mock-board-cell.pos-te{background:linear-gradient(145deg,#5a421a,#302510);border-color:#806026}
.mock-board-cell.pos-dst{background:linear-gradient(145deg,#383b43,#22242a);border-color:#51545e}
.mock-board-cell.pos-k{background:linear-gradient(145deg,#4b2d5c,#281a31);border-color:#6b427f}
.mock-pick-no{font-size:8px;color:#9a9ca4}.mock-pick-player{font-size:9px;color:#fff;font-weight:1000;line-height:1.12;margin-top:4px}.mock-pick-meta{font-size:8px;color:#c0c2c8;margin-top:3px}
.mock-board-legend{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0 8px}.mock-legend-item{font-size:8px;font-weight:900;padding:4px 7px;border-radius:7px}
.mock-roster-row{display:grid;grid-template-columns:34px minmax(0,1fr);gap:7px;padding:6px 0;border-bottom:1px solid #252529}.mock-roster-slot{font-size:8px;color:#31f22f;font-weight:1000}.mock-roster-name{font-size:10px;color:#fff;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mock-queue-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;align-items:center}.mock-complete{background:linear-gradient(145deg,#173317,#121712);border:1px solid #31f22f;border-radius:18px;padding:18px;text-align:center;margin:12px 0}.mock-complete h2{color:#31f22f!important;margin:0}.mock-history{font-size:10px;padding:6px 0;border-bottom:1px solid #28282c;color:#ddd}.mock-controls [data-testid="stHorizontalBlock"]{gap:5px!important}.mock-view-toggle [data-testid="stHorizontalBlock"]{gap:5px!important}
@keyframes mockPulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.18)}}
button[kind="secondary"]{transition:all .12s ease}
@media(min-width:800px){.block-container{max-width:1180px!important}.mock-player-name{font-size:13px}.mock-board{min-width:980px}}
@media(max-width:430px){html,body,.stApp,.block-container{max-width:100vw!important;overflow-x:hidden!important}.mock-topbar{grid-template-columns:repeat(3,minmax(0,1fr))}.mock-chip{padding:7px 5px}.mock-chip-value{font-size:13px}.mock-list-head{grid-template-columns:30px minmax(0,1fr) 42px 48px;padding-left:6px;padding-right:6px}.mock-player-name{font-size:11px}.mock-player-meta{font-size:8px}.mock-board-wrap{max-width:calc(100vw - 24px)}}
</style>
""",
        unsafe_allow_html=True,
    )


def _state_key() -> str:
    return "mock_draft_state_v2"


def _pool_key() -> str:
    return "mock_draft_original_pool_v2"


def _player_analytics(player: dict[str, Any], history: pd.DataFrame, weekly: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {
        "2026 Rank": player.get("rank"), "2026 ADP": player.get("adp"), "NFL Team": player.get("team"), "Bye": player.get("bye")
    }
    if player.get("projected_points") is not None:
        result["2026 Projection"] = player.get("projected_points")
    if history is not None and not history.empty:
        h = history[(history["player_name"].astype(str).str.lower() == player["name"].lower()) & (pd.to_numeric(history["season"], errors="coerce") == 2025)]
        if not h.empty:
            r = h.iloc[0]
            for label, col in [("2025 Fantasy Points", "fantasy_points_ppr"), ("2025 PPG", "ppg"), ("Games Played", "games_played")]:
                if col in h.columns and pd.notna(r.get(col)):
                    result[label] = round(float(r[col]), 1)
    if weekly is not None and not weekly.empty:
        name_col = "player_display_name" if "player_display_name" in weekly.columns else "player_name"
        w = weekly[(weekly[name_col].astype(str).str.lower() == player["name"].lower()) & (pd.to_numeric(weekly["season"], errors="coerce") == 2025)].copy()
        if not w.empty:
            if "fantasy_points_ppr" in w.columns:
                pts = pd.to_numeric(w["fantasy_points_ppr"], errors="coerce")
                result["15+ PPR Games"] = int((pts >= 15).sum())
                result["20+ PPR Games"] = int((pts >= 20).sum())
            for label, col in [("Targets", "targets"), ("Rush Attempts", "carries")]:
                if col in w.columns:
                    vals = pd.to_numeric(w[col], errors="coerce")
                    if vals.notna().any(): result[label] = int(vals.sum())
            if "target_share" in w.columns:
                vals = pd.to_numeric(w["target_share"], errors="coerce")
                if vals.notna().any(): result["Target Share"] = f"{vals.mean()*100:.1f}%"
    return result


def _render_player_details(player: dict[str, Any], history: pd.DataFrame, weekly: pd.DataFrame) -> None:
    data = _player_analytics(player, history, weekly)
    st.markdown(f"### {player['name']} · {player['position']}")
    pairs = list(data.items())
    for i in range(0, len(pairs), 3):
        cols = st.columns(min(3, len(pairs) - i))
        for col, (label, value) in zip(cols, pairs[i:i+3]):
            with col: st.metric(label, value if value is not None else "—")


def _render_top_status(state: dict[str, Any]) -> None:
    current = team_by_id(state, state["currentTeam"])
    is_user = state["currentTeam"] == state["userTeamId"]
    st.markdown(
        f"""<div class="mock-topbar">
        <div class="mock-chip"><div class="mock-chip-label">Round</div><div class="mock-chip-value">{state['currentRound']}</div></div>
        <div class="mock-chip"><div class="mock-chip-label">Overall Pick</div><div class="mock-chip-value">{state['currentOverallPick']}</div></div>
        <div class="mock-chip"><div class="mock-chip-label">Current Team</div><div class="mock-chip-value {'you' if is_user else ''}">{'YOUR PICK' if is_user else html.escape(current['name'])}</div></div>
        </div>""",
        unsafe_allow_html=True,
    )


@st.fragment(run_every="1s")
def _live_timer_fragment() -> None:
    """Refresh the user clock every second without resetting centralized draft state."""
    state = st.session_state.get(_state_key())
    if not state:
        return
    remain = timer_remaining(state)
    st.progress(remain / max(1, int(state["settings"]["secondsPerPick"])), text=f"⏱️ {remain}s")
    if state["status"] == "active" and not state["paused"] and state["currentTeam"] == state["userTeamId"] and remain <= 0:
        auto_pick_user(state)
        advance_cpu_until_user(state)
        st.session_state[_state_key()] = state
        st.rerun()

def _render_controls(state: dict[str, Any], original_pool: list[dict[str, Any]]) -> None:
    cols = st.columns(4)
    with cols[0]:
        if st.button("⏸ Pause", disabled=state["paused"] or state["status"] != "active", use_container_width=True, key="mock_pause"):
            pause_draft(state); st.rerun()
    with cols[1]:
        if st.button("▶ Resume", disabled=not state["paused"] or state["status"] != "active", use_container_width=True, key="mock_resume"):
            resume_draft(state); st.rerun()
    with cols[2]:
        if st.button("↶ Undo", disabled=not state["picks"], use_container_width=True, key="mock_undo"):
            undo_last_pick(state); st.rerun()
    with cols[3]:
        if st.button("↻ Restart", use_container_width=True, key="mock_restart"):
            st.session_state[_state_key()] = restart_draft(state, original_pool); st.rerun()


def _render_recommendations(state: dict[str, Any]) -> None:
    groups = recommendation_groups(state)
    choice = st.segmented_control("Recommendations", list(groups), default="BEST AVAILABLE", key="mock_rec_type", label_visibility="collapsed")
    players = groups.get(choice or "BEST AVAILABLE", [])[:5]
    cards = "".join(
        f'<div class="mock-rec-card"><div class="mock-pos {POSITION_CLASS.get(p["position"], "")}">{html.escape(p["position"])}</div><div class="mock-player-name" style="margin-top:7px">{html.escape(p["name"])}</div><div class="mock-player-meta">ADP {p["adp"]:.1f} · {html.escape(p["team"] or "—")}</div></div>'
        for p in players
    )
    st.markdown(f'<div class="mock-rec">{cards}</div>', unsafe_allow_html=True)


def _render_available(state: dict[str, Any], history: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="mock-section-title">AVAILABLE PLAYERS</div>', unsafe_allow_html=True)
    st.caption('Players are stacked by 2026 rank / ADP. Tap a player name for analytics, or use Queue / Draft.')

    search = st.text_input("Search", placeholder='Search player', key='mock_search', label_visibility='collapsed')
    pos = st.segmented_control(
        "Position", ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"],
        default='ALL', key='mock_position_filter', label_visibility='collapsed'
    ) or 'ALL'

    pool = list(state['availablePlayers'])
    if search.strip():
        pool = [p for p in pool if search.lower().strip() in p['name'].lower()]
    if pos != 'ALL':
        pool = [p for p in pool if p['position'] == pos]
    pool = sorted(pool, key=lambda p: (p.get('rank', 9999), p.get('adp', 9999), p['name']))[:80]

    st.markdown(
        '<div class="mock-list-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>ADP</div></div>',
        unsafe_allow_html=True,
    )

    for p in pool:
        can_draft = state['status'] == 'active' and not state['paused'] and state['currentTeam'] == state['userTeamId']
        row = st.columns([0.45, 3.65, 0.78, 0.82, 1.0, 1.0], gap='small')
        with row[0]:
            st.markdown(f'<div style="padding-top:10px;text-align:center;color:#a2a4ab;font-size:11px;font-weight:900">{p["rank"]}</div>', unsafe_allow_html=True)
        with row[1]:
            label = f"{p['name']}\n{p['team'] or '—'}" + (f" · Bye {p['bye']}" if p.get('bye') else '')
            if st.button(label, key=f"detail_{p['id']}", use_container_width=True):
                st.session_state['mock_detail_player'] = p['id']
        with row[2]:
            pos_cls = POSITION_CLASS.get(p['position'], '')
            st.markdown(f'<div style="padding-top:9px"><span class="mock-pos {pos_cls}">{html.escape(p["position"])}</span></div>', unsafe_allow_html=True)
        with row[3]:
            st.markdown(f'<div style="padding-top:11px;color:#fff;font-size:10px;font-weight:900;text-align:center">{p["adp"]:.1f}</div>', unsafe_allow_html=True)
        with row[4]:
            if st.button('＋', key=f"queue_{p['id']}", help='Add to queue', use_container_width=True):
                queue_add(state, p['id']); st.rerun()
        with row[5]:
            if st.button('DRAFT', key=f"draft_{p['id']}", use_container_width=True, disabled=not can_draft):
                make_pick(state, p['id'], source='user'); advance_cpu_until_user(state); st.rerun()

    detail_id = st.session_state.get('mock_detail_player')
    detail = get_player(state, detail_id) if detail_id else None
    if detail:
        with st.expander('Player Details', expanded=True):
            _render_player_details(detail, history, weekly)


def _render_queue(state: dict[str, Any]) -> None:
    with st.expander(f"Draft Queue ({len(state['queue'])})", expanded=False):
        if not state["queue"]: st.caption("Your queue is empty.")
        for pid in list(state["queue"]):
            p = get_player(state, pid)
            if not p: continue
            cols = st.columns([3, 1, 1, 1])
            with cols[0]: st.write(f"**{p['name']}** · {p['position']} · ADP {p['adp']:.1f}")
            with cols[1]:
                if st.button("↑", key=f"qu_{pid}"): queue_move(state, pid, -1); st.rerun()
            with cols[2]:
                if st.button("↓", key=f"qd_{pid}"): queue_move(state, pid, 1); st.rerun()
            with cols[3]:
                if st.button("×", key=f"qr_{pid}"): queue_remove(state, pid); st.rerun()


def _render_roster(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock-section-title">MY TEAM</div>', unsafe_allow_html=True)
    needs = roster_needs(state, state["userTeamId"])
    needed = [f"{k} {v}" for k, v in needs.items() if v > 0 and k != "BENCH"]
    st.markdown(f'<div class="mock-subtle">Needs: {" · ".join(needed) if needed else "Starting lineup filled"}</div>', unsafe_allow_html=True)
    for slot, player in roster_slots(state, state["userTeamId"]):
        st.markdown(f'<div class="mock-roster-row"><div class="mock-roster-slot">{slot}</div><div class="mock-roster-name">{html.escape(player["name"]) + " · " + player["position"] if player else "—"}</div></div>', unsafe_allow_html=True)


def _render_recent(state: dict[str, Any]) -> None:
    with st.expander("Recent Picks / Draft History", expanded=False):
        if not state["picks"]: st.caption("No picks yet.")
        for pick in reversed(state["picks"]):
            team = team_by_id(state, pick["teamId"])
            st.markdown(f'<div class="mock-history">#{pick["pickNumber"]} · R{pick["round"]} · <b>{html.escape(pick["playerName"])}</b> ({pick["position"]}) → {html.escape(team["name"])}</div>', unsafe_allow_html=True)


def _render_board(state: dict[str, Any]) -> None:
    teams = int(state['settings']['teamsCount'])
    rounds = int(state['settings']['rounds'])
    cols_css = f"54px repeat({teams}, 96px)"

    st.markdown(
        '<div class="mock-board-legend">'
        '<span class="mock-legend-item pos-qb">QB</span>'
        '<span class="mock-legend-item pos-rb">RB</span>'
        '<span class="mock-legend-item pos-wr">WR</span>'
        '<span class="mock-legend-item pos-te">TE</span>'
        '<span class="mock-legend-item pos-dst">D/ST</span>'
        '<span class="mock-legend-item pos-k">K</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    parts = [f'<div class="mock-board" style="grid-template-columns:{cols_css}">', '<div class="mock-board-head">ROUND</div>']
    for t in state['teams']:
        parts.append(f'<div class="mock-board-head {"mine" if t["isUser"] else ""}">{html.escape(t["name"])}</div>')

    pick_map = {int(p['pickNumber']): p for p in state['picks']}
    for rnd in range(1, rounds + 1):
        parts.append(f'<div class="mock-board-head">R{rnd}</div>')
        for team_number in range(1, teams + 1):
            overall = (rnd - 1) * teams + (team_number if rnd % 2 else teams - team_number + 1)
            pick = pick_map.get(overall)
            team_id = f't{team_number}'
            mine = team_id == state['userTeamId']
            current = overall == state['currentOverallPick'] and state['status'] == 'active'
            pos_cls = POSITION_CLASS.get(pick['position'], '') if pick else ''
            cls = f'mock-board-cell {pos_cls} {"mine" if mine else ""} {"current" if current else ""}'
            if pick:
                body = (
                    f'<div class="mock-pick-no">#{overall}</div>'
                    f'<div class="mock-pick-player">{html.escape(pick["playerName"])}</div>'
                    f'<div class="mock-pick-meta">{html.escape(pick["position"])} · {html.escape(pick["nflTeam"] or "—")}</div>'
                )
            else:
                body = f'<div class="mock-pick-no">#{overall}</div>'
            parts.append(f'<div class="{cls}">{body}</div>')
    parts.append('</div>')
    st.markdown('<div class="mock-board-wrap">' + ''.join(parts) + '</div>', unsafe_allow_html=True)


def _render_ask_shiva(state: dict[str, Any], history: pd.DataFrame, roi: pd.DataFrame, rankings: pd.DataFrame, weekly: pd.DataFrame, ask_shiva_func, api_key: str | None) -> None:
    with st.expander("🧠 Ask Shiva — Live Draft", expanded=False):
        quick = st.columns(3)
        quick_questions = ["Who should I draft?", "RB or WR?", "Best value?"]
        for col, q in zip(quick, quick_questions):
            with col:
                if st.button(q, key=f"mock_shiva_{q}", use_container_width=True): st.session_state["mock_shiva_prompt"] = q
        prompt = st.text_input("Ask about this live board", value=st.session_state.get("mock_shiva_prompt", ""), key="mock_shiva_input")
        if st.button("ASK SHIVA GPT", key="mock_ask_shiva", use_container_width=True):
            if not prompt.strip(): st.warning("Ask a draft question first.")
            elif not api_key: st.warning("Connect the OpenAI API key in Shiva Intelligence first.")
            else:
                with st.spinner("Shiva is reading the live board..."):
                    st.session_state["mock_shiva_answer"] = ask_shiva_func(
                        question=prompt, history=history, roi=roi, rankings=rankings, weekly=weekly,
                        api_key=api_key, draft_context=full_draft_context(state),
                    )
        answer = st.session_state.get("mock_shiva_answer")
        if answer:
            st.markdown(f'<div class="report"><div class="report-title">🧠 SHIVA LIVE DRAFT</div><div class="report-answer">{html.escape(str(answer.get("answer") or ""))}</div><div class="report-note">{html.escape(str(answer.get("why") or ""))}</div></div>', unsafe_allow_html=True)


def _render_complete(state: dict[str, Any], db_path) -> None:
    st.markdown('<div class="mock-complete"><h2>DRAFT COMPLETE</h2><div class="mock-subtle">Final board, roster and every selection are locked below.</div></div>', unsafe_allow_html=True)
    save_key = f"mock_saved_{state['draftId']}"
    if not st.session_state.get(save_key):
        try:
            save_completed_draft(state, db_path); st.session_state[save_key] = True
        except Exception as exc: st.warning(f"Draft completed, but persistence could not save it: {exc}")
    _render_board(state); _render_roster(state); _render_recent(state)
    pos_counts: dict[str, int] = {}
    for p in team_by_id(state, state["userTeamId"])["roster"]: pos_counts[p["position"]] = pos_counts.get(p["position"], 0) + 1
    st.write("**Position totals:** " + " · ".join(f"{k} {v}" for k, v in sorted(pos_counts.items())))


def render_mock_draft_room(
    rankings: pd.DataFrame,
    weekly: pd.DataFrame,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    db_path,
    ask_shiva_func,
    api_key: str | None,
) -> None:
    _css()
    st.markdown('<div class="hero"><div class="kicker">🧩 Mock Draft</div><div class="hero-title">2026 Live Interactive Draft Room</div><div class="hero-sub">One draft state. Switch between Players and Draft Board without losing a pick, queue, roster or timer.</div></div>', unsafe_allow_html=True)

    if _pool_key() not in st.session_state:
        st.session_state[_pool_key()] = build_player_pool(rankings, weekly)
    original_pool = st.session_state[_pool_key()]
    if not original_pool:
        st.error("No verified 2026 ranking rows are available for the draft room."); return

    state = st.session_state.get(_state_key())
    if state is None:
        with st.form("mock_setup"):
            a, b, c = st.columns(3)
            with a: teams = st.selectbox("Teams", [8, 10, 12], index=1)
            with b: slot = st.number_input("Draft Position", 1, int(teams), min(4, int(teams)), 1)
            with c: scoring = st.selectbox("Scoring", ["PPR", "Half PPR", "Standard"], index=0)
            d, e = st.columns(2)
            with d: rounds = st.number_input("Rounds", 10, 20, sum(DEFAULT_ROSTER.values()), 1)
            with e: seconds = st.selectbox("Seconds / Pick", [30, 45, 60, 90, 120], index=2)
            with st.expander("Roster Settings", expanded=False):
                rcols = st.columns(3); custom = {}
                keys = list(DEFAULT_ROSTER)
                for i, key in enumerate(keys):
                    with rcols[i % 3]: custom[key] = st.number_input(key, 0, 10, int(DEFAULT_ROSTER[key]), 1, key=f"mock_roster_{key}")
            start = st.form_submit_button("START MOCK DRAFT", use_container_width=True)
        if start:
            state = initialize_draft(original_pool, int(teams), int(slot), scoring, custom, int(rounds), int(seconds))
            start_draft(state); advance_cpu_until_user(state)
            st.session_state[_state_key()] = state; st.rerun()
        with st.expander("Previous Mock Drafts", expanded=False):
            try:
                saved = list_saved_drafts(db_path)
                if not saved: st.caption("No completed mocks saved yet.")
                for row in saved:
                    cols = st.columns([3, 1])
                    with cols[0]: st.write(f"2026 · {row['teams_count']} teams · {row['scoring']} · Slot {row['draft_position']}")
                    with cols[1]:
                        if st.button("Open", key=f"open_mock_{row['draft_id']}"):
                            loaded = load_saved_draft(db_path, row["draft_id"])
                            if loaded: st.session_state[_state_key()] = loaded; st.rerun()
            except Exception as exc: st.caption(f"Previous mocks unavailable: {exc}")
        return

    if state["status"] == "ready": start_draft(state)
    if state["status"] == "active" and not state["paused"] and state["currentTeam"] != state["userTeamId"]:
        advance_cpu_until_user(state)
    st.session_state[_state_key()] = state

    if state["status"] == "complete":
        _render_complete(state, db_path)
        if st.button("START NEW MOCK", use_container_width=True):
            del st.session_state[_state_key()]; st.rerun()
        return

    _render_top_status(state)
    _live_timer_fragment()
    _render_controls(state, original_pool)
    _render_recommendations(state)

    view_cols = st.columns(2)
    with view_cols[0]:
        if st.button("👥 PLAYERS", type="primary" if st.session_state.get("mock_room_view", "PLAYERS") == "PLAYERS" else "secondary", use_container_width=True): st.session_state["mock_room_view"] = "PLAYERS"
    with view_cols[1]:
        if st.button("▦ DRAFT BOARD", type="primary" if st.session_state.get("mock_room_view", "PLAYERS") == "BOARD" else "secondary", use_container_width=True): st.session_state["mock_room_view"] = "BOARD"
    view = st.session_state.get("mock_room_view", "PLAYERS")

    if view == "BOARD": _render_board(state)
    else: _render_available(state, history, weekly)

    _render_queue(state)
    _render_roster(state)
    _render_recent(state)
    _render_ask_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
