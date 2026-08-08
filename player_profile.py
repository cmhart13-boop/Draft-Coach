from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import pandas as pd
import streamlit as st

POSITION_TONE = {
    "QB": ("#ef3038", "#721118"),
    "RB": ("#ff8a00", "#6b3500"),
    "WR": ("#1598f2", "#083d63"),
    "TE": ("#4cc832", "#174c14"),
    "D/ST": ("#a76618", "#49300f"),
    "K": ("#a8adb4", "#353a40"),
}

def player_profile_href(player_name: str) -> str:
    return f"?player={quote(str(player_name))}"

def player_profile_link(player_name: str, css_class: str = "player-link") -> str:
    safe=html.escape(str(player_name)); href=html.escape(player_profile_href(player_name),quote=True)
    return f'<a class="{css_class}" href="{href}" target="_self">{safe}</a>'

def _safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+","_",str(value))[:80]

def open_player_profile(player_name: str, return_page: str | None = None) -> None:
    if return_page: st.session_state["player_profile_return_page"]=return_page
    st.session_state["player_profile_name"]=str(player_name)
    st.session_state.page="Player Profile"

def close_player_profile() -> None:
    st.session_state.pop("player_profile_name",None)
    if "player" in st.query_params: del st.query_params["player"]

def player_name_button(player_name: str, *, return_page: str, key: str, use_container_width: bool = True) -> bool:
    clicked=st.button(str(player_name),key=key,use_container_width=use_container_width)
    if clicked: open_player_profile(player_name,return_page)
    return clicked

def _name_col(frame: pd.DataFrame) -> str | None:
    for col in ("player_display_name","player_name","name"):
        if col in frame.columns: return col
    return None

def _weekly_for_player(weekly: pd.DataFrame, player_name: str) -> pd.DataFrame:
    if weekly is None or weekly.empty: return pd.DataFrame()
    name_col=_name_col(weekly)
    if not name_col: return pd.DataFrame()
    out=weekly.loc[weekly[name_col].astype(str).str.casefold().eq(str(player_name).casefold())].copy()
    if "season_type" in out.columns:
        reg=out["season_type"].astype(str).str.upper().isin(["REG","REGULAR","REGULAR SEASON"])
        if reg.any(): out=out.loc[reg].copy()
    for col in ("season","week","fantasy_points_ppr","fantasy_points","carries","targets","receptions","receiving_yards","receiving_tds","rushing_yards","rushing_tds","passing_yards","passing_tds","interceptions","attempts","target_share","red_zone_touches"):
        if col in out.columns: out[col]=pd.to_numeric(out[col],errors="coerce")
    return out

def _rank_row(rankings: pd.DataFrame, player_name: str) -> dict[str,Any]:
    if rankings is None or rankings.empty or "player_name" not in rankings.columns: return {}
    m=rankings[rankings["player_name"].astype(str).str.casefold().eq(str(player_name).casefold())]
    return m.iloc[0].to_dict() if not m.empty else {}

def _history_row(history: pd.DataFrame, player_name: str, season: int) -> dict[str,Any]:
    if history is None or history.empty or "player_name" not in history.columns: return {}
    mask=history["player_name"].astype(str).str.casefold().eq(str(player_name).casefold())
    if "season" in history.columns: mask &= pd.to_numeric(history["season"],errors="coerce").eq(int(season))
    m=history.loc[mask]
    return m.iloc[0].to_dict() if not m.empty else {}

def _team_value(frame: pd.DataFrame, ranking: dict[str,Any]) -> str:
    if ranking.get("team"): return str(ranking["team"])
    for col in ("recent_team","team"):
        if col in frame.columns:
            vals=frame[col].dropna().astype(str)
            if not vals.empty: return vals.iloc[-1]
    return "—"

def _position_value(frame: pd.DataFrame, ranking: dict[str,Any]) -> str:
    if ranking.get("position"): return str(ranking["position"])
    if "position" in frame.columns:
        vals=frame["position"].dropna().astype(str)
        if not vals.empty: return vals.iloc[-1]
    return "—"

def _sum(frame: pd.DataFrame, col: str) -> float:
    return float(pd.to_numeric(frame[col],errors="coerce").fillna(0).sum()) if col in frame.columns else 0.0

