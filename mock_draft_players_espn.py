from __future__ import annotations

import html

import streamlit as st

import mock_draft_ui_v2 as base


_ORIGINAL_CSS = base._css
_ORIGINAL_PLAYER_ROW = base._player_row
_ORIGINAL_PLAYER_LIST = base._player_list


PLAYERS_AVAILABLE_CSS = r"""
<style>
/* ESPN-style Players Available view only. */
.players-toolbar-marker,.player-row-marker{display:none!important}

div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker){
  width:100%!important;background:#1c1d1e!important;border-bottom:1px solid #3a3b3c!important;
  padding:14px 18px!important;box-sizing:border-box!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) div[data-testid="stHorizontalBlock"]{
  gap:12px!important;align-items:center!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"]>div{
  height:54px!important;min-height:54px!important;background:#202122!important;border:2px solid #3c3d3f!important;
  border-radius:27px!important;padding:0 16px!important;box-shadow:none!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] span,
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-baseweb="select"] div{
  color:#5794f7!important;font-size:17px!important;font-weight:700!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) button{
  height:54px!important;min-height:54px!important;background:transparent!important;border:none!important;
  box-shadow:none!important;color:#5794f7!important;padding:0!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) button p{
  color:#5794f7!important;font-size:17px!important;font-weight:750!important
}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-testid="stTextInput"]{margin-top:9px!important}
div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) [data-testid="stTextInput"] input{
  min-height:48px!important;background:#202122!important;color:#fff!important;border:1px solid #444648!important;
  border-radius:24px!important;padding:0 17px!important;font-size:16px!important
}

.player-table-header{
  width:100%;display:grid;grid-template-columns:9% 39% 9% 13% 15% 15%;min-height:60px;align-items:center;
  padding:0 14px;box-sizing:border-box;background:#1c1d1e;border-top:1px solid #3c3d3f;border-bottom:1px solid #3c3d3f;
  color:#fff;font-size:16px;font-weight:850
}
.player-table-header>div:nth-child(n+3){text-align:center}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker){
  border:none!important;border-radius:0!important;box-shadow:none!important;padding:0!important;margin:0!important;
  width:100%!important;background:#1c1d1e!important
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-even){background:#242526!important}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-odd){background:#1c1d1e!important}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker)>div{padding:0!important}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stHorizontalBlock"]{
  display:grid!important;grid-template-columns:9% 39% 9% 13% 15% 15%!important;width:100%!important;gap:0!important;
  align-items:center!important;min-height:128px!important;padding:0 14px!important;box-sizing:border-box!important;
  border-bottom:1px solid #292a2b!important
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stColumn"]{
  width:auto!important;min-width:0!important;flex:none!important;padding:0!important
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) [data-testid="stMarkdownContainer"]{
  margin:0!important;padding:0!important
}

.player-name{
  display:block;width:100%;color:#5794f7!important;font-size:20px!important;font-weight:750!important;line-height:1.15!important;
  text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis
}
.player-name:hover{color:#72a8ff!important}
.player-meta{
  display:flex;align-items:center;gap:7px;margin-top:6px;color:#a7a7aa;font-size:18px;font-weight:400;line-height:1;white-space:nowrap
}
.position-badge{
  display:inline-flex!important;align-items:center!important;justify-content:center!important;min-width:35px!important;height:24px!important;
  padding:0 7px!important;border-radius:999px!important;box-sizing:border-box!important;color:#101214!important;font-size:14px!important;
  font-weight:900!important;line-height:1!important
}
.player-bye,.player-adp,.player-proj{
  width:100%;text-align:center;color:#a7a7aa;font-size:18px;font-weight:400;white-space:nowrap
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) button{
  width:100%!important;min-height:55px!important;height:55px!important;padding:0 8px!important;background:transparent!important;
  border:2px solid #f4f4f4!important;border-radius:28px!important;color:#fff!important;box-shadow:none!important
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) button p{
  color:#fff!important;font-size:16px!important;font-weight:750!important;white-space:nowrap!important
}
/* Rank remains the existing draft action, but visually matches the screenshot. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stColumn"]:first-child button{
  width:100%!important;height:auto!important;min-height:0!important;padding:0!important;border:none!important;background:transparent!important;border-radius:0!important
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stColumn"]:first-child button p{
  color:#a7a7aa!important;font-size:18px!important;font-weight:400!important;text-align:left!important
}

@media(max-width:390px){
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker){padding:12px 9px!important}
  div[data-testid="stVerticalBlock"]:has(.players-toolbar-marker) div[data-testid="stHorizontalBlock"]{gap:8px!important}
  .player-table-header{grid-template-columns:9% 38% 9% 13% 15% 16%;padding:0 9px;font-size:14px}
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) div[data-testid="stHorizontalBlock"]{
    grid-template-columns:9% 38% 9% 13% 15% 16%!important;padding:0 9px!important;min-height:121px!important
  }
  .player-name{font-size:18px!important}.player-meta{font-size:16px}
  .player-bye,.player-adp,.player-proj{font-size:16px}.position-badge{font-size:13px!important;min-width:32px!important;height:23px!important}
  div[data-testid="stVerticalBlockBorderWrapper"]:has(.player-row-marker) button p{font-size:14px!important}
}
</style>
"""


