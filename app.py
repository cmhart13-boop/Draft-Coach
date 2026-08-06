from __future__ import annotations

import sqlite3
import re
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
  margin:0 0 12px;
  padding:10px 6px 8px;
  border:1px solid #303035;
  border-radius:18px;
  background:#1d1d20;
}
.shiva-nav-title{
  color:#fff;
  font-size:14px;
  font-weight:1000;
  margin:0 0 8px 4px;
}
.st-key-tool_history button,
.st-key-tool_coach button,
.st-key-tool_fit button,
.st-key-tool_plan button,
.st-key-tool_live button,
.st-key-tool_grade button,
.st-key-tool_intel button{
  width:100%!important;
  min-width:0!important;
  min-height:78px!important;
  padding:6px 1px 0!important;
  margin:0!important;
  border:0!important;
  border-radius:0!important;
  background:
    radial-gradient(circle 24px at 50% 24px,#45464c 0 23px,transparent 24px)!important;
  box-shadow:none!important;
  color:#a8a8ad!important;
  font-size:9.5px!important;
  line-height:1.08!important;
  font-weight:800!important;
  white-space:pre-line!important;
  text-align:center!important;
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
  line-height:1.08!important;
  margin:0!important;
}
.st-key-tool_history button[kind="primary"],
.st-key-tool_coach button[kind="primary"],
.st-key-tool_fit button[kind="primary"],
.st-key-tool_plan button[kind="primary"],
.st-key-tool_live button[kind="primary"],
.st-key-tool_grade button[kind="primary"],
.st-key-tool_intel button[kind="primary"]{
  background:
    radial-gradient(circle 25px at 50% 24px,#20f45a 0 2px,#4d4d51 3px 23px,transparent 24px)!important;
  color:#fff!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_intel),
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_live){
  display:flex!important;
  flex-wrap:nowrap!important;
  gap:4px!important;
  width:100%!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_intel)>div,
div[data-testid="stHorizontalBlock"]:has(.st-key-tool_live)>div{
  flex:1 1 0!important;
  width:25%!important;
  min-width:0!important;
}

.daily-tip{
  background:linear-gradient(135deg,#17371f,#1b1b1e);
  border:1px solid #2d5e36;
  border-radius:15px;
  padding:14px;
  margin-bottom:12px;
}
.daily-tip-label{
  color:#31f22f;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.1em;
  text-transform:uppercase;
}
.daily-tip-text{
  color:#fff;
  font-size:14px;
  line-height:1.4;
  font-weight:900;
  margin-top:5px;
}
.coach-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:9px;
  margin-bottom:12px;
}
.coach-card{
  background:#1c1c1f;
  border:1px solid #29292d;
  border-radius:14px;
  min-height:84px;
  padding:10px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}
.coach-label{
  color:#77787e;
  font-size:9px;
  font-weight:1000;
  line-height:1.15;
  letter-spacing:.06em;
  text-transform:uppercase;
}
.coach-value{
  color:#fff;
  font-size:15px;
  line-height:1.08;
  font-weight:1000;
}
.coach-value.green{color:#31f22f;}
.coach-value.blue{color:#5b98ff;}
.coach-value.red{color:#ff525d;}
.coaching-card{
  background:#1c1c1f;
  border:1px solid #29292d;
  border-radius:14px;
  padding:13px;
  margin-bottom:9px;
}
.coaching-title{
  color:#fff;
  font-size:13px;
  line-height:1.38;
  font-weight:900;
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


roi = load_history()
rankings = load_rankings()
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
    round_scores = rows.groupby("round")["Pick Score"].mean().sort_values(ascending=False)
    position_scores = rows.groupby("position")["Pick Score"].mean().sort_values(ascending=False)

    early = rows[rows["round"] <= 3]
    middle = rows[rows["round"].between(4,8)]

    best_round = int(round_scores[round_scores.index <= 8].index[0]) if not round_scores.empty else None
    worst_round = int(round_scores[round_scores.index <= 8].index[-1]) if not round_scores.empty else None
    best_position = position_scores.index[0] if not position_scores.empty else "—"
    worst_position = position_scores.index[-1] if not position_scores.empty else "—"

    early_identity = early["position"].value_counts().index[0] if not early.empty else "—"
    middle_strength = (
        middle.groupby("position")["Pick Score"].mean().sort_values(ascending=False).index[0]
        if not middle.empty else "—"
    )

    return {
        "best_round":best_round,
        "worst_round":worst_round,
        "best_position":best_position,
        "worst_position":worst_position,
        "early_identity":early_identity,
        "middle_strength":middle_strength,
    }


def rules_for(rows: pd.DataFrame) -> tuple[list[str],list[str],list[str]]:
    p = profile(rows)
    rules = [
        f"Use {p['best_position']} as your tiebreaker when similarly ranked players are available.",
        f"Protect Round {p['best_round']}; it has been one of your strongest premium-round decision points.",
        f"Slow down in Round {p['worst_round']}; this is where forced picks have historically hurt you.",
        f"Your early-round identity has been {p['early_identity']}-heavy. Continue only when the tier supports it.",
        f"In Rounds 4–8, your strongest historical position has been {p['middle_strength']}.",
    ]
    do_more = [
        f"Lean into {p['best_position']} value when players are in the same tier.",
        "Prioritize proven weekly scoring and clear roles.",
        "Build the first three rounds around players you can confidently start every week.",
    ]
    do_less = [
        f"Do not force {p['worst_position']} simply because the roster slot is empty.",
        f"Do not repeat the decision pattern that made Round {p['worst_round']} your weakest premium round.",
        "Do not let late-round steals hide mistakes made with premium picks.",
    ]
    return rules,do_more,do_less


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
    """
    Rank only players plausibly available at the selected overall pick.

    Availability is grounded in verified ESPN ADP:
    - Likely available: ADP at or after the selected pick
    - Could slide: ADP up to 6 picks earlier than the selected pick
    - Players with ADP more than 6 picks earlier are excluded
    """
    p = profile(rows)
    result = rankings.copy()

    # Exclude players whose ESPN ADP is materially earlier than this pick.
    earliest_plausible_adp = max(1, overall_pick-6)
    result = result[result["adp"] >= earliest_plausible_adp].copy()

    if result.empty:
        return result

    result["ADP Gap"] = result["adp"]-overall_pick
    result["Availability"] = np.select(
        [
            result["adp"] >= overall_pick,
            result["adp"] >= overall_pick-3,
            result["adp"] >= overall_pick-6,
        ],
        [
            "Likely Available",
            "Possible Slide",
            "Longer Shot",
        ],
        default="Unlikely",
    )

    # Closeness to the selected pick matters more than raw overall rank.
    result["Pick Proximity"] = (
        100-(result["adp"]-overall_pick).abs().clip(0,30)*(100/30)
    ).clip(0,100)

    bonuses = []
    reasons = []

    for _,player in result.iterrows():
        bonus = 0.0
        player_reasons = []

        if player["position"] == p["best_position"]:
            bonus += 12
            player_reasons.append("matches your strongest drafted position")

        if player["position"] == p["middle_strength"]:
            bonus += 7
            player_reasons.append("fits your strongest middle-round profile")

        # Early rounds favor RB/WR foundation; later rounds open QB/TE value.
        if round_number <= 3 and player["position"] in {"RB","WR"}:
            bonus += 7
            player_reasons.append("fits an early-round RB/WR foundation")
        elif round_number >= 6 and player["position"] in {"QB","TE"}:
            bonus += 3
            player_reasons.append("reasonable later-round positional value")

        availability = str(player["Availability"])
        if availability == "Likely Available":
            bonus += 10
            player_reasons.append("projected available at this pick")
        elif availability == "Possible Slide":
            bonus += 4
            player_reasons.append("could slide to this pick")
        elif availability == "Longer Shot":
            bonus -= 4
            player_reasons.append("would need to fall past ADP")

        bonuses.append(bonus)
        reasons.append(", ".join(player_reasons) or "priced from verified 2026 ESPN ADP")

    result["Historical Fit"] = bonuses
    result["Why"] = reasons
    result["Recommendation Score"] = (
        .60*result["Pick Proximity"]
        + result["Historical Fit"]
    )

    # Labels are calculated only within the plausible availability pool.
    q80 = result["Recommendation Score"].quantile(.80)
    q50 = result["Recommendation Score"].quantile(.50)
    q25 = result["Recommendation Score"].quantile(.25)

    def fit_label(value: float) -> str:
        if value >= q80:
            return "Strong Fit"
        if value >= q50:
            return "Acceptable"
        if value >= q25:
            return "Risky"
        return "Avoid at ADP"

    result["Fit"] = result["Recommendation Score"].apply(fit_label)

    availability_order = {
        "Likely Available":0,
        "Possible Slide":1,
        "Longer Shot":2,
        "Unlikely":3,
    }
    result["Availability Order"] = result["Availability"].map(availability_order)

    return result.sort_values(
        ["Availability Order","Recommendation Score","adp"],
        ascending=[True,False,True],
    )


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
    for pos in ["qb","rb","wr","te"]:
        if re.search(rf"\b{pos}\b",query):
            position = pos.upper()
            break

    top_match = re.search(r"top\s*(\d+)",query)
    top_n = int(top_match.group(1)) if top_match else None

    explicit_year_match = re.search(r"\b(20\d{2})\b",query)
    explicit_year = int(explicit_year_match.group(1)) if explicit_year_match else None

    years_match = re.search(r"(?:last|past)\s*(\d+)\s*years?",query)
    last_years = int(years_match.group(1)) if years_match else None

    season_pool = (
        graded.sort_values(["season","position","position_finish_total","fantasy_points_ppr"],ascending=[True,True,True,False])
        .drop_duplicates(["season","player_name","position"])
        .copy()
    )

    if position:
        season_pool = season_pool[season_pool["position"].eq(position)]

    if explicit_year:
        season_pool = season_pool[season_pool["season"].eq(explicit_year)]
    elif last_years and not season_pool.empty:
        max_season = int(season_pool["season"].max())
        min_season = max_season-last_years+1
        season_pool = season_pool[season_pool["season"].between(min_season,max_season)]

    if top_n:
        season_pool = (
            season_pool.sort_values(
                ["season","position_finish_total","fantasy_points_ppr"],
                ascending=[False,True,False],
            )
            .groupby("season",group_keys=False)
            .head(top_n)
        )

    if "age" in query:
        return {
            "title":"Age report unavailable",
            "answer":"Age is not in this app database",
            "note":"The current database does not contain verified historical player age, so the app will not estimate it.",
            "table":pd.DataFrame(),
        }

    if season_pool.empty:
        return {
            "title":"No matching records",
            "answer":"0 records",
            "note":"No verified player-seasons matched that position, finish threshold and season.",
            "table":pd.DataFrame(),
        }

    base_columns = [
        "season","player_name","position","position_finish_total",
        "fantasy_points_ppr","ppg","games_played",
    ]

    if "average" in query and ("ppg" in query or "points per game" in query):
        value = season_pool["ppg"].mean()
        return {
            "title":"Average fantasy points per game",
            "answer":f"{value:.2f} PPG",
            "note":f"{len(season_pool)} unique player-seasons matched.",
            "table":season_pool[base_columns].sort_values(
                ["season","position_finish_total"],
                ascending=[False,True],
            ),
        }

    if "average" in query and ("points" in query or "scoring" in query):
        value = season_pool["fantasy_points_ppr"].mean()
        return {
            "title":"Average full-PPR points",
            "answer":f"{value:.1f} points",
            "note":f"{len(season_pool)} unique player-seasons matched.",
            "table":season_pool[base_columns].sort_values(
                ["season","position_finish_total"],
                ascending=[False,True],
            ),
        }

    if "average" in query and "games" in query:
        value = season_pool["games_played"].mean()
        return {
            "title":"Average games played",
            "answer":f"{value:.1f} games",
            "note":f"{len(season_pool)} unique player-seasons matched.",
            "table":season_pool[base_columns].sort_values(
                ["season","position_finish_total"],
                ascending=[False,True],
            ),
        }

    if "best" in query and "round" in query:
        summary = (
            graded.groupby("round",as_index=False)
            .agg(Picks=("player_name","count"),Average_Score=("Pick Score","mean"))
            .sort_values("Average_Score",ascending=False)
        )
        best = summary.iloc[0]
        return {
            "title":"Best historical draft round",
            "answer":f"Round {int(best['round'])}",
            "note":f"Average pick score {best['Average_Score']:.1f} across {int(best['Picks'])} picks.",
            "table":summary,
        }

    if "bust" in query:
        busts = graded[graded["Result"].eq("Bust")].copy()
        rate = len(busts)/len(graded)*100 if len(graded) else 0
        return {
            "title":"Bust rate",
            "answer":f"{rate:.1f}%",
            "note":f"{len(busts)} busts among {len(graded)} historical draft picks.",
            "table":busts[
                ["season","manager_name","round","player_name","position",
                 "position_draft_rank","position_finish_total"]
            ].sort_values(["season","round"],ascending=[False,True]),
        }

    if "steal" in query or "best picks" in query:
        steals = graded.sort_values("Pick Score",ascending=False).head(20)
        return {
            "title":"Best historical picks",
            "answer":f"{len(steals)} picks shown",
            "note":"Ranked by the app's premium-round-weighted pick score.",
            "table":steals[
                ["season","manager_name","round","player_name","position",
                 "position_draft_rank","position_finish_total","Result"]
            ],
        }

    if top_n or "top" in query or "finish" in query:
        ordered = season_pool[base_columns].sort_values(
            ["season","position_finish_total"],
            ascending=[False,True],
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
            "title":title,
            "answer":f"{len(ordered)} player-seasons",
            "note":"Unique verified player-season results only.",
            "table":ordered,
        }

    return {
        "title":"Quick report",
        "answer":f"{len(season_pool)} matching records",
        "note":"Supported requests include explicit seasons, top positional finishes, average PPG, average points, games played, busts, steals and best rounds.",
        "table":season_pool[base_columns].sort_values(
            ["season","position_finish_total"],
            ascending=[False,True],
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


team_name = franchise_name(manager,scope)


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


if page == "League History":
    st.markdown('<div class="section-label">Search Historical Drafts</div>', unsafe_allow_html=True)

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
                player_search.strip(),
                case=False,
                na=False,
            )
        ]

    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{team_name}</div>
  <div class="card-sub">{manager} · {scope} · {season_choice} · {len(history_rows)} picks</div>
</div>
""",
        unsafe_allow_html=True,
    )

    display = history_rows[
        [
            "season","league_name","round","overall_pick","player_name","position",
            "position_draft_rank","position_finish_total",
            "fantasy_points_ppr","ppg","games_played","Result",
        ]
    ].rename(
        columns={
            "season":"Season",
            "league_name":"League",
            "round":"Round",
            "overall_pick":"Overall",
            "player_name":"Player",
            "position":"Pos",
            "position_draft_rank":"Drafted Pos Rank",
            "position_finish_total":"Final Pos Rank",
            "fantasy_points_ppr":"PPR Points",
            "ppg":"PPG",
            "games_played":"Games",
        }
    )

    st.dataframe(
        display.style.format({
            "PPR Points":"{:.1f}",
            "PPG":"{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

elif page == "Draft Coach":
    score = weighted_score(rows)
    p = profile(rows)
    rules,do_more,do_less = rules_for(rows)

    draft_identity = f"{p['early_identity']}-Heavy"
    best_round_text = f"Round {p['best_round']}" if p["best_round"] else "—"
    focus_text = f"Target {p['best_position']} value"
    daily_tip = (
        f"Your strongest historical profile is {p['best_position']} value, "
        f"while Round {p['worst_round']} has been your biggest premium-round leak."
    )

    st.markdown('<div class="section-label">Your 2026 Draft Plan</div>',unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="daily-tip">
  <div class="daily-tip-label">Today's Draft Tip</div>
  <div class="daily-tip-text">{daily_tip}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="coach-grid">
  <div class="coach-card">
    <div class="coach-label">Your Draft Identity</div>
    <div class="coach-value green">{draft_identity}</div>
  </div>
  <div class="coach-card">
    <div class="coach-label">Best Round</div>
    <div class="coach-value blue">{best_round_text}</div>
  </div>
  <div class="coach-card">
    <div class="coach-label">2026 Focus</div>
    <div class="coach-value red">{focus_text}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Your Five Draft Rules</div>',unsafe_allow_html=True)
    for i,rule in enumerate(rules,1):
        st.markdown(
            f"""
<div class="coaching-card">
  <div class="coaching-title">{i}. {rule}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Do More</div>',unsafe_allow_html=True)
    for item in do_more:
        st.markdown(
            f"""
<div class="coaching-card">
  <div class="coaching-title">✓ {item}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Do Less</div>',unsafe_allow_html=True)
    for item in do_less:
        st.markdown(
            f"""
<div class="coaching-card">
  <div class="coaching-title">⚠ {item}</div>
</div>
""",
            unsafe_allow_html=True,
        )

elif page == "Player Fit":
    st.caption(f"Verified 2026 FantasyPros ESPN ADP is built in: {len(rankings)} players.")

    fit_cols = st.columns(3)
    with fit_cols[0]:
        fit_teams = st.number_input(
            "Teams",
            min_value=8,
            max_value=16,
            value=10,
            step=1,
            key="fit_teams",
        )
    with fit_cols[1]:
        draft_position = st.number_input(
            "Draft Position",
            min_value=1,
            max_value=int(fit_teams),
            value=min(4,int(fit_teams)),
            step=1,
            key="fit_draft_position",
        )
    with fit_cols[2]:
        round_number = st.number_input(
            "Round",
            min_value=1,
            max_value=16,
            value=2,
            step=1,
            key="fit_round",
        )

    overall_pick = (
        (int(round_number)-1)*int(fit_teams)+int(draft_position)
        if int(round_number)%2 == 1
        else int(round_number)*int(fit_teams)-int(draft_position)+1
    )

    st.markdown(
        f"""
<div class="card">
  <div class="card-title">Round {int(round_number)} · Pick {int(draft_position)} · Overall {overall_pick}</div>
  <div class="card-sub">Players with ESPN ADP more than six picks earlier than this selection are removed. The list updates automatically when you change teams, draft position, or round.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    fits = player_fit(
        rows,
        overall_pick=int(overall_pick),
        round_number=int(round_number),
    )

    availability_filter = st.selectbox(
        "Availability",
        ["Likely Available","Possible Slide","Longer Shot","All Plausible"],
        key="fit_availability_filter",
    )
    fit_filter = st.selectbox(
        "Player Fit",
        ["Strong Fit","Acceptable","Risky","Avoid at ADP","All Fits"],
        key="fit_quality_filter",
    )

    selected = fits.copy()
    if availability_filter != "All Plausible":
        selected = selected[selected["Availability"].eq(availability_filter)]
    if fit_filter != "All Fits":
        selected = selected[selected["Fit"].eq(fit_filter)]
    selected = selected.head(15)

    st.markdown('<div class="section-label">Most Likely Best Fits</div>',unsafe_allow_html=True)

    if selected.empty:
        st.info("No players matched those filters. Try All Plausible or All Fits.")
    else:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        for _,player in selected.iterrows():
            tag_class = {
                "Strong Fit":"",
                "Acceptable":" blue",
                "Risky":" gold",
                "Avoid at ADP":" red",
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
    slot = st.number_input("Draft Position",1,10,1,1)
    draft_plan = build_draft_plan(rows,int(slot),10,16)

    st.markdown('<div class="section-label">Your 2026 Round-by-Round Draft Plan</div>',unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">Pick {int(slot)} · 10-Team Snake</div>
  <div class="card-sub">Recommendations use the verified built-in 2026 ESPN ADP and your historical draft profile.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    for _,pick in draft_plan.iterrows():
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

    with st.expander("View full pick schedule"):
        st.dataframe(
            draft_plan[["Round","Pick","Recommended Player","Pos","ESPN ADP","Alternatives"]],
            use_container_width=True,
            hide_index=True,
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

        fits = player_fit(rows,next_pick or current_pick).head(8)
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
    st.markdown('<div class="section-label">Shiva Draft Intelligence Home</div>',unsafe_allow_html=True)
    st.markdown(
        """
<div class="card">
  <div class="card-title">What Do You Want To Know?</div>
  <div class="card-sub">Ask a plain-English fantasy question. The report runs only against verified fields available inside the Shiva database.</div>
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
            "Biggest draft steals",
            key="example_steals",
            use_container_width=True,
            on_click=set_quick_report_prompt,
            args=("Show me the biggest draft steals",),
        )

    with st.form("quick_report_form",clear_on_submit=False):
        quick_prompt = st.text_input(
            "Report request",
            placeholder="Example: Show me the top 5 WR from 2023",
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
            st.dataframe(
                report["table"],
                use_container_width=True,
                hide_index=True,
            )

else:
    st.markdown('<div class="section-label">Grade My Draft</div>',unsafe_allow_html=True)
    st.markdown(
        """
<div class="card">
  <div class="card-title">Upload a Draft Screenshot</div>
  <div class="card-sub">Upload a lineup, roster, or full draft screenshot. Then confirm the detected players before grading.</div>
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