def _player_age(births: pd.DataFrame | None, player_name: str, season: int) -> str:
    if births is None or births.empty or "birth_date" not in births.columns: return ""
    if "name_key" in births.columns:
        key=re.sub(r"[^a-z0-9]+","",player_name.lower())
        keys=births["name_key"].astype(str).str.lower().str.replace(r"[^a-z0-9]+","",regex=True)
        match=births.loc[keys.eq(key)]
    else:
        nc=_name_col(births); match=births.loc[births[nc].astype(str).str.casefold().eq(player_name.casefold())] if nc else births.iloc[0:0]
    if match.empty: return ""
    dob=pd.to_datetime(match.iloc[0].get("birth_date"),errors="coerce")
    if pd.isna(dob): return ""
    return str(int((pd.Timestamp(year=int(season),month=9,day=1)-dob).days/365.2425))

def _position_finish_from_history(hist: dict[str,Any], position: str) -> str:
    for col in ("position_finish_total","season_finish","position_finish"):
        v=pd.to_numeric(pd.Series([hist.get(col)]),errors="coerce").iloc[0]
        if pd.notna(v): return f"{position}{int(v)}"
    return "—"

def _result_text(row: pd.Series) -> str:
    for col in ("result","game_result"):
        if col in row and pd.notna(row[col]): return str(row[col])
    return "—"

def _weekly_table(frame: pd.DataFrame, position: str) -> pd.DataFrame:
    if frame.empty: return pd.DataFrame()
    points_col="fantasy_points_ppr" if "fantasy_points_ppr" in frame.columns else "fantasy_points"
    data={"WK":pd.to_numeric(frame["week"],errors="coerce").astype("Int64") if "week" in frame.columns else pd.Series(range(1,len(frame)+1))}
    for opp_col in ("opponent_team","opponent","opp"):
        if opp_col in frame.columns:
            data["OPP"]=frame[opp_col].fillna("—").astype(str); break
    data["FPTS"]=pd.to_numeric(frame[points_col],errors="coerce").round(1) if points_col in frame.columns else pd.Series([None]*len(frame))
    if str(position).upper()=="QB":
        for label,col in (("PASS YDS","passing_yards"),("PASS TD","passing_tds"),("INT","interceptions"),("RUSH","rushing_yards")):
            if col in frame.columns: data[label]=pd.to_numeric(frame[col],errors="coerce").fillna(0).round(0).astype(int)
    else:
        for label,col in (("RUSH","carries"),("REC","receptions"),("REC YDS","receiving_yards")):
            if col in frame.columns: data[label]=pd.to_numeric(frame[col],errors="coerce").fillna(0).round(0).astype(int)
        td_cols=[c for c in ("rushing_tds","receiving_tds") if c in frame.columns]
        if td_cols:
            data["TD"]=sum(pd.to_numeric(frame[c],errors="coerce").fillna(0) for c in td_cols).astype(int)
    table=pd.DataFrame(data).sort_values("WK")
    return table[pd.to_numeric(table["WK"],errors="coerce").between(1,17)]