def _patched_css() -> None:
    _ORIGINAL_CSS()
    st.markdown(PLAYERS_AVAILABLE_CSS, unsafe_allow_html=True)


def _player_row(state, player, on_clock: bool, queued: set[str], row_index: int) -> None:
    pid = str(player["id"])
    pos = str(player.get("position") or "")
    row_class = "player-row-even" if row_index % 2 else "player-row-odd"

    with st.container(border=True):
        st.markdown(f'<span class="player-row-marker {row_class}"></span>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns([0.09, 0.39, 0.09, 0.13, 0.15, 0.15], gap="small")

        with c1:
            rank = int(player.get("rank") or 0)
            if st.button(
                str(rank),
                key=f"draft_rank_{pid}",
                use_container_width=True,
                disabled=not on_clock,
                help="Draft this player" if on_clock else None,
            ):
                if base.get_player(state, pid):
                    base.make_pick(state, pid, source="user")
                    base.advance_cpu_until_user(state)
                    st.session_state.pop("mock2_shiva_answer", None)
                    st.session_state[base.STATE_KEY] = state
                    st.rerun()

        with c2:
            name = str(player.get("name") or "")
            link = base.player_link_html(
                pid,
                name,
                css_class="player-name",
                return_page="Mock Draft",
                return_query=base._return_query("PLAYERS_AVAILABLE"),
            )
            team = html.escape(str(player.get("team") or "—"))
            st.markdown(
                f'{link}<div class="player-meta"><span>{team}</span>{base._position_badge(pos)}</div>',
                unsafe_allow_html=True,
            )

        with c3:
            bye = "—" if player.get("bye") is None else str(player.get("bye"))
            st.markdown(f'<div class="player-bye">{html.escape(bye)}</div>', unsafe_allow_html=True)

        with c4:
            adp = player.get("adp")
            adp_text = "—" if adp is None else f"{float(adp):.1f}"
            st.markdown(f'<div class="player-adp">{adp_text}</div>', unsafe_allow_html=True)

        with c5:
            proj = player.get("projected_points")
            proj_text = "—" if proj is None else f"{float(proj):.2f}".rstrip("0").rstrip(".")
            st.markdown(f'<div class="player-proj">{proj_text}</div>', unsafe_allow_html=True)

        with c6:
            queued_now = pid in queued
            if st.button("QUEUED" if queued_now else "QUEUE", key=f"queue_btn_{pid}", use_container_width=True):
                if queued_now:
                    base.queue_remove(state, pid)
                else:
                    base.queue_add(state, pid)
                st.session_state[base.STATE_KEY] = state
                st.rerun()


def _player_list(state, history, roi, rankings, weekly, ask_shiva_func, api_key):
    st.session_state.setdefault("mock2_pos", "ALL")
    st.session_state.setdefault("mock2_sort", "PROJ")
    st.session_state.setdefault("mock2_search", "")
    st.session_state.setdefault("mock2_search_open", False)

    with st.container():
        st.markdown('<span class="players-toolbar-marker"></span>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1.30, 1.25, 0.72, 0.35], gap="small")
        with c1:
            pos = st.selectbox(
                "Position",
                ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"],
                key="mock2_pos",
                label_visibility="collapsed",
                format_func=lambda value: "All Pos" if value == "ALL" else value,
            )
        with c2:
            sort_mode = st.selectbox(
                "Sort",
                ["PROJ", "ADP", "RK"],
                key="mock2_sort",
                label_visibility="collapsed",
                format_func=lambda value: {"PROJ": "Proj Pts", "ADP": "ADP", "RK": "Rank"}[value],
            )
        with c3:
            if st.button("Reset", key="mock_reset_filters", use_container_width=True):
                st.session_state["mock2_pos"] = "ALL"
                st.session_state["mock2_sort"] = "PROJ"
                st.session_state["mock2_search"] = ""
                st.session_state["mock2_search_open"] = False
                st.rerun()
        with c4:
            if st.button("⌕", key="mock_search_toggle", use_container_width=True):
                st.session_state["mock2_search_open"] = not st.session_state["mock2_search_open"]
                st.rerun()
        if st.session_state["mock2_search_open"]:
            st.text_input("Search players", key="mock2_search", placeholder="Search players...", label_visibility="collapsed")

    search = str(st.session_state.get("mock2_search") or "")
    pool = list(state.get("availablePlayers") or [])
    if search.strip():
        needle = search.strip().casefold()
        pool = [player for player in pool if needle in str(player.get("name", "")).casefold()]
    if pos != "ALL":
        pool = [player for player in pool if base._position_key(player.get("position")) == base._position_key(pos)]

    if sort_mode == "PROJ":
        pool.sort(
            key=lambda player: (
                -(float(player["projected_points"]) if player.get("projected_points") is not None else -1e9),
                player.get("rank", 9999),
                player.get("adp", 9999),
            )
        )
    elif sort_mode == "ADP":
        pool.sort(key=lambda player: (player.get("adp", 9999), player.get("rank", 9999)))
    else:
        pool.sort(key=lambda player: (player.get("rank", 9999), player.get("adp", 9999)))

    pool = pool[:140]
    st.markdown(
        '<div class="player-table-header"><div>RK</div><div>PLAYER</div><div>BYE</div><div>ADP</div><div>PROJ</div><div></div></div>',
        unsafe_allow_html=True,
    )

    on_clock = (
        state.get("status") == "active"
        and not state.get("paused")
        and state.get("currentTeam") == state.get("userTeamId")
    )
    queued = set(state.get("queue") or [])
    for index, player in enumerate(pool):
        _player_row(state, player, on_clock, queued, index)

    if on_clock and st.button(
        "🤖 WHO SHOULD I PICK?",
        key="mock2_shiva_btn",
        use_container_width=True,
        type="primary",
    ):
        base._run_shiva(state, history, roi, rankings, weekly, ask_shiva_func, api_key)

    answer = st.session_state.get("mock2_shiva_answer")
    if answer and st.session_state.get("mock2_shiva_pick") == int(state.get("currentOverallPick", 0)):
        st.markdown(
            f'<div style="background:#1c1d1e;border-top:1px solid #343536;padding:12px;margin:0">'
            f'<div style="font-size:10px;color:#5794f7;font-weight:900">ASK SHIVA GPT</div>'
            f'<div style="font-size:16px;color:#fff;font-weight:900;margin-top:4px">{html.escape(str(answer.get("answer") or ""))}</div>'
            f'<div style="font-size:11px;color:#a7a7aa;margin-top:3px">{html.escape(str(answer.get("why") or ""))}</div></div>',
            unsafe_allow_html=True,
        )


def render_mock_draft_room_v2(*args, **kwargs) -> None:
    """Render the existing mock draft engine with only Players Available presentation replaced."""
    previous_css = base._css
    previous_row = base._player_row
    previous_list = base._player_list
    base._css = _patched_css
    base._player_row = _player_row
    base._player_list = _player_list
    try:
        base.render_mock_draft_room_v2(*args, **kwargs)
    finally:
        base._css = previous_css
        base._player_row = previous_row
        base._player_list = previous_list
