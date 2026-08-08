from pathlib import Path
import re

path = Path("mock_draft_ui.py")
text = path.read_text()

if "from player_profile import open_player_profile" not in text:
    text = text.replace("import streamlit as st\n", "import streamlit as st\n\nfrom player_profile import open_player_profile\n", 1)

new_css = '''def _css() -> None:
    st.markdown(
        r"""
<style>
.mock-shell{width:100%;max-width:100%;overflow-x:hidden}.mock-page-title{text-align:center;font-size:23px;font-weight:1000;letter-spacing:.03em}.mock-page-sub{text-align:center;color:#e7edf2;font-size:12px;margin-top:2px}.mock-back button,.mock-gear button{border:0!important;background:transparent!important;box-shadow:none!important;font-size:24px!important;padding:0!important;min-height:42px!important}
.mock-topbar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:8px 0}.mock-chip{background:#08131c;border:1px solid #1c3548;border-radius:10px;padding:8px;min-width:0}.mock-chip-label{color:#8899a7;font-size:9px;font-weight:1000;text-transform:uppercase;letter-spacing:.08em}.mock-chip-value{color:#fff;font-size:15px;font-weight:1000;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mock-chip-value.you{color:#d8ff00}.mock-section-title{font-size:13px;font-weight:1000;color:#fff;margin:12px 0 6px}.mock-subtle{font-size:11px;color:#9fabb6;line-height:1.35}
.mock-list-head{display:grid;grid-template-columns:34px minmax(0,1fr) 44px 54px;gap:5px;align-items:center;padding:7px 8px;background:#08131c;border:1px solid #183247;border-bottom:0;border-radius:10px 10px 0 0;color:#8493a0;font-size:9px;font-weight:1000;letter-spacing:.06em;text-transform:uppercase}.mock-rank{font-size:11px;color:#dce5eb;font-weight:1000;text-align:center}.mock-player-name{font-size:12px;color:#fff;font-weight:1000}.mock-player-meta{font-size:9px;color:#d7dee4;line-height:1.25;margin-top:2px}.mock-pos{font-size:10px;font-weight:1000;border-radius:7px;padding:5px 6px;text-align:center;min-width:34px;display:inline-block}
.pos-qb{background:#b62327;color:#fff}.pos-rb{background:#e66d00;color:#fff}.pos-wr{background:#0878bd;color:#fff}.pos-te{background:#3b942c;color:#fff}.pos-dst{background:#73460f;color:#fff}.pos-k{background:#454a51;color:#fff}.pos-flex{background:#7430a7;color:#fff}
.mock-rec{display:flex;gap:7px;overflow-x:auto;padding:2px 0 8px;scrollbar-width:none}.mock-rec::-webkit-scrollbar{display:none}.mock-rec-card{flex:0 0 136px;background:#0a1721;border:1px solid #1c3548;border-radius:11px;padding:8px}.mock-rec-card button{min-height:52px!important;text-align:left!important;background:transparent!important;border:0!important;box-shadow:none!important;padding:3px!important}.mock-rec-card button p{font-size:12px!important;line-height:1.2!important}
.mock-player-row{border-radius:8px;padding:2px 3px;margin:4px 0}.st-key-playerrow_QB{background:#8f1e22}.st-key-playerrow_RB{background:#bc5700}.st-key-playerrow_WR{background:#06669f}.st-key-playerrow_TE{background:#2f7425}.st-key-playerrow_DST{background:#5d390d}.st-key-playerrow_K{background:#353a40}
[class*="st-key-playerrow_QB_"]{background:linear-gradient(90deg,#a71e22,#7d181b)!important;border:1px solid #db393f!important;border-radius:9px;padding:2px 4px;margin:3px 0}[class*="st-key-playerrow_RB_"]{background:linear-gradient(90deg,#d66300,#a94800)!important;border:1px solid #ff8e2d!important;border-radius:9px;padding:2px 4px;margin:3px 0}[class*="st-key-playerrow_WR_"]{background:linear-gradient(90deg,#0876b9,#05578b)!important;border:1px solid #25a9f5!important;border-radius:9px;padding:2px 4px;margin:3px 0}[class*="st-key-playerrow_TE_"]{background:linear-gradient(90deg,#388d2c,#27651f)!important;border:1px solid #62d550!important;border-radius:9px;padding:2px 4px;margin:3px 0}[class*="st-key-playerrow_DST_"]{background:linear-gradient(90deg,#73460f,#52310b)!important;border:1px solid #a76b22!important;border-radius:9px;padding:2px 4px;margin:3px 0}[class*="st-key-playerrow_K_"]{background:linear-gradient(90deg,#454a51,#33383e)!important;border:1px solid #727981!important;border-radius:9px;padding:2px 4px;margin:3px 0}
[class*="st-key-playerrow_"] button{background:transparent!important;border:0!important;box-shadow:none!important;min-height:44px!important;padding:4px!important}[class*="st-key-playerrow_"] button p{color:#fff!important;font-size:11px!important;line-height:1.15!important;white-space:pre-line!important}
.mock-board-legend{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0 8px}.mock-legend-item{font-size:9px;font-weight:900;padding:5px 8px;border-radius:7px}.st-key-mock_board_scroll{overflow-x:auto!important;overflow-y:hidden!important;border:1px solid #23394a!important;border-radius:12px!important;background:#050b10!important;padding:5px!important;-webkit-overflow-scrolling:touch!important}.st-key-mock_board_scroll [data-testid="stHorizontalBlock"]{min-width:1040px!important;flex-wrap:nowrap!important;gap:4px!important}.st-key-mock_board_scroll button{min-height:72px!important;border-radius:7px!important;padding:4px!important}.st-key-mock_board_scroll button p{white-space:pre-line!important;font-size:9px!important;line-height:1.15!important;font-weight:900!important}.st-key-board_round button{background:#101820!important;color:#93a1ac!important;border-color:#22384a!important}.st-key-board_head button{min-height:42px!important;background:#111b24!important;border-color:#284155!important}.st-key-board_head_mine button{min-height:42px!important;background:#142006!important;border-color:#d8ff00!important;color:#d8ff00!important}[class*="st-key-boardcell_QB_"] button{background:#9c2025!important;border-color:#da3b42!important}[class*="st-key-boardcell_RB_"] button{background:#c85c00!important;border-color:#ff8e2a!important}[class*="st-key-boardcell_WR_"] button{background:#076aa5!important;border-color:#20a3ef!important}[class*="st-key-boardcell_TE_"] button{background:#347d28!important;border-color:#60c850!important}[class*="st-key-boardcell_DST_"] button{background:#66400f!important;border-color:#9a651e!important}[class*="st-key-boardcell_K_"] button{background:#3b4046!important;border-color:#69717a!important}[class*="st-key-boardcell_empty_"] button{background:#0b1218!important;border-color:#1d3040!important;color:#63717c!important}[class*="_mine_"] button{box-shadow:inset 0 0 0 2px #d8ff00!important}[class*="_current_"] button{box-shadow:inset 0 0 0 3px #d8ff00,0 0 12px rgba(216,255,0,.35)!important}
.mock-roster-row{display:grid;grid-template-columns:42px minmax(0,1fr);gap:7px;padding:8px 0;border-bottom:1px solid #172937}.mock-roster-slot{font-size:10px;color:#d8ff00;font-weight:1000}.mock-roster-name{font-size:12px;color:#fff;font-weight:800}.mock-history{font-size:11px;padding:7px 0;border-bottom:1px solid #172937;color:#ddd}.mock-complete{background:linear-gradient(145deg,#173317,#121712);border:1px solid #d8ff00;border-radius:18px;padding:18px;text-align:center;margin:12px 0}.mock-complete h2{color:#d8ff00!important;margin:0}.mock-view-tabs [data-testid="stSegmentedControl"] button{min-height:42px!important;border-radius:0!important;border:0!important;border-bottom:2px solid transparent!important;background:transparent!important}.mock-view-tabs [data-testid="stSegmentedControl"] button[aria-pressed="true"]{border-bottom-color:#d8ff00!important;color:#d8ff00!important}.mock-view-tabs [data-testid="stSegmentedControl"] button p{font-size:10px!important;font-weight:1000!important}.shiva-live-card{background:linear-gradient(135deg,#071c2d,#07121b)!important;border-color:#124b70!important}
@media(max-width:430px){html,body,.stApp,.block-container{max-width:100vw!important;overflow-x:hidden!important}.mock-topbar{grid-template-columns:repeat(3,minmax(0,1fr))}.mock-chip{padding:7px 5px}.mock-chip-value{font-size:13px}.st-key-mock_board_scroll{max-width:calc(100vw - 24px)!important}.mock-view-tabs [data-testid="stSegmentedControl"]{overflow-x:auto!important;justify-content:flex-start!important}.mock-view-tabs [data-testid="stSegmentedControl"] button{flex:0 0 auto!important;min-width:72px!important}}
</style>
""",
        unsafe_allow_html=True,
    )
'''
text = re.sub(r"def _css\(\) -> None:.*?\n\ndef _state_key\(\)", new_css + "\n\ndef _state_key()", text, flags=re.S)

