from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

POSITION_TONE={"QB":("#ef2f35","#711217"),"RB":("#f57a00","#7a3500"),"WR":("#188fda","#064b78"),"TE":("#43ad2f","#1d6218"),"FLEX":("#9141d0","#4a1d70"),"D/ST":("#87500b","#422907"),"K":("#596573","#2d3740")}

def _safe_key(v:str)->str:return re.sub(r"[^A-Za-z0-9_-]+","_",str(v))[:90]
def _name_key(v:str)->str:return re.sub(r"[^a-z0-9]+","",str(v).casefold())
def _name_col(df:pd.DataFrame)->str|None:
    for c in ("player_display_name","player_name","name"):
        if c in df.columns:return c
    return None

def canonical_player_id(weekly:pd.DataFrame|None,player_name:str,fallback:str|None=None)->str:
    if weekly is not None and not weekly.empty and "player_id" in weekly.columns:
        nc=_name_col(weekly)
        if nc:
            m=weekly.loc[weekly[nc].astype(str).map(_name_key).eq(_name_key(player_name)),"player_id"].dropna().astype(str)
            if not m.empty:return m.iloc[-1]
    return str(fallback or f"name::{_name_key(player_name)}")

def player_profile_href(player_name:str,player_id:str|None=None,*,return_page:str|None=None,return_query:str|None=None,season:int|None=None,profile_tab:str|None=None)->str:
    p={"player":str(player_name)}
    if player_id:p["player_id"]=str(player_id)
    if return_page:p["return_page"]=str(return_page)
    if return_query:p["return_q"]=str(return_query)
    if season is not None:p["season"]=str(int(season))
    if profile_tab:p["profile_tab"]=str(profile_tab)
    return "?"+urlencode(p)

def player_link_html(player_id:str,player_name:str,*,css_class:str="player-link",return_page:str|None=None,return_query:str|None=None)->str:
    href=html.escape(player_profile_href(player_name,player_id,return_page=return_page,return_query=return_query),quote=True)
    return f'<a class="{css_class}" href="{href}" target="_self">{html.escape(str(player_name))}</a>'

def linkify_player_names(text:str,rankings:pd.DataFrame,weekly:pd.DataFrame,*,return_page:str)->str:
    safe=html.escape(str(text or ""))
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:return safe
    for name in sorted(rankings["player_name"].dropna().astype(str).unique(),key=len,reverse=True):
        en=html.escape(name)
        if en in safe:safe=safe.replace(en,player_link_html(canonical_player_id(weekly,name),name,css_class="inline-player-link",return_page=return_page))
    return safe

def open_player_profile(player_name:str,return_page:str|None=None,player_id:str|None=None)->None:
    if return_page:st.session_state["player_profile_return_page"]=return_page
    st.session_state["player_profile_name"]=str(player_name)
    if player_id:st.session_state["player_profile_id"]=str(player_id)
    st.session_state["page"]="Player Profile"

def close_player_profile()->None:
    for k in ("player_profile_name","player_profile_id"):st.session_state.pop(k,None)
    for k in ("player","player_id","season","profile_tab","return_page","return_q","favorite"):
        if k in st.query_params:del st.query_params[k]

def _weekly_for_player(weekly:pd.DataFrame,player_id:str|None,player_name:str)->pd.DataFrame:
    if weekly is None or weekly.empty:return pd.DataFrame()
    out=pd.DataFrame()
    if player_id and "player_id" in weekly.columns and not str(player_id).startswith("name::"):out=weekly.loc[weekly["player_id"].astype(str).eq(str(player_id))].copy()
    if out.empty:
        nc=_name_col(weekly)
        if nc:out=weekly.loc[weekly[nc].astype(str).map(_name_key).eq(_name_key(player_name))].copy()
    if "season_type" in out.columns and not out.empty:
        reg=out["season_type"].astype(str).str.upper().isin(["REG","REGULAR","REGULAR SEASON"])
        if reg.any():out=out.loc[reg].copy()
    for c in ("season","week","fantasy_points_ppr","fantasy_points","carries","targets","receptions","receiving_yards","receiving_tds","rushing_yards","rushing_tds","passing_yards","passing_tds","interceptions","passing_attempts","completions","fumbles_lost","passing_two_point_conversions","rushing_two_point_conversions","receiving_two_point_conversions"):
        if c in out.columns:out[c]=pd.to_numeric(out[c],errors="coerce")
    return out

