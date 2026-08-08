from __future__ import annotations

from html import escape
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from mock_draft_ui_v2 import render_mock_draft_room_v2
from player_profile import canonical_player_id, linkify_player_names, player_link_html, render_player_profile
from shiva_app_v2 import DB_PATH, _api_key, load_births, load_news, load_rankings, load_roi, load_weekly
from shiva_chatgpt_service import ask_shiva_via_chatgpt
from shiva_engine import build_history_frame

PAGES = {
    "Home",
    "Mock Draft",
    "Players",
    "League History",
    "Draft Coach",
    "Sleepers",
    "Cheat Sheets",
    "Shiva Intelligence",
    "Player Profile",
}

POSITION_COLORS = {
    "QB": "#9B6FE8",
    "RB": "#F28C18",
    "WR": "#39B5DE",
    "TE": "#4DD8C5",
    "D/ST": "#F0CF32",
    "DST": "#F0CF32",
    "DEF": "#F0CF32",
    "K": "#E968A5",
}


def _css() -> None:
    st.markdown(
        """
<style>
:root{--bg:#05080b;--panel:#0c1218;--panel2:#111a22;--line:#203342;--text:#f6f8fa;--muted:#9ba9b5;--lime:#dfff00;--blue:#55a8ff}
html,body,.stApp{background:var(--bg)!important;color:var(--text)!important;overflow-x:hidden!important;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
header,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stToolbarActions"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stAppDeployButton"],#MainMenu,footer{display:none!important}
[data-testid="stAppViewBlockContainer"],.block-container{width:100%!important;max-width:520px!important;margin:0 auto!important;padding:10px 10px 105px!important;box-sizing:border-box!important;overflow-x:hidden!important}
.stButton button{min-height:46px!important;border-radius:10px!important;border:1px solid #294151!important;background:#0d1821!important;color:#fff!important;font-weight:850!important;box-shadow:none!important}
.stButton button[kind="primary"]{background:#dfff00!important;color:#081006!important;border-color:#dfff00!important}.stButton button[kind="primary"] p{color:#081006!important}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{background:#0b151d!important;color:#fff!important;border:1px solid #294151!important;border-radius:10px!important}
.app-head{display:flex;align-items:center;justify-content:space-between;padding:2px 2px 10px}.brand{font-size:19px;font-weight:1000;font-style:italic;letter-spacing:.06em;color:#dfff00}.brand-sub{font-size:10px;color:#d6dee5;margin-top:3px}.page-head{font-size:24px;font-weight:1000;text-align:center;margin:3px 0 2px}.page-sub{font-size:11px;color:#aebac4;text-align:center;margin-bottom:11px}.section-head{font-size:14px;font-weight:1000;color:#dfff00;margin:16px 0 8px}
.home-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:6px 0 12px}.st-key-home_draft button,.st-key-home_players button,.st-key-home_team button,.st-key-home_sleepers button,.st-key-home_cheats button,.st-key-home_shiva button{min-height:92px!important;font-size:13px!important;border-radius:14px!important}.st-key-home_draft button{border-color:#a66b12!important}.st-key-home_players button{border-color:#24758a!important}.st-key-home_team button{border-color:#4a8b35!important}.st-key-home_sleepers button{border-color:#a8861b!important}.st-key-home_cheats button{border-color:#a64b79!important}.st-key-home_shiva button{border-color:#5794f7!important}
.news-link{display:block;text-decoration:none!important;color:#fff!important;background:#0b141c;border:1px solid #20394c;border-radius:10px;padding:11px;margin:7px 0}.news-title{font-size:13px;font-weight:900;color:#fff}.news-meta{font-size:9px;color:#8fa2b0;margin-top:4px}.news-desc{font-size:10px;color:#c8d2da;line-height:1.35;margin-top:6px}.news-open{font-size:10px;color:#5794f7;font-weight:900;margin-top:7px}
.player-row{display:grid;grid-template-columns:34px minmax(0,1fr) 44px 48px;align-items:center;gap:5px;min-height:54px;padding:7px 7px;margin:2px 0;background:#0d151c;border:1px solid #1d3140;border-radius:8px}.player-rank{font-size:11px;font-weight:900;color:#a7b3bd;text-align:center}.player-name{font-size:12px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}.player-meta{font-size:9px;color:#aab7c1;margin-top:3px}.pos-badge{display:inline-block;border-radius:999px;padding:2px 5px;color:#091015;font-size:8px;font-weight:1000}.player-adp{font-size:10px;text-align:right;color:#d7e0e6}.player-proj{font-size:10px;text-align:right;color:#7fdcff}
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:8px 0 12px}.metric{background:#0d151c;border:1px solid #213745;border-radius:10px;padding:10px;text-align:center}.metric-v{font-size:19px;font-weight:1000;color:#fff}.metric-l{font-size:8px;color:#9caab5;margin-top:3px}.iq-card{background:#0d151c;border:1px solid #213745;border-radius:10px;padding:10px;margin:6px 0}.iq-name{font-size:12px;font-weight:950}.iq-meta{font-size:9px;color:#9faeba;margin-top:4px}.iq-value{font-size:12px;font-weight:1000;color:#dfff00;text-align:right}
.cheat-tabs [data-baseweb="tab-list"]{gap:4px!important}.cheat-tabs button{font-size:11px!important}
.ask-card{background:#0b1720;border:1px solid #23516c;border-radius:10px;padding:12px;margin:8px 0}.ask-answer{font-size:18px;font-weight:1000;color:#dfff00;line-height:1.25}.ask-why{font-size:11px;color:#d3dde4;line-height:1.45;margin-top:7px}.inline-player-link{color:#dfff00!important;text-decoration:underline!important;font-weight:1000}
.st-key-app_bottom_nav{position:fixed!important;left:50%!important;bottom:0!important;transform:translateX(-50%)!important;width:min(520px,100vw)!important;z-index:2147482000!important;background:#04090d!important;border-top:1px solid #1b3344!important;padding:6px 6px max(8px,env(safe-area-inset-bottom))!important;box-sizing:border-box!important}.st-key-app_bottom_nav div[data-testid="stHorizontalBlock"]{gap:3px!important}.st-key-app_bottom_nav button{min-height:58px!important;height:58px!important;border:0!important;background:transparent!important;border-radius:8px!important;padding:2px!important;color:#b7c2ca!important}.st-key-app_bottom_nav button p{font-size:10px!important;line-height:1.15!important}.st-key-app_bottom_nav button[kind="primary"]{background:#111b21!important}.st-key-app_bottom_nav button[kind="primary"] p{color:#dfff00!important}
@media(max-width:390px){[data-testid="stAppViewBlockContainer"],.block-container{padding-left:7px!important;padding-right:7px!important}.player-row{grid-template-columns:31px minmax(0,1fr) 41px 44px}.brand{font-size:17px}.metric-v{font-size:17px}}
</style>
""",
        unsafe_allow_html=True,
    )