new_recs = '''def _render_recommendations(state: dict[str, Any]) -> None:
    groups = recommendation_groups(state)
    choice = st.segmented_control("Recommendations", list(groups), default="BEST AVAILABLE", key="mock_rec_type", label_visibility="collapsed")
    players = groups.get(choice or "BEST AVAILABLE", [])[:5]
    cols = st.columns(min(5, max(1, len(players))), gap="small") if players else []
    for i, (col, player) in enumerate(zip(cols, players)):
        with col:
            pos = player.get("position", "")
            st.markdown(f'<span class="mock-pos {POSITION_CLASS.get(pos, "")}">{html.escape(pos)}</span>', unsafe_allow_html=True)
            if st.button(player["name"], key=f"rec_profile_{i}_{player['id']}", use_container_width=True):
                open_player_profile(player["name"], "Mock Draft")
                st.rerun()
            st.caption(f"ADP {player['adp']:.1f} · {player.get('team') or '—'}")
'''
text = re.sub(r"def _render_recommendations\(state: dict\[str, Any\]\) -> None:.*?\n\ndef _render_available", new_recs + "\n\ndef _render_available", text, flags=re.S)

new_available = '''def _render_available(state: dict[str, Any], history: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="mock-section-title">AVAILABLE PLAYERS</div>', unsafe_allow_html=True)
    filter_cols = st.columns([1.5, 1, 1], gap="small")
    with filter_cols[0]:
        search = st.text_input("Search", placeholder="⌕  Search players...", key="mock_search", label_visibility="collapsed")
    with filter_cols[1]:
        pos = st.selectbox("Position", ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"], key="mock_position_filter", label_visibility="collapsed")
    pool0 = list(state["availablePlayers"])
    teams = sorted({str(p.get("team") or "") for p in pool0 if p.get("team")})
    with filter_cols[2]:
        team_filter = st.selectbox("Team", ["ALL"] + teams, key="mock_team_filter", label_visibility="collapsed")
    pool = pool0
    if search.strip():
        pool = [p for p in pool if search.lower().strip() in p["name"].lower()]
    if pos != "ALL":
        pool = [p for p in pool if p["position"] == pos]
    if team_filter != "ALL":
        pool = [p for p in pool if str(p.get("team") or "") == team_filter]
    pool = sorted(pool, key=lambda p: (p.get("rank", 9999), p.get("adp", 9999), p["name"]))[:80]
    st.markdown('<div class="mock-list-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>ADP</div></div>', unsafe_allow_html=True)
    for i, p in enumerate(pool):
        can_draft = state["status"] == "active" and not state["paused"] and state["currentTeam"] == state["userTeamId"]
        slug = "DST" if p["position"] == "D/ST" else p["position"]
        with st.container(key=f"playerrow_{slug}_{i}"):
            row = st.columns([0.45, 3.7, 0.72, 0.72, 0.86, 0.92], gap="small")
            with row[0]:
                st.markdown(f'<div style="padding-top:11px;text-align:center;color:#fff;font-size:11px;font-weight:1000">{p["rank"]}</div>', unsafe_allow_html=True)
            with row[1]:
                if st.button(f"{p['name']}\n{p.get('team') or '—'}" + (f" · Bye {p['bye']}" if p.get('bye') else ""), key=f"profile_{i}_{p['id']}", use_container_width=True):
                    open_player_profile(p["name"], "Mock Draft")
                    st.rerun()
            with row[2]:
                st.markdown(f'<div style="padding-top:9px"><span class="mock-pos {POSITION_CLASS.get(p["position"], "")}">{html.escape(p["position"])}</span></div>', unsafe_allow_html=True)
            with row[3]:
                st.markdown(f'<div style="padding-top:12px;color:#fff;font-size:10px;font-weight:1000;text-align:center">{p["adp"]:.1f}</div>', unsafe_allow_html=True)
            with row[4]:
                if st.button("＋", key=f"queue_{i}_{p['id']}", help="Add to queue", use_container_width=True):
                    queue_add(state, p["id"]); st.rerun()
            with row[5]:
                if st.button("DRAFT", key=f"draft_{i}_{p['id']}", use_container_width=True, disabled=not can_draft):
                    make_pick(state, p["id"], source="user"); advance_cpu_until_user(state); st.rerun()
'''
text = re.sub(r"def _render_available\(state: dict\[str, Any\], history: pd.DataFrame, weekly: pd.DataFrame\) -> None:.*?\n\ndef _render_queue", new_available + "\n\ndef _render_queue", text, flags=re.S)

