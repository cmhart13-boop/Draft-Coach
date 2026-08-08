from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote

import pandas as pd
import streamlit as st


def player_profile_href(player_name: str) -> str:
    return f"?player={quote(str(player_name))}"


def player_profile_link(player_name: str, css_class: str = "player-link") -> str:
    safe = html.escape(str(player_name))
    href = html.escape(player_profile_href(player_name), quote=True)
    return f'<a class="{css_class}" href="{href}" target="_self">{safe}</a>'


def open_player_profile(player_name: str, return_page: str | None = None) -> None:
    if return_page:
        st.session_state["player_profile_return_page"] = return_page
    st.session_state["player_profile_name"] = str(player_name)
    st.query_params["player"] = str(player_name)


def close_player_profile() -> None:
    st.session_state.pop("player_profile_name", None)
    if "player" in st.query_params:
        del st.query_params["player"]


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
    for col in ("season", "week", "fantasy_points_ppr", "fantasy_points", "carries", "targets", "receptions", "receiving_yards", "receiving_tds", "rushing_yards", "rushing_tds", "passing_yards", "passing_tds", "interceptions"):
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


def _team_value(frame: pd.DataFrame) -> str:
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


def _weekly_table(frame: pd.DataFrame, position: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    points_col = "fantasy_points_ppr" if "fantasy_points_ppr" in frame.columns else "fantasy_points"
    data: dict[str, Any] = {
        "WK": pd.to_numeric(frame.get("week"), errors="coerce").astype("Int64") if "week" in frame.columns else pd.Series(range(1, len(frame)+1)),
        "FPTS": pd.to_numeric(frame.get(points_col), errors="coerce").round(1) if points_col in frame.columns else pd.Series([None] * len(frame)),
    }
    if "opponent_team" in frame.columns:
        data["OPP"] = frame["opponent_team"].fillna("—").astype(str)
    elif "opponent" in frame.columns:
        data["OPP"] = frame["opponent"].fillna("—").astype(str)

    pos = str(position).upper()
    if pos == "QB":
        for label, col in (("PASS YDS", "passing_yards"), ("PASS TD", "passing_tds"), ("INT", "interceptions"), ("RUSH", "rushing_yards")):
            if col in frame.columns:
                data[label] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)
    else:
        for label, col in (("RUSH", "carries"), ("RUSH YDS", "rushing_yards"), ("TGT", "targets"), ("REC", "receptions"), ("REC YDS", "receiving_yards")):
            if col in frame.columns:
                data[label] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)
        td_cols = [c for c in ("rushing_tds", "receiving_tds") if c in frame.columns]
        if td_cols:
            total_td = sum(pd.to_numeric(frame[c], errors="coerce").fillna(0) for c in td_cols)
            data["TD"] = total_td.astype(int)
    table = pd.DataFrame(data)
    cols = ["WK"] + (["OPP"] if "OPP" in table.columns else []) + [c for c in table.columns if c not in {"WK", "OPP"}]
    return table[cols].sort_values("WK")