def _clear_profile_state() -> None:
    for key in ("player_profile_name", "player_profile_id", "player_profile_return_page"):
        st.session_state.pop(key, None)
    for key in list(st.query_params.keys()):
        if key in {"player", "player_id", "return_page", "return_q", "season", "profile_tab", "favorite"}:
            del st.query_params[key]


def _go(page: str) -> None:
    target = page if page in PAGES else "Home"
    _clear_profile_state()
    if "page" in st.query_params:
        del st.query_params["page"]
    st.session_state["page"] = target


def _resolve_page() -> str:
    query_page = str(st.query_params.get("page") or "").strip()
    if query_page:
        page = query_page if query_page in PAGES else "Home"
        _clear_profile_state()
        st.session_state["page"] = page
        if "page" in st.query_params:
            del st.query_params["page"]
        return page

    query_player = st.query_params.get("player")
    query_player_id = st.query_params.get("player_id")
    if query_player or query_player_id:
        if query_player:
            st.session_state["player_profile_name"] = str(query_player)
        if query_player_id:
            st.session_state["player_profile_id"] = str(query_player_id)
        if st.query_params.get("return_page"):
            st.session_state["player_profile_return_page"] = str(st.query_params.get("return_page"))
        st.session_state["page"] = "Player Profile"
        return "Player Profile"

    page = str(st.session_state.get("page") or "Home")
    if page not in PAGES:
        page = "Home"
        st.session_state["page"] = page
    return page