new_queue = '''def _render_queue(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock-section-title">DRAFT QUEUE</div>', unsafe_allow_html=True)
    if not state["queue"]:
        st.caption("Your queue is empty. Add players from the Players tab.")
    for i, pid in enumerate(list(state["queue"])):
        p = get_player(state, pid)
        if not p:
            continue
        cols = st.columns([3.2, .65, .65, .65])
        with cols[0]:
            if st.button(f"{p['name']} · {p['position']} · ADP {p['adp']:.1f}", key=f"queue_profile_{i}_{pid}", use_container_width=True):
                open_player_profile(p["name"], "Mock Draft"); st.rerun()
        with cols[1]:
            if st.button("↑", key=f"qu_{i}_{pid}"): queue_move(state, pid, -1); st.rerun()
        with cols[2]:
            if st.button("↓", key=f"qd_{i}_{pid}"): queue_move(state, pid, 1); st.rerun()
        with cols[3]:
            if st.button("×", key=f"qr_{i}_{pid}"): queue_remove(state, pid); st.rerun()
'''
text = re.sub(r"def _render_queue\(state: dict\[str, Any\]\) -> None:.*?\n\ndef _render_roster", new_queue + "\n\ndef _render_roster", text, flags=re.S)

new_roster = '''def _render_roster(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock-section-title">MY TEAM</div>', unsafe_allow_html=True)
    needs = roster_needs(state, state["userTeamId"])
    needed = [f"{k} {v}" for k, v in needs.items() if v > 0 and k != "BENCH"]
    st.markdown(f'<div class="mock-subtle">Needs: {" · ".join(needed) if needed else "Starting lineup filled"}</div>', unsafe_allow_html=True)
    for i, (slot, player) in enumerate(roster_slots(state, state["userTeamId"])):
        cols = st.columns([.8, 4.2])
        with cols[0]:
            st.markdown(f'<div class="mock-roster-slot" style="padding-top:12px">{slot}</div>', unsafe_allow_html=True)
        with cols[1]:
            if player:
                if st.button(f"{player['name']} · {player['position']}", key=f"roster_profile_{i}_{player['id']}", use_container_width=True):
                    open_player_profile(player["name"], "Mock Draft"); st.rerun()
            else:
                st.markdown('<div class="mock-roster-name" style="padding-top:11px">—</div>', unsafe_allow_html=True)
'''
text = re.sub(r"def _render_roster\(state: dict\[str, Any\]\) -> None:.*?\n\ndef _render_recent", new_roster + "\n\ndef _render_recent", text, flags=re.S)