def render_player_profile(player_name: str, rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame) -> None:
    player_weekly = _weekly_for_player(weekly, player_name)
    ranking = _rank_row(rankings, player_name)
    years = sorted(pd.to_numeric(player_weekly.get("season"), errors="coerce").dropna().astype(int).unique().tolist(), reverse=True) if not player_weekly.empty and "season" in player_weekly.columns else []

    st.markdown("""
<style>
.profile-shell{background:#05090d;color:#fff}.profile-top{display:flex;align-items:center;justify-content:space-between;margin:4px 0 10px}.profile-name{font-size:29px;font-weight:1000;line-height:1.05;text-align:center}.profile-sub{font-size:14px;color:#b8c1ca;text-align:center;margin-top:3px}.profile-star{font-size:30px;color:#ffb000}.profile-panel{background:linear-gradient(145deg,#0b151e,#081018);border:1px solid #24384a;border-radius:17px;padding:14px;margin:10px 0}.profile-hero{display:grid;grid-template-columns:90px 1fr;gap:14px;align-items:center}.profile-avatar{width:86px;height:86px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#0d62a8,#052d50);border:3px solid #1c9cff;font-size:30px;font-weight:1000}.profile-team{font-size:16px;color:#65bfff;font-weight:900}.profile-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:12px}.profile-metric{background:#071018;border:1px solid #18334a;border-radius:12px;padding:10px 5px;text-align:center}.profile-value{font-size:22px;font-weight:1000;color:#ffb000}.profile-label{font-size:10px;color:#b9c3cd;margin-top:4px;font-weight:800}.profile-section-title{font-size:16px;font-weight:1000;margin:15px 0 7px}.player-link{color:inherit!important;text-decoration:none!important}.player-link:hover{text-decoration:underline!important}
[data-testid="stDataFrame"]{border:1px solid #22384a;border-radius:14px;overflow:hidden}.profile-back button{background:#0c141c!important;border:1px solid #30465a!important}
@media(max-width:430px){.profile-name{font-size:26px}.profile-hero{grid-template-columns:76px 1fr}.profile-avatar{width:72px;height:72px}.profile-value{font-size:20px}.profile-metrics{gap:5px}}
</style>
""", unsafe_allow_html=True)

    back_col, title_col, star_col = st.columns([0.8, 4.5, 0.8])
    with back_col:
        if st.button("‹", key="profile_back", use_container_width=True):
            close_player_profile()
            st.rerun()
    position = _position_value(player_weekly, ranking)
    team = _team_value(player_weekly)
    with title_col:
        st.markdown(f'<div class="profile-name">{html.escape(player_name.upper())}</div><div class="profile-sub">{html.escape(position)} · {html.escape(team)}</div>', unsafe_allow_html=True)
    with star_col:
        st.markdown('<div class="profile-star">★</div>', unsafe_allow_html=True)

    if not years:
        st.warning("No weekly scoring rows are available for this player in the loaded weekly dataset.")
        if ranking:
            st.write({k: ranking.get(k) for k in ("position", "team", "adp", "overall_rank") if ranking.get(k) is not None})
        return

    selected_year = st.selectbox("Season", years, index=0, key=f"profile_year_{player_name}")
    season_frame = player_weekly[pd.to_numeric(player_weekly["season"], errors="coerce").eq(int(selected_year))].copy().sort_values("week")
    points_col = "fantasy_points_ppr" if "fantasy_points_ppr" in season_frame.columns else "fantasy_points"
    points = pd.to_numeric(season_frame.get(points_col), errors="coerce").dropna() if points_col in season_frame.columns else pd.Series(dtype=float)
    total = float(points.sum()) if not points.empty else 0.0
    games = int(points.count())
    ppg = total / games if games else 0.0
    hist = _history_row(history, player_name, int(selected_year))
    pos_finish = hist.get("position_finish_total")
    pos_finish_text = f"{position}{int(pos_finish)}" if pd.notna(pos_finish) else "—"

    initials = "".join(part[0] for part in player_name.split()[:2]).upper()
    st.markdown(
        f'<div class="profile-panel"><div class="profile-hero"><div class="profile-avatar">{html.escape(initials)}</div><div><div class="profile-team">{html.escape(team)} · {html.escape(position)}</div><div style="font-size:21px;font-weight:1000;margin-top:5px">{selected_year} Season</div><div style="color:#aeb9c4;font-size:13px;margin-top:4px">Verified weekly full-PPR scoring from the loaded Shiva dataset.</div></div></div>'
        f'<div class="profile-metrics"><div class="profile-metric"><div class="profile-value">{total:.1f}</div><div class="profile-label">FPTS</div></div><div class="profile-metric"><div class="profile-value">{ppg:.1f}</div><div class="profile-label">PPG</div></div><div class="profile-metric"><div class="profile-value">{games}</div><div class="profile-label">GAMES</div></div><div class="profile-metric"><div class="profile-value">{html.escape(pos_finish_text)}</div><div class="profile-label">RANK</div></div></div></div>',
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(4)
    summary_stats = []
    if position == "QB":
        summary_stats = [("PASS YDS", _sum(season_frame, "passing_yards")), ("PASS TD", _sum(season_frame, "passing_tds")), ("INT", _sum(season_frame, "interceptions")), ("RUSH YDS", _sum(season_frame, "rushing_yards"))]
    else:
        summary_stats = [("CARRIES", _sum(season_frame, "carries")), ("RUSH YDS", _sum(season_frame, "rushing_yards")), ("TARGETS", _sum(season_frame, "targets")), ("REC", _sum(season_frame, "receptions"))]
    for col, (label, value) in zip(stat_cols, summary_stats):
        with col:
            st.metric(label, int(value))

    st.markdown('<div class="profile-section-title">WEEKLY GAME LOG</div>', unsafe_allow_html=True)
    table = _weekly_table(season_frame, position)
    if table.empty:
        st.info("No weekly game log rows are available for this season.")
    else:
        st.dataframe(table, use_container_width=True, hide_index=True, height=min(580, 42 + len(table) * 36))