def _bottom_nav(page: str) -> None:
    active = "Players" if page == "Player Profile" else page
    items = [
        ("🏠\nHome", "Home"),
        ("🏈\nDraft", "Mock Draft"),
        ("👤\nPlayers", "Players"),
        ("👥\nTeam IQ", "League History"),
        ("•••\nCoach", "Draft Coach"),
    ]
    with st.container(key="app_bottom_nav"):
        cols = st.columns(5, gap="small")
        for col, (label, target) in zip(cols, items):
            with col:
                if st.button(label, key=f"bottom_{target.replace(' ', '_')}", use_container_width=True, type="primary" if active == target else "secondary"):
                    _go(target)
                    st.rerun()


def _header() -> None:
    st.markdown('<div class="app-head"><div><div class="brand">SHIVA INTELLIGENCE</div><div class="brand-sub">Fantasy Football Draft Command Center</div></div></div>', unsafe_allow_html=True)


def _pos_badge(pos: str) -> str:
    key = str(pos or "").upper()
    color = POSITION_COLORS.get(key, "#777777")
    label = "D/ST" if key in {"DST", "DEF"} else key
    return f'<span class="pos-badge" style="background:{color}">{escape(label)}</span>'


def _safe_url(value: object) -> str:
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    return raw if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _player_rows(frame: pd.DataFrame, weekly: pd.DataFrame, limit: int = 100, return_page: str = "Players") -> None:
    if frame is None or frame.empty:
        st.info("No verified players match this view.")
        return
    sort_col = "overall_rank" if "overall_rank" in frame.columns else "adp"
    frame = frame.sort_values([sort_col, "adp"], na_position="last").head(limit)
    for _, row in frame.iterrows():
        name = str(row.get("player_name") or "").strip()
        if not name:
            continue
        pid = canonical_player_id(weekly, name)
        link = player_link_html(pid, name, css_class="player-name", return_page=return_page)
        rank_value = pd.to_numeric(pd.Series([row.get(sort_col)]), errors="coerce").iloc[0]
        rank = int(rank_value) if pd.notna(rank_value) else "—"
        adp = pd.to_numeric(pd.Series([row.get("adp")]), errors="coerce").iloc[0]
        proj = pd.to_numeric(pd.Series([row.get("projected_points")]), errors="coerce").iloc[0]
        team = escape(str(row.get("team") or "—"))
        pos = str(row.get("position") or "")
        adp_text = f"{float(adp):.1f}" if pd.notna(adp) else "—"
        proj_text = f"{float(proj):.1f}" if pd.notna(proj) else "—"
        st.markdown(
            f'<div class="player-row"><div class="player-rank">{rank}</div><div>{link}<div class="player-meta">{team} &nbsp; {_pos_badge(pos)}</div></div><div class="player-adp">{adp_text}</div><div class="player-proj">{proj_text}</div></div>',
            unsafe_allow_html=True,
        )


def _home(rankings: pd.DataFrame, roi: pd.DataFrame) -> None:
    _header()
    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("🏆\nDRAFT BOARD", key="home_draft", use_container_width=True):
            _go("Mock Draft"); st.rerun()
        if st.button("⭐\nMY TEAM IQ", key="home_team", use_container_width=True):
            _go("League History"); st.rerun()
        if st.button("📋\nCHEAT SHEETS", key="home_cheats", use_container_width=True):
            _go("Cheat Sheets"); st.rerun()
    with c2:
        if st.button("👤\nPLAYER PROFILES", key="home_players", use_container_width=True):
            _go("Players"); st.rerun()
        if st.button("🥷\nSLEEPERS", key="home_sleepers", use_container_width=True):
            _go("Sleepers"); st.rerun()
        if st.button("🤖\nASK SHIVA", key="home_shiva", use_container_width=True):
            _go("Shiva Intelligence"); st.rerun()

    leagues = sorted(roi["league_name"].dropna().astype(str).unique().tolist()) if "league_name" in roi.columns else []
    league_name = leagues[0] if leagues else "Shiva Champion League"
    st.markdown(f'<div class="section-head">MY LEAGUE</div><div class="iq-card"><div class="iq-name">{escape(league_name)}</div><div class="iq-meta">10-Team • Full PPR</div></div>', unsafe_allow_html=True)

    news = load_news()
    st.markdown('<div class="section-head">LIVE ESPN FANTASY / NFL NEWS</div>', unsafe_allow_html=True)
    if not news:
        st.info("ESPN news is temporarily unavailable. The app will retry automatically on the next cache refresh.")
    for article in news[:5]:
        title = escape(str(article.get("title") or "NFL Update"))
        published = escape(str(article.get("published") or ""))
        desc = escape(str(article.get("description") or "")[:220])
        link = _safe_url(article.get("link"))
        body = f'<div class="news-title">{title}</div><div class="news-meta">{published}</div><div class="news-desc">{desc}</div>'
        if link:
            st.markdown(f'<a class="news-link" href="{escape(link, quote=True)}" target="_blank" rel="noopener noreferrer">{body}<div class="news-open">OPEN ON ESPN ↗</div></a>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="news-link">{body}</div>', unsafe_allow_html=True)