new_recent = '''def _render_recent(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock-section-title">DRAFT RESULTS</div>', unsafe_allow_html=True)
    if not state["picks"]:
        st.caption("No picks yet.")
    for pick in reversed(state["picks"]):
        team = team_by_id(state, pick["teamId"])
        cols = st.columns([1.0, 3.4, 1.4])
        with cols[0]:
            st.markdown(f'<div class="mock-history">#{pick["pickNumber"]}<br>R{pick["round"]}</div>', unsafe_allow_html=True)
        with cols[1]:
            if st.button(pick["playerName"], key=f"history_profile_{pick['pickNumber']}", use_container_width=True):
                open_player_profile(pick["playerName"], "Mock Draft"); st.rerun()
        with cols[2]:
            st.markdown(f'<div class="mock-history">{html.escape(pick["position"])}<br>{html.escape(team["name"])}</div>', unsafe_allow_html=True)
'''
text = re.sub(r"def _render_recent\(state: dict\[str, Any\]\) -> None:.*?\n\ndef _render_board", new_recent + "\n\ndef _render_board", text, flags=re.S)

new_board = '''def _render_board(state: dict[str, Any]) -> None:
    teams = int(state["settings"]["teamsCount"])
    rounds = int(state["settings"]["rounds"])
    st.markdown('<div class="mock-board-legend"><span class="mock-legend-item pos-qb">QB</span><span class="mock-legend-item pos-rb">RB</span><span class="mock-legend-item pos-wr">WR</span><span class="mock-legend-item pos-te">TE</span><span class="mock-legend-item pos-dst">D/ST</span><span class="mock-legend-item pos-k">K</span></div>', unsafe_allow_html=True)
    pick_map = {int(p["pickNumber"]): p for p in state["picks"]}
    with st.container(key="mock_board_scroll"):
        header = st.columns([.58] + [1] * teams, gap="small")
        with header[0]:
            with st.container(key="board_round"):
                st.button("ROUND", key="board_round_head", disabled=True, use_container_width=True)
        for team_number, col in enumerate(header[1:], start=1):
            team = state["teams"][team_number - 1]
            key = "board_head_mine" if team["isUser"] else "board_head"
            with col:
                with st.container(key=f"{key}_{team_number}"):
                    st.button(team["name"], key=f"board_head_btn_{team_number}", disabled=True, use_container_width=True)
        for rnd in range(1, rounds + 1):
            row = st.columns([.58] + [1] * teams, gap="small")
            with row[0]:
                with st.container(key=f"board_round_{rnd}"):
                    st.button(f"R{rnd}", key=f"board_round_btn_{rnd}", disabled=True, use_container_width=True)
            for team_number, col in enumerate(row[1:], start=1):
                overall = (rnd - 1) * teams + (team_number if rnd % 2 else teams - team_number + 1)
                pick = pick_map.get(overall)
                mine = f"t{team_number}" == state["userTeamId"]
                current = overall == state["currentOverallPick"] and state["status"] == "active"
                with col:
                    if pick:
                        slug = "DST" if pick["position"] == "D/ST" else pick["position"]
                        flags = ("_mine" if mine else "") + ("_current" if current else "")
                        with st.container(key=f"boardcell_{slug}_{overall}{flags}"):
                            if st.button(f"#{overall}\n{pick['playerName']}\n{pick['position']} · {pick.get('nflTeam') or '—'}", key=f"board_pick_{overall}", use_container_width=True):
                                open_player_profile(pick["playerName"], "Mock Draft"); st.rerun()
                    else:
                        flags = ("_mine" if mine else "") + ("_current" if current else "")
                        with st.container(key=f"boardcell_empty_{overall}{flags}"):
                            st.button(f"#{overall}\n—", key=f"board_empty_{overall}", disabled=True, use_container_width=True)
'''
text = re.sub(r"def _render_board\(state: dict\[str, Any\]\) -> None:.*?\n\ndef _render_ask_shiva", new_board + "\n\ndef _render_ask_shiva", text, flags=re.S)

