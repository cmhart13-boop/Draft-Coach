from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from mock_draft_engine import (
    DEFAULT_ROSTER, advance_cpu_until_user, build_player_pool, full_draft_context,
    get_player, initialize_draft, make_pick, pause_draft, queue_add, queue_remove,
    resume_draft, roster_slots, start_draft, timer_remaining, undo_last_pick,
)
from player_profile import player_link_html, player_profile_href

STATE_KEY = "mock_draft_state_v2"
POOL_KEY = "mock_draft_original_pool_v2"
TAB_KEY = "mock2_tab"

# Single source of truth for every mock-draft position color treatment.
POSITION_COLORS = {
    "QB": {"card": "#261B38", "border": "#7754A8", "badge": "#9B6FE8"},
    "RB": {"card": "#332411", "border": "#8A5515", "badge": "#F28C18"},
    "WR": {"card": "#102B33", "border": "#24758A", "badge": "#39B5DE"},
    "TE": {"card": "#16332F", "border": "#3C8F84", "badge": "#4DD8C5"},
    "D/ST": {"card": "#342E12", "border": "#A18A21", "badge": "#F0CF32"},
    "DST": {"card": "#342E12", "border": "#A18A21", "badge": "#F0CF32"},
    "DEF": {"card": "#342E12", "border": "#A18A21", "badge": "#F0CF32"},
    "K": {"card": "#351B2A", "border": "#A64B79", "badge": "#E968A5"},
    "FLEX": {"card": "#151515", "border": "#444444", "badge": "#777777"},
}
DEFAULT_POSITION_COLORS = {"card": "#151515", "border": "#444444", "badge": "#777777"}

TABS = (
    ("PLAYERS_AVAILABLE", "PLAYERS AVAILABLE"),
    ("QUEUE", "QUEUE"),
    ("DRAFT_BOARD", "DRAFT BOARD"),
    ("ROSTER", "ROSTER"),
)


def _position_key(pos) -> str:
    key = str(pos or "").upper().strip()
    return "D/ST" if key in {"D/ST", "DST", "DEF"} else key


def _position_style(pos) -> dict[str, str]:
    return POSITION_COLORS.get(_position_key(pos), DEFAULT_POSITION_COLORS)


def _position_slug(pos) -> str:
    key = _position_key(pos)
    return "dst" if key == "D/ST" else key.lower()


def _position_badge(pos) -> str:
    style = _position_style(pos)
    label = "D/ST" if _position_key(pos) == "D/ST" else str(pos or "")
    return (
        f'<span class="position-badge" style="background:{style["badge"]};">'
        f'{html.escape(label)}</span>'
    )