def _rank_row(rankings:pd.DataFrame,name:str)->dict[str,Any]:
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:return {}
    m=rankings.loc[rankings["player_name"].astype(str).map(_name_key).eq(_name_key(name))]
    return m.iloc[0].to_dict() if not m.empty else {}

def _history_row(history:pd.DataFrame,name:str,season:int)->dict[str,Any]:
    if history is None or history.empty or "player_name" not in history.columns:return {}
    mask=history["player_name"].astype(str).map(_name_key).eq(_name_key(name))
    if "season" in history.columns:mask&=pd.to_numeric(history["season"],errors="coerce").eq(int(season))
    m=history.loc[mask];return m.iloc[0].to_dict() if not m.empty else {}

def _birth_row(births:pd.DataFrame|None,name:str)->dict[str,Any]:
    if births is None or births.empty:return {}
    if "name_key" in births.columns:m=births.loc[births["name_key"].astype(str).map(_name_key).eq(_name_key(name))]
    else:
        nc=_name_col(births);m=births.loc[births[nc].astype(str).map(_name_key).eq(_name_key(name))] if nc else births.iloc[0:0]
    return m.iloc[0].to_dict() if not m.empty else {}

def _team_value(frame:pd.DataFrame,ranking:dict[str,Any])->str:
    if ranking.get("team"):return str(ranking["team"])
    for c in ("recent_team","team"):
        if c in frame.columns:
            v=frame[c].dropna().astype(str)
            if not v.empty:return v.iloc[-1]
    return "—"

def _position_value(frame:pd.DataFrame,ranking:dict[str,Any])->str:
    if ranking.get("position"):return str(ranking["position"])
    if "position" in frame.columns:
        v=frame["position"].dropna().astype(str)
        if not v.empty:return v.iloc[-1]
    return "—"

def _age(b:dict[str,Any],season:int)->str:
    dob=pd.to_datetime(b.get("birth_date"),errors="coerce")
    if pd.isna(dob):return ""
    return str(int((pd.Timestamp(year=int(season),month=9,day=1)-dob).days/365.2425))

def _espn_ppr_row(r:pd.Series)->float|None:
    comp={"passing_yards":.04,"passing_tds":4.0,"interceptions":-2.0,"rushing_yards":.1,"rushing_tds":6.0,"receptions":1.0,"receiving_yards":.1,"receiving_tds":6.0,"fumbles_lost":-2.0,"passing_two_point_conversions":2.0,"rushing_two_point_conversions":2.0,"receiving_two_point_conversions":2.0}
    avail=[c for c in comp if c in r.index and pd.notna(r.get(c))]
    if not avail:
        f=r.get("fantasy_points_ppr");return float(f) if pd.notna(f) else None
    return float(sum(float(r.get(c) or 0)*comp[c] for c in avail))

def _points(frame:pd.DataFrame)->pd.Series:
    if frame.empty:return pd.Series(dtype=float)
    return pd.to_numeric(frame.apply(_espn_ppr_row,axis=1),errors="coerce")

def _position_finish(history:pd.DataFrame,name:str,season:int,pos:str)->str:
    h=_history_row(history,name,season)
    for c in ("position_finish_total","season_finish","position_finish"):
        v=pd.to_numeric(pd.Series([h.get(c)]),errors="coerce").iloc[0]
        if pd.notna(v):return f"{pos}{int(v)}"
    return "—"

def _sum(frame:pd.DataFrame,col:str)->float:return float(pd.to_numeric(frame[col],errors="coerce").fillna(0).sum()) if col in frame.columns else 0.0