def _profile_css() -> None:
    st.markdown("""
<style>
.profile-name{font-size:25px;font-weight:1000;line-height:1.02;text-align:center;letter-spacing:.01em}
.profile-sub{font-size:12px;color:#fff;text-align:center;margin-top:3px}
.profile-top-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #24313a;margin:8px 0 9px}
.profile-top-tab{text-align:center;padding:8px 2px;font-size:11px;font-weight:900;color:#fff}.profile-top-tab.active{border-bottom:3px solid #dfff00}
.profile-panel{background:linear-gradient(145deg,#0a151f,#061018);border:1px solid #20384a;border-radius:11px;padding:10px;margin:7px 0}
.profile-hero{display:grid;grid-template-columns:94px minmax(0,1fr);gap:10px;align-items:center}
.profile-avatar{width:90px;height:84px;border-radius:7px;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#0b4e83,#05243f);border:1px solid #168bd7;font-size:27px;font-weight:1000}
.profile-team{font-size:13px;font-weight:900}
.profile-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:4px;margin-top:8px}
.profile-metric{text-align:center;padding:5px 2px}.profile-value{font-size:18px;font-weight:1000;color:#ffb000}.profile-label{font-size:9px;color:#c5ced6;margin-top:1px;font-weight:900}
.profile-bio{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:3px;margin-top:7px;background:#071018;border-radius:7px;padding:5px}
.profile-bio span{text-align:center;font-size:9px;color:#dbe5ec}
.profile-years{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;margin:7px 0}.profile-year{background:#0a1822;border:1px solid #274055;border-radius:6px;text-align:center;padding:6px 1px;font-size:10px;font-weight:900}.profile-year.active{background:#0d67ad;color:#fff}
.profile-section-title{font-size:14px;font-weight:1000;margin:12px 0 6px}
.profile-table{width:100%;border-collapse:collapse;font-size:9px}.profile-table th{font-size:8px;color:#d2dae0;padding:4px 2px;text-align:center;border-bottom:1px solid #263745}.profile-table td{padding:4px 2px;text-align:center;border-bottom:1px solid #152633}.profile-table td.fpts{color:#38d8ff;font-weight:1000}
.player-link{color:inherit!important;text-decoration:none!important}
@media(max-width:430px){.profile-name{font-size:22px}.profile-hero{grid-template-columns:82px minmax(0,1fr)}.profile-avatar{width:78px;height:76px}.profile-value{font-size:16px}.profile-table{font-size:8px}}
</style>
""",unsafe_allow_html=True)

def render_player_directory(rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, births: pd.DataFrame | None = None) -> None:
    _profile_css()
    st.markdown('<div style="text-align:center;font-size:24px;font-weight:1000;margin:4px 0 3px">PLAYER PROFILES</div><div style="text-align:center;color:#aab6c1;font-size:12px;margin-bottom:12px">Tap any player for verified year-by-year Full-PPR stats.</div>',unsafe_allow_html=True)
    search=st.text_input("Search players",placeholder="Search player...",key="profile_directory_search",label_visibility="collapsed")
    pos=st.selectbox("Position",["ALL","QB","RB","WR","TE","D/ST","K"],key="profile_directory_pos",label_visibility="collapsed")
    pool=rankings.copy() if rankings is not None else pd.DataFrame()
    if pool.empty: st.info("No current player rankings are loaded."); return
    if search.strip(): pool=pool[pool["player_name"].astype(str).str.contains(search.strip(),case=False,na=False)]
    if pos!="ALL": pool=pool[pool["position"].astype(str).eq(pos)]
    sort_col="overall_rank" if "overall_rank" in pool.columns else "adp"
    for _,row in pool.sort_values(sort_col).head(120).iterrows():
        name=str(row["player_name"]); position=str(row.get("position") or "—"); team=str(row.get("team") or "—")
        tone,dark=POSITION_TONE.get(position,("#7f8c99","#27313a"))
        adp=pd.to_numeric(pd.Series([row.get("adp")]),errors="coerce").iloc[0]
        href=html.escape(player_profile_href(name),quote=True)
        st.markdown(f'<div style="display:grid;grid-template-columns:38px minmax(0,1fr) 55px;gap:7px;align-items:center;padding:8px;border-radius:8px;margin:4px 0;background:linear-gradient(90deg,{dark},{tone});border:1px solid rgba(255,255,255,.12)"><div style="font-size:11px;font-weight:1000;text-align:center">{html.escape(position)}</div><a href="{href}" target="_self" style="color:#fff;text-decoration:none;font-size:14px;font-weight:1000">{html.escape(name)}<span style="display:block;font-size:9px;font-weight:700;color:#e4e8eb">{html.escape(team)}</span></a><div style="text-align:right;font-size:10px;font-weight:900">ADP {float(adp):.1f}</div></div>' if pd.notna(adp) else '',unsafe_allow_html=True)

