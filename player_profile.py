from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import streamlit as st


def _safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value))[:90]


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def _name_col(df: pd.DataFrame) -> str | None:
    for col in ("player_display_name", "player_name", "display_name", "name"):
        if col in df.columns:
            return col
    return None


def canonical_player_id(weekly: pd.DataFrame | None, player_name: str, fallback: str | None = None) -> str:
    if weekly is not None and not weekly.empty and "player_id" in weekly.columns:
        name_col = _name_col(weekly)
        if name_col:
            match = weekly.loc[
                weekly[name_col].astype(str).map(_name_key).eq(_name_key(player_name)), "player_id"
            ].dropna().astype(str)
            if not match.empty:
                return match.iloc[-1]
    return str(fallback or f"name::{_name_key(player_name)}")


def player_profile_href(
    player_name: str,
    player_id: str | None = None,
    *,
    return_page: str | None = None,
    return_query: str | None = None,
    season: int | None = None,
    profile_tab: str | None = None,
) -> str:
    params = {"player": str(player_name)}
    if player_id:
        params["player_id"] = str(player_id)
    if return_page:
        params["return_page"] = str(return_page)
    if return_query:
        params["return_q"] = str(return_query)
    if season is not None:
        params["season"] = str(int(season))
    if profile_tab:
        params["profile_tab"] = str(profile_tab)
    return "?" + urlencode(params)


def player_link_html(
    player_id: str,
    player_name: str,
    *,
    css_class: str = "player-link",
    return_page: str | None = None,
    return_query: str | None = None,
) -> str:
    href = html.escape(
        player_profile_href(player_name, player_id, return_page=return_page, return_query=return_query),
        quote=True,
    )
    return f'<a class="{css_class}" href="{href}" target="_self">{html.escape(str(player_name))}</a>'


def linkify_player_names(text: str, rankings: pd.DataFrame, weekly: pd.DataFrame, *, return_page: str) -> str:
    safe = html.escape(str(text or ""))
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:
        return safe
    for name in sorted(rankings["player_name"].dropna().astype(str).unique(), key=len, reverse=True):
        escaped = html.escape(name)
        if escaped in safe:
            safe = safe.replace(
                escaped,
                player_link_html(
                    canonical_player_id(weekly, name),
                    name,
                    css_class="inline-player-link",
                    return_page=return_page,
                ),
            )
    return safe


def open_player_profile(player_name: str, return_page: str | None = None, player_id: str | None = None) -> None:
    if return_page:
        st.session_state["player_profile_return_page"] = return_page
    st.session_state["player_profile_name"] = str(player_name)
    if player_id:
        st.session_state["player_profile_id"] = str(player_id)
    st.session_state["page"] = "Player Profile"


def close_player_profile() -> None:
    for key in ("player_profile_name", "player_profile_id"):
        st.session_state.pop(key, None)
    for key in ("player", "player_id", "season", "profile_tab", "return_page", "return_q", "favorite"):
        if key in st.query_params:
            del st.query_params[key]


def _weekly_for_player(weekly: pd.DataFrame, player_id: str | None, player_name: str) -> pd.DataFrame:
    if weekly is None or weekly.empty:
        return pd.DataFrame()
    out = pd.DataFrame()
    if player_id and "player_id" in weekly.columns and not str(player_id).startswith("name::"):
        out = weekly.loc[weekly["player_id"].astype(str).eq(str(player_id))].copy()
    if out.empty:
        name_col = _name_col(weekly)
        if name_col:
            out = weekly.loc[weekly[name_col].astype(str).map(_name_key).eq(_name_key(player_name))].copy()
    if "season_type" in out.columns and not out.empty:
        regular = out["season_type"].astype(str).str.upper().isin(["REG", "REGULAR", "REGULAR SEASON"])
        if regular.any():
            out = out.loc[regular].copy()
    numeric_cols = (
        "season", "week", "fantasy_points_ppr", "fantasy_points", "carries", "targets", "receptions",
        "receiving_yards", "receiving_tds", "rushing_yards", "rushing_tds", "passing_yards", "passing_tds",
        "interceptions", "passing_attempts", "completions", "fumbles_lost", "passing_two_point_conversions",
        "rushing_two_point_conversions", "receiving_two_point_conversions",
    )
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _rank_row(rankings: pd.DataFrame, name: str) -> dict[str, Any]:
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:
        return {}
    match = rankings.loc[rankings["player_name"].astype(str).map(_name_key).eq(_name_key(name))]
    return match.iloc[0].to_dict() if not match.empty else {}