def _weekly_table(frame:pd.DataFrame,pos:str)->pd.DataFrame:
    if frame.empty:return pd.DataFrame()
    data={"WK":pd.to_numeric(frame.get("week"),errors="coerce").astype("Int64") if "week" in frame.columns else pd.Series(range(1,len(frame)+1))}
    for c in ("opponent_team","opponent","opp"):
        if c in frame.columns:data["OPP"]=frame[c].fillna("—").astype(str);break
    if "result" in frame.columns:data["RESULT"]=frame["result"].fillna("—").astype(str)
    data["FPTS"]=_points(frame).round(1);p=str(pos).upper()
    if p=="QB":
        pairs=(("PASS YDS","passing_yards"),("PASS TD","passing_tds"),("INT","interceptions"),("RUSH YDS","rushing_yards"),("RUSH TD","rushing_tds"))
    elif p in {"WR","TE"}:pairs=(("TGT","targets"),("REC","receptions"),("REC YDS","receiving_yards"),("RUSH","carries"),("RUSH YDS","rushing_yards"))
    else:pairs=(("RUSH","carries"),("RUSH YDS","rushing_yards"),("REC","receptions"),("REC YDS","receiving_yards"))
    for label,c in pairs:
        if c in frame.columns:data[label]=pd.to_numeric(frame[c],errors="coerce").fillna(0).round(0).astype(int)
    if p!="QB":
        t=[c for c in ("rushing_tds","receiving_tds") if c in frame.columns]
        if t:data["TD"]=sum(pd.to_numeric(frame[c],errors="coerce").fillna(0) for c in t).astype(int)
    table=pd.DataFrame(data)
    if "WK" in table.columns:table=table[pd.to_numeric(table["WK"],errors="coerce").between(1,18)].sort_values("WK")
    return table

def _css()->None:
    st.markdown("""
<style>
.profile-top{display:grid;grid-template-columns:34px 1fr 72px;align-items:start;gap:6px;margin:1px 0 4px}.profile-back{font-size:34px;line-height:1;color:#fff!important;text-decoration:none!important}.profile-name{font-size:22px;font-weight:1000;line-height:1;text-align:center}.profile-sub{font-size:11px;color:#d0d7de;text-align:center;margin-top:4px}.profile-actions{display:flex;justify-content:flex-end;gap:12px;font-size:25px}.profile-actions a{color:#fff!important;text-decoration:none!important}.profile-actions .fav{color:#ffad00!important}.profile-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #25313b;margin:6px 0 8px}.profile-tab{text-align:center;padding:9px 1px;color:#fff!important;text-decoration:none!important;font-size:10px;font-weight:900}.profile-tab.active{border-bottom:2px solid #dfff00}.profile-card{background:linear-gradient(145deg,#09131d,#050b11);border:1px solid #173044;border-radius:10px;padding:8px;margin:7px 0}.profile-photo{height:82px;display:flex;align-items:flex-end;justify-content:center;overflow:hidden}.profile-photo img{max-width:88px;max-height:82px;object-fit:contain}.profile-teamline{display:flex;align-items:center;gap:6px;color:#d8e1e7;font-size:10px}.profile-teamline img{width:30px;height:30px;object-fit:contain}.profile-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:2px;margin-top:4px}.profile-metric{text-align:center;padding:3px 1px}.profile-value{font-size:17px;font-weight:1000;color:#ffb000}.profile-value.rank{color:#ff4050}.profile-label{font-size:8px;font-weight:900;color:#e3e8ec}.profile-bio{display:flex;justify-content:space-between;gap:5px;background:#08121a;border-radius:6px;padding:5px 7px;margin-top:5px;color:#dbe2e8;font-size:8px}.profile-years{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin:6px 0}.profile-year{background:linear-gradient(#122334,#0a1721);border:1px solid #274158;color:#fff!important;text-decoration:none!important;text-align:center;border-radius:6px;padding:5px 2px;font-size:10px;font-weight:900}.profile-year.active{background:linear-gradient(#138de0,#0d5d9a);border-color:#1597ef}.profile-section-title{font-size:12px;font-weight:1000;margin:9px 0 4px}.profile-log{width:100%;border-collapse:collapse;background:#02070b;font-size:8px}.profile-log th{color:#cbd4dc;font-size:7px;font-weight:900;text-align:right;padding:4px 3px;border-bottom:1px solid #263540;white-space:nowrap}.profile-log td{color:#fff;text-align:right;padding:3px;border-bottom:1px solid #16222c;white-space:nowrap}.profile-log th:first-child,.profile-log td:first-child,.profile-log th:nth-child(2),.profile-log td:nth-child(2){text-align:left}.profile-log .fpts{color:#36d7e9;font-weight:1000}.profile-stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}.profile-stat{background:#08131c;border:1px solid #1c3445;border-radius:7px;text-align:center;padding:7px 2px}.profile-stat-v{font-size:15px;font-weight:1000}.profile-stat-l{font-size:7px;color:#aeb9c2}.profile-news{background:#07131d;border:1px solid #20394c;border-radius:8px;padding:8px;margin:5px 0}.inline-player-link{color:#dfff00!important;text-decoration:underline!important;font-weight:900}.player-link{color:inherit!important;text-decoration:none!important}@media(max-width:390px){.profile-name{font-size:20px}.profile-photo{height:74px}.profile-photo img{max-height:74px}.profile-value{font-size:15px}.profile-log{font-size:7.5px}.profile-log th{font-size:6.5px;padding:4px 2px}.profile-log td{padding:3px 2px}}
</style>""",unsafe_allow_html=True)

