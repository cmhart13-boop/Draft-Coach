from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import pandas as pd
import streamlit as st


POSITION_TONE = {
    "QB": ("#ff3b30", "#5a1212"),
    "RB": ("#ff8a00", "#5a2d00"),
    "WR": ("#16a8ff", "#063e64"),
    "TE": ("#49d23a", "#164b13"),
    "D/ST": ("#a76618", "#49300f"),
    "K": ("#a8adb4", "#353a40"),
}


def player_profile_href(player_name: str) -> str:
    return f"?player={quote(str(player_name))}"


def player_profile_link(player_name: str, css_class: str = "player-link") -> str:
    safe = html.escape(str(player_name))
    href = html.escape(player_profile_href(player_name), quote=True)
    return f'<a class="{css_class}" href="{href}" target="_self">{safe}</a>'


def _safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value))[:80]


def open_player_profile(player_name: str, return_page: str | None = None) -> None:
    if return_page:
        st.session_state["player_profile_return_page"] = return_page
    st.session_state["player_profile_name"] = str(player_name)
    st.session_state.page = "Player Profile"


def close_player_profile() -> None:
    st.session_state.pop("player_profile_name", None)
    if "player" in st.query_params:
        del st.query_params["player"]


def player_name_button(player_name: str, *, return_page: str, key: str, use_container_width: bool = True) -> bool:
    clicked = st.button(str(player_name), key=key, use_container_width=use_container_width)
    if clicked:
        open_player_profile(player_name, return_page)
    return clicked


def _name_col(frame: pd.DataFrame) -> str | None:
    for col in ("player_display_name", "player_name", "name"):
        if col in frame.columns:
            return col
    return None


def _weekly_for_player(weekly: pd.DataFrame, player_name: str) -> pd.DataFrame:
    if weekly is None or weekly.empty:
        return pd.DataFrame()
    name_col = _name_col(weekly)
    if not name_col:
        return pd.DataFrame()
    mask = weekly[name_col].astype(str).str.casefold().eq(str(player_name).casefold())
    out = weekly.loc[mask].copy()
    if "season_type" in out.columns:
        reg = out["season_type"].astype(str).str.upper().isin(["REG", "REGULAR", "REGULAR SEASON"])
        if reg.any():
            out = out.loc[reg].copy()
    for col in (
        "season", "week", "fantasy_points_ppr", "fantasy_points", "carries", "targets", "receptions",
        "receiving_yards", "receiving_tds", "rushing_yards", "rushing_tds", "passing_yards", "passing_tds",
        "interceptions", "attempts", "target_share", "red_zone_touches"
    ):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _rank_row(rankings: pd.DataFrame, player_name: str) -> dict[str, Any]:
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:
        return {}
    match = rankings[rankings["player_name"].astype(str).str.casefold().eq(str(player_name).casefold())]
    return match.iloc[0].to_dict() if not match.empty else {}


def _history_row(history: pd.DataFrame, player_name: str, season: int) -> dict[str, Any]:
    if history is None or history.empty or "player_name" not in history.columns:
        return {}
    mask = history["player_name"].astype(str).str.casefold().eq(str(player_name).casefold())
    if "season" in history.columns:
        mask &= pd.to_numeric(history["season"], errors="coerce").eq(int(season))
    match = history.loc[mask]
    return match.iloc[0].to_dict() if not match.empty else {}


def _team_value(frame: pd.DataFrame, ranking: dict[str, Any]) -> str:
    if ranking.get("team"):
        return str(ranking["team"])
    for col in ("recent_team", "team"):
        if col in frame.columns:
            vals = frame[col].dropna().astype(str)
            if not vals.empty:
                return vals.iloc[-1]
    return "—"


def _position_value(frame: pd.DataFrame, ranking: dict[str, Any]) -> str:
    if ranking.get("position"):
        return str(ranking["position"])
    if "position" in frame.columns:
        vals = frame["position"].dropna().astype(str)
        if not vals.empty:
            return vals.iloc[-1]
    return "—"


def _sum(frame: pd.DataFrame, col: str) -> float:
    if col not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[col], errors="coerce").fillna(0).sum())


