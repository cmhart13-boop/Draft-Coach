from pathlib import Path
import re

# ---------------- shiva_app_v2.py ----------------
app_path = Path('shiva_app_v2.py')
app = app_path.read_text()

# Player profiles need DOB context for season-specific age.
app = app.replace(
    'render_player_profile(player,rankings,weekly,history)',
    'render_player_profile(player,rankings,weekly,history,births)',
)

# Link player names inside Ask Shiva output without changing the model answer.
if 'def _linkify_player_names(' not in app:
    anchor = '\ndef _ask_shiva(rankings: pd.DataFrame, history: pd.DataFrame, roi: pd.DataFrame, weekly: pd.DataFrame) -> None:\n'
    helper = r'''
def _linkify_player_names(text: str, rankings: pd.DataFrame) -> str:
    """Escape model text, then turn exact loaded player names into profile links."""
    value = escape(str(text or ""))
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:
        return value
    names = sorted({str(x) for x in rankings["player_name"].dropna() if str(x).strip()}, key=len, reverse=True)
    for name in names:
        escaped_name = escape(name)
        if escaped_name.casefold() not in value.casefold():
            continue
        href = escape(player_profile_href(name), quote=True)
        pattern = re.compile(re.escape(escaped_name), flags=re.IGNORECASE)
        value = pattern.sub(lambda m: f'<a class="directory-name" href="{href}" target="_self">{m.group(0)}</a>', value)
    return value

'''
    app = app.replace(anchor, helper + anchor, 1)
    if 'import re\n' not in app:
        app = app.replace('import os\n', 'import os\nimport re\n', 1)

old_answer = "st.markdown(f'<div class=\"league-card\" style=\"border-color:#2ba1d7\"><div style=\"font-size:11px;color:#4ed4ff;font-weight:1000\">SHIVA ANSWER</div><div style=\"font-size:23px;font-weight:1000;color:#dfff00;margin-top:8px\">{escape(str(rep.get(\"answer\") or \"\"))}</div><div style=\"font-size:14px;color:#d6e0e6;line-height:1.45;margin-top:8px\">{escape(str(rep.get(\"why\") or \"\"))}</div></div>',unsafe_allow_html=True)"
new_answer = "st.markdown(f'<div class=\"league-card\" style=\"border-color:#2ba1d7\"><div style=\"font-size:11px;color:#4ed4ff;font-weight:1000\">SHIVA ANSWER</div><div style=\"font-size:23px;font-weight:1000;color:#dfff00;margin-top:8px\">{_linkify_player_names(str(rep.get(\"answer\") or \"\"), rankings)}</div><div style=\"font-size:14px;color:#d6e0e6;line-height:1.45;margin-top:8px\">{_linkify_player_names(str(rep.get(\"why\") or \"\"), rankings)}</div></div>',unsafe_allow_html=True)"
app = app.replace(old_answer, new_answer)

app_path.write_text(app)

# ---------------- mock_draft_ui_v2.py ----------------
mock_path = Path('mock_draft_ui_v2.py')
mock = mock_path.read_text()

# Expand engine imports for a real live room clock + controls + results.
mock = mock.replace(
    '    advance_cpu_until_user,\n    build_player_pool,',
    '    advance_cpu_until_user,\n    auto_pick_user,\n    build_player_pool,',
)
mock = mock.replace(
    '    make_pick,\n    queue_add,',
    '    make_pick,\n    pause_draft,\n    queue_add,',
)
mock = mock.replace(
    '    recommendation_groups,\n    roster_slots,\n    start_draft,',
    '    recommendation_groups,\n    restart_draft,\n    resume_draft,\n    roster_slots,\n    start_draft,',
)
mock = mock.replace(
    '    team_by_id,\n    undo_last_pick,',
    '    team_by_id,\n    timer_remaining,\n    undo_last_pick,',
)

# Make the reference tabs/player list more compact and include a live status strip.
css_insert = r'''
.mock2-status{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:8px 0}.mock2-statusbox{background:#071018;border:1px solid #24394a;border-radius:9px;padding:8px}.mock2-status-label{font-size:8px;color:#90a0ad;font-weight:1000;letter-spacing:.06em}.mock2-status-value{font-size:14px;color:#fff;font-weight:1000;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mock2-status-value.you{color:#dcff00}.mock2-controlbar [data-testid="stHorizontalBlock"]{gap:5px!important}.mock2-controlbar button{min-height:40px!important;font-size:10px!important;padding:5px!important}.mock2-result{display:grid;grid-template-columns:45px minmax(0,1fr) 70px;gap:7px;align-items:center;padding:8px;border-bottom:1px solid #21303b}.mock2-result-pick{color:#aab5be;font-size:11px;font-weight:1000}.mock2-result-player{color:#fff!important;text-decoration:none!important;font-size:13px;font-weight:1000}.mock2-result-team{font-size:10px;color:#c7d0d7;text-align:right}.mock2-settings{background:#071018;border:1px solid #263b4e;border-radius:12px;padding:10px;margin:8px 0}.mock2-backrow{display:grid;grid-template-columns:44px 1fr 44px;align-items:center;margin:0 0 3px}.mock2-backlink{text-decoration:none!important;color:#fff!important;font-size:28px;text-align:left}.mock2-gear{text-align:right;font-size:22px}.mock2-timer.live{min-width:74px;text-align:center}.mock2-board-wrap{max-width:100%;-webkit-overflow-scrolling:touch}.mock2-name:hover,.mock2-boardname:hover,.mock2-roster-player:hover,.mock2-result-player:hover{text-decoration:underline!important}
'''
if '.mock2-status{' not in mock:
    mock = mock.replace('</style>', css_insert + '\n</style>', 1)