def _history_row(history: pd.DataFrame, name: str, season: int) -> dict[str, Any]:
    if history is None or history.empty or "player_name" not in history.columns:
        return {}
    mask = history["player_name"].astype(str).map(_name_key).eq(_name_key(name))
    if "season" in history.columns:
        mask &= pd.to_numeric(history["season"], errors="coerce").eq(int(season))
    match = history.loc[mask]
    return match.iloc[0].to_dict() if not match.empty else {}


def _birth_row(births: pd.DataFrame | None, name: str) -> dict[str, Any]:
    if births is None or births.empty:
        return {}
    if "name_key" in births.columns:
        match = births.loc[births["name_key"].astype(str).map(_name_key).eq(_name_key(name))]
    else:
        name_col = _name_col(births)
        match = births.loc[births[name_col].astype(str).map(_name_key).eq(_name_key(name))] if name_col else births.iloc[0:0]
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


def _espn_ppr_row(row: pd.Series) -> float | None:
    scoring = {
        "passing_yards": .04,
        "passing_tds": 4.0,
        "interceptions": -2.0,
        "rushing_yards": .1,
        "rushing_tds": 6.0,
        "receptions": 1.0,
        "receiving_yards": .1,
        "receiving_tds": 6.0,
        "fumbles_lost": -2.0,
        "passing_two_point_conversions": 2.0,
        "rushing_two_point_conversions": 2.0,
        "receiving_two_point_conversions": 2.0,
    }
    available = [c for c in scoring if c in row.index and pd.notna(row.get(c))]
    if available:
        return float(sum(float(row.get(c) or 0) * scoring[c] for c in available))
    value = row.get("fantasy_points_ppr")
    return float(value) if pd.notna(value) else None


def _points(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame.apply(_espn_ppr_row, axis=1), errors="coerce")


def _position_finish(history: pd.DataFrame, name: str, season: int, pos: str) -> str:
    row = _history_row(history, name, season)
    for col in ("position_finish_total", "season_finish", "position_finish"):
        value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
        if pd.notna(value):
            return f"{pos}{int(value)}"
    return "—"


def _sum(frame: pd.DataFrame, col: str) -> float:
    return float(pd.to_numeric(frame[col], errors="coerce").fillna(0).sum()) if col in frame.columns else 0.0


def _return_href() -> str:
    page = str(st.query_params.get("return_page") or st.session_state.get("player_profile_return_page") or "Players")
    return "?" + urlencode({"page": page})


def _base(name: str, pid: str, year: int, tab: str) -> dict[str, str]:
    params = {"player": name, "player_id": pid, "season": str(year), "profile_tab": tab}
    for key in ("return_page", "return_q"):
        if st.query_params.get(key):
            params[key] = str(st.query_params.get(key))
    return params


