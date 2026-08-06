from __future__ import annotations

import sqlite3
import re
import base64
import time
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"
SPLASH_PATH = APP_DIR / "shiva_splash_screen.jpeg"

LEAGUE_IDS = {
    "Shiva": 1465338,
    "Shiva 2.0": 1506903,
}
CURRENT_SEASON = 2026

st.set_page_config(
    page_title="Shiva 2026 Draft Coach",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def show_startup_splash() -> None:
    """Show the branded startup image once per browser session, then open the app."""
    if st.session_state.get("startup_splash_complete", False):
        return

    try:
        splash_bytes = SPLASH_PATH.read_bytes()
        splash_b64 = base64.b64encode(splash_bytes).decode("utf-8")
    except Exception:
        st.session_state["startup_splash_complete"] = True
        return

    splash_slot = st.empty()
    splash_slot.markdown(
        f"""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp {{
  background:#0619ad !important;
  overflow:hidden !important;
}}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {{
  display:none !important;
}}
.block-container {{
  padding:0 !important;
  margin:0 !important;
  max-width:100% !important;
}}
.shiva-startup-splash {{
  position:fixed;
  inset:0;
  z-index:2147483647;
  width:100vw;
  height:100dvh;
  background:#0619ad;
  display:flex;
  align-items:center;
  justify-content:center;
  overflow:hidden;
  animation:shivaSplashFade 2.6s ease forwards;
}}
.shiva-startup-splash img {{
  width:100%;
  height:100%;
  object-fit:cover;
  object-position:center center;
  display:block;
}}
@keyframes shivaSplashFade {{
  0%,78% {{ opacity:1; }}
  100% {{ opacity:0; }}
}}
</style>
<div class="shiva-startup-splash" aria-label="Shiva Intelligence loading screen">
  <img src="data:image/jpeg;base64,{splash_b64}" alt="Shiva Intelligence App loading screen">
</div>
""",
        unsafe_allow_html=True,
    )

    # Keep the splash visible briefly, then transition to the normal home screen.
    time.sleep(2.6)
    st.session_state["startup_splash_complete"] = True
    splash_slot.empty()
    st.rerun()


show_startup_splash()


st.markdown(
    """
<style>
:root{
  --bg:#101012;
  --top:#080809;
  --card:#1c1c1f;
  --card2:#27272b;
  --line:#35353a;
  --muted:#85868c;
  --white:#f7f7f8;
  --green:#31f22f;
  --blue:#5b98ff;
  --red:#ff525d;
  --gold:#ffb52b;
}
html,body,[class*="css"]{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
.stApp{background:var(--bg);color:var(--white);}
.block-container{max-width:430px;padding:0 14px 56px!important;}
#MainMenu,footer,header{visibility:hidden;}

.top-shell{
  position:sticky;
  top:0;
  z-index:999;
  margin:0 -14px 12px;
  padding:14px 14px 10px;
  background:var(--top);
  border-bottom:1px solid #222226;
}
.top-title-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  min-height:34px;
}
.back-text{color:#d9d9dc;font-size:15px;font-weight:700;}
.page-title{
  color:#fff;
  font-size:16px;
  font-weight:1000;
  text-transform:uppercase;
  white-space:nowrap;
}
.section-label{
  color:#7d7e84;
  font-size:10px;
  font-weight:1000;
  letter-spacing:.1em;
  text-transform:uppercase;
  margin:18px 0 8px;
}
.card{
  background:var(--card);
  border:1px solid #28282c;
  border-radius:15px;
  padding:14px;
  margin-bottom:12px;
  box-shadow:0 10px 24px rgba(0,0,0,.17);
}
.card-title{color:#fff;font-size:15px;font-weight:1000;}
.card-sub{color:var(--muted);font-size:11px;line-height:1.4;margin-top:4px;}

.metric-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:9px;
  margin-bottom:12px;
}
.metric-box{
  min-height:78px;
  background:var(--card);
  border:1px solid #29292d;
  border-radius:14px;
  padding:11px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}
.metric-label{
  color:#77787e;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.06em;
  line-height:1.2;
  text-transform:uppercase;
}
.metric-value{color:#fff;font-size:20px;font-weight:1000;line-height:1;}
.metric-value.green{color:var(--green);}
.metric-value.blue{color:var(--blue);}
.metric-value.red{color:var(--red);}

.callout{
  border-left:4px solid var(--green);
  padding:8px 0 8px 11px;
  margin:5px 0;
}
.callout.red{border-left-color:var(--red);}
.callout.blue{border-left-color:var(--blue);}
.callout.gold{border-left-color:var(--gold);}
.callout-title{color:#fff;font-size:13px;font-weight:900;line-height:1.35;}
.callout-sub{color:#9a9ba1;font-size:11px;line-height:1.4;margin-top:3px;}

.list-row{
  display:grid;
  grid-template-columns:34px 1fr auto;
  gap:10px;
  align-items:center;
  padding:11px 0;
  border-top:1px solid #2a2a2e;
}
.list-row:first-child{border-top:0;}
.rank-circle{
  width:30px;height:30px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  background:var(--card2);color:#fff;font-size:12px;font-weight:1000;
}
.row-title{color:#fff;font-size:14px;font-weight:1000;line-height:1.25;}
.row-sub{color:#82838a;font-size:10px;line-height:1.35;margin-top:3px;}
.row-tag{font-size:10px;font-weight:1000;text-transform:uppercase;color:var(--green);}
.row-tag.blue{color:var(--blue);}
.row-tag.red{color:var(--red);}
.row-tag.gold{color:var(--gold);}

.pos-badge{
  width:34px;height:23px;border-radius:6px;
  display:inline-flex;align-items:center;justify-content:center;
  color:#111;font-size:10px;font-weight:1000;
}
.pos-RB{background:#55d68b;}
.pos-WR{background:#6bb8ff;}
.pos-QB{background:#ff6b70;}
.pos-TE{background:#c78cff;}

[data-baseweb="select"]>div{
  min-height:46px;
  background:#1f2330!important;
  border:1px solid #2d3240!important;
  border-radius:14px!important;
}
[data-baseweb="select"] span,[data-baseweb="select"] input{
  color:#fff!important;font-weight:800!important;
}
.stSelectbox label p,.stNumberInput label p,.stFileUploader label p{
  color:#dedee1!important;font-weight:900!important;
}
[data-testid="stDataFrame"]{
  background:var(--card)!important;
  border:1px solid #29292d!important;
  border-radius:14px!important;
  overflow:hidden;
}

/* ACTUAL CLICKABLE ESPN PILL BUTTONS */
.stButton button{
  width:100%!important;
  min-height:46px!important;
  padding:0 14px!important;
  border-radius:999px!important;
  border:1px solid #3b3b40!important;
  background:#2a2a2d!important;
  color:#d8d8dc!important;
  font-size:11px!important;
  line-height:1.1!important;
  font-weight:1000!important;
  box-shadow:none!important;
}
.stButton button:hover{
  background:#343438!important;
  border-color:#4d4d52!important;
  color:#fff!important;
}
.stButton button[kind="primary"]{
  background:var(--green)!important;
  border-color:var(--green)!important;
  color:#071007!important;
  box-shadow:0 4px 14px rgba(49,242,47,.18)!important;
}
.stButton button p{
  color:inherit!important;
  font-size:inherit!important;
  font-weight:inherit!important;
  margin:0!important;
}
h1,h2,h3,h4,p,label,.stMarkdown{color:var(--white)!important;}
@media(min-width:900px){.block-container{max-width:430px;}}

/* Intelligence report form */
div[data-testid="stFormSubmitButton"] button{
  min-height:46px!important;
  border-radius:999px!important;
  border:1px solid #3b3b40!important;
  background:#2a2a2d!important;
  color:#ffffff!important;
  font-size:12px!important;
  font-weight:1000!important;
  box-shadow:none!important;
}
div[data-testid="stFormSubmitButton"] button:hover{
  background:#343438!important;
  border-color:#4d4d52!important;
  color:#ffffff!important;
}

</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="top-shell">
  <div class="top-title-row">
    <div style="width:52px"></div>
    <div class="page-title">Shiva Draft Intelligence</div>
    <div style="width:52px"></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


st.markdown('''

<style>
/* Compact ESPN-style icon navigation */
.nav-caption{
  color:#77787d;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.1em;
  text-transform:uppercase;
  margin:10px 0 7px;
}
.st-key-nav_history button,
.st-key-nav_coach button,
.st-key-nav_fit button,
.st-key-nav_slot button,
.st-key-nav_live button,
.st-key-nav_grade button,
.st-key-nav_intel button{
  min-height:72px!important;
  padding:8px 4px!important;
  border-radius:18px!important;
  border:1px solid #313136!important;
  background:#1c1c1f!important;
  color:#a9a9ae!important;
  font-size:10px!important;
  line-height:1.12!important;
  font-weight:1000!important;
  box-shadow:none!important;
}
.st-key-nav_history button p,
.st-key-nav_coach button p,
.st-key-nav_fit button p,
.st-key-nav_slot button p,
.st-key-nav_live button p,
.st-key-nav_grade button p,
.st-key-nav_intel button p{
  white-space:pre-line!important;
  text-align:center!important;
  line-height:1.15!important;
  color:inherit!important;
}
.st-key-nav_history button[kind="primary"],
.st-key-nav_coach button[kind="primary"],
.st-key-nav_fit button[kind="primary"],
.st-key-nav_slot button[kind="primary"],
.st-key-nav_live button[kind="primary"],
.st-key-nav_grade button[kind="primary"],
.st-key-nav_intel button[kind="primary"]{
  background:#2a2a2e!important;
  color:#ffffff!important;
  border-color:#31f22f!important;
  box-shadow:inset 0 -4px 0 #31f22f!important;
}
.st-key-nav_history button:hover,
.st-key-nav_coach button:hover,
.st-key-nav_fit button:hover,
.st-key-nav_slot button:hover,
.st-key-nav_live button:hover,
.st-key-nav_grade button:hover,
.st-key-nav_intel button:hover{
  background:#252529!important;
  color:#fff!important;
}
.report-box{
  background:#151518;
  border:1px solid #2c2c31;
  border-radius:14px;
  padding:13px;
  margin:8px 0 12px;
}
.report-title{
  color:#fff;
  font-size:14px;
  font-weight:1000;
}
.report-answer{
  color:#31f22f;
  font-size:25px;
  line-height:1.05;
  font-weight:1000;
  margin-top:6px;
}
.report-note{
  color:#929399;
  font-size:11px;
  line-height:1.45;
  margin-top:6px;
}
[data-testid="stTextInput"] input{
  min-height:48px!important;
  border-radius:14px!important;
  background:#1f2330!important;
  color:#fff!important;
}
</style>

''', unsafe_allow_html=True)


st.markdown('''

<style>
/* ESPN-LIKE MOBILE TEAM SELECTOR */
.team-selector-shell{
  background:#080809;
  margin:0 -14px 10px;
  padding:0 14px 12px;
  border-bottom:1px solid #222226;
}
.team-selector-label{
  color:#76777d;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.09em;
  text-transform:uppercase;
  margin-bottom:6px;
}
.st-key-top_manager [data-baseweb="select"]>div{
  background:#17171a!important;
  border:1px solid #303035!important;
  border-radius:13px!important;
  min-height:48px!important;
}
.st-key-top_manager [data-baseweb="select"] span{
  color:#fff!important;
  font-size:15px!important;
  font-weight:1000!important;
}
.st-key-top_league [data-baseweb="select"]>div{
  background:#17171a!important;
  border:1px solid #303035!important;
  border-radius:13px!important;
  min-height:44px!important;
}
.st-key-top_league [data-baseweb="select"] span{
  color:#5b98ff!important;
  font-weight:900!important;
}

</style>

''', unsafe_allow_html=True)


st.markdown('''

<style>
.shiva-nav-shell{
  width:100%;
  margin:0 0 8px;
  padding:8px 4px 4px;
  border:0;
  border-radius:0;
  background:transparent;
  box-shadow:none;
}
.shiva-nav-title{
  color:#ffffff;
  font-size:14px;
  font-weight:1000;
  margin:0 0 4px 2px;
}

/* Native Streamlit buttons remain fully functional.
   The visual treatment is transparent: no square, pill, circle, or card behind the icon. */
.st-key-tool_history button,
.st-key-tool_coach button,
.st-key-tool_fit button,
.st-key-tool_plan button,
.st-key-tool_live button,
.st-key-tool_grade button,
.st-key-tool_intel button{
  width:100%!important;
  min-width:0!important;
  min-height:70px!important;
  padding:3px 1px 2px!important;
  margin:0!important;
  border:0!important;
  border-radius:0!important;
  background:transparent!important;
  box-shadow:none!important;
  color:#9a9ba1!important;
  font-size:10px!important;
  line-height:1.05!important;
  font-weight:850!important;
  white-space:pre-line!important;
  text-align:center!important;
  overflow:visible!important;
  transition:
    color 150ms ease,
    transform 150ms ease,
    filter 150ms ease!important;
}

.st-key-tool_history button p,
.st-key-tool_coach button p,
.st-key-tool_fit button p,
.st-key-tool_plan button p,
.st-key-tool_live button p,
.st-key-tool_grade button p,
.st-key-tool_intel button p{
  color:inherit!important;
  white-space:pre-line!important;
  text-align:center!important;
  line-height:1.05!important;
  margin:0!important;
  font-size:10px!important;
  font-weight:850!important;
  overflow:visible!important;
}

/* Make only the first line — the symbol — visually larger. */
.st-key-tool_history button p::first-line,
.st-key-tool_coach button p::first-line,
.st-key-tool_fit button p::first-line,
.st-key-tool_plan button p::first-line,
.st-key-tool_live button p::first-line,
.st-key-tool_grade button p::first-line,
.st-key-tool_intel button p::first-line{
  font-size:31px!important;
  line-height:1.1!important;
}

/* Selected section: symbol and label light up, with no box behind them. */
.st-key-tool_history button[kind="primary"],
.st-key-tool_coach button[kind="primary"],
.st-key-tool_fit button[kind="primary"],
.st-key-tool_plan button[kind="primary"],
.st-key-tool_live button[kind="primary"],
.st-key-tool_grade button[kind="primary"],
.st-key-tool_intel button[kind="primary"]{
  background:transparent!important;
  border:0!important;
  color:#ffffff!important;
  box-shadow:none!important;
  filter:drop-shadow(0 0 7px rgba(32,244,90,.48))!important;
}

.st-key-tool_history button[kind="primary"] p::first-line,
.st-key-tool_coach button[kind="primary"] p::first-line,
.st-key-tool_fit button[kind="primary"] p::first-line,
.st-key-tool_plan button[kind="primary"] p::first-line,
.st-key-tool_live button[kind="primary"] p::first-line,
.st-key-tool_grade button[kind="primary"] p::first-line,
.st-key-tool_intel button[kind="primary"] p::first-line{
  color:#20f45a!important;
  text-shadow:
    0 0 5px rgba(32,244,90,.9),
    0 0 12px rgba(32,244,90,.45)!important;
}

/* Hover/tap keeps the same clean treatment. */
.st-key-tool_history button:hover,
.st-key-tool_coach button:hover,
.st-key-tool_fit button:hover,
.st-key-tool_plan button:hover,
.st-key-tool_live button:hover,
.st-key-tool_grade button:hover,
.st-key-tool_intel button:hover{
  background:transparent!important;
  border:0!important;
  color:#ffffff!important;
  box-shadow:none!important;
}
.st-key-tool_history button:active,
.st-key-tool_coach button:active,
.st-key-tool_fit button:active,
.st-key-tool_plan button:active,
.st-key-tool_live button:active,
.st-key-tool_grade button:active,
.st-key-tool_intel button:active{
  transform:scale(.96)!important;
}

/* Lock both navigation rows side-by-side on mobile. */
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_intel),
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_live){
  display:flex!important;
  flex-wrap:nowrap!important;
  gap:2px!important;
  width:100%!important;
  margin-bottom:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_intel)>div,
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_live)>div{
  flex:1 1 0!important;
  width:25%!important;
  min-width:0!important;
}

@media(max-width:390px){
  .st-key-tool_history button,
  .st-key-tool_coach button,
  .st-key-tool_fit button,
  .st-key-tool_plan button,
  .st-key-tool_live button,
  .st-key-tool_grade button,
  .st-key-tool_intel button{
    min-height:66px!important;
    font-size:9px!important;
  }

  .st-key-tool_history button p,
  .st-key-tool_coach button p,
  .st-key-tool_fit button p,
  .st-key-tool_plan button p,
  .st-key-tool_live button p,
  .st-key-tool_grade button p,
  .st-key-tool_intel button p{
    font-size:9px!important;
  }

  .st-key-tool_history button p::first-line,
  .st-key-tool_coach button p::first-line,
  .st-key-tool_fit button p::first-line,
  .st-key-tool_plan button p::first-line,
  .st-key-tool_live button p::first-line,
  .st-key-tool_grade button p::first-line,
  .st-key-tool_intel button p::first-line{
    font-size:28px!important;
  }
}

.daily-tip{
  position:relative;
  overflow:hidden;
  background:
    linear-gradient(135deg,rgba(24,74,37,.96),rgba(24,25,28,.98));
  border:1px solid rgba(49,242,47,.42);
  border-radius:18px;
  padding:18px 17px;
  margin-bottom:14px;
  box-shadow:0 10px 28px rgba(0,0,0,.22);
}
.daily-tip::before{
  content:"";
  position:absolute;
  left:0;
  top:0;
  bottom:0;
  width:5px;
  background:#31f22f;
}
.daily-tip-label{
  color:#31f22f;
  font-size:10px;
  font-weight:1000;
  letter-spacing:.11em;
  text-transform:uppercase;
}
.daily-tip-text{
  color:#ffffff;
  font-size:17px;
  line-height:1.38;
  font-weight:950;
  margin-top:7px;
  letter-spacing:-.01em;
}

.coach-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:10px;
  margin-bottom:16px;
}
.coach-card{
  background:linear-gradient(180deg,#202024,#19191c);
  border:1px solid #303035;
  border-radius:16px;
  min-height:102px;
  padding:13px 12px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  box-shadow:0 8px 20px rgba(0,0,0,.16);
}
.coach-label{
  color:#8d8e94;
  font-size:9px;
  font-weight:1000;
  line-height:1.18;
  letter-spacing:.07em;
  text-transform:uppercase;
}
.coach-value{
  color:#ffffff;
  font-size:17px;
  line-height:1.08;
  font-weight:1000;
  letter-spacing:-.02em;
}
.coach-value.green{color:#31f22f;}
.coach-value.blue{color:#67a0ff;}
.coach-value.red{color:#ff5c66;}

.rule-list{
  display:flex;
  flex-direction:column;
  gap:10px;
  margin-bottom:14px;
}
.rule-card{
  display:grid;
  grid-template-columns:38px minmax(0,1fr);
  gap:12px;
  align-items:flex-start;
  background:linear-gradient(180deg,#202024,#1a1a1d);
  border:1px solid #303035;
  border-radius:16px;
  padding:14px;
  box-shadow:0 7px 18px rgba(0,0,0,.14);
}
.rule-number{
  width:36px;
  height:36px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:#2b2b30;
  border:1px solid #3b3b41;
  color:#31f22f;
  font-size:15px;
  font-weight:1000;
}
.rule-text{
  color:#ffffff;
  font-size:15px;
  line-height:1.42;
  font-weight:900;
  letter-spacing:-.01em;
}

.action-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:9px;
}
.action-card{
  display:grid;
  grid-template-columns:30px minmax(0,1fr);
  gap:10px;
  align-items:flex-start;
  border-radius:14px;
  padding:13px;
  background:#1d1d21;
  border:1px solid #303035;
}
.action-card.good{
  border-left:4px solid #31f22f;
}
.action-card.warn{
  border-left:4px solid #ff5c66;
}
.action-icon{
  width:28px;
  height:28px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:#2b2b30;
  font-size:14px;
  font-weight:1000;
}
.action-card.good .action-icon{color:#31f22f;}
.action-card.warn .action-icon{color:#ff5c66;}
.action-text{
  color:#f4f4f5;
  font-size:14px;
  line-height:1.4;
  font-weight:850;
}

div[data-testid="stExpander"]{
  border:1px solid #303035!important;
  border-radius:16px!important;
  background:#19191c!important;
  overflow:hidden!important;
  margin-bottom:10px!important;
}
div[data-testid="stExpander"] summary{
  min-height:52px!important;
  padding:0 14px!important;
}
div[data-testid="stExpander"] summary p{
  color:#ffffff!important;
  font-size:14px!important;
  font-weight:950!important;
}

@media(max-width:390px){
  .daily-tip{
    padding:16px 15px;
  }
  .daily-tip-text{
    font-size:16px;
  }
  .coach-grid{
    gap:7px;
  }
  .coach-card{
    min-height:96px;
    padding:11px 9px;
  }
  .coach-value{
    font-size:15px;
  }
  .rule-card{
    grid-template-columns:34px minmax(0,1fr);
    gap:10px;
    padding:13px 12px;
  }
  .rule-number{
    width:32px;
    height:32px;
    font-size:14px;
  }
  .rule-text{
    font-size:14px;
  }
}

.hero-card{
  position:relative;
  overflow:hidden;
  background:linear-gradient(145deg,#202126,#151518);
  border:1px solid #34353b;
  border-radius:20px;
  padding:18px;
  margin:0 0 14px;
  box-shadow:0 12px 30px rgba(0,0,0,.24);
}
.hero-card::after{
  content:"";
  position:absolute;
  width:150px;
  height:150px;
  right:-72px;
  top:-82px;
  border-radius:50%;
  background:radial-gradient(circle,rgba(49,242,47,.16),transparent 68%);
  pointer-events:none;
}
.hero-kicker{
  color:#31f22f;
  font-size:10px;
  font-weight:1000;
  letter-spacing:.1em;
  text-transform:uppercase;
}
.hero-title{
  color:#ffffff;
  font-size:24px;
  line-height:1.08;
  font-weight:1000;
  letter-spacing:-.025em;
  margin-top:7px;
}
.hero-sub{
  color:#a0a1a7;
  font-size:13px;
  line-height:1.45;
  margin-top:7px;
}
.hero-score{
  color:#31f22f;
  font-size:35px;
  line-height:1;
  font-weight:1000;
  margin-top:10px;
}
.hero-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:8px;
  margin-top:14px;
}
.hero-mini{
  background:rgba(255,255,255,.035);
  border:1px solid #303137;
  border-radius:13px;
  padding:10px;
  min-height:68px;
}
.hero-mini-label{
  color:#7f8087;
  font-size:8px;
  line-height:1.15;
  font-weight:1000;
  letter-spacing:.07em;
  text-transform:uppercase;
}
.hero-mini-value{
  color:#ffffff;
  font-size:14px;
  line-height:1.1;
  font-weight:1000;
  margin-top:8px;
}
.hero-mini-value.green{color:#31f22f;}
.hero-mini-value.blue{color:#67a0ff;}
.hero-mini-value.red{color:#ff5c66;}

.quick-answer{
  background:#19191c;
  border:1px solid #303035;
  border-radius:16px;
  padding:14px;
  margin-bottom:10px;
}
.quick-answer-title{
  color:#ffffff;
  font-size:16px;
  font-weight:1000;
}
.quick-answer-sub{
  color:#929399;
  font-size:12px;
  line-height:1.4;
  margin-top:4px;
}
.compact-pick-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:8px;
  margin-bottom:12px;
}
.compact-pick{
  display:grid;
  grid-template-columns:52px minmax(0,1fr) auto;
  gap:10px;
  align-items:center;
  background:#1b1b1f;
  border:1px solid #303035;
  border-radius:14px;
  padding:11px;
}
.compact-round{
  color:#31f22f;
  font-size:13px;
  font-weight:1000;
}
.compact-player{
  color:#ffffff;
  font-size:14px;
  font-weight:950;
}
.compact-meta{
  color:#8e8f95;
  font-size:10px;
  margin-top:3px;
}
.compact-adp{
  color:#67a0ff;
  font-size:12px;
  font-weight:1000;
}
@media(max-width:390px){
  .hero-card{padding:16px;}
  .hero-title{font-size:21px;}
  .hero-score{font-size:31px;}
  .hero-grid{gap:6px;}
  .hero-mini{padding:8px;}
  .hero-mini-value{font-size:13px;}
}

</style>

''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_history() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(
            "SELECT * FROM draft_roi_scores ORDER BY league_name,season,overall_pick",
            con,
        )


@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    rankings = pd.read_csv(RANKINGS_PATH)
    rankings["adp"] = pd.to_numeric(rankings["adp"],errors="coerce")
    rankings["position_rank"] = pd.to_numeric(rankings["position_rank"],errors="coerce")
    return rankings.dropna(subset=["player_name","position","adp"])


@st.cache_data(show_spinner=False)
def load_birth_dates() -> pd.DataFrame:
    births = pd.read_csv(BIRTH_DATES_PATH)
    births["birth_date"] = pd.to_datetime(births["birth_date"], errors="coerce")
    return births.dropna(subset=["name_key", "birth_date"]).drop_duplicates("name_key")


def normalize_player_name(value: str) -> str:
    value = str(value or "").lower().strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


roi = load_history()
rankings = load_rankings()
birth_dates = load_birth_dates()
latest_season = int(roi["season"].max())

current_franchises = (
    roi[roi["season"].eq(latest_season)]
    [["league_name","team_id","team_name","manager_name","owner_id"]]
    .drop_duplicates(["league_name","team_id"])
    .sort_values(["league_name","team_id"])
)

player_seasons = (
    roi[
        ["season","player_id","position","position_finish_total",
         "fantasy_points_ppr","ppg","games_played"]
    ]
    .drop_duplicates(["season","player_id","position"])
)

benchmarks = (
    player_seasons.groupby(["position","position_finish_total"],as_index=False)
    .agg(expected_points=("fantasy_points_ppr","mean"),expected_ppg=("ppg","mean"))
    .rename(columns={"position_finish_total":"position_draft_rank"})
)

base = roi.merge(
    benchmarks,
    on=["position","position_draft_rank"],
    how="left",
)


def finish_buffer(rank: int) -> int:
    if rank <= 5: return 2
    if rank <= 12: return 4
    if rank <= 24: return 6
    return 9


def round_weight(round_number: int) -> float:
    return {
        1:1.00,2:.92,3:.84,4:.74,5:.64,6:.55,7:.46,8:.38,
        9:.29,10:.22,11:.17,12:.13,13:.10,14:.08,15:.06,16:.05,
    }.get(int(round_number),.05)


def grade_pick(row: pd.Series) -> pd.Series:
    expected = int(row["position_draft_rank"])
    actual = int(row["position_finish_total"])
    buffer = finish_buffer(expected)
    gap = actual-expected

    point_ratio = (
        float(row["fantasy_points_ppr"])/float(row["expected_points"])
        if pd.notna(row["expected_points"]) and row["expected_points"] > 0
        else np.nan
    )
    ppg_ratio = (
        float(row["ppg"])/float(row["expected_ppg"])
        if pd.notna(row["expected_ppg"]) and row["expected_ppg"] > 0
        else np.nan
    )

    finish_pass = gap <= buffer
    production_pass = (
        (pd.notna(point_ratio) and point_ratio >= .85)
        or (pd.notna(ppg_ratio) and ppg_ratio >= .90)
    )
    injury = (
        not finish_pass and pd.notna(ppg_ratio) and ppg_ratio >= .95
        and int(row["games_played"]) <= 13
    )
    steal = (
        actual <= max(1,expected-buffer)
        and (
            (pd.notna(point_ratio) and point_ratio >= 1.05)
            or (pd.notna(ppg_ratio) and ppg_ratio >= 1.05)
        )
    )

    result = (
        "Steal" if steal
        else "Hit" if finish_pass and production_pass
        else "Injury-Protected" if injury
        else "Bust"
    )

    finish_score = max(0,min(100,100-max(0,gap-buffer)*6.5))
    point_score = max(0,min(110,point_ratio*100)) if pd.notna(point_ratio) else 45
    ppg_score = max(0,min(110,ppg_ratio*100)) if pd.notna(ppg_ratio) else 45
    score = .55*finish_score + .30*point_score + .15*ppg_score

    if result == "Injury-Protected":
        score = min(max(score,58),69)

    return pd.Series({
        "Result":result,
        "Pick Score":max(0,min(100,score)),
        "Round Weight":round_weight(row["round"]),
    })


graded = base.join(base.apply(grade_pick,axis=1))


def letter_grade(score: float) -> str:
    if pd.isna(score): return "—"
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "B-"
    if score >= 65: return "C+"
    if score >= 60: return "C"
    if score >= 55: return "C-"
    if score >= 50: return "D"
    return "F"


def weighted_score(rows: pd.DataFrame) -> float:
    if rows.empty:
        return np.nan
    return float(np.average(rows["Pick Score"],weights=rows["Round Weight"]))


def current_managers(scope: str) -> list[str]:
    if scope == "Combined":
        return sorted(current_franchises["manager_name"].unique().tolist())
    return sorted(
        current_franchises[current_franchises["league_name"].eq(scope)]
        ["manager_name"].unique().tolist()
    )


def franchise_rows(manager: str,scope: str) -> pd.DataFrame:
    current = current_franchises[current_franchises["manager_name"].eq(manager)]
    if scope != "Combined":
        current = current[current["league_name"].eq(scope)]
    keys = set(zip(current["league_name"],current["team_id"]))
    if not keys:
        return graded.iloc[0:0].copy()
    mask = graded.apply(
        lambda row:(row["league_name"],row["team_id"]) in keys,
        axis=1,
    )
    return graded[mask].copy()


def franchise_name(manager: str,scope: str) -> str:
    current = current_franchises[current_franchises["manager_name"].eq(manager)]
    if scope != "Combined":
        current = current[current["league_name"].eq(scope)]
    names = current["team_name"].dropna().unique().tolist()
    return " / ".join(names) if names else manager


def profile(rows: pd.DataFrame) -> dict[str,Any]:
    """
    Build a sample-aware historical coaching profile.

    Draft Coach is descriptive: it explains the manager's verified historical
    results. It does not turn a historically strong position into a command to
    reach for that position in 2026.
    """
    if rows.empty:
        return {
            "best_round":None,
            "worst_round":None,
            "best_round_score":np.nan,
            "worst_round_score":np.nan,
            "best_round_picks":0,
            "worst_round_picks":0,
            "best_position":"—",
            "best_position_score":np.nan,
            "best_position_picks":0,
            "early_identity":"—",
            "early_identity_share":np.nan,
            "round_gap":np.nan,
            "round_summary":pd.DataFrame(),
            "position_summary":pd.DataFrame(),
        }

    premium = rows[rows["round"].between(1,8)].copy()
    seasons = max(1,int(rows["season"].nunique()))
    min_round_samples = max(4,min(8,math.ceil(seasons*.50)))

    round_summary = (
        premium.groupby("round",as_index=False)
        .agg(
            Picks=("player_name","count"),
            Average_Score=("Pick Score","mean"),
            Success_Rate=(
                "Result",
                lambda values: values.isin(
                    ["Steal","Hit","Injury-Protected"]
                ).mean()*100,
            ),
        )
        .sort_values("round")
    )

    eligible_rounds = round_summary[
        round_summary["Picks"].ge(min_round_samples)
    ].copy()
    if eligible_rounds.empty:
        eligible_rounds = round_summary.copy()

    best_row = (
        eligible_rounds.sort_values(
            ["Average_Score","Picks","round"],
            ascending=[False,False,True],
        ).iloc[0]
        if not eligible_rounds.empty else None
    )
    worst_row = (
        eligible_rounds.sort_values(
            ["Average_Score","Picks","round"],
            ascending=[True,False,True],
        ).iloc[0]
        if not eligible_rounds.empty else None
    )

    # Premium-round position history is a tiebreaker signal only.
    min_position_samples = max(4,min(8,math.ceil(len(premium)*.08)))
    position_summary = (
        premium.groupby("position",as_index=False)
        .agg(
            Picks=("player_name","count"),
            Average_Score=("Pick Score","mean"),
            Success_Rate=(
                "Result",
                lambda values: values.isin(
                    ["Steal","Hit","Injury-Protected"]
                ).mean()*100,
            ),
        )
    )
    eligible_positions = position_summary[
        position_summary["Picks"].ge(min_position_samples)
    ].copy()
    if eligible_positions.empty:
        eligible_positions = position_summary.copy()

    best_position_row = (
        eligible_positions.sort_values(
            ["Average_Score","Picks","position"],
            ascending=[False,False,True],
        ).iloc[0]
        if not eligible_positions.empty else None
    )

    early = premium[premium["round"].le(3)]
    early_counts = early["position"].value_counts()
    early_identity = early_counts.index[0] if not early_counts.empty else "—"
    early_identity_share = (
        float(early_counts.iloc[0]/early_counts.sum()*100)
        if not early_counts.empty else np.nan
    )

    best_round_score = (
        float(best_row["Average_Score"]) if best_row is not None else np.nan
    )
    worst_round_score = (
        float(worst_row["Average_Score"]) if worst_row is not None else np.nan
    )

    return {
        "best_round":int(best_row["round"]) if best_row is not None else None,
        "worst_round":int(worst_row["round"]) if worst_row is not None else None,
        "best_round_score":best_round_score,
        "worst_round_score":worst_round_score,
        "best_round_picks":int(best_row["Picks"]) if best_row is not None else 0,
        "worst_round_picks":int(worst_row["Picks"]) if worst_row is not None else 0,
        "best_position":(
            str(best_position_row["position"])
            if best_position_row is not None else "—"
        ),
        "best_position_score":(
            float(best_position_row["Average_Score"])
            if best_position_row is not None else np.nan
        ),
        "best_position_picks":(
            int(best_position_row["Picks"])
            if best_position_row is not None else 0
        ),
        "early_identity":early_identity,
        "early_identity_share":early_identity_share,
        "round_gap":(
            best_round_score-worst_round_score
            if pd.notna(best_round_score) and pd.notna(worst_round_score)
            else np.nan
        ),
        "round_summary":round_summary,
        "position_summary":position_summary,
    }


def rules_for(rows: pd.DataFrame) -> tuple[list[str],list[str],list[str]]:
    p = profile(rows)

    if p["best_round"] is None or p["worst_round"] is None:
        return (
            ["Not enough verified premium-round history to create coaching rules."],
            ["Use verified ADP tiers and best-player-available decisions."],
            ["Do not force a position without supporting data."],
        )

    position_rule = (
        f"{p['best_position']} has your strongest verified premium-round score "
        f"({p['best_position_score']:.1f}/100 across "
        f"{p['best_position_picks']} picks). Use that only as a tiebreaker "
        "between players in the same tier—not as permission to reach."
    )

    rules = [
        (
            f"In Round {p['worst_round']}, slow the decision down and follow "
            "the highest remaining ADP tier. That round has averaged "
            f"{p['worst_round_score']:.1f}/100 across "
            f"{p['worst_round_picks']} verified picks."
        ),
        (
            f"Round {p['best_round']} has been your cleanest premium-round "
            f"decision point at {p['best_round_score']:.1f}/100 across "
            f"{p['best_round_picks']} picks. Preserve that patient, value-first "
            "approach."
        ),
        position_rule,
    ]

    do_more = [
        (
            f"Use a tier-based shortlist before Round {p['worst_round']} so "
            "you are choosing among comparable values instead of forcing need."
        ),
        (
            f"Keep using best player available in the first three rounds; "
            f"{p['early_identity']} has been {p['early_identity_share']:.0f}% "
            "of your early-round selections, but position should never override tier."
        ),
    ]

    do_less = [
        (
            f"Do not interpret historical {p['best_position']} success as a "
            "2026 mandate to draft that position early."
        ),
        (
            f"Do not repeat the decision pattern behind the "
            f"{p['round_gap']:.1f}-point gap between your best and weakest "
            "premium rounds."
        ),
    ]

    # Preserve order while removing accidental duplicate wording.
    def unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    return unique(rules),unique(do_more),unique(do_less)


def snake_schedule(slot: int,teams: int=10,rounds: int=16) -> list[dict[str,int]]:
    output = []
    for rnd in range(1,rounds+1):
        overall = (rnd-1)*teams+slot if rnd%2==1 else rnd*teams-slot+1
        output.append({"Round":rnd,"Overall":overall})
    return output


def player_fit(
    rows: pd.DataFrame,
    overall_pick: int,
    round_number: int,
) -> pd.DataFrame:
    """ADP-driven Best Player Available engine. Manager history is not used."""
    result = rankings.copy()
    result["adp"] = pd.to_numeric(result["adp"], errors="coerce")
    result["position_rank"] = pd.to_numeric(result["position_rank"], errors="coerce")
    result = result.dropna(subset=["player_name", "position", "adp"]).copy()

    slide_window = 5 if round_number <= 3 else 7
    earliest_plausible_adp = max(1, overall_pick - slide_window)
    latest_relevant_adp = overall_pick + 24
    result = result[result["adp"].between(
        earliest_plausible_adp, latest_relevant_adp
    )].copy()

    if result.empty:
        return result

    result["ADP Gap"] = result["adp"] - overall_pick
    result["Availability"] = np.select(
        [
            result["adp"] >= overall_pick,
            result["adp"] >= overall_pick - 2,
            result["adp"] >= earliest_plausible_adp,
        ],
        ["Likely Available", "Possible Slide", "Longer Shot"],
        default="Unlikely",
    )

    result["ADP Proximity"] = (
        100 - (result["adp"] - overall_pick).abs().clip(0, 24) * (100 / 24)
    ).clip(0, 100)

    if round_number == 1:
        result["Position Value"] = np.where(
            result["position"].isin(["RB", "WR"]), 10, -18
        )
    elif round_number == 2:
        result["Position Value"] = np.select(
            [
                result["position"].isin(["RB", "WR"]),
                result["position"].eq("TE"),
                result["position"].eq("QB"),
            ],
            [8, -5, -14],
            default=0,
        )
    elif round_number == 3:
        result["Position Value"] = np.select(
            [
                result["position"].isin(["RB", "WR"]),
                result["position"].eq("TE"),
                result["position"].eq("QB"),
            ],
            [6, 0, -9],
            default=0,
        )
    elif round_number == 4:
        result["Position Value"] = np.select(
            [
                result["position"].isin(["RB", "WR"]),
                result["position"].eq("TE"),
                result["position"].eq("QB"),
            ],
            [4, 1, -5],
            default=0,
        )
    elif round_number <= 6:
        result["Position Value"] = np.select(
            [
                result["position"].isin(["RB", "WR"]),
                result["position"].eq("TE"),
                result["position"].eq("QB"),
            ],
            [2, 2, 0],
            default=0,
        )
    else:
        result["Position Value"] = np.select(
            [
                result["position"].isin(["RB", "WR"]),
                result["position"].eq("TE"),
                result["position"].eq("QB"),
            ],
            [1, 2, 3],
            default=0,
        )

    result["Availability Score"] = np.select(
        [
            result["Availability"].eq("Likely Available"),
            result["Availability"].eq("Possible Slide"),
            result["Availability"].eq("Longer Shot"),
        ],
        [8, 2, -6],
        default=-12,
    )

    result["Recommendation Score"] = (
        0.82 * result["ADP Proximity"]
        + result["Position Value"]
        + result["Availability Score"]
    )

    result["Fit"] = np.select(
        [
            result["Recommendation Score"] >= 82,
            result["Recommendation Score"] >= 70,
            result["Recommendation Score"] >= 58,
        ],
        ["Best Available", "Strong Option", "Acceptable"],
        default="Reach",
    )

    def explain(player: pd.Series) -> str:
        parts = [
            f"ESPN ADP {float(player['adp']):.1f}",
            str(player["Availability"]).lower(),
        ]
        if player["position"] in {"RB", "WR"} and round_number <= 4:
            parts.append("premium early-round position")
        elif player["position"] == "QB" and round_number <= 3:
            parts.append("QB cost is discounted this early")
        elif player["position"] == "QB" and round_number >= 7:
            parts.append("reasonable QB value range")
        return " · ".join(parts)

    result["Why"] = result.apply(explain, axis=1)
    availability_order = {
        "Likely Available": 0,
        "Possible Slide": 1,
        "Longer Shot": 2,
        "Unlikely": 3,
    }
    result["Availability Order"] = result["Availability"].map(availability_order)

    return result.sort_values(
        ["Recommendation Score", "Availability Order", "adp"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def selected_franchise_keys(manager: str, scope: str) -> set[tuple[str,int]]:
    current = current_franchises[current_franchises["manager_name"].eq(manager)]
    if scope != "Combined":
        current = current[current["league_name"].eq(scope)]
    return set(zip(current["league_name"], current["team_id"]))


def historical_draft_lookup(manager: str, scope: str, season_choice: str) -> pd.DataFrame:
    keys = selected_franchise_keys(manager, scope)
    if not keys:
        return graded.iloc[0:0].copy()

    result = graded[
        graded.apply(
            lambda row: (row["league_name"], row["team_id"]) in keys,
            axis=1,
        )
    ].copy()

    if season_choice != "All Seasons":
        result = result[result["season"].eq(int(season_choice))]

    return result.sort_values(["season", "round", "overall_pick"], ascending=[False, True, True])


def parse_quick_report(prompt: str) -> dict[str, Any]:
    query = prompt.lower().strip()

    position = None
    for pos in ["qb", "rb", "wr", "te"]:
        if re.search(rf"\b{pos}\b", query):
            position = pos.upper()
            break

    top_match = re.search(r"top\s*(\d+)", query)
    top_n = int(top_match.group(1)) if top_match else None

    explicit_year_match = re.search(r"\b(20\d{2})\b", query)
    explicit_year = int(explicit_year_match.group(1)) if explicit_year_match else None

    years_match = re.search(r"(?:last|past)\s*(\d+)\s*years?", query)
    last_years = int(years_match.group(1)) if years_match else None

    # The same NFL result can appear once per league draft. Keep one verified
    # player-season-position record before calculating or displaying reports.
    season_pool = (
        graded.sort_values(
            ["season", "position", "position_finish_total", "fantasy_points_ppr"],
            ascending=[True, True, True, False],
        )
        .drop_duplicates(["season", "player_name", "position"])
        .copy()
    )

    season_pool["name_key"] = season_pool["player_name"].map(normalize_player_name)
    season_pool = season_pool.merge(
        birth_dates[["name_key", "birth_date"]],
        on="name_key",
        how="left",
    )
    season_pool["season_reference_date"] = pd.to_datetime(
        season_pool["season"].astype(int).astype(str) + "-09-01",
        errors="coerce",
    )
    season_pool["age"] = (
        (season_pool["season_reference_date"] - season_pool["birth_date"]).dt.days
        / 365.2425
    )

    if position:
        season_pool = season_pool[season_pool["position"].eq(position)]

    if explicit_year:
        season_pool = season_pool[season_pool["season"].eq(explicit_year)]
    elif last_years and not season_pool.empty:
        max_season = int(season_pool["season"].max())
        min_season = max_season - last_years + 1
        season_pool = season_pool[
            season_pool["season"].between(min_season, max_season)
        ]

    if top_n:
        season_pool = (
            season_pool.sort_values(
                ["season", "position_finish_total", "fantasy_points_ppr"],
                ascending=[False, True, False],
            )
            .groupby("season", group_keys=False)
            .head(top_n)
        )

    if season_pool.empty:
        return {
            "title": "No matching records",
            "answer": "0 records",
            "note": "No verified player-seasons matched that request.",
            "table": pd.DataFrame(),
        }

    base_columns = [
        "season", "player_name", "position", "position_finish_total",
        "fantasy_points_ppr", "ppg", "games_played",
    ]
    age_columns = base_columns + ["birth_date", "age"]

    if any(term in query for term in ["age", "dob", "birth date", "birthday"]):
        age_pool = season_pool.dropna(subset=["birth_date", "age"]).copy()
        if age_pool.empty:
            return {
                "title": "Age report unavailable for these matches",
                "answer": "0 verified DOB matches",
                "note": "The request matched players, but none had a verified birth date in the packaged roster data.",
                "table": pd.DataFrame(),
            }

        average_age = age_pool["age"].mean()
        age_pool["age"] = age_pool["age"].round(1)
        return {
            "title": "Average player age",
            "answer": f"{average_age:.1f} years",
            "note": (
                f"{len(age_pool)} unique player-seasons with verified DOB. "
                "Age is calculated as of September 1 of each season."
            ),
            "table": age_pool[age_columns].sort_values(
                ["season", "position_finish_total"],
                ascending=[False, True],
            ),
        }

    if "average" in query and ("ppg" in query or "points per game" in query):
        value = season_pool["ppg"].mean()
        return {
            "title": "Average fantasy points per game",
            "answer": f"{value:.2f} PPG",
            "note": f"{len(season_pool)} unique player-seasons matched.",
            "table": season_pool[base_columns].sort_values(
                ["season", "position_finish_total"],
                ascending=[False, True],
            ),
        }

    if "average" in query and ("points" in query or "scoring" in query):
        value = season_pool["fantasy_points_ppr"].mean()
        return {
            "title": "Average full-PPR points",
            "answer": f"{value:.1f} points",
            "note": f"{len(season_pool)} unique player-seasons matched.",
            "table": season_pool[base_columns].sort_values(
                ["season", "position_finish_total"],
                ascending=[False, True],
            ),
        }

    if "average" in query and "games" in query:
        value = season_pool["games_played"].mean()
        return {
            "title": "Average games played",
            "answer": f"{value:.1f} games",
            "note": f"{len(season_pool)} unique player-seasons matched.",
            "table": season_pool[base_columns].sort_values(
                ["season", "position_finish_total"],
                ascending=[False, True],
            ),
        }

    if "best" in query and "round" in query:
        summary = (
            graded.groupby("round", as_index=False)
            .agg(Picks=("player_name", "count"), Average_Score=("Pick Score", "mean"))
            .sort_values("Average_Score", ascending=False)
        )
        best = summary.iloc[0]
        return {
            "title": "Best historical draft round",
            "answer": f"Round {int(best['round'])}",
            "note": (
                f"Average pick score {best['Average_Score']:.1f} "
                f"across {int(best['Picks'])} picks."
            ),
            "table": summary,
        }

    if "bust" in query:
        busts = graded[graded["Result"].eq("Bust")].copy()
        rate = len(busts) / len(graded) * 100 if len(graded) else 0
        return {
            "title": "Bust rate",
            "answer": f"{rate:.1f}%",
            "note": f"{len(busts)} busts among {len(graded)} historical draft picks.",
            "table": busts[
                [
                    "season", "manager_name", "round", "player_name", "position",
                    "position_draft_rank", "position_finish_total",
                ]
            ].sort_values(["season", "round"], ascending=[False, True]),
        }

    if "steal" in query or "best picks" in query:
        steals = graded.sort_values("Pick Score", ascending=False).head(20)
        return {
            "title": "Best historical picks",
            "answer": f"{len(steals)} picks shown",
            "note": "Ranked by the app's premium-round-weighted pick score.",
            "table": steals[
                [
                    "season", "manager_name", "round", "player_name", "position",
                    "position_draft_rank", "position_finish_total", "Result",
                ]
            ],
        }

    if top_n or "top" in query or "finish" in query:
        ordered = season_pool[base_columns].sort_values(
            ["season", "position_finish_total"],
            ascending=[False, True],
        )
        scope_bits = []
        if position:
            scope_bits.append(position)
        if top_n:
            scope_bits.append(f"Top {top_n}")
        if explicit_year:
            scope_bits.append(str(explicit_year))
        title = " · ".join(scope_bits) if scope_bits else "Matched top-finish report"
        return {
            "title": title,
            "answer": f"{len(ordered)} player-seasons",
            "note": "Unique verified player-season results only.",
            "table": ordered,
        }

    return {
        "title": "Quick report",
        "answer": f"{len(season_pool)} matching records",
        "note": (
            "Supported requests include explicit seasons, top positional finishes, "
            "age, DOB, average PPG, average points, games played, busts, steals and best rounds."
        ),
        "table": season_pool[base_columns].sort_values(
            ["season", "position_finish_total"],
            ascending=[False, True],
        ).head(50),
    }


# ESPN-style team selector at the top.
top_league_col, top_manager_col = st.columns([0.36,0.64])

with top_league_col:
    scope = st.selectbox(
        "League",
        ["Shiva","Shiva 2.0","Combined"],
        key="top_league",
        label_visibility="collapsed",
    )

managers = current_managers(scope)

with top_manager_col:
    manager = st.selectbox(
        "Current Manager",
        managers,
        key="top_manager",
        label_visibility="collapsed",
    )

rows = franchise_rows(manager,scope)
team_name = franchise_name(manager,scope)

# Functional ESPN-style Shiva Tools navigation.
TOOLS = [
    ("Draft Intelligence","📊\nIntelligence","intel"),
    ("Draft Coach","📋\nDraft Coach","coach"),
    ("Player Fit","🎯\nPlayer Fit","fit"),
    ("Draft Slot","🗺️\nDraft Plan","plan"),
    ("Live Draft","🧩\nLive Draft","live"),
    ("Grade My Draft","📝\nGrade Draft","grade"),
    ("League History","🏛️\nHistory","history"),
]

if "section_nav" not in st.session_state:
    st.session_state.section_nav = "Draft Intelligence"

st.markdown(
    f"""
<div class="shiva-nav-shell">
  <div class="shiva-nav-title">{team_name}</div>
</div>
""",
    unsafe_allow_html=True,
)

nav_row1 = st.columns(4)
nav_row2 = st.columns(4)
nav_columns = [
    nav_row1[0],nav_row1[1],nav_row1[2],nav_row1[3],
    nav_row2[0],nav_row2[1],nav_row2[2],
]

for (page_name,label,key),column in zip(TOOLS,nav_columns):
    with column:
        if st.button(
            label,
            key=f"tool_{key}",
            use_container_width=True,
            type="primary" if st.session_state.section_nav == page_name else "secondary",
        ):
            st.session_state.section_nav = page_name
            st.rerun()

page = st.session_state.section_nav



def build_draft_plan(rows: pd.DataFrame, slot: int, teams: int=10, rounds: int=16) -> pd.DataFrame:
    """Create an ADP-grounded, round-by-round draft plan without inventing availability."""
    schedule = snake_schedule(slot, teams, rounds)
    pool = rankings.copy().sort_values(["adp","position_rank"], na_position="last")
    profile_data = profile(rows)

    selected_names:set[str] = set()
    roster_counts = {"QB":0,"RB":0,"WR":0,"TE":0}
    output = []

    for pick in schedule:
        rnd = int(pick["Round"])
        overall = int(pick["Overall"])

        available = pool[~pool["player_name"].isin(selected_names)].copy()

        # A player is considered plausibly available when ADP is not materially earlier
        # than this selection. This is fully grounded in the built-in verified ESPN ADP.
        plausible = available[available["adp"] >= max(1, overall-7)].copy()
        if plausible.empty:
            plausible = available.copy()

        plausible["availability_gap"] = (plausible["adp"]-overall).abs()
        plausible["fit_bonus"] = 0.0

        plausible.loc[plausible["position"].eq(profile_data["best_position"]), "fit_bonus"] += 7
        plausible.loc[plausible["position"].eq(profile_data["middle_strength"]), "fit_bonus"] += 4

        # Roster construction guardrails.
        if rnd <= 3:
            plausible.loc[plausible["position"].isin(["RB","WR"]), "fit_bonus"] += 9
            plausible.loc[plausible["position"].isin(["QB","TE"]), "fit_bonus"] -= 4
        elif rnd <= 6:
            plausible.loc[plausible["position"].isin(["RB","WR"]), "fit_bonus"] += 5
            if roster_counts["QB"] == 0:
                plausible.loc[plausible["position"].eq("QB"), "fit_bonus"] += 2
        elif rnd <= 9:
            if roster_counts["QB"] == 0:
                plausible.loc[plausible["position"].eq("QB"), "fit_bonus"] += 6
            if roster_counts["TE"] == 0:
                plausible.loc[plausible["position"].eq("TE"), "fit_bonus"] += 4
        else:
            plausible.loc[plausible["position"].isin(["RB","WR"]), "fit_bonus"] += 3

        plausible["plan_score"] = (
            -1.6*plausible["availability_gap"]
            -0.15*plausible["adp"]
            +plausible["fit_bonus"]
        )

        choice = plausible.sort_values(
            ["plan_score","adp"],
            ascending=[False,True],
        ).iloc[0]

        selected_names.add(str(choice["player_name"]))
        pos = str(choice["position"])
        if pos in roster_counts:
            roster_counts[pos] += 1

        alternatives = plausible[
            plausible["player_name"].ne(choice["player_name"])
        ].sort_values(["plan_score","adp"], ascending=[False,True]).head(2)

        alt_text = ", ".join(alternatives["player_name"].tolist()) or "—"
        reason_bits = [f"ESPN ADP {float(choice['adp']):.1f}"]
        if pos == profile_data["best_position"]:
            reason_bits.append("matches strongest historical position")
        if rnd <= 3 and pos in {"RB","WR"}:
            reason_bits.append("builds early RB/WR foundation")
        if rnd >= 7 and pos in {"QB","TE"}:
            reason_bits.append("fills a starting position at value")

        output.append({
            "Round":rnd,
            "Pick":overall,
            "Recommended Player":choice["player_name"],
            "Pos":pos,
            "ESPN ADP":float(choice["adp"]),
            "Why":" · ".join(reason_bits),
            "Alternatives":alt_text,
        })

    return pd.DataFrame(output)




def set_quick_report_prompt(value: str) -> None:
    st.session_state["quick_report_prompt"] = value
    st.session_state["last_quick_report"] = parse_quick_report(value)


if page == "League History":
    season_summary = (
        rows.groupby("season",as_index=False)
        .agg(
            Avg_Score=("Pick Score","mean"),
            Picks=("player_name","count"),
        )
        .sort_values(["Avg_Score","season"],ascending=[False,False])
    )
    best_history = season_summary.iloc[0] if not season_summary.empty else None
    best_season = int(best_history["season"]) if best_history is not None else "—"
    best_grade = letter_grade(float(best_history["Avg_Score"])) if best_history is not None else "—"

    st.markdown(
        f"""
<div class="hero-card">
  <div class="hero-kicker">🏛️ League History</div>
  <div class="hero-title">Your Best Historical Draft</div>
  <div class="hero-score">{best_season}</div>
  <div class="hero-sub">Highest average premium-weighted pick score for {team_name}.</div>
  <div class="hero-grid">
    <div class="hero-mini"><div class="hero-mini-label">Draft Grade</div><div class="hero-mini-value green">{best_grade}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Seasons</div><div class="hero-mini-value">{rows['season'].nunique()}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Draft Picks</div><div class="hero-mini-value blue">{len(rows)}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Search Historical Drafts",expanded=False):
        available_seasons = sorted(
            rows["season"].dropna().astype(int).unique(),
            reverse=True,
        )
        season_choice = st.selectbox(
            "Season",
            ["All Seasons"]+[str(x) for x in available_seasons],
            key="history_season",
        )
        player_search = st.text_input(
            "Search Player",
            placeholder="Optional: type a player name",
            key="history_player_search",
        )

        history_rows = rows.copy()
        if season_choice != "All Seasons":
            history_rows = history_rows[history_rows["season"].eq(int(season_choice))]
        if player_search.strip():
            history_rows = history_rows[
                history_rows["player_name"].str.contains(
                    player_search.strip(),case=False,na=False
                )
            ]

        display = history_rows[
            [
                "season","league_name","round","overall_pick","player_name","position",
                "position_draft_rank","position_finish_total",
                "fantasy_points_ppr","ppg","games_played","Result",
            ]
        ].rename(
            columns={
                "season":"Season","league_name":"League","round":"Round",
                "overall_pick":"Overall","player_name":"Player","position":"Pos",
                "position_draft_rank":"Drafted Pos Rank",
                "position_finish_total":"Final Pos Rank",
                "fantasy_points_ppr":"PPR Points","ppg":"PPG","games_played":"Games",
            }
        )
        st.dataframe(
            display.style.format({"PPR Points":"{:.1f}","PPG":"{:.2f}"}),
            use_container_width=True,
            hide_index=True,
        )

elif page == "Draft Coach":
    p = profile(rows)
    rules,do_more,do_less = rules_for(rows)

    draft_identity = (
        f"{p['early_identity']}-Heavy"
        if p["early_identity"] != "—" else "Insufficient Data"
    )
    best_round_text = (
        f"Round {p['best_round']}" if p["best_round"] else "—"
    )
    weakest_round_text = (
        f"Round {p['worst_round']}" if p["worst_round"] else "—"
    )

    if p["best_round"] and p["worst_round"]:
        coaching_focus = (
            f"Your clearest 2026 correction point is Round "
            f"{p['worst_round']}. It has averaged "
            f"{p['worst_round_score']:.1f}/100, compared with "
            f"{p['best_round_score']:.1f}/100 in Round "
            f"{p['best_round']}. Use the highest remaining ADP tier and "
            "best player available there—do not force a position."
        )
    else:
        coaching_focus = (
            "There is not enough verified premium-round history to produce "
            "a reliable manager-specific coaching focus."
        )

    st.markdown(
        '<div class="section-label">Your 2026 Draft Coach</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="daily-tip">
  <div class="daily-tip-label">2026 Coaching Focus</div>
  <div class="daily-tip-text">{coaching_focus}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="coach-grid">
  <div class="coach-card">
    <div class="coach-label">Early Draft Identity</div>
    <div class="coach-value green">{draft_identity}</div>
    <div class="card-sub">{p['early_identity_share']:.0f}% of Rounds 1–3</div>
  </div>
  <div class="coach-card">
    <div class="coach-label">Best Premium Round</div>
    <div class="coach-value blue">{best_round_text}</div>
    <div class="card-sub">{p['best_round_score']:.1f}/100 · {p['best_round_picks']} picks</div>
  </div>
  <div class="coach-card">
    <div class="coach-label">Biggest Premium Leak</div>
    <div class="coach-value red">{weakest_round_text}</div>
    <div class="card-sub">{p['worst_round_score']:.1f}/100 · {p['worst_round_picks']} picks</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-label">Three Actionable Coaching Rules</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="rule-list">', unsafe_allow_html=True)
    for i,rule in enumerate(rules,1):
        st.markdown(
            f"""
<div class="rule-card">
  <div class="rule-number">{i}</div>
  <div class="rule-text">{rule}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("✓ Do More",expanded=False):
        st.markdown('<div class="action-grid">',unsafe_allow_html=True)
        for item in do_more:
            st.markdown(
                f"""
<div class="action-card good">
  <div class="action-icon">✓</div>
  <div class="action-text">{item}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown('</div>',unsafe_allow_html=True)

    with st.expander("⚠ Avoid",expanded=False):
        st.markdown('<div class="action-grid">',unsafe_allow_html=True)
        for item in do_less:
            st.markdown(
                f"""
<div class="action-card warn">
  <div class="action-icon">!</div>
  <div class="action-text">{item}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown('</div>',unsafe_allow_html=True)

    with st.expander("View Draft Coach Evidence",expanded=False):
        evidence = p["round_summary"].rename(
            columns={
                "round":"Round",
                "Picks":"Verified Picks",
                "Average_Score":"Average Score",
                "Success_Rate":"Hit / Protected Rate",
            }
        )
        st.dataframe(
            evidence.style.format(
                {
                    "Average Score":"{:.1f}",
                    "Hit / Protected Rate":"{:.1f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

elif page == "Player Fit":
    fit_cols = st.columns(3)
    with fit_cols[0]:
        fit_teams = st.number_input("Teams",8,16,10,1,key="fit_teams")
    with fit_cols[1]:
        draft_position = st.number_input(
            "Draft Position",1,int(fit_teams),min(4,int(fit_teams)),1,
            key="fit_draft_position",
        )
    with fit_cols[2]:
        round_number = st.number_input("Round",1,16,2,1,key="fit_round")

    overall_pick = (
        (int(round_number)-1)*int(fit_teams)+int(draft_position)
        if int(round_number)%2 == 1
        else int(round_number)*int(fit_teams)-int(draft_position)+1
    )
    fits = player_fit(rows,int(overall_pick),int(round_number))
    top_fit = fits.iloc[0] if not fits.empty else None

    if top_fit is not None:
        st.markdown(
            f"""
<div class="hero-card">
  <div class="hero-kicker">🎯 Best Available At Pick {overall_pick}</div>
  <div class="hero-title">{top_fit['player_name']}</div>
  <div class="hero-sub">{top_fit['position']} · ESPN ADP {float(top_fit['adp']):.1f} · {top_fit['Availability']}</div>
  <div class="hero-grid">
    <div class="hero-mini"><div class="hero-mini-label">Player Fit</div><div class="hero-mini-value green">{top_fit['Fit']}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Round</div><div class="hero-mini-value">{int(round_number)}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Overall Pick</div><div class="hero-mini-value blue">{overall_pick}</div></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("View And Filter Available Players",expanded=True):
        availability_filter = st.selectbox(
            "Availability",
            ["Likely Available","Possible Slide","Longer Shot","All Plausible"],
            key="fit_availability_filter",
        )
        fit_filter = st.selectbox(
            "Player Fit",
            ["Best Available","Strong Option","Acceptable","Reach","All Fits"],
            key="fit_quality_filter",
        )
        selected = fits.copy()
        if availability_filter != "All Plausible":
            selected = selected[selected["Availability"].eq(availability_filter)]
        if fit_filter != "All Fits":
            selected = selected[selected["Fit"].eq(fit_filter)]
        selected = selected.head(12)

        if selected.empty:
            st.info("No players matched those filters.")
        else:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            for _,player in selected.iterrows():
                tag_class = {
                    "Best Available":"",
                    "Strong Option":" blue",
                    "Acceptable":" gold",
                    "Reach":" red",
                }[player["Fit"]]
                st.markdown(
                    f"""
<div class="list-row">
  <div><span class="pos-badge pos-{player['position']}">{player['position']}</span></div>
  <div>
    <div class="row-title">{player['player_name']}</div>
    <div class="row-sub">ESPN ADP {float(player['adp']):.1f} · {player['Availability']} · {player['Why']}</div>
  </div>
  <div class="row-tag{tag_class}">{player['Fit']}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            st.markdown('</div>',unsafe_allow_html=True)

elif page == "Draft Slot":
    slot = st.number_input("Draft Position",1,10,1,1,key="draft_plan_slot")
    draft_plan = build_draft_plan(rows,int(slot),10,16)

    first_pick = draft_plan.iloc[0] if not draft_plan.empty else None
    if first_pick is not None:
        st.markdown(
            f"""
<div class="hero-card">
  <div class="hero-kicker">🗺️ Draft Plan · Pick {int(slot)}</div>
  <div class="hero-title">{first_pick['Recommended Player']}</div>
  <div class="hero-sub">Your recommended Round 1 selection based on verified ESPN ADP and historical fit.</div>
  <div class="hero-grid">
    <div class="hero-mini"><div class="hero-mini-label">Position</div><div class="hero-mini-value green">{first_pick['Pos']}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Overall Pick</div><div class="hero-mini-value">{int(first_pick['Pick'])}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">ESPN ADP</div><div class="hero-mini-value blue">{float(first_pick['ESPN ADP']):.1f}</div></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">First Three Rounds</div>',unsafe_allow_html=True)
    st.markdown('<div class="compact-pick-grid">',unsafe_allow_html=True)
    for _,pick in draft_plan.head(3).iterrows():
        st.markdown(
            f"""
<div class="compact-pick">
  <div class="compact-round">R{int(pick['Round'])}</div>
  <div><div class="compact-player">{pick['Recommended Player']} ({pick['Pos']})</div><div class="compact-meta">Pick {int(pick['Pick'])} · {pick['Why']}</div></div>
  <div class="compact-adp">ADP {float(pick['ESPN ADP']):.1f}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>',unsafe_allow_html=True)

    with st.expander("View Full 16-Round Plan",expanded=False):
        for _,pick in draft_plan.iloc[3:].iterrows():
            st.markdown(
                f"""
<div class="coaching-card">
  <div class="coaching-title">Round {int(pick['Round'])} · Pick {int(pick['Pick'])}: {pick['Recommended Player']} ({pick['Pos']})</div>
  <div class="coaching-body">{pick['Why']}</div>
  <div class="row-sub">Other likely options: {pick['Alternatives']}</div>
</div>
""",
                unsafe_allow_html=True,
            )

elif page == "Live Draft":
    live_league = scope if scope in LEAGUE_IDS else st.selectbox("Live League",["Shiva","Shiva 2.0"])
    slot = st.number_input("Your Draft Slot",1,10,9,1,key="live_slot")

    st.caption(f"Verified 2026 ESPN ADP is already loaded. No upload is required.")

    def fetch_live():
        league_id = LEAGUE_IDS[live_league]
        url = (
            f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
            f"seasons/{CURRENT_SEASON}/segments/0/leagues/{league_id}"
            f"?view=mDraftDetail&view=mTeam&view=mStatus"
        )
        cookies = {}
        try:
            if st.secrets.get("ESPN_SWID",""):
                cookies["SWID"] = st.secrets["ESPN_SWID"]
            if st.secrets.get("ESPN_S2",""):
                cookies["espn_s2"] = st.secrets["ESPN_S2"]
        except Exception:
            pass

        try:
            response = requests.get(
                url,
                headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"},
                cookies=cookies,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            picks = ((data.get("draftDetail") or {}).get("picks") or [])
            return pd.DataFrame(picks),"Connected"
        except Exception as exc:
            return pd.DataFrame(),f"Feed unavailable: {exc}"

    @st.fragment(run_every="5s")
    def live_panel():
        picks,status = fetch_live()
        st.caption(status)

        if picks.empty:
            current_pick = 1
            drafted_ids:set[int] = set()
        else:
            completed = pd.to_numeric(picks.get("overallPickNumber"),errors="coerce").dropna()
            current_pick = int(completed.max())+1 if not completed.empty else 1
            drafted_ids = set(
                pd.to_numeric(picks.get("playerId"),errors="coerce").dropna().astype(int).tolist()
            )

        schedule = pd.DataFrame(snake_schedule(int(slot),10,16))
        future = schedule[schedule["Overall"] >= current_pick]
        next_pick = int(future["Overall"].iloc[0]) if not future.empty else None

        st.markdown(
            f"""
<div class="metric-grid">
  <div class="metric-box"><div class="metric-label">Current Pick</div><div class="metric-value">{current_pick}</div></div>
  <div class="metric-box"><div class="metric-label">Your Next Pick</div><div class="metric-value blue">{next_pick if next_pick else "—"}</div></div>
  <div class="metric-box"><div class="metric-label">Picks Until You</div><div class="metric-value green">{next_pick-current_pick if next_pick else "—"}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )

        available = rankings.copy()
        if drafted_ids and "espn_player_id" in available.columns:
            available = available[
                ~pd.to_numeric(available["espn_player_id"],errors="coerce")
                .fillna(-999999).astype(int).isin(drafted_ids)
            ]

        fits = player_fit(rows,next_pick or current_pick,max(1,int(np.ceil((next_pick or current_pick)/10)))).head(8)
        if not fits.empty:
            best_live = fits.iloc[0]
            st.markdown(
                f"""
<div class="hero-card">
  <div class="hero-kicker">🧩 Best Live Pick</div>
  <div class="hero-title">{best_live['player_name']}</div>
  <div class="hero-sub">{best_live['position']} · ESPN ADP {float(best_live['adp']):.1f} · {best_live['Why']}</div>
  <div class="hero-grid">
    <div class="hero-mini"><div class="hero-mini-label">Fit</div><div class="hero-mini-value green">{best_live['Fit']}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Next Pick</div><div class="hero-mini-value">{next_pick if next_pick else "—"}</div></div>
    <div class="hero-mini"><div class="hero-mini-label">Availability</div><div class="hero-mini-value blue">{best_live['Availability']}</div></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown('<div class="section-label">Recommended Picks</div>',unsafe_allow_html=True)
        st.markdown('<div class="card">',unsafe_allow_html=True)
        for _,player in fits.iterrows():
            st.markdown(
                f"""
<div class="list-row">
  <div><span class="pos-badge pos-{player['position']}">{player['position']}</span></div>
  <div>
    <div class="row-title">{player['player_name']}</div>
    <div class="row-sub">ESPN ADP {float(player['adp']):.1f} · {player['Why']}</div>
  </div>
  <div class="row-tag">{player['Fit']}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        st.markdown('</div>',unsafe_allow_html=True)

    live_panel()

elif page == "Draft Intelligence":
    st.markdown(
        '<div class="section-label">Shiva Draft Intelligence Home</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="hero-card">
  <div class="hero-kicker">📊 Ask Shiva</div>
  <div class="hero-title">What Do You Want To Know?</div>
  <div class="hero-sub">Ask a plain-English fantasy question. Shiva answers from verified historical scoring, draft, ADP and DOB data.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    examples = st.columns(2)
    with examples[0]:
        st.button(
            "Top-5 RB average PPG",
            key="example_top5_rb",
            use_container_width=True,
            on_click=set_quick_report_prompt,
            args=("Show average PPG for RBs that finished top 5 over the last 5 years",),
        )
    with examples[1]:
        st.button(
            "Top-5 RB average age",
            key="example_top5_rb_age",
            use_container_width=True,
            on_click=set_quick_report_prompt,
            args=("Show average age for RBs that finished top 5 over the last 5 years",),
        )

    with st.form("quick_report_form", clear_on_submit=False):
        quick_prompt = st.text_input(
            "Report request",
            placeholder="Example: Show average age for top 5 RBs over the last 5 years",
            key="quick_report_prompt",
        )
        run_report = st.form_submit_button(
            "Run Report",
            use_container_width=True,
        )

    if run_report:
        if not quick_prompt.strip():
            st.warning("Type a report request first.")
        else:
            st.session_state["last_quick_report"] = parse_quick_report(quick_prompt)

    report = st.session_state.get("last_quick_report")
    if report:
        st.markdown(
            f"""
<div class="report-box">
  <div class="report-title">{report['title']}</div>
  <div class="report-answer">{report['answer']}</div>
  <div class="report-note">{report['note']}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        if not report["table"].empty:
            with st.expander("View Supporting Data",expanded=False):
                st.dataframe(
                    report["table"],
                    use_container_width=True,
                    hide_index=True,
                )

else:
    st.markdown(
        """
<div class="hero-card">
  <div class="hero-kicker">📝 Grade My Draft</div>
  <div class="hero-title">Upload Your Draft</div>
  <div class="hero-sub">Upload a lineup, roster or full draft screenshot. Confirm the players, then receive a premium-round-weighted grade.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    grade_teams = st.number_input("Teams",8,16,10,1,key="grade_teams")
    grade_slot = st.number_input("Your Draft Slot",1,int(grade_teams),9,1,key="grade_slot")
    image_file = st.file_uploader("Draft Screenshot",type=["png","jpg","jpeg","webp"])

    if image_file is not None:
        image = Image.open(image_file)
        st.image(image,use_container_width=True)
        st.info(
            "Screenshot received. Use the editable table below to enter or confirm the players "
            "from the screenshot before grading."
        )

        blank = pd.DataFrame(
            columns=["Round","Overall Pick","Player","Pos","ADP"]
        )
        draft = st.data_editor(
            blank,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )

        if st.button("Grade This Draft",use_container_width=True):
            if draft.empty:
                st.warning("Add the drafted players to the table first.")
            else:
                draft["Round"] = pd.to_numeric(draft["Round"],errors="coerce")
                draft["Overall Pick"] = pd.to_numeric(draft["Overall Pick"],errors="coerce")
                draft["ADP"] = pd.to_numeric(draft["ADP"],errors="coerce")

                schedule = {x["Round"]:x["Overall"] for x in snake_schedule(int(grade_slot),int(grade_teams),20)}
                draft["Overall Pick"] = draft.apply(
                    lambda row:schedule.get(int(row["Round"]),np.nan)
                    if pd.isna(row["Overall Pick"]) and pd.notna(row["Round"])
                    else row["Overall Pick"],
                    axis=1,
                )
                draft["Value vs ADP"] = draft["Overall Pick"]-draft["ADP"]
                draft["Pick Score"] = (72+1.15*draft["Value vs ADP"].clip(-25,25)).clip(25,98)
                draft["Weight"] = draft["Round"].fillna(10).apply(round_weight)

                valid = draft.dropna(subset=["Pick Score","Weight"])
                score = float(np.average(valid["Pick Score"],weights=valid["Weight"])) if not valid.empty else np.nan

                st.markdown(
                    f"""
<div class="card">
  <div class="card-title">Draft Grade: {letter_grade(score)}</div>
  <div class="card-sub">{score:.1f}/100 · Premium rounds count most</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                st.dataframe(
                    draft[["Round","Overall Pick","Player","Pos","ADP","Value vs ADP"]],
                    use_container_width=True,
                    hide_index=True,
                )