def _players(rankings: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">PLAYERS</div><div class="page-sub">Search the current 2026 board and open verified player profiles.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.5, 1], gap="small")
    with c1:
        search = st.text_input("Search", key="players_search", placeholder="Search players...", label_visibility="collapsed")
    with c2:
        pos = st.selectbox("Position", ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"], key="players_pos", label_visibility="collapsed")
    frame = rankings.copy()
    if search.strip():
        frame = frame[frame["player_name"].astype(str).str.contains(search.strip(), case=False, na=False)]
    if pos != "ALL":
        frame = frame[frame["position"].astype(str).str.upper().eq(pos)]
    _player_rows(frame, weekly, 160, "Players")


def _sleepers(rankings: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">SLEEPERS</div><div class="page-sub">Current-board ADP value candidates. Derived only from verified ranking and ADP fields.</div>', unsafe_allow_html=True)
    frame = rankings.copy()
    if "overall_rank" not in frame.columns:
        st.info("The current rankings file does not contain overall rank, so a verified ADP-value sleeper view cannot be calculated.")
        return
    frame["_rank"] = pd.to_numeric(frame["overall_rank"], errors="coerce")
    frame["_adp"] = pd.to_numeric(frame["adp"], errors="coerce")
    frame["_value"] = frame["_adp"] - frame["_rank"]
    frame = frame[(frame["_adp"] >= 35) & (frame["_value"] >= 8)].sort_values(["_value", "_adp"], ascending=[False, True])
    if frame.empty:
        st.info("No current players meet the verified sleeper threshold right now.")
        return
    st.markdown('<div class="section-head">BEST ADP DISCOUNTS</div>', unsafe_allow_html=True)
    for _, row in frame.head(50).iterrows():
        name = str(row.get("player_name") or "")
        pid = canonical_player_id(weekly, name)
        link = player_link_html(pid, name, css_class="player-name", return_page="Sleepers")
        st.markdown(f'<div class="iq-card"><div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px"><div>{link}<div class="iq-meta">{escape(str(row.get("team") or "—"))} • {_pos_badge(str(row.get("position") or ""))} • ADP {float(row["_adp"]):.1f}</div></div><div class="iq-value">+{float(row["_value"]):.0f}</div></div></div>', unsafe_allow_html=True)


def _cheat_sheets(rankings: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">CHEAT SHEETS</div><div class="page-sub">Current verified 2026 ranking board by position.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["OVERALL", "RB", "WR", "QB", "TE", "D/ST", "K"])
    for tab, pos in zip(tabs, ["ALL", "RB", "WR", "QB", "TE", "D/ST", "K"]):
        with tab:
            frame = rankings if pos == "ALL" else rankings[rankings["position"].astype(str).str.upper().eq(pos)]
            _player_rows(frame.copy(), weekly, 80 if pos == "ALL" else 40, "Cheat Sheets")


def _draft_coach(rankings: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">DRAFT COACH</div><div class="page-sub">Actionable views built from the current verified draft board.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["VALUE", "POSITION", "PLAN"])
    with tabs[0]:
        frame = rankings.copy()
        if "overall_rank" in frame.columns:
            frame["_value"] = pd.to_numeric(frame["adp"], errors="coerce") - pd.to_numeric(frame["overall_rank"], errors="coerce")
            frame = frame.sort_values(["_value", "adp"], ascending=[False, True])
        _player_rows(frame, weekly, 60, "Draft Coach")
    with tabs[1]:
        pos = st.selectbox("Position", ["RB", "WR", "QB", "TE", "D/ST", "K"], key="coach_pos")
        frame = rankings[rankings["position"].astype(str).str.upper().eq(pos)].copy()
        _player_rows(frame, weekly, 50, "Draft Coach")
    with tabs[2]:
        st.markdown('<div class="section-head">LIVE DRAFT CONTEXT</div>', unsafe_allow_html=True)
        state = st.session_state.get("mock_draft_state_v2") or {}
        if not state:
            st.info("Start a mock draft to populate live roster and current-pick context here.")
        else:
            teams = int(state.get("settings", {}).get("teamsCount", 10))
            overall = int(state.get("currentOverallPick", 1))
            current_round = int(state.get("currentRound", 1))
            roster = next((t.get("roster", []) for t in state.get("teams", []) if t.get("id") == state.get("userTeamId")), [])
            st.markdown(f'<div class="metric-grid"><div class="metric"><div class="metric-v">{current_round}</div><div class="metric-l">ROUND</div></div><div class="metric"><div class="metric-v">{overall}</div><div class="metric-l">OVERALL PICK</div></div><div class="metric"><div class="metric-v">{len(roster)}</div><div class="metric-l">ROSTERED</div></div></div>', unsafe_allow_html=True)
            if st.button("OPEN LIVE MOCK DRAFT", key="coach_open_mock", use_container_width=True, type="primary"):
                _go("Mock Draft"); st.rerun()


def _manager_column(frame: pd.DataFrame) -> str | None:
    for col in ("manager_name", "owner_name", "owner", "manager", "team_owner", "team_name"):
        if col in frame.columns and frame[col].dropna().astype(str).str.strip().ne("").any():
            return col
    return None


def _team_iq(roi: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">MY TEAM IQ</div><div class="page-sub">League-history filters that never strand you on a blank page.</div>', unsafe_allow_html=True)
    if roi is None or roi.empty:
        st.info("No verified league-history data is loaded.")
        return
    frame = roi.copy()
    leagues = sorted(frame["league_name"].dropna().astype(str).unique()) if "league_name" in frame.columns else []
    manager_col = _manager_column(frame)
    managers = sorted(frame[manager_col].dropna().astype(str).unique()) if manager_col else []
    seasons = sorted(pd.to_numeric(frame["season"], errors="coerce").dropna().astype(int).unique(), reverse=True) if "season" in frame.columns else []
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        league = st.selectbox("League", ["ALL"] + list(leagues), key="iq_league")
    with c2:
        manager = st.selectbox("Manager", ["ALL"] + list(managers), key="iq_manager")
    with c3:
        year = st.selectbox("Year", ["ALL"] + list(seasons), key="iq_year")
    if league != "ALL" and "league_name" in frame.columns:
        frame = frame[frame["league_name"].astype(str).eq(str(league))]
    if manager != "ALL" and manager_col:
        frame = frame[frame[manager_col].astype(str).eq(str(manager))]
    if year != "ALL" and "season" in frame.columns:
        frame = frame[pd.to_numeric(frame["season"], errors="coerce").eq(int(year))]
    if frame.empty:
        st.info("No verified rows match those filters. Change a filter to continue.")
        return
    seasons_count = int(pd.to_numeric(frame["season"], errors="coerce").nunique()) if "season" in frame.columns else 0
    managers_count = int(frame[manager_col].astype(str).nunique()) if manager_col else 0
    st.markdown(f'<div class="metric-grid"><div class="metric"><div class="metric-v">{len(frame)}</div><div class="metric-l">DRAFTED PLAYERS</div></div><div class="metric"><div class="metric-v">{seasons_count}</div><div class="metric-l">SEASONS</div></div><div class="metric"><div class="metric-v">{managers_count}</div><div class="metric-l">MANAGERS</div></div></div>', unsafe_allow_html=True)
    sort_cols = [c for c in ("season", "overall_pick") if c in frame.columns]
    if sort_cols:
        frame = frame.sort_values(sort_cols, ascending=[False, True][:len(sort_cols)])
    if "player_name" not in frame.columns:
        st.dataframe(frame.head(100), use_container_width=True, hide_index=True)
        return
    for _, row in frame.head(120).iterrows():
        name = str(row.get("player_name") or "").strip()
        if not name:
            continue
        pid = canonical_player_id(weekly, name)
        link = player_link_html(pid, name, css_class="player-name", return_page="League History")
        season = pd.to_numeric(pd.Series([row.get("season")]), errors="coerce").iloc[0]
        pick = pd.to_numeric(pd.Series([row.get("overall_pick")]), errors="coerce").iloc[0]
        ppg = pd.to_numeric(pd.Series([row.get("ppg")]), errors="coerce").iloc[0]
        manager_text = str(row.get(manager_col) or "") if manager_col else ""
        meta = " • ".join([x for x in [str(int(season)) if pd.notna(season) else "", f"Pick {int(pick)}" if pd.notna(pick) else "", manager_text] if x])
        ppg_text = f"{float(ppg):.1f} PPG" if pd.notna(ppg) else ""
        st.markdown(f'<div class="iq-card"><div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px"><div>{link}<div class="iq-meta">{escape(meta)}</div></div><div class="iq-value">{escape(ppg_text)}</div></div></div>', unsafe_allow_html=True)


def _ask_shiva(rankings: pd.DataFrame, history: pd.DataFrame, roi: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="page-head">ASK SHIVA</div><div class="page-sub">Data-first fantasy football analysis using the app’s loaded datasets and live draft context.</div>', unsafe_allow_html=True)
    key = _api_key()
    if not key:
        with st.expander("Connect ChatGPT", expanded=True):
            entered = st.text_input("OpenAI API key", type="password", key="v3_api_key", placeholder="sk-...")
            if entered.strip():
                st.session_state["shiva_openai_api_key"] = entered.strip()
                key = entered.strip()
    with st.form("v3_ask_form"):
        question = st.text_area("Question", key="v3_question", placeholder="Who should I draft? Compare two players. Show weekly consistency...", height=110)
        submitted = st.form_submit_button("ASK SHIVA GPT", use_container_width=True, type="primary")
    if submitted:
        if not question.strip():
            st.warning("Enter a question first.")
        elif not key:
            st.error("Connect the OpenAI API key first.")
        else:
            with st.spinner("Shiva is calculating the evidence..."):
                st.session_state["v3_shiva_report"] = ask_shiva_via_chatgpt(question, history, roi, rankings, weekly, key, st.session_state.get("mock_draft_state_v2"))
    report = st.session_state.get("v3_shiva_report")
    if report:
        answer = linkify_player_names(str(report.get("answer") or ""), rankings, weekly, return_page="Shiva Intelligence")
        why = linkify_player_names(str(report.get("why") or ""), rankings, weekly, return_page="Shiva Intelligence")
        st.markdown(f'<div class="ask-card"><div class="ask-answer">{answer}</div><div class="ask-why">{why}</div></div>', unsafe_allow_html=True)


def run() -> None:
    _css()
    roi = load_roi()
    rankings = load_rankings()
    births = load_births()
    weekly = load_weekly()
    for col in ("season", "round", "overall_pick", "position_draft_rank", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "final_draft_roi"):
        if col in roi.columns:
            roi[col] = pd.to_numeric(roi[col], errors="coerce")
    history = build_history_frame(roi, births)
    page = _resolve_page()

    if page == "Player Profile":
        player = str(st.session_state.get("player_profile_name") or st.query_params.get("player") or "")
        player_id = str(st.session_state.get("player_profile_id") or st.query_params.get("player_id") or canonical_player_id(weekly, player))
        render_player_profile(player, rankings, weekly, history, births, player_id, st.session_state.get("mock_draft_state_v2"))
        _bottom_nav(page)
        return

    if page == "Home":
        _home(rankings, roi)
    elif page == "Mock Draft":
        render_mock_draft_room_v2(rankings, weekly, history, roi, DB_PATH, ask_shiva_via_chatgpt, _api_key() or None)
    elif page == "Players":
        _players(rankings, weekly)
    elif page == "League History":
        _team_iq(roi, weekly)
    elif page == "Sleepers":
        _sleepers(rankings, weekly)
    elif page == "Cheat Sheets":
        _cheat_sheets(rankings, weekly)
    elif page == "Shiva Intelligence":
        _ask_shiva(rankings, history, roi, weekly)
    else:
        _draft_coach(rankings, weekly)

    _bottom_nav(page)