def _base(name:str,pid:str,year:int,tab:str)->dict[str,str]:
    p={"player":name,"player_id":pid,"season":str(year),"profile_tab":tab}
    for k in ("return_page","return_q"):
        if st.query_params.get(k):p[k]=str(st.query_params.get(k))
    return p

def _return_href()->str:
    page=str(st.query_params.get("return_page") or st.session_state.get("player_profile_return_page") or "Players");p={"page":page};raw=str(st.query_params.get("return_q") or "")
    for pair in raw.split("&"):
        if "=" in pair:
            k,v=pair.split("=",1)
            if k:p[k]=v
    return "?"+urlencode(p)

def _favorite(player_id:str,state:dict[str,Any]|None)->bool:
    fav=set(st.session_state.get("favorite_player_ids") or []);action=st.query_params.get("favorite")
    if action=="toggle":
        if player_id in fav:
            fav.remove(player_id)
            if state and player_id in state.get("queue",[]):state["queue"]=[x for x in state["queue"] if x!=player_id]
        else:
            fav.add(player_id)
            if state and player_id in {str(p.get("id")) for p in state.get("availablePlayers",[])} and player_id not in state.get("queue",[]):state.setdefault("queue",[]).append(player_id)
        st.session_state["favorite_player_ids"]=sorted(fav);del st.query_params["favorite"];st.rerun()
    return player_id in fav