# Add team filtering next to search and position.
old_filters = '''    search = st.text_input("Search players", placeholder="⌕  Search players...", key="mock2_search", label_visibility="collapsed")
    positions = ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"]
    pos = st.selectbox("Position", positions, index=0, key="mock2_pos", label_visibility="collapsed")'''
new_filters = '''    filter_cols = st.columns([1.5, 1, 1], gap="small")
    with filter_cols[0]:
        search = st.text_input("Search players", placeholder="⌕  Search players...", key="mock2_search", label_visibility="collapsed")
    positions = ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"]
    with filter_cols[1]:
        pos = st.selectbox("Position", positions, index=0, key="mock2_pos", label_visibility="collapsed")
    all_teams = sorted({str(p.get("team") or "") for p in state.get("availablePlayers", []) if p.get("team")})
    with filter_cols[2]:
        nfl_team = st.selectbox("NFL Team", ["ALL"] + all_teams, key="mock2_nfl_team", label_visibility="collapsed")'''
mock = mock.replace(old_filters, new_filters)
mock = mock.replace(
    '    if pos != "ALL":\n        pool = [p for p in pool if p.get("position") == pos]\n',
    '    if pos != "ALL":\n        pool = [p for p in pool if p.get("position") == pos]\n    if nfl_team != "ALL":\n        pool = [p for p in pool if str(p.get("team") or "") == nfl_team]\n',
    1,
)

# Replace the static LIVE badge with actual countdown time.
old_clock = '''    if on_clock:
        st.markdown(f'<div class="mock2-onclock"><div><div class="mock2-clock-label">You\\'re on the clock!</div><div class="mock2-clock-pick">Pick {state.get("currentRound")}.{((int(state.get("currentOverallPick",1))-1)%int(state["settings"]["teamsCount"]))+1:02d}</div></div><div class="mock2-timer">LIVE</div></div>', unsafe_allow_html=True)
        if st.button("🤖 WHO SHOULD I PICK?", key="mock2_shiva_btn", use_container_width=True, type="primary"):
            _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)'''
new_clock = '''    if on_clock:
        remain = timer_remaining(state)
        mins, secs = divmod(max(0, int(remain)), 60)
        st.markdown(f'<div class="mock2-onclock"><div><div class="mock2-clock-label">You\\'re on the clock!</div><div class="mock2-clock-pick">Pick {state.get("currentRound")}.{((int(state.get("currentOverallPick",1))-1)%int(state["settings"]["teamsCount"]))+1:02d}</div></div><div class="mock2-timer live">{mins:02d}:{secs:02d}</div></div>', unsafe_allow_html=True)
        if remain <= 0:
            auto_pick_user(state)
            advance_cpu_until_user(state)
            st.rerun()
        if st.button("🤖 WHO SHOULD I PICK?", key="mock2_shiva_btn", use_container_width=True, type="primary"):
            _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)'''
mock = mock.replace(old_clock, new_clock)

# Add full results view.
if 'def _render_results(' not in mock:
    marker = '\ndef render_mock_draft_room_v2('
    results_func = r'''
def _render_results(state: dict[str, Any]) -> None:
    st.markdown('<div class="mock2-section">RESULTS</div>', unsafe_allow_html=True)
    if not state.get("picks"):
        st.info("No selections have been made yet.")
        return
    for pick in state["picks"]:
        team = team_by_id(state, pick["teamId"])
        href = _player_href(str(pick["playerName"]))
        st.markdown(
            f'<div class="mock2-result"><div class="mock2-result-pick">#{pick["pickNumber"]}<br>R{pick["round"]}</div><div><a class="mock2-result-player" href="{href}" target="_self">{html.escape(str(pick["playerName"]))}</a><div class="mock2-meta">{html.escape(str(pick["position"]))} · {html.escape(str(pick.get("nflTeam") or "—"))}</div></div><div class="mock2-result-team">{html.escape(str(team["name"]))}</div></div>',
            unsafe_allow_html=True,
        )

'''
    mock = mock.replace(marker, '\n' + results_func + marker, 1)