new_render = '''def render_mock_draft_room(
    rankings: pd.DataFrame,
    weekly: pd.DataFrame,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    db_path,
    ask_shiva_func,
    api_key: str | None,
) -> None:
    _css()
    head = st.columns([.7, 4.5, .7])
    with head[0]:
        with st.container(key="mock-back"):
            if st.button("‹", key="mock_back_home", use_container_width=True):
                st.session_state.page = "Home"; st.rerun()
    with head[1]:
        st.markdown('<div class="mock-page-title">MOCK DRAFT</div>', unsafe_allow_html=True)
    with head[2]:
        with st.container(key="mock-gear"):
            if st.button("⚙", key="mock_settings_toggle", use_container_width=True):
                st.session_state["mock_show_settings"] = not st.session_state.get("mock_show_settings", False)

    if _pool_key() not in st.session_state:
        st.session_state[_pool_key()] = build_player_pool(rankings, weekly)
    original_pool = st.session_state[_pool_key()]
    if not original_pool:
        st.error("No verified 2026 ranking rows are available for the draft room.")
        return

    state = st.session_state.get(_state_key())
    if state is None:
        st.markdown('<div class="mock-page-sub">2026 · ESPN Full PPR · Snake Draft</div>', unsafe_allow_html=True)
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
    scoring_label = "PPR" if state["settings"]["scoring"] == "PPR" else state["settings"]["scoring"]
    st.markdown(f'<div class="mock-page-sub">{state["settings"]["teamsCount"]}-Team {html.escape(scoring_label)} · Snake Draft</div>', unsafe_allow_html=True)

    if state["status"] == "complete":
        _render_complete(state, db_path)
        if st.button("START NEW MOCK", use_container_width=True):
            del st.session_state[_state_key()]; st.rerun()
        return

    if st.session_state.get("mock_show_settings"):
        with st.expander("Draft Settings", expanded=True):
            st.write(f"**Teams:** {state['settings']['teamsCount']}  ·  **Scoring:** {state['settings']['scoring']}  ·  **Rounds:** {state['settings']['rounds']}  ·  **Clock:** {state['settings']['secondsPerPick']}s")
            st.caption("Restart the draft to change league settings.")

    _render_top_status(state)
    _live_timer_fragment()
    _render_controls(state, original_pool)

    current_view = st.session_state.get("mock_room_view", "PLAYERS")
    options = ["PLAYERS", "DRAFT BOARD", "QUEUE", "TEAM", "RESULTS"]
    if current_view == "BOARD": current_view = "DRAFT BOARD"
    if current_view not in options: current_view = "PLAYERS"
    with st.container(key="mock-view-tabs"):
        view = st.segmented_control("Draft Room", options, default=current_view, key="mock_room_tabs", label_visibility="collapsed") or current_view
    st.session_state["mock_room_view"] = "BOARD" if view == "DRAFT BOARD" else view

    if view == "PLAYERS":
        _render_recommendations(state)
        _render_available(state, history, weekly)
        _render_pick_advisor(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
        _render_ask_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    elif view == "DRAFT BOARD":
        _render_board(state)
    elif view == "QUEUE":
        _render_queue(state)
    elif view == "TEAM":
        _render_roster(state)
    else:
        _render_recent(state)
'''
text = re.sub(r"def render_mock_draft_room\(.*\Z", new_render, text, flags=re.S)

path.write_text(text)
print("Reference mock draft layout integrated.")