def render_player_profile(player_name:str,rankings:pd.DataFrame,weekly:pd.DataFrame,history:pd.DataFrame,births:pd.DataFrame|None=None,player_id:str|None=None,draft_state:dict[str,Any]|None=None)->None:
    _css();player_id=str(player_id or st.query_params.get("player_id") or canonical_player_id(weekly,player_name));frame=_weekly_for_player(weekly,player_id,player_name)
    if not player_name and not frame.empty:
        nc=_name_col(frame)
        if nc:player_name=str(frame[nc].dropna().astype(str).iloc[-1])
    ranking=_rank_row(rankings,player_name);years=sorted(pd.to_numeric(frame.get("season"),errors="coerce").dropna().astype(int).unique().tolist(),reverse=True) if not frame.empty and "season" in frame.columns else [];fav=_favorite(player_id,draft_state);star="★" if fav else "☆";position=_position_value(frame,ranking);team=_team_value(frame,ranking)
    jersey=ranking.get("jersey_number") or ranking.get("jersey");jnum=pd.to_numeric(pd.Series([jersey]),errors="coerce").iloc[0];jtxt=f" #{int(jnum)}" if pd.notna(jnum) else ""
    base={"player":player_name,"player_id":player_id,"profile_tab":str(st.query_params.get("profile_tab") or "OVERVIEW"),"favorite":"toggle"}
    for k in ("return_page","return_q","season"):
        if st.query_params.get(k):base[k]=str(st.query_params.get(k))
    st.markdown(f'<div class="profile-top"><a class="profile-back" href="{html.escape(_return_href(),quote=True)}" target="_self">‹</a><div><div class="profile-name">{html.escape(player_name.upper())}</div><div class="profile-sub">{html.escape(position)} • {html.escape(team)}{html.escape(jtxt)}</div></div><div class="profile-actions"><a class="fav" href="?{urlencode(base)}" target="_self">{star}</a><span>⌯</span></div></div>',unsafe_allow_html=True)
    if not years:st.warning("No verified weekly game rows are available for this player in the loaded 2014–2025 historical dataset.");return
    qy=pd.to_numeric(pd.Series([st.query_params.get("season")]),errors="coerce").iloc[0];year=int(qy) if pd.notna(qy) and int(qy) in years else years[0];tab=str(st.query_params.get("profile_tab") or "OVERVIEW").upper();tab=tab if tab in {"OVERVIEW","STATS","GAME LOG","NEWS"} else "OVERVIEW"
    st.markdown('<div class="profile-tabs">'+''.join(f'<a class="profile-tab{" active" if tab==t else ""}" href="?{urlencode(_base(player_name,player_id,year,t))}" target="_self">{t}</a>' for t in ("OVERVIEW","STATS","GAME LOG","NEWS"))+'</div>',unsafe_allow_html=True)
    sf=frame.loc[pd.to_numeric(frame["season"],errors="coerce").eq(year)].copy().sort_values("week");pts=_points(sf).dropna();total=float(pts.sum()) if not pts.empty else 0.0;games=int(pts.count());ppg=total/games if games else 0.0;ranktxt=_position_finish(history,player_name,year,position);birth=_birth_row(births,player_name);age=_age(birth,year);eid=pd.to_numeric(pd.Series([birth.get("espn_id")]),errors="coerce").iloc[0];head=f"https://a.espncdn.com/i/headshots/nfl/players/full/{int(eid)}.png" if pd.notna(eid) else "";slug={"JAX":"jax","WSH":"wsh","LV":"lv","LAR":"lar","LAC":"lac"}.get(team.upper(),team.lower());logo=f"https://a.espncdn.com/i/teamlogos/nfl/500/{slug}.png" if team and team!="—" else "";tone,_=POSITION_TONE.get(position,("#62c4ff","#05243f"));photo=f'<img src="{html.escape(head,quote=True)}" alt="{html.escape(player_name)}">' if head else f'<div style="font-size:28px;font-weight:1000;color:{tone}">{html.escape("".join(x[0] for x in player_name.split()[:2]).upper())}</div>';logohtml=f'<img src="{html.escape(logo,quote=True)}" alt="{html.escape(team)}">' if logo else "";ykey=f"profile_year_{_safe_key(player_id)}"
    if st.session_state.get(ykey) not in years or int(st.session_state.get(ykey,year))!=year:st.session_state[ykey]=year
    st.markdown('<div class="profile-card">',unsafe_allow_html=True);left,right=st.columns([1.05,3.8],gap="small")
    with left:st.markdown(f'<div class="profile-photo">{photo}</div>',unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="profile-teamline">{logohtml}<span>{html.escape(team)} • {html.escape(position)}</span></div>',unsafe_allow_html=True);sel=st.selectbox("Year",years,key=ykey,format_func=lambda y:f"{y} (Year)",label_visibility="collapsed")
        if int(sel)!=year:st.query_params["season"]=str(int(sel));st.rerun()
    st.markdown(f'<div class="profile-metrics"><div class="profile-metric"><div class="profile-value">{total:.1f}</div><div class="profile-label">FPTS</div></div><div class="profile-metric"><div class="profile-value">{ppg:.1f}</div><div class="profile-label">PPG</div></div><div class="profile-metric"><div class="profile-value">{games}</div><div class="profile-label">GAMES</div></div><div class="profile-metric"><div class="profile-value rank">{html.escape(ranktxt)}</div><div class="profile-label">RANK</div></div></div>',unsafe_allow_html=True)
    bio=[]
    for label,value in (("Height",ranking.get("height")),("Weight",ranking.get("weight")),("College",ranking.get("college")),("Age",age)):
        if value not in (None,"") and not (isinstance(value,float) and pd.isna(value)):bio.append(f"{label}: {value}")
    if bio:st.markdown('<div class="profile-bio">'+''.join(f'<span>{html.escape(str(v))}</span>' for v in bio)+'</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True);recent=years[:5];st.markdown('<div class="profile-years">'+''.join(f'<a class="profile-year{" active" if y==year else ""}" href="?{urlencode(_base(player_name,player_id,y,tab))}" target="_self">{y}</a>' for y in recent)+'</div>',unsafe_allow_html=True)
    if tab in {"OVERVIEW","GAME LOG"}:
        st.markdown('<div class="profile-section-title">GAME LOG</div>',unsafe_allow_html=True);table=_weekly_table(sf,position)
        if table.empty:st.info("No weekly game log rows are available for this season.")
        else:
            cols=list(table.columns);header=''.join(f'<th>{html.escape(str(c))}</th>' for c in cols);rows=[]
            for _,r in table.iterrows():
                cells=[]
                for c in cols:
                    v=r[c];text="—" if pd.isna(v) else (f"{float(v):.1f}" if c=="FPTS" else str(v));cls=' class="fpts"' if c=="FPTS" else "";cells.append(f'<td{cls}>{html.escape(text)}</td>')
                rows.append('<tr>'+''.join(cells)+'</tr>')
            st.markdown(f'<table class="profile-log"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>',unsafe_allow_html=True)
    if tab=="STATS":
        stats=[("PASS YDS",_sum(sf,"passing_yards")),("PASS TD",_sum(sf,"passing_tds")),("INT",_sum(sf,"interceptions")),("RUSH YDS",_sum(sf,"rushing_yards")),("RUSH TD",_sum(sf,"rushing_tds"))] if position=="QB" else [("RUSH ATT",_sum(sf,"carries")),("RUSH YDS",_sum(sf,"rushing_yards")),("TARGETS",_sum(sf,"targets")),("REC",_sum(sf,"receptions")),("REC YDS",_sum(sf,"receiving_yards")),("RUSH TD",_sum(sf,"rushing_tds")),("REC TD",_sum(sf,"receiving_tds"))];st.markdown('<div class="profile-stats-grid">'+''.join(f'<div class="profile-stat"><div class="profile-stat-v">{int(round(v))}</div><div class="profile-stat-l">{html.escape(k)}</div></div>' for k,v in stats)+'</div>',unsafe_allow_html=True)
    if tab=="NEWS":
        try:
            from espn_news_service import fetch_espn_news;articles=fetch_espn_news(limit=30)
        except Exception:articles=[]
        hits=[a for a in articles if player_name.casefold() in (str(a.get("title",""))+" "+str(a.get("description",""))).casefold()]
        if not hits:st.info("No current ESPN news item in the app cache mentions this player.")
        for a in hits[:8]:st.markdown(f'<div class="profile-news"><div style="font-size:12px;font-weight:1000">{html.escape(str(a.get("title") or "NFL Update"))}</div><div style="font-size:9px;color:#9fb0bd;margin-top:3px">{html.escape(str(a.get("published") or ""))}</div><div style="font-size:10px;color:#d1d9df;margin-top:4px">{html.escape(str(a.get("description") or "")[:220])}</div></div>',unsafe_allow_html=True)