# Replace render_mock_draft_room_v2 body with reference header/tabs, preserving centralized engine.
start = mock.index('def render_mock_draft_room_v2(')
prefix = mock[:start]
new_render = r'''def render_mock_draft_room_v2(rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, roi: pd.DataFrame, db_path, ask_shiva_func, api_key: str | None) -> None:
    _css()
    st.markdown('<div class="mock2-backrow"><a class="mock2-backlink" href="?page=Home" target="_self">‹</a><div><div class="mock2-title">MOCK DRAFT</div><div class="mock2-sub">2026 · Live Interactive Draft Room</div></div><div class="mock2-gear">⚙</div></div>', unsafe_allow_html=True)

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
            c5, c6 = st.columns(2)
            with c5:
                seconds = st.selectbox("Seconds / Pick", [30, 45, 60, 90, 120], index=3)
            with c6:
                st.caption("Default roster: QB1 · RB2 · WR2 · TE1 · FLEX1 · D/ST1 · K1 · Bench7")
            with st.expander("Roster Settings", expanded=False):
                rcols = st.columns(3)
                custom = {}
                for i, roster_key in enumerate(DEFAULT_ROSTER):
                    with rcols[i % 3]:
                        custom[roster_key] = st.number_input(roster_key, 0, 10, int(DEFAULT_ROSTER[roster_key]), 1, key=f"mock2_roster_{roster_key}")
            if st.form_submit_button("START MOCK DRAFT", use_container_width=True, type="primary"):
                state = initialize_draft(pool, int(teams), int(slot), scoring, custom, int(rounds), int(seconds))
                start_draft(state)
                advance_cpu_until_user(state)
                st.session_state[STATE_KEY] = state
                st.rerun()
        return

    if state.get("status") == "active" and not state.get("paused") and state.get("currentTeam") != state.get("userTeamId"):
        advance_cpu_until_user(state)
    st.session_state[STATE_KEY] = state

    teams_count = int(state["settings"]["teamsCount"])
    scoring = str(state["settings"]["scoring"])
    st.markdown(f'<div class="mock2-sub">{teams_count}-Team {html.escape(scoring)} · Snake Draft</div>', unsafe_allow_html=True)
    current_team = team_by_id(state, state["currentTeam"])
    is_user = state["currentTeam"] == state["userTeamId"]
    st.markdown(
        f'<div class="mock2-status"><div class="mock2-statusbox"><div class="mock2-status-label">ROUND</div><div class="mock2-status-value">{state["currentRound"]}</div></div><div class="mock2-statusbox"><div class="mock2-status-label">OVERALL PICK</div><div class="mock2-status-value">{state["currentOverallPick"]}</div></div><div class="mock2-statusbox"><div class="mock2-status-label">CURRENT TEAM</div><div class="mock2-status-value {"you" if is_user else ""}">{"YOUR PICK" if is_user else html.escape(current_team["name"])}</div></div></div>',
        unsafe_allow_html=True,
    )

    tabs = ["PLAYERS", "DRAFT BOARD", "QUEUE", "TEAM", "RESULTS"]
    if "mock2_tab" not in st.session_state:
        st.session_state["mock2_tab"] = "PLAYERS"
    tab_cols = st.columns(5, gap="small")
    for col, tab_name in zip(tab_cols, tabs):
        with col:
            if st.button(tab_name, key=f"mock2_tab_{tab_name}", use_container_width=True, type="primary" if st.session_state["mock2_tab"] == tab_name else "secondary"):
                st.session_state["mock2_tab"] = tab_name
                st.rerun()

    with st.container(key="mock2-controlbar"):
        ctrls = st.columns(4, gap="small")
        with ctrls[0]:
            if st.button("⏸ PAUSE", key="mock2_pause", use_container_width=True, disabled=state.get("paused") or state.get("status") != "active"):
                pause_draft(state); st.rerun()
        with ctrls[1]:
            if st.button("▶ RESUME", key="mock2_resume", use_container_width=True, disabled=not state.get("paused") or state.get("status") != "active"):
                resume_draft(state); st.rerun()
        with ctrls[2]:
            if st.button("↶ UNDO", key="mock2_undo", use_container_width=True, disabled=not state.get("picks")):
                undo_last_pick(state); st.rerun()
        with ctrls[3]:
            if st.button("↻ RESTART", key="mock2_restart", use_container_width=True):
                st.session_state[STATE_KEY] = restart_draft(state, pool)
                st.rerun()

    tab = st.session_state["mock2_tab"]
    if tab == "PLAYERS":
        _render_player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    elif tab == "DRAFT BOARD":
        _render_board(state)
    elif tab == "QUEUE":
        _render_queue(state)
    elif tab == "TEAM":
        _render_team(state)
    else:
        _render_results(state)
'''
mock = prefix + new_render
mock_path.write_text(mock)
print('Production v2 reference layout patch applied.')
