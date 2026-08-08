from __future__ import annotations

import os
import sqlite3
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from espn_news_service import fetch_espn_news
from mock_draft_ui_v2 import render_mock_draft_room_v2
from player_profile import canonical_player_id, linkify_player_names, player_link_html, render_player_profile
from shiva_chatgpt_service import ask_shiva_via_chatgpt
from shiva_engine import build_history_frame

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"
WEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"

@st.cache_data(show_spinner=False)
def load_roi() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as con: return pd.read_sql_query("SELECT * FROM draft_roi_scores", con)

@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    df=pd.read_csv(RANKINGS_PATH)
    for col in ("adp","overall_rank","position_rank","projected_points"):
        if col in df.columns: df[col]=pd.to_numeric(df[col],errors="coerce")
    return df.dropna(subset=["player_name","position","adp"]).copy()

@st.cache_data(show_spinner=False)
def load_births() -> pd.DataFrame:
    if not BIRTH_DATES_PATH.exists(): return pd.DataFrame(columns=["name_key","birth_date","espn_id"])
    df=pd.read_csv(BIRTH_DATES_PATH)
    if "birth_date" in df.columns: df["birth_date"]=pd.to_datetime(df["birth_date"],errors="coerce")
    return df.dropna(subset=["name_key"]).drop_duplicates("name_key",keep="last")