def _weekly_table(frame: pd.DataFrame, pos: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    data: dict[str, Any] = {}
    data["WK"] = pd.to_numeric(frame["week"], errors="coerce").astype("Int64") if "week" in frame.columns else range(1, len(frame) + 1)
    for col in ("opponent_team", "opponent", "opp"):
        if col in frame.columns:
            data["OPP"] = frame[col].fillna("—").astype(str)
            break
    data["FPTS"] = _points(frame).round(1)
    p = str(pos).upper()
    if p == "QB":
        pairs = (("YDS", "passing_yards"), ("TD", "passing_tds"), ("I/F", "interceptions"))
    elif p in {"WR", "TE"}:
        pairs = (("REC", "receptions"), ("YDS", "receiving_yards"), ("TD", "receiving_tds"), ("TGT", "targets"))
    else:
        pairs = (("ATT", "carries"), ("YDS", "rushing_yards"), ("TD", "rushing_tds"), ("REC", "receptions"))
    for label, col in pairs:
        if col in frame.columns:
            data[label] = pd.to_numeric(frame[col], errors="coerce").fillna(0).round(0).astype(int)
    table = pd.DataFrame(data)
    if "WK" in table.columns:
        table = table[pd.to_numeric(table["WK"], errors="coerce").between(1, 18)].sort_values("WK")
    return table


def _css() -> None:
    st.markdown("""
<style>
[data-testid="stAppViewBlockContainer"],.block-container{max-width:520px!important;padding-left:0!important;padding-right:0!important;background:#111214!important}
.pp-wrap{background:#111214;color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.pp-back{display:inline-block;color:#fff!important;text-decoration:none!important;font-size:28px;padding:4px 16px 2px}
.pp-hero{position:relative;overflow:hidden;background:linear-gradient(180deg,#183047 0%,#202225 54%,#202225 100%);min-height:265px;padding:22px 22px 16px;border-radius:0 0 14px 14px}
.pp-name{font-size:25px;font-weight:1000;letter-spacing:-.02em;position:relative;z-index:3}.pp-team{font-size:15px;color:#eee;margin-top:4px;position:relative;z-index:3}.pp-logo{width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:7px}.pp-photo{position:absolute;right:0;top:0;height:185px;max-width:58%;object-fit:contain;object-position:right bottom;z-index:2}.pp-photo-fallback{position:absolute;right:20px;top:45px;font-size:54px;font-weight:1000;color:#4c5359}.pp-metrics{position:absolute;left:20px;right:20px;bottom:14px;display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #55585a;border-radius:12px;background:#252729;padding:14px 4px}.pp-metric{text-align:center}.pp-v{font-size:22px;font-weight:1000}.pp-l{font-size:10px;color:#aeb0b3;margin-top:2px}.pp-tabs{display:grid;grid-template-columns:repeat(6,1fr);border-bottom:1px solid #303236;background:#111214;overflow:hidden}.pp-tab{color:#aaa!important;text-decoration:none!important;text-align:center;font-size:10px;font-weight:700;padding:18px 1px 13px;white-space:nowrap}.pp-tab.active{color:#fff!important;border-bottom:4px solid #fff}.pp-card{margin:14px 0 0;background:#202224;border-radius:14px 14px 0 0;padding:18px 20px 20px}.pp-card-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.pp-title{font-size:18px;font-weight:1000}.pp-yearselect [data-baseweb="select"]>div{background:#050505!important;border:1px solid #555!important;border-radius:22px!important;min-height:40px!important}.pp-subtabs{display:grid;grid-template-columns:repeat(3,1fr);background:#555759;border-radius:24px;overflow:hidden;margin:16px 0 10px}.pp-subtab{padding:11px 4px;text-align:center;font-size:12px;font-weight:800;color:#fff}.pp-subtab.active{background:#090a0b;border-radius:24px}.pp-log{width:100%;border-collapse:collapse;table-layout:fixed;margin:0 -20px;width:calc(100% + 40px)}.pp-log th{font-size:10px;color:#f2f2f2;text-align:center;padding:10px 4px;border-top:1px solid #3a3b3d;border-bottom:1px solid #3a3b3d}.pp-log td{font-size:11px;color:#b9bbbe;text-align:center;padding:14px 4px;border-bottom:1px solid #292b2d}.pp-log tr:nth-child(odd) td{background:#27292b}.pp-log .fpts{font-weight:900;color:#d6d7d9}.pp-statgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.pp-stat{background:#292b2d;border-radius:9px;padding:12px 5px;text-align:center}.pp-stat-v{font-size:18px;font-weight:1000}.pp-stat-l{font-size:9px;color:#aaa}.pp-news{background:#292b2d;border-radius:9px;padding:12px;margin:9px 0}.inline-player-link{color:#dfff00!important;text-decoration:underline!important;font-weight:900}.player-link{color:inherit!important;text-decoration:none!important}
@media(max-width:390px){.pp-name{font-size:23px}.pp-photo{height:172px}.pp-v{font-size:19px}.pp-tab{font-size:9px}.pp-log th,.pp-log td{font-size:9px}.pp-hero{min-height:250px}}
</style>
""", unsafe_allow_html=True)


def render_player_profile(
    player_name: str,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame,
    history: pd.DataFrame,
    births: pd.DataFrame | None = None,
    player_id: str | None = None,
    draft_state: dict[str, Any] | None = None,
) -> None:
    _css()
    player_id = str(player_id or st.query_params.get("player_id") or canonical_player_id(weekly, player_name))
    frame = _weekly_for_player(weekly, player_id, player_name)
    ranking = _rank_row(rankings, player_name)
    years = sorted(
        pd.to_numeric(frame["season"], errors="coerce").dropna().astype(int).unique().tolist(), reverse=True
    ) if not frame.empty and "season" in frame.columns else []

    position = _position_value(frame, ranking)
    team = _team_value(frame, ranking)
    birth = _birth_row(births, player_name)
    espn_id = pd.to_numeric(pd.Series([birth.get("espn_id")]), errors="coerce").iloc[0]
    headshot = f"https://a.espncdn.com/i/headshots/nfl/players/full/{int(espn_id)}.png" if pd.notna(espn_id) else ""
    slug = {"JAX":"jax","WSH":"wsh","LV":"lv","LAR":"lar","LAC":"lac"}.get(team.upper(), team.lower())
    logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{slug}.png" if team and team != "—" else ""
    jersey = ranking.get("jersey_number") or ranking.get("jersey")
    jersey_num = pd.to_numeric(pd.Series([jersey]), errors="coerce").iloc[0]
    jersey_text = f" • #{int(jersey_num)}" if pd.notna(jersey_num) else ""

    if not years:
        st.markdown(f'<a class="pp-back" href="{html.escape(_return_href(),quote=True)}" target="_self">‹</a>', unsafe_allow_html=True)
        st.warning("No verified weekly game rows are available for this player in the loaded historical dataset.")
        return

    qyear = pd.to_numeric(pd.Series([st.query_params.get("season")]), errors="coerce").iloc[0]
    year = int(qyear) if pd.notna(qyear) and int(qyear) in years else years[0]
    tab = str(st.query_params.get("profile_tab") or "GAME LOG").upper()
    valid_tabs = ("OVERVIEW", "NEWS", "STATS", "ODDS", "GAME LOG", "PROJECTIONS")
    if tab not in valid_tabs:
        tab = "GAME LOG"

    season_frame = frame.loc[pd.to_numeric(frame["season"], errors="coerce").eq(year)].copy()
    if "week" in season_frame.columns:
        season_frame = season_frame.sort_values("week")
    pts = _points(season_frame).dropna()
    total = float(pts.sum()) if not pts.empty else 0.0
    games = int(pts.count())
    ppg = total / games if games else 0.0
    pos_rank = _position_finish(history, player_name, year, position)
    current_rank = ranking.get("position_rank")
    current_rank_num = pd.to_numeric(pd.Series([current_rank]), errors="coerce").iloc[0]
    hero_rank = str(int(current_rank_num)) if pd.notna(current_rank_num) else pos_rank.replace(position, "") if pos_rank != "—" else "—"
    roster_pct = ranking.get("percent_rostered") or ranking.get("roster_pct") or ranking.get("rostered")
    roster_num = pd.to_numeric(pd.Series([roster_pct]), errors="coerce").iloc[0]
    roster_text = f"{float(roster_num):.1f}" if pd.notna(roster_num) else "—"

    st.markdown(f'<a class="pp-back" href="{html.escape(_return_href(),quote=True)}" target="_self">‹</a>', unsafe_allow_html=True)
    photo = f'<img class="pp-photo" src="{html.escape(headshot,quote=True)}" alt="{html.escape(player_name)}">' if headshot else f'<div class="pp-photo-fallback">{html.escape("".join(x[0] for x in player_name.split()[:2]).upper())}</div>'
    logo_html = f'<img class="pp-logo" src="{html.escape(logo,quote=True)}" alt="{html.escape(team)}">' if logo else ""
    st.markdown(
        f'<div class="pp-hero"><div class="pp-name">{html.escape(player_name.upper())}</div>'
        f'<div class="pp-team">{logo_html}{html.escape(team)} • {html.escape(position)}{html.escape(jersey_text)}</div>{photo}'
        f'<div class="pp-metrics">'
        f'<div class="pp-metric"><div class="pp-v">{html.escape(hero_rank)}</div><div class="pp-l">POS RANK</div></div>'
        f'<div class="pp-metric"><div class="pp-v">{ppg:.1f}</div><div class="pp-l">AVG FPTS</div></div>'
        f'<div class="pp-metric"><div class="pp-v">{total:.1f}</div><div class="pp-l">{year} FPTS</div></div>'
        f'<div class="pp-metric"><div class="pp-v">{roster_text}</div><div class="pp-l">%ROST</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="pp-tabs">' + ''.join(
            f'<a class="pp-tab{" active" if tab == t else ""}" href="?{urlencode(_base(player_name, player_id, year, t))}" target="_self">{t.title()}</a>'
            for t in valid_tabs
        ) + '</div>',
        unsafe_allow_html=True,
    )

    if tab == "NEWS":
        st.markdown('<div class="pp-card"><div class="pp-title">PLAYER NEWS</div>', unsafe_allow_html=True)
        try:
            from espn_news_service import fetch_espn_news
            articles = fetch_espn_news(limit=40)
        except Exception:
            articles = []
        hits = [a for a in articles if player_name.casefold() in (str(a.get("title", "")) + " " + str(a.get("description", ""))).casefold()]
        if not hits:
            st.info("No current verified ESPN news item in the app cache mentions this player.")
        for article in hits[:8]:
            st.markdown(
                f'<div class="pp-news"><div style="font-size:13px;font-weight:900">{html.escape(str(article.get("title") or "NFL Update"))}</div>'
                f'<div style="font-size:9px;color:#999;margin-top:4px">{html.escape(str(article.get("published") or ""))}</div>'
                f'<div style="font-size:10px;color:#ccc;margin-top:5px">{html.escape(str(article.get("description") or "")[:260])}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if tab == "ODDS":
        st.markdown('<div class="pp-card"><div class="pp-title">ODDS</div>', unsafe_allow_html=True)
        st.info("A verified live player-prop odds feed is not connected. Draft Coach will not fabricate betting lines.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if tab == "PROJECTIONS":
        st.markdown('<div class="pp-card"><div class="pp-title">PROJECTIONS</div>', unsafe_allow_html=True)
        projection = None
        for col in ("projected_points", "projection", "projected_fantasy_points", "fpts"):
            if col in ranking and pd.notna(ranking.get(col)):
                projection = pd.to_numeric(pd.Series([ranking.get(col)]), errors="coerce").iloc[0]
                if pd.notna(projection):
                    break
        if projection is None or pd.isna(projection):
            st.info("No verified projection is present in the current rankings feed, so no projection is being invented.")
        else:
            st.metric("Projected PPR Points", f"{float(projection):.1f}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="pp-card">', unsafe_allow_html=True)
    left, right = st.columns([3.2, 1.2], gap="small")
    with left:
        st.markdown(f'<div class="pp-title">{year} REGULAR SEASON ({html.escape(team)})</div>', unsafe_allow_html=True)
    with right:
        ykey = f"profile_year_{_safe_key(player_id)}"
        if st.session_state.get(ykey) not in years:
            st.session_state[ykey] = year
        selected = st.selectbox("Season", years, key=ykey, label_visibility="collapsed")
        if int(selected) != year:
            st.query_params["season"] = str(int(selected))
            st.rerun()

    if tab in {"GAME LOG", "OVERVIEW"}:
        if position.upper() == "QB":
            sublabels = ("Passing", "Rushing", "Misc TD")
        elif position.upper() in {"WR", "TE"}:
            sublabels = ("Receiving", "Rushing", "Misc TD")
        else:
            sublabels = ("Rushing", "Receiving", "Misc TD")
        st.markdown(
            '<div class="pp-subtabs">' + ''.join(
                f'<div class="pp-subtab{" active" if i == 0 else ""}">{label}</div>' for i, label in enumerate(sublabels)
            ) + '</div>',
            unsafe_allow_html=True,
        )
        table = _weekly_table(season_frame, position)
        if table.empty:
            st.info("No verified weekly game log rows are available for this season.")
        else:
            cols = list(table.columns)
            header = ''.join(f'<th>{html.escape(str(c))}</th>' for c in cols)
            rows = []
            for _, row in table.iterrows():
                cells = []
                for col in cols:
                    value = row[col]
                    text = "—" if pd.isna(value) else (f"{float(value):.1f}" if col == "FPTS" else str(value))
                    css = ' class="fpts"' if col == "FPTS" else ""
                    cells.append(f'<td{css}>{html.escape(text)}</td>')
                rows.append('<tr>' + ''.join(cells) + '</tr>')
            st.markdown(f'<table class="pp-log"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)

    if tab in {"STATS", "OVERVIEW"}:
        if position.upper() == "QB":
            stats = [
                ("PASS YDS", _sum(season_frame, "passing_yards")), ("PASS TD", _sum(season_frame, "passing_tds")),
                ("INT", _sum(season_frame, "interceptions")), ("RUSH YDS", _sum(season_frame, "rushing_yards")),
                ("RUSH TD", _sum(season_frame, "rushing_tds")),
            ]
        else:
            stats = [
                ("RUSH ATT", _sum(season_frame, "carries")), ("RUSH YDS", _sum(season_frame, "rushing_yards")),
                ("TARGETS", _sum(season_frame, "targets")), ("REC", _sum(season_frame, "receptions")),
                ("REC YDS", _sum(season_frame, "receiving_yards")), ("RUSH TD", _sum(season_frame, "rushing_tds")),
                ("REC TD", _sum(season_frame, "receiving_tds")),
            ]
        st.markdown(
            '<div class="pp-statgrid">' + ''.join(
                f'<div class="pp-stat"><div class="pp-stat-v">{int(round(value))}</div><div class="pp-stat-l">{html.escape(label)}</div></div>'
                for label, value in stats
            ) + '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