def _player_age(births: pd.DataFrame | None, player_name: str, season: int) -> str:
    if births is None or births.empty or "birth_date" not in births.columns:
        return ""
    if "name_key" in births.columns:
        key = re.sub(r"[^a-z0-9]+", "", player_name.lower())
        keys = births["name_key"].astype(str).str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)
        match = births.loc[keys.eq(key)]
    else:
        name_col = _name_col(births)
        match = births.loc[births[name_col].astype(str).str.casefold().eq(player_name.casefold())] if name_col else births.iloc[0:0]
    if match.empty:
        return ""
    dob = pd.to_datetime(match.iloc[0].get("birth_date"), errors="coerce")
    if pd.isna(dob):
        return ""
    as_of = pd.Timestamp(year=int(season), month=9, day=1)
    age = int((as_of - dob).days / 365.2425)
    return str(age)


def _position_finish_from_history(hist: dict[str, Any], position: str) -> str:
    for col in ("position_finish_total", "season_finish", "position_finish"):
        value = pd.to_numeric(pd.Series([hist.get(col)]), errors="coerce").iloc[0]
        if pd.notna(value):
            return f"{position}{int(value)}"
    return "—"


def _weekly_table(frame: pd.DataFrame, position: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    points_col = "fantasy_points_ppr" if "fantasy_points_ppr" in frame.columns else "fantasy_points"
    data: dict[str, Any] = {
        "WK": pd.to_numeric(frame.get("week"), errors="coerce").astype("Int64") if "week" in frame.columns else pd.Series(range(1, len(frame) + 1)),
        "FPTS": pd.to_numeric(frame.get(points_col), errors="coerce").round(1) if points_col in frame.columns else pd.Series([None] * len(frame)),
    }
    for opp_col in ("opponent_team", "opponent", "opp"):
        if opp_col in frame.columns:
            data["OPP"] = frame[opp_col].fillna("—").astype(str)
            break

    pos = str(position).upper()
    if pos == "QB":
        for label, col in (("PASS YDS", "passing_yards"), ("PASS TD", "passing_tds"), ("INT", "interceptions"), ("RUSH", "rushing_yards")):
            if col in frame.columns:
                data[label] = pd.to_numeric(frame[col], errors="coerce").fillna(0).round(0).astype(int)
    else:
        for label, col in (("RUSH", "carries"), ("RUSH YDS", "rushing_yards"), ("REC", "receptions"), ("REC YDS", "receiving_yards"), ("TGT", "targets")):
            if col in frame.columns:
                data[label] = pd.to_numeric(frame[col], errors="coerce").fillna(0).round(0).astype(int)
        td_cols = [c for c in ("rushing_tds", "receiving_tds") if c in frame.columns]
        if td_cols:
            total_td = sum(pd.to_numeric(frame[c], errors="coerce").fillna(0) for c in td_cols)
            data["TD"] = total_td.astype(int)
    table = pd.DataFrame(data)
    cols = ["WK"] + (["OPP"] if "OPP" in table.columns else []) + [c for c in table.columns if c not in {"WK", "OPP"}]
    table = table[cols].sort_values("WK")
    # The app's fantasy view is Week 1 through Week 17, matching the requested profile design.
    if "WK" in table.columns:
        table = table[pd.to_numeric(table["WK"], errors="coerce").between(1, 17)]
    return table


def _profile_css() -> None:
    st.markdown(r"""
<style>
.profile-page{background:#05090d;color:#fff}.profile-name{font-size:28px;font-weight:1000;line-height:1.05;text-align:center}.profile-sub{font-size:13px;color:#c1cad3;text-align:center;margin-top:4px}.profile-panel{background:linear-gradient(145deg,#0b151e,#071018);border:1px solid #254158;border-radius:17px;padding:13px;margin:9px 0}.profile-hero{display:grid;grid-template-columns:82px minmax(0,1fr);gap:13px;align-items:center}.profile-avatar{width:78px;height:78px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#0b4e83,#05243f);border:2px solid #168bd7;font-size:27px;font-weight:1000}.profile-team{font-size:14px;color:#62c4ff;font-weight:900}.profile-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:10px}.profile-metric{background:#071018;border:1px solid #17344b;border-radius:10px;padding:9px 4px;text-align:center}.profile-value{font-size:20px;font-weight:1000;color:#ffb000}.profile-label{font-size:9px;color:#c0c9d2;margin-top:3px;font-weight:800}.profile-bio{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.profile-bio span{background:#0b1822;border:1px solid #1f3a4e;border-radius:9px;padding:6px 8px;font-size:11px;color:#dbe5ec}.profile-section-title{font-size:15px;font-weight:1000;margin:14px 0 7px}.profile-tabs{display:flex;gap:8px;margin:9px 0}.profile-link{color:inherit!important;text-decoration:none!important}.profile-link:hover{text-decoration:underline!important}[data-testid="stDataFrame"]{border:1px solid #22384a;border-radius:12px;overflow:hidden}.profile-player-list button{text-align:left!important;background:#0a141d!important;border:1px solid #203a50!important}.profile-player-list button p{font-weight:1000!important}.profile-tone{height:4px;border-radius:4px;margin:7px 0 3px}
@media(max-width:430px){.profile-name{font-size:24px}.profile-hero{grid-template-columns:70px minmax(0,1fr)}.profile-avatar{width:66px;height:66px}.profile-value{font-size:18px}.profile-metrics{gap:4px}}
</style>
""", unsafe_allow_html=True)


def render_player_directory(rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, births: pd.DataFrame | None = None) -> None:
    _profile_css()
    st.markdown('<div style="text-align:center;font-size:24px;font-weight:1000;margin:4px 0 3px">PLAYER PROFILES</div><div style="text-align:center;color:#aab6c1;font-size:12px;margin-bottom:12px">Tap any player to open verified year-by-year stats and weekly game logs.</div>', unsafe_allow_html=True)
    search = st.text_input("Search players", placeholder="Search player...", key="profile_directory_search", label_visibility="collapsed")
    pos = st.segmented_control("Position", ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"], default="ALL", key="profile_directory_pos", label_visibility="collapsed") or "ALL"
    pool = rankings.copy() if rankings is not None else pd.DataFrame()
    if pool.empty:
        st.info("No current player rankings are loaded.")
        return
    if search.strip():
        pool = pool[pool["player_name"].astype(str).str.contains(search.strip(), case=False, na=False)]
    if pos != "ALL":
        pool = pool[pool["position"].astype(str).eq(pos)]
    sort_col = "overall_rank" if "overall_rank" in pool.columns else "adp"
    pool = pool.sort_values(sort_col).head(100)
    with st.container(key="profile_player_list"):
        for i, row in pool.iterrows():
            name = str(row["player_name"])
            position = str(row.get("position") or "—")
            team = str(row.get("team") or "—")
            adp = pd.to_numeric(pd.Series([row.get("adp")]), errors="coerce").iloc[0]
            tone, dark = POSITION_TONE.get(position, ("#7f8c99", "#27313a"))
            cols = st.columns([0.55, 3.6, 1.0])
            with cols[0]:
                st.markdown(f'<div style="background:{dark};color:{tone};border:1px solid {tone};border-radius:10px;padding:10px 4px;text-align:center;font-size:11px;font-weight:1000">{html.escape(position)}</div>', unsafe_allow_html=True)
            with cols[1]:
                if st.button(f"{name}\n{team}", key=f"directory_{_safe_key(name)}_{i}", use_container_width=True):
                    open_player_profile(name, "Player Profiles")
                    st.rerun()
            with cols[2]:
                st.markdown(f'<div style="padding-top:11px;text-align:right;color:#fff;font-size:12px;font-weight:900">ADP {float(adp):.1f}</div>' if pd.notna(adp) else '', unsafe_allow_html=True)


def render_player_profile(player_name: str, rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, births: pd.DataFrame | None = None) -> None:
    _profile_css()
    player_weekly = _weekly_for_player(weekly, player_name)
    ranking = _rank_row(rankings, player_name)
    years = sorted(pd.to_numeric(player_weekly.get("season"), errors="coerce").dropna().astype(int).unique().tolist(), reverse=True) if not player_weekly.empty and "season" in player_weekly.columns else []

    return_page = st.session_state.get("player_profile_return_page", "Player Profiles")
    back_col, title_col, star_col = st.columns([0.7, 4.6, 0.7])
    with back_col:
        if st.button("‹", key="profile_back", use_container_width=True):
            close_player_profile()
            st.session_state.page = return_page
            st.rerun()
    position = _position_value(player_weekly, ranking)
    team = _team_value(player_weekly, ranking)
    with title_col:
        st.markdown(f'<div class="profile-name">{html.escape(player_name.upper())}</div><div class="profile-sub">{html.escape(position)} · {html.escape(team)}</div>', unsafe_allow_html=True)
    with star_col:
        st.markdown('<div style="font-size:28px;color:#ffb000;text-align:center">★</div>', unsafe_allow_html=True)

    if not years:
        st.warning("No weekly scoring rows are available for this player in the loaded 2014-2025 weekly dataset.")
        if ranking:
            st.write({k: ranking.get(k) for k in ("position", "team", "adp", "overall_rank") if ranking.get(k) is not None})
        return

    selected_year = st.selectbox("Season", years, index=0, key=f"profile_year_{_safe_key(player_name)}")
    season_frame = player_weekly[pd.to_numeric(player_weekly["season"], errors="coerce").eq(int(selected_year))].copy().sort_values("week")
    points_col = "fantasy_points_ppr" if "fantasy_points_ppr" in season_frame.columns else "fantasy_points"
    points = pd.to_numeric(season_frame.get(points_col), errors="coerce").dropna() if points_col in season_frame.columns else pd.Series(dtype=float)
    total = float(points.sum()) if not points.empty else 0.0
    games = int(points.count())
    ppg = total / games if games else 0.0
    hist = _history_row(history, player_name, int(selected_year))
    pos_finish_text = _position_finish_from_history(hist, position)
    initials = "".join(part[0] for part in player_name.split()[:2]).upper()
    age = _player_age(births, player_name, int(selected_year))
    bye = ranking.get("bye")
    current_rank = ranking.get("overall_rank")
    current_adp = ranking.get("adp")
    tone, dark = POSITION_TONE.get(position, ("#62c4ff", "#05243f"))

    bio_bits = [f"Team: {team}"]
    if age:
        bio_bits.append(f"Age: {age}")
    if pd.notna(pd.to_numeric(pd.Series([bye]), errors="coerce").iloc[0]):
        bio_bits.append(f"2026 Bye: {int(float(bye))}")
    if pd.notna(pd.to_numeric(pd.Series([current_adp]), errors="coerce").iloc[0]):
        bio_bits.append(f"2026 ADP: {float(current_adp):.1f}")
    if pd.notna(pd.to_numeric(pd.Series([current_rank]), errors="coerce").iloc[0]):
        bio_bits.append(f"2026 Rank: {int(float(current_rank))}")

    st.markdown(
        f'<div class="profile-panel"><div class="profile-hero"><div class="profile-avatar" style="background:linear-gradient(145deg,{dark},#06111b);border-color:{tone};color:{tone}">{html.escape(initials)}</div><div><div class="profile-team" style="color:{tone}">{html.escape(team)} · {html.escape(position)}</div><div style="font-size:21px;font-weight:1000;margin-top:4px">{selected_year} OVERVIEW</div><div style="color:#aeb9c4;font-size:12px;margin-top:4px">Verified Full-PPR data from the loaded Shiva weekly dataset.</div></div></div>'
        f'<div class="profile-metrics"><div class="profile-metric"><div class="profile-value">{total:.1f}</div><div class="profile-label">FPTS</div></div><div class="profile-metric"><div class="profile-value">{ppg:.1f}</div><div class="profile-label">PPG</div></div><div class="profile-metric"><div class="profile-value">{games}</div><div class="profile-label">GAMES</div></div><div class="profile-metric"><div class="profile-value">{html.escape(pos_finish_text)}</div><div class="profile-label">RANK</div></div></div><div class="profile-bio">' + ''.join(f'<span>{html.escape(bit)}</span>' for bit in bio_bits) + '</div></div>',
        unsafe_allow_html=True,
    )

    summary_stats: list[tuple[str, float]]
    if position == "QB":
        summary_stats = [("PASS YDS", _sum(season_frame, "passing_yards")), ("PASS TD", _sum(season_frame, "passing_tds")), ("INT", _sum(season_frame, "interceptions")), ("RUSH YDS", _sum(season_frame, "rushing_yards"))]
    else:
        summary_stats = [("CARRIES", _sum(season_frame, "carries")), ("RUSH YDS", _sum(season_frame, "rushing_yards")), ("TARGETS", _sum(season_frame, "targets")), ("REC", _sum(season_frame, "receptions"))]
    stat_cols = st.columns(4)
    for col, (label, value) in zip(stat_cols, summary_stats):
        with col:
            st.metric(label, int(round(value)))

    st.markdown('<div class="profile-section-title">GAME LOG · WEEK 1-17</div>', unsafe_allow_html=True)
    table = _weekly_table(season_frame, position)
    if table.empty:
        st.info("No weekly game log rows are available for this season.")
    else:
        st.dataframe(table, use_container_width=True, hide_index=True, height=min(650, 42 + len(table) * 36))