def _css() -> None:
    row_rules = []
    button_rules = []
    for pos in ("QB", "RB", "WR", "TE", "K", "D/ST", "FLEX"):
        slug = _position_slug(pos)
        style = _position_style(pos)
        row_rules.append(
            f'div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-{slug})'
            f'{{background:{style["card"]}!important;border-color:{style["border"]}!important}}'
        )
        button_rules.append(
            f'div[data-testid="stColumn"]:has(.pos-marker-{slug}) button'
            f'{{background:{style["card"]}!important;border-color:{style["border"]}!important;color:{style["badge"]}!important}}'
        )
    position_css = "\n".join(button_rules + row_rules)

    st.markdown(
        f"""
<style>
.mock-title{{text-align:center;font-size:22px;font-weight:1000;line-height:1}}
.mock-sub{{text-align:center;font-size:11px;color:#d7e0e7;margin-top:4px}}
.mock-nav-marker,.pos-marker,.player-row-marker{{display:none!important}}
div[data-testid="stVerticalBlock"]:has(.mock-nav-marker){{gap:0!important}}
div[data-testid="stVerticalBlock"]:has(.mock-nav-marker) div[data-testid="stHorizontalBlock"]{{gap:2px!important;border-bottom:1px solid #27323b;margin:5px 0 8px}}
div[data-testid="stVerticalBlock"]:has(.mock-nav-marker) button{{
  min-height:38px!important;height:38px!important;padding:0 2px!important;border:0!important;border-radius:0!important;
  background:transparent!important;color:#fff!important;font-size:9px!important;font-weight:1000!important;box-shadow:none!important
}}
div[data-testid="stVerticalBlock"]:has(.mock-nav-marker) button[kind="primary"]{{
  color:#dfff00!important;border-bottom:2px solid #dfff00!important;background:transparent!important
}}
div[data-testid="stVerticalBlock"]:has(.mock-nav-marker) button[kind="primary"] p{{color:#dfff00!important}}
.mock-filter-button button{{height:38px!important;min-height:38px!important}}
{position_css}
div[data-testid="stColumn"]:has(.pos-marker) button{{min-height:30px!important;height:30px!important;padding:0!important;font-size:9px!important;border-radius:6px!important}}
.mock-list-head{{display:grid;grid-template-columns:30px minmax(0,1fr) 34px 32px 36px 40px 44px;gap:2px;padding:5px;color:#c4cbd2;font-size:8px;font-weight:900;background:#091017;border-radius:6px;margin-top:4px}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker){{
  border-radius:7px!important;border:1px solid #444!important;padding:2px 4px!important;margin:2px 0!important;
  box-shadow:none!important
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stHorizontalBlock"]{{gap:2px!important;align-items:center!important}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) button{{
  min-height:27px!important;height:27px!important;padding:0 3px!important;border-radius:5px!important;font-size:8px!important;font-weight:1000!important
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) [data-testid="stMarkdownContainer"]{{margin:0!important}}
.mock-rank{{width:23px;height:23px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.18);font-size:10px;font-weight:1000}}
.mock-name{{font-size:10.5px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;line-height:1.05}}
.mock-cell{{font-size:8px;font-weight:900;text-align:center;white-space:nowrap}}
.mock-adp{{font-size:8px;font-weight:1000;text-align:right}}
.position-badge{{display:inline-block;min-width:25px;padding:2px 5px;border-radius:999px;color:#071018;font-size:8px;font-weight:1000;text-align:center;line-height:1.15}}
.queue-row,.team-row{{display:grid;grid-template-columns:48px minmax(0,1fr) 48px;gap:6px;align-items:center;padding:8px;border-bottom:1px solid #1d2a34}}
.slot{{color:#dfff00;font-size:10px;font-weight:1000}}
.section-title{{font-size:14px;font-weight:1000;margin:10px 0 5px}}
.mock-name-plain{{font-size:12px!important;font-weight:900!important;color:#fff!important;text-decoration:none!important}}
.mock-spacer{{height:68px}}
.settings-card{{background:#07121b;border:1px solid #24405a;border-radius:9px;padding:8px;margin:5px 0 8px}}
.settings-line{{font-size:10px;color:#cbd4db}}
.draft-status{{position:fixed;left:50%;bottom:67px;transform:translateX(-50%);width:min(500px,calc(100vw - 20px));z-index:9998;display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;background:#050b10;border:1px solid #25394a;border-radius:9px;padding:8px 9px;box-shadow:0 -5px 20px rgba(0,0,0,.42)}}
.clock-label{{font-size:10px}}.clock-pick{{font-size:13px;font-weight:1000;color:#dfff00}}.clock-team{{font-size:11px;font-weight:900}}.clock-timer{{background:#dfff00;color:#061006;border-radius:6px;padding:6px 8px;font-size:14px;font-weight:1000}}
.board-top{{display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;margin:3px 0 4px}}.board-title{{text-align:center;font-size:17px;font-weight:1000}}.board-round{{text-align:center;font-size:9px;color:#fff}}.board-meta{{text-align:right;font-size:8px}}
.board-legend{{display:flex;justify-content:center;gap:7px;flex-wrap:wrap;margin:4px 0 7px;font-size:7px;font-weight:900}}.legend-dot{{display:inline-block;width:7px;height:7px;border-radius:1px;margin-right:2px}}
.board-wrap{{background:#020609;border:1px solid #1c2b36;border-radius:7px;padding:3px;overflow:hidden}}.draft-board{{display:grid;gap:2px;width:100%}}.team-head{{background:#071018;border:1px solid #26313a;border-radius:3px;padding:4px 0;font-size:6px;font-weight:1000;text-align:center;overflow:hidden}}
.pick-card{{min-height:45px;border-radius:3px;padding:2px 1px;border:1px solid #444;overflow:hidden}}.pick-no{{font-size:6px;color:#fff9}}.pick-name{{font-size:6px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;display:block;line-height:1.05;overflow-wrap:anywhere}}.pick-pos{{font-size:6px;text-align:center;font-weight:900;margin-top:2px}}
.pick-pos .position-badge{{font-size:6px;min-width:20px;padding:1px 4px}}
@media(max-width:390px){{
  div[data-testid="stVerticalBlock"]:has(.mock-nav-marker) button{{font-size:7.6px!important}}
  .mock-list-head{{grid-template-columns:27px minmax(0,1fr) 32px 28px 32px 37px 39px;font-size:7px}}
  .mock-name{{font-size:9.5px!important}}.mock-cell,.mock-adp{{font-size:7px}}.pick-card{{min-height:41px}}.pick-name{{font-size:5.5px!important}}.team-head{{font-size:5.5px}}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def _state():
    return st.session_state.get(STATE_KEY)


def _return_query(tab):
    return f"draft_tab={tab}"


def _set_page_home() -> None:
    st.session_state["page"] = "Home"
    for key in list(st.query_params.keys()):
        del st.query_params[key]
    st.rerun()


def _header(state) -> None:
    c1, c2, c3 = st.columns([0.35, 2.7, 0.35], gap="small")
    with c1:
        if st.button("‹", key="mock_back", use_container_width=True):
            _set_page_home()
    with c2:
        subtitle = "Mock Draft • 10-Team PPR • Snake Draft" if not state else (
            f'Mock Draft • {int(state["settings"]["teamsCount"])}-Team '
            f'{html.escape(str(state["settings"]["scoring"]))} • Snake Draft'
        )
        st.markdown(
            f'<div class="mock-title">DRAFT BOARD</div><div class="mock-sub">{subtitle}</div>',
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("⚙", key="mock_settings_btn", use_container_width=True):
            st.session_state["mock2_settings_open"] = not bool(st.session_state.get("mock2_settings_open", False))
            st.rerun()


def _tab_bar(current: str) -> str:
    st.markdown('<span class="mock-nav-marker"></span>', unsafe_allow_html=True)
    cols = st.columns(4, gap="small")
    for col, (key, label) in zip(cols, TABS):
        with col:
            if st.button(
                label,
                key=f"mock_tab_{key}",
                use_container_width=True,
                type="primary" if current == key else "secondary",
            ):
                st.session_state[TAB_KEY] = key
                st.rerun()
    return current


def _position_buttons(selected: str) -> str:
    cols = st.columns(7, gap="small")
    specs = (("QB", "QB", "qb"), ("RB", "RB", "rb"), ("WR", "WR", "wr"), ("TE", "TE", "te"),
             ("FLEX", "FLEX", "flex"), ("K", "K", "k"), ("D/ST", "DEF", "dst"))
    for col, (pos, label, slug) in zip(cols, specs):
        with col:
            st.markdown(f'<span class="pos-marker pos-marker-{slug}"></span>', unsafe_allow_html=True)
            if st.button(label, key=f"mock_pos_{slug}", use_container_width=True):
                st.session_state["mock2_pos"] = "ALL" if selected == pos else pos
                st.rerun()
    return str(st.session_state.get("mock2_pos", selected))


def _status_inner(state):
    if state.get("status") != "active":
        return
    overall = int(state.get("currentOverallPick", 1))
    teams = int(state["settings"]["teamsCount"])
    rnd = int(state.get("currentRound", 1))
    pir = (overall - 1) % teams + 1
    rem = timer_remaining(state)
    mins, secs = divmod(max(0, rem), 60)
    team_num = int(str(state.get("currentTeam", "t1")).lstrip("t") or 1)
    label = "You're on the clock!" if state.get("currentTeam") == state.get("userTeamId") else "Draft in progress"
    st.markdown(
        f'<div class="draft-status"><div><div class="clock-label">{label}</div>'
        f'<div class="clock-pick">Pick {rnd}.{pir:02d}</div></div>'
        f'<div class="clock-team">Team {team_num}</div>'
        f'<div class="clock-timer">{mins:02d}:{secs:02d}</div></div><div class="mock-spacer"></div>',
        unsafe_allow_html=True,
    )


def _status_bar(state):
    frag = getattr(st, "fragment", None)
    if frag is None:
        _status_inner(state)
        return

    @frag(run_every=1.0)
    def live_status():
        _status_inner(state)

    live_status()


def _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key):
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


def _player_row(state, player, on_clock: bool, queued: set[str]) -> None:
    pid = str(player["id"])
    pos = str(player.get("position") or "")
    slug = _position_slug(pos)
    with st.container(border=True):
        st.markdown(f'<span class="player-row-marker player-row-{slug}"></span>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.48, 2.05, 0.48, 0.52, 0.58, 0.62, 0.72], gap="small")
        with c1:
            st.markdown(f'<div class="mock-rank">{int(player.get("rank") or 0)}</div>', unsafe_allow_html=True)
        with c2:
            link = player_link_html(
                pid,
                str(player.get("name") or ""),
                css_class="mock-name",
                return_page="Mock Draft",
                return_query=_return_query("PLAYERS_AVAILABLE"),
            )
            st.markdown(link, unsafe_allow_html=True)
        with c3:
            if st.button("✓" if pid in queued else "＋", key=f"queue_btn_{pid}", use_container_width=True):
                if pid in queued:
                    queue_remove(state, pid)
                else:
                    queue_add(state, pid)
                st.session_state[STATE_KEY] = state
                st.rerun()
        with c4:
            st.markdown(_position_badge(pos), unsafe_allow_html=True)
        with c5:
            st.markdown(f'<div class="mock-cell">{html.escape(str(player.get("team") or "—"))}</div>', unsafe_allow_html=True)
        with c6:
            st.markdown(f'<div class="mock-adp">{float(player.get("adp") or 0):.1f}</div>', unsafe_allow_html=True)
        with c7:
            if st.button("DRAFT", key=f"draft_btn_{pid}", use_container_width=True, disabled=not on_clock):
                if get_player(state, pid):
                    make_pick(state, pid, source="user")
                    advance_cpu_until_user(state)
                    st.session_state.pop("mock2_shiva_answer", None)
                    st.session_state[STATE_KEY] = state
                    st.rerun()


def _player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key):
    if "mock2_search" not in st.session_state:
        st.session_state["mock2_search"] = ""
    if "mock2_pos" not in st.session_state:
        st.session_state["mock2_pos"] = "ALL"
    if "mock2_team" not in st.session_state:
        st.session_state["mock2_team"] = "ALL"

    c1, c2, c3, c4 = st.columns([1.45, 0.9, 0.9, 0.35], gap="small")
    with c1:
        search = st.text_input("Search", placeholder="⌕ Search players...", key="mock2_search", label_visibility="collapsed")
    with c2:
        pos = st.selectbox(
            "Position",
            ["ALL", "QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"],
            key="mock2_pos",
            label_visibility="collapsed",
            format_func=lambda x: "All Positions" if x == "ALL" else x,
        )
    teams = ["ALL"] + sorted({str(p.get("team")) for p in state.get("availablePlayers", []) if p.get("team")})
    if st.session_state.get("mock2_team") not in teams:
        st.session_state["mock2_team"] = "ALL"
    with c3:
        team_filter = st.selectbox(
            "Team",
            teams,
            key="mock2_team",
            label_visibility="collapsed",
            format_func=lambda x: "All Teams" if x == "ALL" else x,
        )
    with c4:
        if st.button("↺", key="mock_reset_filters", use_container_width=True):
            st.session_state["mock2_search"] = ""
            st.session_state["mock2_pos"] = "ALL"
            st.session_state["mock2_team"] = "ALL"
            st.rerun()

    pos = _position_buttons(pos)
    pool = list(state.get("availablePlayers") or [])
    if search.strip():
        pool = [p for p in pool if search.strip().casefold() in str(p.get("name", "")).casefold()]
    if pos != "ALL":
        pool = [p for p in pool if (p.get("position") in {"RB", "WR", "TE"} if pos == "FLEX" else p.get("position") == pos)]
    if team_filter != "ALL":
        pool = [p for p in pool if str(p.get("team")) == team_filter]
    pool = sorted(pool, key=lambda p: (p.get("rank", 9999), p.get("adp", 9999), p.get("name", "")))[:140]

    st.markdown(
        '<div class="mock-list-head"><div>RK</div><div>PLAYER</div><div>+</div>'
        '<div>POS</div><div>TEAM</div><div style="text-align:right">ADP</div><div></div></div>',
        unsafe_allow_html=True,
    )
    on_clock = (
        state.get("status") == "active"
        and not state.get("paused")
        and state.get("currentTeam") == state.get("userTeamId")
    )
    queued = set(state.get("queue") or [])
    for player in pool:
        _player_row(state, player, on_clock, queued)

    if on_clock and st.button(
        "🤖 WHO SHOULD I PICK?",
        key="mock2_shiva_btn",
        use_container_width=True,
        type="primary",
    ):
        _run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)

    ans = st.session_state.get("mock2_shiva_answer")
    if ans and st.session_state.get("mock2_shiva_pick") == int(state.get("currentOverallPick", 0)):
        st.markdown(
            f'<div style="background:#072237;border:1px solid #126b9d;border-radius:9px;padding:9px;margin-top:7px">'
            f'<div style="font-size:9px;color:#5ad0ff;font-weight:1000">ASK SHIVA GPT</div>'
            f'<div style="font-size:16px;color:#dfff00;font-weight:1000;margin-top:4px">{html.escape(str(ans.get("answer") or ""))}</div>'
            f'<div style="font-size:10px;margin-top:3px">{html.escape(str(ans.get("why") or ""))}</div></div>',
            unsafe_allow_html=True,
        )


def _compact_name(name):
    parts = str(name).replace("'", "").split()
    return "—" if not parts else (parts[0][:9] if len(parts) == 1 else f"{parts[0][0]}.{parts[-1]}"[:10])


def _board(state):
    teams = int(state["settings"]["teamsCount"])
    rounds = int(state["settings"]["rounds"])
    cr = int(state.get("currentRound", 1))
    st.markdown(
        f'<div class="board-top"><div></div><div><div class="board-title">MOCK DRAFT BOARD</div>'
        f'<div class="board-round">Round {cr}⌄</div></div>'
        f'<div class="board-meta">{teams} Teams • {html.escape(str(state["settings"].get("scoring", "PPR")))}</div></div>',
        unsafe_allow_html=True,
    )
    legend = []
    for pos in ("QB", "RB", "WR", "TE", "K", "D/ST"):
        style = _position_style(pos)
        label = "DEF" if pos == "D/ST" else pos
        legend.append(f'<span><i class="legend-dot" style="background:{style["badge"]}"></i>{label}</span>')
    st.markdown('<div class="board-legend">' + "".join(legend) + "</div>", unsafe_allow_html=True)

    picks = {int(p["pickNumber"]): p for p in state.get("picks", [])}
    parts = [f'<div class="draft-board" style="grid-template-columns:repeat({teams},minmax(0,1fr))">']
    for i in range(1, teams + 1):
        parts.append(f'<div class="team-head">TEAM {i}</div>')
    for rnd in range(1, rounds + 1):
        for col in range(1, teams + 1):
            overall = (rnd - 1) * teams + (col if rnd % 2 else teams - col + 1)
            pick = picks.get(overall)
            rp = (overall - 1) % teams + 1
            if pick:
                pid = str(pick.get("playerId"))
                pname = str(pick.get("playerName"))
                pos = str(pick.get("position"))
                style = _position_style(pos)
                href = player_profile_href(
                    pname,
                    pid,
                    return_page="Mock Draft",
                    return_query=_return_query("DRAFT_BOARD"),
                )
                link = (
                    f'<a class="pick-name" href="{html.escape(href, quote=True)}" target="_self">'
                    f'{html.escape(_compact_name(pname))}</a>'
                )
                parts.append(
                    f'<div class="pick-card" style="background:{style["card"]};border-color:{style["border"]}">'
                    f'<div class="pick-no">{rnd}.{rp}</div>{link}<div class="pick-pos">{_position_badge(pos)}</div></div>'
                )
            else:
                parts.append(f'<div class="pick-card" style="background:#071018"><div class="pick-no">{rnd}.{rp}</div></div>')
    parts.append("</div>")
    st.markdown('<div class="board-wrap">' + "".join(parts) + "</div>", unsafe_allow_html=True)


def _queue(state):
    st.markdown('<div class="section-title">QUEUE</div>', unsafe_allow_html=True)
    queue_ids = list(state.get("queue") or [])
    if not queue_ids:
        st.info("Your draft queue is empty. Tap + beside a player in Players Available.")
        return
    for pid in queue_ids:
        player = get_player(state, pid)
        if not player:
            continue
        c1, c2, c3 = st.columns([0.65, 2.7, 0.75], gap="small")
        with c1:
            st.markdown(_position_badge(player.get("position")), unsafe_allow_html=True)
        with c2:
            link = player_link_html(
                str(player["id"]),
                str(player["name"]),
                css_class="mock-name-plain",
                return_page="Mock Draft",
                return_query="draft_tab=QUEUE",
            )
            st.markdown(link, unsafe_allow_html=True)
        with c3:
            if st.button("REMOVE", key=f"queue_remove_{pid}", use_container_width=True):
                queue_remove(state, str(pid))
                st.session_state[STATE_KEY] = state
                st.rerun()


def _roster(state):
    st.markdown('<div class="section-title">MY ROSTER</div>', unsafe_allow_html=True)
    for slot, player in roster_slots(state, state["userTeamId"]):
        body = (
            player_link_html(
                str(player["id"]),
                str(player["name"]),
                css_class="mock-name-plain",
                return_page="Mock Draft",
                return_query="draft_tab=ROSTER",
            )
            if player
            else '<span style="color:#75808a">—</span>'
        )
        pos_badge = _position_badge(player.get("position")) if player else ""
        st.markdown(
            f'<div class="team-row"><div class="slot">{html.escape(slot)}</div><div>{body}</div>'
            f'<div class="mock-cell">{pos_badge}</div></div>',
            unsafe_allow_html=True,
        )


def _settings(state):
    s = state["settings"]
    st.markdown(
        f'<div class="settings-card"><div class="section-title">DRAFT SETTINGS</div>'
        f'<div class="settings-line">{int(s["teamsCount"])} Teams • {html.escape(str(s["scoring"]))} • '
        f'Snake Draft • {int(s["rounds"])} Rounds • {int(s["secondsPerPick"])} sec/pick</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2, gap="small")
    with c1:
        label = "RESUME DRAFT" if state.get("paused") else "PAUSE DRAFT"
        if st.button(label, use_container_width=True, key="toggle_pause"):
            resume_draft(state) if state.get("paused") else pause_draft(state)
            st.session_state[STATE_KEY] = state
            st.rerun()
    with c2:
        if st.button("UNDO LAST PICK", use_container_width=True, key="undo_draft", disabled=not bool(state.get("picks"))):
            undo_last_pick(state)
            st.session_state[STATE_KEY] = state
            st.rerun()


def render_mock_draft_room_v2(
    rankings: pd.DataFrame,
    weekly: pd.DataFrame,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    db_path,
    ask_shiva_func,
    api_key: str | None,
) -> None:
    _css()
    state = _state()
    _header(state)

    if POOL_KEY not in st.session_state:
        st.session_state[POOL_KEY] = build_player_pool(rankings, weekly)
    pool = st.session_state[POOL_KEY]
    if not pool:
        st.error("No verified 2026 ranking rows are available for the mock draft.")
        return

    if state is None:
        st.markdown('<div class="section-title">CREATE MOCK DRAFT</div>', unsafe_allow_html=True)
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
                state = initialize_draft(
                    pool,
                    int(teams),
                    int(slot),
                    scoring,
                    DEFAULT_ROSTER.copy(),
                    int(rounds),
                    90,
                )
                start_draft(state)
                advance_cpu_until_user(state)
                st.session_state[STATE_KEY] = state
                st.session_state[TAB_KEY] = "PLAYERS_AVAILABLE"
                st.rerun()
        return

    if state.get("status") == "active" and not state.get("paused") and state.get("currentTeam") != state.get("userTeamId"):
        advance_cpu_until_user(state)
    st.session_state[STATE_KEY] = state

    # Legacy return links from Player Profile may include draft_tab. Read it once,
    # then immediately keep navigation in session state so tab changes never reload the app.
    requested_tab = str(st.query_params.get("draft_tab") or "").upper()
    aliases = {"TEAM": "ROSTER", "RESULTS": "DRAFT_BOARD"}
    requested_tab = aliases.get(requested_tab, requested_tab)
    if requested_tab in {k for k, _ in TABS}:
        st.session_state[TAB_KEY] = requested_tab
        if "draft_tab" in st.query_params:
            del st.query_params["draft_tab"]

    tab = str(st.session_state.get(TAB_KEY, "PLAYERS_AVAILABLE")).upper()
    if tab not in {k for k, _ in TABS}:
        tab = "PLAYERS_AVAILABLE"
        st.session_state[TAB_KEY] = tab

    _tab_bar(tab)

    if st.session_state.get("mock2_settings_open", False):
        _settings(state)

    if tab == "PLAYERS_AVAILABLE":
        _player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key)
    elif tab == "QUEUE":
        _queue(state)
    elif tab == "DRAFT_BOARD":
        _board(state)
    else:
        _roster(state)

    _status_bar(state)