@st.cache_resource(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    if not WEEKLY_PATH.exists(): return pd.DataFrame()
    header=pd.read_csv(WEEKLY_PATH,compression="gzip",nrows=0).columns.tolist()
    wanted=["season","week","season_type","player_id","player_display_name","player_name","name","position","recent_team","team","opponent_team","opponent","game_id","result","fantasy_points_ppr","fantasy_points","targets","receptions","receiving_yards","receiving_tds","carries","rushing_yards","rushing_tds","target_share","red_zone_touches","attempts","passing_yards","passing_tds","interceptions","passing_attempts","completions","fumbles_lost","passing_two_point_conversions","rushing_two_point_conversions","receiving_two_point_conversions"]
    usecols=[c for c in wanted if c in header]
    return pd.read_csv(WEEKLY_PATH,compression="gzip",usecols=usecols or None,low_memory=False)

@st.cache_data(ttl=600,show_spinner=False)
def load_news() -> list[dict[str,str]]: return fetch_espn_news(limit=6)

def _api_key() -> str:
    try: secret_key=str(st.secrets.get("OPENAI_API_KEY","")).strip()
    except Exception: secret_key=""
    return str(os.environ.get("OPENAI_API_KEY","")).strip() or secret_key or str(st.session_state.get("shiva_openai_api_key","")).strip()

def _global_css() -> None:
    st.markdown("""
<style>
:root{--bg:#02070c;--panel:#07121b;--line:#183044;--lime:#dfff00;--cyan:#32c8ff}html,body,.stApp{background:radial-gradient(circle at 50% -20%,#0a2840 0,#02070c 38%,#010408 100%)!important;color:#fff!important;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;overflow-x:hidden!important}.block-container{max-width:520px!important;padding:7px 9px 82px!important;overflow-x:hidden!important}#MainMenu,footer,header{visibility:hidden}.stApp p,.stApp label{color:#fff}.stButton button{min-height:42px!important;border-radius:9px!important;border:1px solid #263d50!important;background:linear-gradient(180deg,#10202c,#08131d)!important;color:#fff!important;font-size:12px!important;font-weight:900!important}.stButton button[kind="primary"]{background:linear-gradient(135deg,#dfff00,#9dff00)!important;color:#061006!important;border-color:#e9ff4d!important}.stButton button[kind="primary"] p{color:#061006!important}[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#07121c!important;color:#fff!important;border:1px solid #263b4c!important;border-radius:8px!important;min-height:38px!important;height:38px!important;font-size:11px!important}[data-testid="stTextArea"] textarea{background:#07121c!important;color:#fff!important;border:1px solid #263b4c!important;border-radius:9px!important}.app-top{display:flex;justify-content:space-between;align-items:flex-start;padding:4px 2px 7px}.brand{font-size:18px;font-weight:1000;font-style:italic;color:#dfff00;letter-spacing:.08em}.brand-sub{font-size:11px;color:#fff;margin-top:2px}.top-icons{font-size:20px}.home-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:7px 0 10px}.home-card{min-height:100px;border-radius:10px;border:1px solid;padding:10px 6px;display:flex;flex-direction:column;justify-content:center;text-align:center;text-decoration:none!important;color:#fff!important}.home-icon{font-size:30px;line-height:1}.home-title{font-size:12px;font-weight:1000;margin-top:7px}.home-sub{font-size:9px;color:#e1e6ea;margin-top:3px}.ask-home{display:grid;grid-template-columns:44px 1fr 22px;gap:8px;align-items:center;background:linear-gradient(135deg,#08283e,#061827);border:1px solid #0f6998;border-radius:10px;padding:10px;margin:8px 0;text-decoration:none!important;color:#fff!important}.ask-bot{font-size:29px}.ask-title{font-size:15px;font-weight:1000}.ask-sub{font-size:10px;color:#d1e4ef;margin-top:2px}.league-card{background:#07131e;border:1px solid #24405a;border-radius:10px;padding:10px;margin:8px 0}.league-label{font-size:9px;color:#9fb0bd}.league-name{font-size:14px;font-weight:1000;margin-top:3px}.league-meta{font-size:10px;color:#d3dbe1;margin-top:3px}.page-head{text-align:center;font-size:22px;font-weight:1000;margin:2px 0}.page-sub{text-align:center;font-size:10px;color:#bdc8d1;margin-bottom:7px}.section-head{font-size:14px;font-weight:1000;color:#dfff00;margin:12px 0 5px}.directory-row{display:grid;grid-template-columns:31px minmax(0,1fr) 36px 43px;gap:4px;align-items:center;padding:6px;border-radius:6px;margin:2px 0;border:1px solid rgba(255,255,255,.10)}.directory-rank{font-size:10px;font-weight:1000}.directory-name{font-size:11px!important;font-weight:1000!important;color:#fff!important;text-decoration:none!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}.directory-meta{font-size:8px;color:#e0e5e8}.pos-pill{font-size:8px;text-align:center;font-weight:900}.adp{text-align:right;font-size:9px;font-weight:1000}.bottom-nav{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(520px,100vw);z-index:9999;background:rgba(2,8,13,.98);border-top:1px solid #163048;display:grid;grid-template-columns:repeat(5,1fr);padding:6px 4px max(7px,env(safe-area-inset-bottom));backdrop-filter:blur(12px)}.bottom-item{text-align:center;text-decoration:none!important;color:#d3dbe1!important;font-size:9px;font-weight:800}.bottom-icon{font-size:19px;display:block;margin-bottom:1px}.bottom-item.active{color:#dfff00!important}.news-card{background:#07131d;border:1px solid #20394c;border-radius:9px;padding:8px;margin:5px 0}.news-title{font-size:11px;font-weight:900}.news-meta{font-size:8px;color:#9fb0bd;margin-top:3px}.news-desc{font-size:9px;color:#d1d9df;line-height:1.3;margin-top:4px}.inline-player-link{color:#dfff00!important;text-decoration:underline!important;font-weight:1000}@media(max-width:390px){.block-container{padding-left:7px!important;padding-right:7px!important}.home-grid{gap:6px}.home-card{min-height:94px}.home-title{font-size:11px}}
</style>""",unsafe_allow_html=True)

def _bottom_nav(page:str)->None:
    items=[("Home","⌂","Home"),("Draft","◉","Mock Draft"),("Players","♙","Players"),("Team","♧","League History"),("More","•••","Draft Coach")]; parts=[]; active_target="Players" if page=="Player Profile" else page
    for label,icon,target in items:
        cls="bottom-item active" if active_target==target else "bottom-item"; parts.append(f'<a class="{cls}" href="?page={target.replace(" ","%20")}" target="_self"><span class="bottom-icon">{icon}</span>{label}</a>')
    st.markdown('<div class="bottom-nav">'+''.join(parts)+'</div>',unsafe_allow_html=True)

def _position_colors(pos:str)->tuple[str,str]: return {"QB":("#d5232b","#8a1017"),"RB":("#ff7a00","#a94300"),"WR":("#138dd8","#075688"),"TE":("#42a92d","#205f17"),"FLEX":("#9341d2","#58217f"),"D/ST":("#8d5008","#52300a"),"K":("#58636e","#303941")}.get(str(pos).upper(),("#5b6570","#2d343b"))

def _resolve_page()->str:
    query_player=st.query_params.get("player"); query_player_id=st.query_params.get("player_id")
    if query_player or query_player_id:
        if query_player: st.session_state["player_profile_name"]=str(query_player)
        if query_player_id: st.session_state["player_profile_id"]=str(query_player_id)
        if st.query_params.get("return_page"): st.session_state["player_profile_return_page"]=str(st.query_params.get("return_page"))
        return "Player Profile"
    query_page=st.query_params.get("page")
    if query_page: st.session_state["page"]=str(query_page)
    if "page" not in st.session_state: st.session_state["page"]="Home"
    return str(st.session_state["page"])

def _home(rankings:pd.DataFrame,roi:pd.DataFrame)->None:
    st.markdown('<div class="app-top"><div><div class="brand">SHIVA INTELLIGENCE</div><div class="brand-sub">Your Draft Command Center</div></div><div class="top-icons">☰ &nbsp; ♧</div></div>',unsafe_allow_html=True)
    cards=[("🏆","DRAFT BOARD","2026 Rankings","Mock Draft","#ff9d00","#2f2000"),("👥","MOCK DRAFT","Practice & Plan","Mock Draft","#b95cff","#27103c"),("👤","PLAYER PROFILES","Stats & Trends","Players","#33c8ff","#072b3b"),("⭐","MY TEAM HQ","Roster & Lineup","League History","#62d930","#15330a"),("🥷","SLEEPERS","Hidden Gems","Draft Coach","#ffb000","#352500"),("📋","CHEAT SHEETS","Key Rankings","Draft Coach","#ee417d","#3a0e1f")]
    st.markdown('<div class="home-grid">'+''.join(f'<a class="home-card" href="?page={target.replace(" ","%20")}" target="_self" style="border-color:{border};background:linear-gradient(145deg,{bg},#061018)"><div class="home-icon">{icon}</div><div class="home-title">{title}</div><div class="home-sub">{sub}</div></a>' for icon,title,sub,target,border,bg in cards)+'</div>',unsafe_allow_html=True)
    st.markdown('<a class="ask-home" href="?page=Shiva%20Intelligence" target="_self"><div class="ask-bot">🤖</div><div><div class="ask-title">ASK SHIVA GPT</div><div class="ask-sub">Ask questions, get advice, win your league.</div></div><div style="font-size:24px">›</div></a>',unsafe_allow_html=True)
    leagues=sorted(roi["league_name"].dropna().astype(str).unique().tolist()) if "league_name" in roi.columns else []; league_name=leagues[0] if leagues else "Shiva Champion League"; st.markdown(f'<div class="league-card"><div class="league-label">MY LEAGUE</div><div class="league-name">{escape(league_name)}</div><div class="league-meta">10-Team • Full PPR</div></div>',unsafe_allow_html=True)
    news=load_news()
    if news:
        st.markdown('<div class="section-head">LIVE FANTASY NEWS</div>',unsafe_allow_html=True)
        for a in news[:3]: st.markdown(f'<div class="news-card"><div class="news-title">{escape(str(a.get("title") or "NFL Update"))}</div><div class="news-meta">{escape(str(a.get("published") or ""))}</div><div class="news-desc">{escape(str(a.get("description") or "")[:180])}</div></div>',unsafe_allow_html=True)

def _players(rankings:pd.DataFrame,weekly:pd.DataFrame)->None:
    st.markdown('<div class="page-head">PLAYER PROFILES</div><div class="page-sub">2026 board • tap any player for verified history</div>',unsafe_allow_html=True); c1,c2=st.columns([1.6,1],gap="small")
    with c1: search=st.text_input("Search players",placeholder="Search players...",label_visibility="collapsed",key="directory_search")
    with c2: pos=st.selectbox("Position",["ALL","QB","RB","WR","TE","D/ST","K"],label_visibility="collapsed",key="directory_pos")
    frame=rankings.copy()
    if search.strip(): frame=frame[frame["player_name"].astype(str).str.contains(search.strip(),case=False,na=False)]
    if pos!="ALL": frame=frame[frame["position"].astype(str).eq(pos)]
    sort_col="overall_rank" if "overall_rank" in frame.columns else "adp"; frame=frame.sort_values([sort_col,"adp"]).head(160)
    for _,r in frame.iterrows():
        c1c,c2c=_position_colors(str(r["position"])); rank=int(r[sort_col]) if pd.notna(r.get(sort_col)) else int(r["adp"]); name=str(r["player_name"]); pid=canonical_player_id(weekly,name); link=player_link_html(pid,name,css_class="directory-name",return_page="Players"); st.markdown(f'<div class="directory-row" style="background:linear-gradient(90deg,{c2c},{c1c})"><div class="directory-rank">{rank}</div><div>{link}<div class="directory-meta">{escape(str(r.get("team") or "—"))}</div></div><div class="pos-pill">{escape(str(r["position"]))}</div><div class="adp">{float(r["adp"]):.1f}</div></div>',unsafe_allow_html=True)

def _ask_shiva(rankings:pd.DataFrame,history:pd.DataFrame,roi:pd.DataFrame,weekly:pd.DataFrame)->None:
    st.markdown('<div class="page-head">ASK SHIVA GPT</div><div class="page-sub">Data first. Shiva makes the decision.</div>',unsafe_allow_html=True); key=_api_key()
    if not key:
        with st.expander("Connect ChatGPT",expanded=True):
            entered=st.text_input("OpenAI API key",type="password",placeholder="sk-...",key="v2_api_key")
            if entered.strip(): st.session_state["shiva_openai_api_key"]=entered.strip(); key=entered.strip()
    with st.form("v2_ask_form"):
        q=st.text_area("What do you want to know?",placeholder="Who should I draft? Compare two players. Show me 2025 weekly consistency...",height=105); send=st.form_submit_button("ASK SHIVA GPT",use_container_width=True,type="primary")
    if send:
        if not q.strip(): st.warning("Ask Shiva a question first.")
        elif not key: st.error("Connect the OpenAI API key first.")
        else:
            with st.spinner("Shiva is calculating the evidence..."): st.session_state["v2_shiva_report"]=ask_shiva_via_chatgpt(q,history,roi,rankings,weekly,key,st.session_state.get("mock_draft_state_v2"))
    rep=st.session_state.get("v2_shiva_report")
    if rep:
        answer=linkify_player_names(str(rep.get("answer") or ""),rankings,weekly,return_page="Shiva Intelligence"); why=linkify_player_names(str(rep.get("why") or ""),rankings,weekly,return_page="Shiva Intelligence"); st.markdown(f'<div class="league-card" style="border-color:#2ba1d7"><div style="font-size:9px;color:#4ed4ff;font-weight:1000">SHIVA ANSWER</div><div style="font-size:18px;font-weight:1000;color:#dfff00;margin-top:6px">{answer}</div><div style="font-size:11px;color:#d6e0e6;line-height:1.4;margin-top:6px">{why}</div></div>',unsafe_allow_html=True)

def _draft_coach(rankings:pd.DataFrame,roi:pd.DataFrame,weekly:pd.DataFrame)->None:
    st.markdown('<div class="page-head">DRAFT COACH</div><div class="page-sub">Values, sleepers and board context</div>',unsafe_allow_html=True); frame=rankings.copy()
    if "overall_rank" in frame.columns: frame["value"]=pd.to_numeric(frame["adp"],errors="coerce")-pd.to_numeric(frame["overall_rank"],errors="coerce"); frame=frame.sort_values("value",ascending=False)
    st.markdown('<div class="section-head">VALUE BOARD</div>',unsafe_allow_html=True)
    for _,r in frame.head(30).iterrows():
        c1,c2=_position_colors(str(r["position"])); name=str(r["player_name"]); pid=canonical_player_id(weekly,name); link=player_link_html(pid,name,css_class="directory-name",return_page="Draft Coach"); value=float(r.get("value") or 0); st.markdown(f'<div class="directory-row" style="background:linear-gradient(90deg,{c2},{c1})"><div class="directory-rank">{escape(str(r["position"]))}</div><div>{link}<div class="directory-meta">ADP {float(r["adp"]):.1f}</div></div><div></div><div class="adp" style="color:#dfff00">{value:+.0f}</div></div>',unsafe_allow_html=True)

def _league_history(roi:pd.DataFrame,weekly:pd.DataFrame)->None:
    st.markdown('<div class="page-head">LEAGUE HISTORY</div><div class="page-sub">Your actual historical drafts</div>',unsafe_allow_html=True); leagues=sorted(roi["league_name"].dropna().astype(str).unique().tolist()) if "league_name" in roi.columns else []; c1,c2=st.columns(2,gap="small")
    with c1: league=st.selectbox("League",["ALL"]+leagues)
    seasons=sorted(pd.to_numeric(roi["season"],errors="coerce").dropna().astype(int).unique().tolist(),reverse=True) if "season" in roi.columns else []
    with c2: season=st.selectbox("Season",["ALL"]+seasons)
    frame=roi.copy()
    if league!="ALL": frame=frame[frame["league_name"].astype(str).eq(league)]
    if season!="ALL": frame=frame[pd.to_numeric(frame["season"],errors="coerce").eq(int(season))]
    for _,r in frame.sort_values(["season","overall_pick"],ascending=[False,True]).head(200).iterrows():
        name=str(r["player_name"]); pid=canonical_player_id(weekly,name); link=player_link_html(pid,name,css_class="directory-name",return_page="League History"); c1c,c2c=_position_colors(str(r["position"])); st.markdown(f'<div class="directory-row" style="background:linear-gradient(90deg,{c2c},{c1c})"><div class="directory-rank">R{int(r["round"])}</div><div>{link}<div class="directory-meta">{int(r["season"])} • Pick {int(r["overall_pick"])} • {escape(str(r.get("team_name") or ""))}</div></div><div class="pos-pill">{escape(str(r["position"]))}</div><div class="adp">{float(r.get("ppg") or 0):.1f}</div></div>',unsafe_allow_html=True)

def run()->None:
    st.set_page_config(page_title="Shiva Intelligence",page_icon="🏆",layout="centered",initial_sidebar_state="collapsed"); _global_css(); roi=load_roi(); rankings=load_rankings(); births=load_births(); weekly=load_weekly()
    for col in ["season","round","overall_pick","position_draft_rank","position_finish_total","fantasy_points_ppr","ppg","games_played","final_draft_roi"]:
        if col in roi.columns: roi[col]=pd.to_numeric(roi[col],errors="coerce")
    history=build_history_frame(roi,births); page=_resolve_page()
    if page=="Player Profile":
        player=str(st.session_state.get("player_profile_name") or st.query_params.get("player") or ""); player_id=str(st.session_state.get("player_profile_id") or st.query_params.get("player_id") or canonical_player_id(weekly,player)); render_player_profile(player,rankings,weekly,history,births,player_id,st.session_state.get("mock_draft_state_v2")); _bottom_nav("Player Profile"); return
    if page=="Home": _home(rankings,roi)
    elif page=="Players": _players(rankings,weekly)
    elif page=="Shiva Intelligence": _ask_shiva(rankings,history,roi,weekly)
    elif page=="Mock Draft": render_mock_draft_room_v2(rankings,weekly,history,roi,DB_PATH,ask_shiva_via_chatgpt,_api_key() or None)
    elif page=="League History": _league_history(roi,weekly)
    else: _draft_coach(rankings,roi,weekly)
    _bottom_nav(page)
