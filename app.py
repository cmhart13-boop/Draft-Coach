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
    <div class="back-text">‹ League</div>
    <div class="page-title">Shiva Draft Intelligence</div>
    <div style="width:52px"></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


st.markdown('''



''', unsafe_allow_html=True)


st.markdown('''

<style>
/* ESPN-STYLE SHIVA TOOLS ROW */
.nav-caption{
  color:#77787d;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.1em;
  text-transform:uppercase;
  margin:10px 0 7px;
}

.shiva-tools-panel{
  width:100%;
  margin:0 0 14px;
  padding:16px 10px 14px;
  border:1px solid #313136;
  border-radius:18px;
  background:#202023;
  box-sizing:border-box;
  overflow:hidden;
  max-height:150px;
}

.shiva-tools-scroll{
  display:flex;
  flex-direction:row;
  flex-wrap:nowrap;
  align-items:flex-start;
  gap:10px;
  width:100%;
  overflow-x:auto;
  overflow-y:hidden;
  padding:0 2px 2px;
  scroll-snap-type:x proximity;
  scrollbar-width:none;
  -ms-overflow-style:none;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior-x:contain;
}

.shiva-tools-scroll::-webkit-scrollbar{
  display:none;
}

.shiva-tool{
  flex:0 0 74px;
  min-width:74px;
  max-width:74px;
  min-height:92px;
  margin:0;
  padding:0;
  border:0;
  border-radius:0;
  background:transparent;
  box-shadow:none;
  color:#a8a8ad;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:flex-start;
  gap:8px;
  text-align:center;
  cursor:pointer;
  scroll-snap-align:start;
  -webkit-tap-highlight-color:transparent;
  text-decoration:none!important;
}

.shiva-tool:hover,
.shiva-tool:focus,
.shiva-tool:visited{
  text-decoration:none!important;
}

.shiva-tool-icon{
  width:58px;
  height:58px;
  flex:0 0 58px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:#444448;
  font-size:26px;
  line-height:1;
  border:2px solid transparent;
  box-sizing:border-box;
  transition:
    background 160ms ease,
    border-color 160ms ease,
    transform 160ms ease;
}

.shiva-tool-label{
  display:block;
  width:74px;
  max-width:74px;
  color:#a8a8ad;
  font-size:12.5px;
  font-weight:700;
  line-height:1.08;
  text-align:center;
  white-space:normal;
  overflow-wrap:normal;
}

.shiva-tool.active .shiva-tool-icon{
  background:#4d4d51;
  border-color:#24f13d;
}

.shiva-tool.active .shiva-tool-label{
  color:#ffffff;
}

.shiva-tool:active .shiva-tool-icon{
  transform:scale(.96);
}

@media(min-width:700px){
  .shiva-tool{
    flex-basis:82px;
    min-width:82px;
    max-width:82px;
  }

  .shiva-tool-label{
    width:82px;
    max-width:82px;
  }
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


def player_fit(rows: pd.DataFrame,current_pick: int) -> pd.DataFrame:
    p = profile(rows)
    result = rankings.copy()

    result["ADP Value"] = current_pick-result["adp"]
    result["ADP Strength"] = (1-result["adp"].rank(pct=True))*100

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

        if not player_reasons:
            player_reasons.append("priced from verified 2026 ESPN ADP")

        bonuses.append(bonus)
        reasons.append(", ".join(player_reasons))

    result["Historical Fit"] = bonuses
    result["Why"] = reasons
    result["Recommendation Score"] = (
        .70*result["ADP Strength"]
        + 1.4*result["ADP Value"].clip(-20,20)
        + result["Historical Fit"]
    )

    q80 = result["Recommendation Score"].quantile(.80)
    q50 = result["Recommendation Score"].quantile(.50)
    q25 = result["Recommendation Score"].quantile(.25)

    def fit_label(value: float) -> str:
        if value >= q80: return "Strong Fit"
        if value >= q50: return "Acceptable"
        if value >= q25: return "Risky"
        return "Avoid at ADP"

    result["Fit"] = result["Recommendation Score"].apply(fit_label)
    return result.sort_values(["Recommendation Score","adp"],ascending=[False,True])



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

    years_match = re.search(r"(?:last|past)\s*(\d+)\s*years?", query)
    last_years = int(years_match.group(1)) if years_match else None

    season_pool = graded.copy()
    if position:
        season_pool = season_pool[season_pool["position"].eq(position)]

    if last_years:
        max_season = int(season_pool["season"].max())
        min_season = max_season-last_years+1
        season_pool = season_pool[season_pool["season"].between(min_season, max_season)]

    if top_n:
        season_pool = season_pool[season_pool["position_finish_total"].le(top_n)]

    if "age" in query:
        return {
            "title":"Age report unavailable",
            "answer":"Age is not in this app database",
            "note":"The current SQLite app contains league drafts, positional finishes, PPR points, PPG and games played. It does not contain verified historical player age, so the app will not estimate or invent it.",
            "table":pd.DataFrame(),
        }

    if season_pool.empty:
        return {
            "title":"No matching records",
            "answer":"0 records",
            "note":"Try changing the position, finish threshold or date range.",
            "table":pd.DataFrame(),
        }

    if "average" in query and ("ppg" in query or "points per game" in query):
        value = season_pool["ppg"].mean()
        return {
            "title":"Average fantasy points per game",
            "answer":f"{value:.2f} PPG",
            "note":f"{len(season_pool)} matched player-seasons.",
            "table":season_pool[
                ["season","player_name","position","position_finish_total","ppg","games_played"]
            ].sort_values(["season","position_finish_total"]),
        }

    if "average" in query and ("points" in query or "scoring" in query):
        value = season_pool["fantasy_points_ppr"].mean()
        return {
            "title":"Average full-PPR points",
            "answer":f"{value:.1f} points",
            "note":f"{len(season_pool)} matched player-seasons.",
            "table":season_pool[
                ["season","player_name","position","position_finish_total","fantasy_points_ppr","ppg"]
            ].sort_values(["season","position_finish_total"]),
        }

    if "average" in query and ("games" in query or "games played" in query):
        value = season_pool["games_played"].mean()
        return {
            "title":"Average games played",
            "answer":f"{value:.1f} games",
            "note":f"{len(season_pool)} matched player-seasons.",
            "table":season_pool[
                ["season","player_name","position","position_finish_total","games_played","ppg"]
            ].sort_values(["season","position_finish_total"]),
        }

    if "best" in query and "round" in query:
        summary = (
            season_pool.groupby("round", as_index=False)
            .agg(
                Picks=("player_name","count"),
                Average_Score=("Pick Score","mean"),
            )
            .sort_values("Average_Score", ascending=False)
        )
        best = summary.iloc[0]
        return {
            "title":"Best historical draft round",
            "answer":f"Round {int(best['round'])}",
            "note":f"Average pick score {best['Average_Score']:.1f} across {int(best['Picks'])} picks.",
            "table":summary,
        }

    if "bust" in query:
        busts = season_pool[season_pool["Result"].eq("Bust")]
        rate = len(busts)/len(season_pool)*100
        return {
            "title":"Bust rate",
            "answer":f"{rate:.1f}%",
            "note":f"{len(busts)} busts among {len(season_pool)} matched picks.",
            "table":busts[
                ["season","manager_name","round","player_name","position","position_draft_rank","position_finish_total"]
            ].sort_values(["season","round"], ascending=[False,True]),
        }

    if "steal" in query or "best picks" in query:
        steals = season_pool.sort_values("Pick Score", ascending=False).head(20)
        return {
            "title":"Best historical picks",
            "answer":f"{len(steals)} picks shown",
            "note":"Ranked by the app's premium-round-weighted pick score.",
            "table":steals[
                ["season","manager_name","round","player_name","position","position_draft_rank","position_finish_total","Result"]
            ],
        }

    if "top" in query or "finish" in query:
        value = season_pool["fantasy_points_ppr"].mean()
        return {
            "title":"Matched top-finish report",
            "answer":f"{len(season_pool)} player-seasons",
            "note":f"Average production: {value:.1f} full-PPR points.",
            "table":season_pool[
                ["season","player_name","position","position_finish_total","fantasy_points_ppr","ppg","games_played"]
            ].sort_values(["season","position_finish_total"]),
        }

    return {
        "title":"Quick report",
        "answer":f"{len(season_pool)} matching records",
        "note":"Supported requests include average PPG, average points, games played, top positional finishes, busts, steals and best rounds. Historical age is not currently available in the app database.",
        "table":season_pool[
            ["season","manager_name","round","player_name","position","position_draft_rank","position_finish_total","fantasy_points_ppr","ppg"]
        ].head(50),
    }



# Single mapped Shiva Tools navigation row.
TOOLS = [
    {"id":"history", "page":"League History", "label":"History", "icon":"🏛️"},
    {"id":"draft-coach", "page":"Draft Coach", "label":"Draft Coach", "icon":"📋"},
    {"id":"player-fit", "page":"Player Fit", "label":"Player Fit", "icon":"🎯"},
    {"id":"draft-plan", "page":"Draft Slot", "label":"Draft Plan", "icon":"🗺️"},
    {"id":"live-draft", "page":"Live Draft", "label":"Live Draft", "icon":"🧩"},
    {"id":"grade-draft", "page":"Grade My Draft", "label":"Grade Draft", "icon":"📝"},
    {"id":"intelligence", "page":"Draft Intelligence", "label":"Intelligence", "icon":"📊"},
]

tool_id_to_page = {tool["id"]:tool["page"] for tool in TOOLS}
page_to_tool_id = {tool["page"]:tool["id"] for tool in TOOLS}

requested_tool = st.query_params.get("tool")
if isinstance(requested_tool, list):
    requested_tool = requested_tool[0] if requested_tool else None

if requested_tool in tool_id_to_page:
    st.session_state.section_nav = tool_id_to_page[requested_tool]
elif "section_nav" not in st.session_state:
    st.session_state.section_nav = "Draft Coach"

page = st.session_state.section_nav
active_tool_id = page_to_tool_id.get(page, "draft-coach")

tool_links = []
for tool in TOOLS:
    active_class = " active" if tool["id"] == active_tool_id else ""
    tool_links.append(
        f"""
<a
  class="shiva-tool{active_class}"
  href="?tool={tool['id']}"
  target="_self"
  aria-label="{tool['label']}"
>
  <span class="shiva-tool-icon">{tool['icon']}</span>
  <span class="shiva-tool-label">{tool['label']}</span>
</a>
"""
    )

st.markdown(
    '<div class="nav-caption">Shiva Tools</div>'
    '<section class="shiva-tools-panel">'
    '<div class="shiva-tools-scroll">'
    + "".join(tool_links)
    + '</div></section>',
    unsafe_allow_html=True,
)

scope = st.selectbox("League",["Shiva","Shiva 2.0","Combined"])
managers = current_managers(scope)
manager = st.selectbox("Current Manager",managers)
rows = franchise_rows(manager,scope)
team_name = franchise_name(manager,scope)

if page == "League History":
    st.markdown('<div class="section-label">Search Historical Drafts</div>', unsafe_allow_html=True)

    search_scope = st.selectbox(
        "League",
        ["Shiva","Shiva 2.0","Combined"],
        key="history_scope",
    )
    history_managers = current_managers(search_scope)
    history_manager = st.selectbox(
        "Team / Manager",
        history_managers,
        key="history_manager",
    )

    available_seasons = sorted(
        franchise_rows(history_manager, search_scope)["season"].dropna().astype(int).unique(),
        reverse=True,
    )
    season_choice = st.selectbox(
        "Season",
        ["All Seasons"]+[str(x) for x in available_seasons],
        key="history_season",
    )
    player_search = st.text_input(
        "Search player name",
        placeholder="Optional: type a player name",
        key="history_player_search",
    )

    history_rows = historical_draft_lookup(
        history_manager,
        search_scope,
        season_choice,
    )

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
  <div class="card-title">{franchise_name(history_manager, search_scope)}</div>
  <div class="card-sub">{history_manager} · {search_scope} · {season_choice} · {len(history_rows)} picks</div>
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

    st.markdown('<div class="section-label">Your 2026 Draft Plan</div>',unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{team_name}</div>
  <div class="card-sub">{manager} · Personalized from your complete historical draft record</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="metric-grid">
  <div class="metric-box"><div class="metric-label">Historical Draft Grade</div><div class="metric-value green">{letter_grade(score)}</div></div>
  <div class="metric-box"><div class="metric-label">Strongest Position</div><div class="metric-value blue">{p['best_position']}</div></div>
  <div class="metric-box"><div class="metric-label">Weakest Premium Round</div><div class="metric-value red">R{p['worst_round']}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Your Five Draft Rules</div>',unsafe_allow_html=True)
    st.markdown('<div class="card">',unsafe_allow_html=True)
    for i,rule in enumerate(rules,1):
        st.markdown(
            f"""
<div class="list-row">
  <div class="rank-circle">{i}</div>
  <div class="row-title">{rule}</div>
  <div class="row-tag">2026</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="section-label">Do More</div>',unsafe_allow_html=True)
    st.markdown('<div class="card">',unsafe_allow_html=True)
    for item in do_more:
        st.markdown(f'<div class="callout"><div class="callout-title">{item}</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="section-label">Do Less</div>',unsafe_allow_html=True)
    st.markdown('<div class="card">',unsafe_allow_html=True)
    for item in do_less:
        st.markdown(f'<div class="callout red"><div class="callout-title">{item}</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

elif page == "Player Fit":
    st.caption(f"Verified 2026 FantasyPros ESPN ADP is built in: {len(rankings)} players.")
    current_pick = st.number_input("Your Current Overall Pick",1,200,9,1)
    fits = player_fit(rows,int(current_pick))
    fit_filter = st.selectbox("Show",["Strong Fit","Acceptable","Risky","Avoid at ADP"])
    selected = fits[fits["Fit"].eq(fit_filter)].head(15)

    st.markdown('<div class="section-label">2026 Player Fit</div>',unsafe_allow_html=True)
    st.markdown('<div class="card">',unsafe_allow_html=True)
    for _,player in selected.iterrows():
        tag_class = {"Strong Fit":"","Acceptable":" blue","Risky":" gold","Avoid at ADP":" red"}[player["Fit"]]
        st.markdown(
            f"""
<div class="list-row">
  <div><span class="pos-badge pos-{player['position']}">{player['position']}</span></div>
  <div>
    <div class="row-title">{player['player_name']}</div>
    <div class="row-sub">ESPN ADP {float(player['adp']):.1f} · {player['Why']}</div>
  </div>
  <div class="row-tag{tag_class}">{player['Fit']}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>',unsafe_allow_html=True)

elif page == "Draft Slot":
    slot = st.number_input("Your Draft Slot",1,10,9,1)
    schedule = pd.DataFrame(snake_schedule(int(slot),10,16))

    st.markdown('<div class="section-label">Your Pick Schedule</div>',unsafe_allow_html=True)
    st.dataframe(schedule,use_container_width=True,hide_index=True)

    phases = [
        ("Rounds 1–2","Build the foundation","Take the highest-tier RB/WR value. Do not force a position after the tier dries up."),
        ("Round 3","Complete the core","Leave the first three rounds with dependable weekly starters."),
        ("Rounds 4–6","Add weekly usability","Prioritize clear roles and proven scoring paths."),
        ("Rounds 7–9","Chase upside","Target players who can become weekly starters."),
        ("Rounds 10+","Swing for impact","Late misses are cheap. Chase breakout and contingent value."),
    ]

    st.markdown('<div class="section-label">Round-by-Round Plan</div>',unsafe_allow_html=True)
    st.markdown('<div class="card">',unsafe_allow_html=True)
    for phase,title,body in phases:
        st.markdown(
            f"""
<div class="callout blue">
  <div class="callout-title">{phase}: {title}</div>
  <div class="callout-sub">{body}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>',unsafe_allow_html=True)

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
    st.markdown('<div class="section-label">Quick Historical Reports</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="card">
  <div class="card-title">Ask the Shiva Database</div>
  <div class="card-sub">Type a plain-English historical request. Reports run only against verified fields available inside the app.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    quick_prompt = st.text_input(
        "Report request",
        placeholder="Example: Show average PPG for RBs that finished top 5 over the last 5 years",
        key="quick_report_prompt",
    )

    examples = st.columns(2)
    with examples[0]:
        if st.button("Top-5 RB average PPG", key="example_top5_rb", use_container_width=True):
            st.session_state.quick_report_prompt = "Show average PPG for RBs that finished top 5 over the last 5 years"
            st.rerun()
    with examples[1]:
        if st.button("Biggest draft steals", key="example_steals", use_container_width=True):
            st.session_state.quick_report_prompt = "Show me the biggest draft steals"
            st.rerun()

    if st.button("Run Report", key="run_quick_report", use_container_width=True):
        if not quick_prompt.strip():
            st.warning("Type a report request first.")
        else:
            report = parse_quick_report(quick_prompt)
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