def render_player_profile(player_name: str, rankings: pd.DataFrame, weekly: pd.DataFrame, history: pd.DataFrame, births: pd.DataFrame | None = None) -> None:
    _profile_css()
    player_weekly=_weekly_for_player(weekly,player_name); ranking=_rank_row(rankings,player_name)
    years=sorted(pd.to_numeric(player_weekly["season"],errors="coerce").dropna().astype(int).unique().tolist(),reverse=True) if not player_weekly.empty and "season" in player_weekly.columns else []
    return_page=st.session_state.get("player_profile_return_page","Player Profiles")
    b,t,s=st.columns([.7,4.6,.7])
    with b:
        if st.button("‹",key="profile_back",use_container_width=True):
            close_player_profile(); st.session_state.page=return_page; st.rerun()
    position=_position_value(player_weekly,ranking); team=_team_value(player_weekly,ranking)
    with t: st.markdown(f'<div class="profile-name">{html.escape(player_name.upper())}</div><div class="profile-sub">{html.escape(position)} • {html.escape(team)}</div>',unsafe_allow_html=True)
    with s: st.markdown('<div style="font-size:26px;color:#ffb000;text-align:center">★</div>',unsafe_allow_html=True)
    st.markdown('<div class="profile-top-tabs"><div class="profile-top-tab active">OVERVIEW</div><div class="profile-top-tab">STATS</div><div class="profile-top-tab">GAME LOG</div><div class="profile-top-tab">NEWS</div></div>',unsafe_allow_html=True)

    if not years:
        st.warning("No weekly scoring rows are available for this player in the verified 2014-2025 weekly dataset."); return

    cyr,cblank=st.columns([1.3,2.7])
    with cyr: selected_year=st.selectbox("Season",years,index=0,key=f"profile_year_{_safe_key(player_name)}",label_visibility="collapsed")
    season_frame=player_weekly[pd.to_numeric(player_weekly["season"],errors="coerce").eq(int(selected_year))].copy().sort_values("week")
    points_col="fantasy_points_ppr" if "fantasy_points_ppr" in season_frame.columns else "fantasy_points"
    points=pd.to_numeric(season_frame[points_col],errors="coerce").dropna() if points_col in season_frame.columns else pd.Series(dtype=float)
    total=float(points.sum()) if not points.empty else 0.0; games=int(points.count()); ppg=total/games if games else 0.0
    hist=_history_row(history,player_name,int(selected_year)); finish=_position_finish_from_history(hist,position)
    initials="".join(part[0] for part in player_name.split()[:2]).upper(); age=_player_age(births,player_name,int(selected_year))
    tone,dark=POSITION_TONE.get(position,("#62c4ff","#05243f"))

    st.markdown(
        f'<div class="profile-panel"><div class="profile-hero"><div class="profile-avatar" style="background:linear-gradient(145deg,{dark},#06111b);border-color:{tone};color:{tone}">{html.escape(initials)}</div>'
        f'<div><div class="profile-team" style="color:{tone}">{html.escape(team)} • {html.escape(position)}</div>'
        f'<div class="profile-metrics"><div class="profile-metric"><div class="profile-value">{total:.1f}</div><div class="profile-label">FPTS</div></div><div class="profile-metric"><div class="profile-value">{ppg:.1f}</div><div class="profile-label">PPG</div></div><div class="profile-metric"><div class="profile-value">{games}</div><div class="profile-label">GAMES</div></div><div class="profile-metric"><div class="profile-value">{html.escape(finish)}</div><div class="profile-label">RANK</div></div></div></div></div>'
        f'<div class="profile-bio"><span>Year: {selected_year}</span><span>Team: {html.escape(team)}</span><span>Age: {html.escape(age or "—")}</span><span>Full PPR</span></div></div>',unsafe_allow_html=True)

    year_cells=[]
    for y in years[:5]:
        cls="profile-year active" if y==selected_year else "profile-year"
        year_cells.append(f'<div class="{cls}">{y}</div>')
    st.markdown('<div class="profile-years">'+''.join(year_cells)+'</div>',unsafe_allow_html=True)

    table=_weekly_table(season_frame,position)
    st.markdown('<div class="profile-section-title">GAME LOG</div>',unsafe_allow_html=True)
    if table.empty: st.info("No weekly game log rows are available for this season."); return
    headers=''.join(f'<th>{html.escape(str(c))}</th>' for c in table.columns)
    rows=[]
    for _,r in table.iterrows():
        cells=[]
        for c in table.columns:
            val=r[c]
            txt="—" if pd.isna(val) else str(val)
            cls=' class="fpts"' if c=="FPTS" else ""
            cells.append(f'<td{cls}>{html.escape(txt)}</td>')
        rows.append('<tr>'+''.join(cells)+'</tr>')
    st.markdown(f'<table class="profile-table"><thead><tr>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table>',unsafe_allow_html=True)
