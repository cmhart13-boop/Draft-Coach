from __future__ import annotations

import math
import re
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
WEEKLY_PATH = APP_DIR / "weekly_player_ppr.csv"
BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"

st.set_page_config(
    page_title="Shiva Draft Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root{
  --bg:#101012;--card:#1c1c1f;--card2:#25252a;--line:#34343a;
  --muted:#929399;--white:#f7f7f8;--green:#31f22f;--blue:#67a0ff;--red:#ff5c66;
}
html,body,[class*="css"]{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;}
.stApp{background:var(--bg);color:var(--white);}
.block-container{max-width:430px;padding:12px 14px 60px!important;}
#MainMenu,footer,header{visibility:hidden;}
h1,h2,h3,h4,p,label{color:var(--white)!important;}
.app-title{text-align:center;font-size:18px;font-weight:1000;margin:4px 0 12px;}
.nav-label{color:#7f8087;font-size:10px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;margin:8px 0 6px;}
.stButton button{width:100%!important;min-height:54px!important;border-radius:16px!important;border:1px solid var(--line)!important;background:transparent!important;color:#a5a6ac!important;font-weight:900!important;white-space:pre-line!important;line-height:1.1!important;padding:7px 3px!important;}
.stButton button[kind="primary"]{color:#fff!important;border-color:var(--green)!important;box-shadow:0 0 12px rgba(49,242,47,.25)!important;}
.stButton button:hover{color:#fff!important;border-color:#55565d!important;}
[data-baseweb="select"]>div,[data-testid="stNumberInput"]>div>div,[data-testid="stTextInput"] input{background:#20232d!important;border:1px solid #303541!important;border-radius:14px!important;color:#fff!important;min-height:48px!important;}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:16px!important;background:#18181b!important;overflow:hidden!important;margin:10px 0!important;}
[data-testid="stExpander"] summary p{font-weight:950!important;}
.hero{background:linear-gradient(145deg,#202126,#151518);border:1px solid var(--line);border-radius:20px;padding:17px;margin:12px 0;}
.kicker{color:var(--green);font-size:10px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;}
.hero-title{font-size:24px;font-weight:1000;line-height:1.08;margin-top:7px;}
.hero-sub{color:var(--muted);font-size:13px;line-height:1.45;margin-top:7px;}
.metric-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0;}
.metric{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px;min-height:78px;}
.metric-label{color:#85868c;font-size:9px;font-weight:1000;text-transform:uppercase;letter-spacing:.05em;}
.metric-value{color:#fff;font-size:19px;font-weight:1000;margin-top:15px;}.green{color:var(--green)!important}.blue{color:var(--blue)!important}.red{color:var(--red)!important}
.player-card{display:grid;grid-template-columns:42px minmax(0,1fr) auto;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px;margin:8px 0;}
.pos{font-weight:1000;color:var(--green)}.player{font-size:14px;font-weight:1000}.meta{font-size:10px;color:var(--muted);line-height:1.35;margin-top:3px}.tag{font-size:10px;font-weight:1000;color:var(--blue);text-align:right}
.report{background:#151518;border:1px solid var(--line);border-radius:16px;padding:14px;margin:12px 0}.report-title{font-size:14px;font-weight:1000}.report-answer{color:var(--green);font-size:25px;font-weight:1000;margin-top:7px}.report-note{color:var(--muted);font-size:11px;line-height:1.4;margin-top:6px}
.small{font-size:11px;color:var(--muted)}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_history() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("SELECT * FROM draft_roi_scores", con)


@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    df = pd.read_csv(RANKINGS_PATH)
    df["adp"] = pd.to_numeric(df["adp"], errors="coerce")
    df["position_rank"] = pd.to_numeric(df.get("position_rank"), errors="coerce")
    return df.dropna(subset=["player_name", "position", "adp"]).copy()


@st.cache_data(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    if not WEEKLY_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(WEEKLY_PATH, low_memory=False)
    for col in ["season", "week", "ppr_points"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_births() -> pd.DataFrame:
    if not BIRTH_DATES_PATH.exists():
        return pd.DataFrame(columns=["name_key", "birth_date"])
    df = pd.read_csv(BIRTH_DATES_PATH)
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    return df.dropna(subset=["name_key", "birth_date"]).drop_duplicates("name_key")


roi = load_history()
rankings = load_rankings()
weekly = load_weekly()
births = load_births()

for col in ["season", "round", "overall_pick", "position_draft_rank", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played"]:
    if col in roi.columns:
        roi[col] = pd.to_numeric(roi[col], errors="coerce")


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def current_franchises() -> pd.DataFrame:
    latest = int(roi["season"].max())
    cols = ["league_name", "team_id", "team_name", "manager_name"]
    return roi[roi["season"].eq(latest)][cols].drop_duplicates(["league_name", "team_id"])


CURRENT = current_franchises()


def managers_for(scope: str) -> list[str]:
    df = CURRENT if scope == "Combined" else CURRENT[CURRENT["league_name"].eq(scope)]
    return sorted(df["manager_name"].dropna().unique().tolist())


def franchise_rows(manager: str, scope: str) -> pd.DataFrame:
    current = CURRENT[CURRENT["manager_name"].eq(manager)]
    if scope != "Combined":
        current = current[current["league_name"].eq(scope)]
    keys = set(zip(current["league_name"], current["team_id"]))
    if not keys:
        return roi.iloc[0:0].copy()
    mask = roi.apply(lambda row: (row["league_name"], row["team_id"]) in keys, axis=1)
    return roi[mask].copy()


def context_selector(prefix: str) -> tuple[str, str, pd.DataFrame]:
    scope = st.selectbox("League", ["Shiva", "Shiva 2.0", "Combined"], index=2, key=f"{prefix}_scope")
    managers = managers_for(scope)
    default = next((x for x in ["Chris H", "Chris Hart"] if x in managers), managers[0] if managers else "")
    manager = st.selectbox("Manager", managers, index=managers.index(default) if default in managers else 0, key=f"{prefix}_manager")
    return scope, manager, franchise_rows(manager, scope)


def snake_schedule(slot: int, teams: int, rounds: int = 16) -> list[dict[str, int]]:
    return [
        {
            "Round": rnd,
            "Overall": (rnd - 1) * teams + slot if rnd % 2 else rnd * teams - slot + 1,
        }
        for rnd in range(1, rounds + 1)
    ]


def player_fit(overall_pick: int, round_number: int) -> pd.DataFrame:
    pool = rankings.copy()
    window_before = 5 if round_number <= 3 else 7
    pool = pool[pool["adp"].between(max(1, overall_pick - window_before), overall_pick + 24)].copy()
    if pool.empty:
        return pool
    pool["distance"] = (pool["adp"] - overall_pick).abs()
    pool["availability"] = np.select(
        [pool["adp"] >= overall_pick, pool["adp"] >= overall_pick - 2],
        ["Likely Available", "Possible Slide"],
        default="Longer Shot",
    )
    pool["score"] = 100 - pool["distance"].clip(0, 25) * 3
    if round_number <= 3:
        pool.loc[pool["position"].isin(["RB", "WR"]), "score"] += 10
        pool.loc[pool["position"].eq("QB"), "score"] -= 12
        pool.loc[pool["position"].eq("TE"), "score"] -= 6
    elif round_number <= 6:
        pool.loc[pool["position"].isin(["RB", "WR"]), "score"] += 5
    else:
        pool.loc[pool["position"].isin(["QB", "TE"]), "score"] += 3
    pool["fit"] = np.select(
        [pool["score"] >= 82, pool["score"] >= 70, pool["score"] >= 58],
        ["Best Available", "Strong Option", "Acceptable"],
        default="Reach",
    )
    return pool.sort_values(["score", "adp"], ascending=[False, True]).reset_index(drop=True)


def build_plan(slot: int, teams: int = 10, rounds: int = 16) -> pd.DataFrame:
    selected: set[str] = set()
    roster = {"QB": 0, "RB": 0, "WR": 0, "TE": 0}
    output: list[dict[str, Any]] = []
    for pick in snake_schedule(slot, teams, rounds):
        rnd, overall = pick["Round"], pick["Overall"]
        options = player_fit(overall, rnd)
        options = options[~options["player_name"].isin(selected)].copy()
        if options.empty:
            options = rankings[~rankings["player_name"].isin(selected)].copy()
            options["score"] = 100 - (options["adp"] - overall).abs().clip(0, 30) * 3
        if roster["QB"] >= 1 and rnd <= 10:
            options.loc[options["position"].eq("QB"), "score"] -= 20
        if roster["TE"] >= 1 and rnd <= 10:
            options.loc[options["position"].eq("TE"), "score"] -= 14
        if rnd <= 3:
            options.loc[options["position"].isin(["RB", "WR"]), "score"] += 8
        choice = options.sort_values(["score", "adp"], ascending=[False, True]).iloc[0]
        selected.add(str(choice["player_name"]))
        pos = str(choice["position"])
        if pos in roster:
            roster[pos] += 1
        alternatives = options[options["player_name"].ne(choice["player_name"])].sort_values(["score", "adp"], ascending=[False, True]).head(3)
        output.append({
            "Round": rnd,
            "Pick": overall,
            "Player": str(choice["player_name"]),
            "Pos": pos,
            "ADP": float(choice["adp"]),
            "Alternatives": ", ".join(alternatives["player_name"].astype(str).tolist()),
        })
    return pd.DataFrame(output)


def coach_profile(rows: pd.DataFrame) -> dict[str, Any]:
    premium = rows[rows["round"].between(1, 8)].copy()
    if premium.empty:
        return {"best_round": None, "worst_round": None, "best_pos": "—", "early_pos": "—"}
    premium["value"] = premium["position_draft_rank"] - premium["position_finish_total"]
    round_summary = premium.groupby("round").agg(Picks=("player_name", "count"), Value=("value", "mean"))
    eligible = round_summary[round_summary["Picks"].ge(max(3, math.ceil(rows["season"].nunique() * .4)))]
    if eligible.empty:
        eligible = round_summary
    best_round = int(eligible["Value"].idxmax())
    worst_round = int(eligible["Value"].idxmin())
    pos_summary = premium.groupby("position").agg(Picks=("player_name", "count"), Value=("value", "mean"))
    best_pos = str(pos_summary.sort_values(["Value", "Picks"], ascending=[False, False]).index[0])
    early = premium[premium["round"].le(3)]["position"].value_counts()
    early_pos = str(early.index[0]) if not early.empty else "—"
    return {"best_round": best_round, "worst_round": worst_round, "best_pos": best_pos, "early_pos": early_pos}


def report_engine(prompt: str) -> dict[str, Any]:
    query = re.sub(r"\s+", " ", prompt.lower().strip())
    aliases = {
        "QB": ["qb", "quarterback", "quarterbacks"],
        "RB": ["rb", "rbs", "running back", "running backs"],
        "WR": ["wr", "wrs", "wide receiver", "wide receivers"],
        "TE": ["te", "tes", "tight end", "tight ends"],
    }
    position = next((pos for pos, names in aliases.items() if any(re.search(rf"\b{re.escape(name)}\b", query) for name in names)), None)
    top_match = re.search(r"top\s*(\d+)", query)
    top_n = int(top_match.group(1)) if top_match else None
    year_match = re.search(r"\b(20\d{2})\b", query)
    year = int(year_match.group(1)) if year_match else None
    years_match = re.search(r"(?:last|past)\s*(\d+)\s*years?", query)
    last_years = int(years_match.group(1)) if years_match else None

    if re.search(r"(?:2|two)\s*(?:rb|rbs|running backs?)", query) and re.search(r"first\s*(?:2|two)\s*rounds?", query):
        top20 = rankings[rankings["adp"].le(20)].sort_values("adp")
        backs = top20[top20["position"].eq("RB")]
        return {
            "title": "2026 RB-RB Strategy",
            "answer": "RB-RB is viable when both backs remain in the best available ADP tier. Do not force it over a clearly superior WR.",
            "note": f"{len(backs)} running backs currently carry top-20 ESPN ADP.",
            "table": top20,
        }

    pool = roi.sort_values(["season", "position", "position_finish_total", "fantasy_points_ppr"], ascending=[True, True, True, False]).drop_duplicates(["season", "player_name", "position"]).copy()
    if position:
        pool = pool[pool["position"].eq(position)]
    if year:
        pool = pool[pool["season"].eq(year)]
    elif last_years and not pool.empty:
        latest = int(pool["season"].max())
        pool = pool[pool["season"].between(latest - last_years + 1, latest)]
    if top_n:
        pool = pool.sort_values(["season", "position_finish_total", "fantasy_points_ppr"], ascending=[False, True, False]).groupby("season", group_keys=False).head(top_n)
    if pool.empty:
        return {"title": "No Matching Data", "answer": "0 records", "note": "No verified records matched.", "table": pd.DataFrame()}

    if "age" in query:
        if births.empty:
            return {"title": "Age Report", "answer": "DOB data unavailable", "note": "No verified birth-date file is loaded.", "table": pd.DataFrame()}
        pool["name_key"] = pool["player_name"].map(normalize_name)
        merged = pool.merge(births[["name_key", "birth_date"]], on="name_key", how="left").dropna(subset=["birth_date"])
        ref = pd.to_datetime(merged["season"].astype(int).astype(str) + "-09-01")
        merged["age"] = ((ref - merged["birth_date"]).dt.days / 365.2425).round(1)
        return {"title": "Average Player Age", "answer": f"{merged['age'].mean():.1f} years", "note": f"{len(merged)} unique player-seasons.", "table": merged}
    if "ppg" in query or "points per game" in query:
        return {"title": "Average Full-PPR PPG", "answer": f"{pool['ppg'].mean():.2f} PPG", "note": f"{len(pool)} unique player-seasons.", "table": pool}
    if "average" in query and "points" in query:
        return {"title": "Average Full-PPR Points", "answer": f"{pool['fantasy_points_ppr'].mean():.1f} points", "note": f"{len(pool)} unique player-seasons.", "table": pool}
    return {"title": "Verified Fantasy Report", "answer": f"{len(pool)} player-seasons", "note": "Unique verified player-season results only.", "table": pool}


st.markdown('<div class="app-title">SHIVA DRAFT INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown('<div class="nav-label">Shiva Tools</div>', unsafe_allow_html=True)

TOOLS = [
    ("Shiva Intelligence", "📊\nIntelligence", "intel"),
    ("Draft Coach", "📋\nDraft Coach", "coach"),
    ("Live Draft", "🧩\nLive Draft", "live"),
    ("Grade Draft", "📝\nGrade Draft", "grade"),
    ("Shiva League History", "🏛️\nHistory", "history"),
]
if "page" not in st.session_state:
    st.session_state.page = "Shiva Intelligence"
row1 = st.columns(3)
row2 = st.columns(2)
for (name, label, key), col in zip(TOOLS, [*row1, *row2]):
    with col:
        if st.button(label, key=f"nav_{key}", use_container_width=True, type="primary" if st.session_state.page == name else "secondary"):
            st.session_state.page = name
            st.rerun()
page = st.session_state.page


if page == "Shiva Intelligence":
    st.markdown('<div class="hero"><div class="kicker">📊 Shiva Intelligence</div><div class="hero-title">Ask the Database</div><div class="hero-sub">Run verified reports across historical Full-PPR scoring, player age, current ESPN ADP and league draft history.</div></div>', unsafe_allow_html=True)
    with st.form("intelligence_form"):
        prompt = st.text_input("What do you want to know?", placeholder="Example: Show average PPG for top-5 RBs over the last five years")
        submitted = st.form_submit_button("Run Report", use_container_width=True)
    if submitted:
        if prompt.strip():
            st.session_state.report = report_engine(prompt)
        else:
            st.warning("Type a report request first.")
    report = st.session_state.get("report")
    if report:
        st.markdown(f'<div class="report"><div class="report-title">{report["title"]}</div><div class="report-answer">{report["answer"]}</div><div class="report-note">{report["note"]}</div></div>', unsafe_allow_html=True)
        table = report.get("table", pd.DataFrame())
        if not table.empty:
            with st.expander("View Supporting Data"):
                display_cols = [c for c in ["season", "player_name", "position", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "adp"] if c in table.columns]
                st.dataframe(table[display_cols].head(100), use_container_width=True, hide_index=True)

elif page == "Draft Coach":
    st.markdown('<div class="hero"><div class="kicker">📋 Draft Coach</div><div class="hero-title">Build Your 2026 Draft</div><div class="hero-sub">Your coaching profile, Player Fit and full Draft Plan now live together in one place.</div></div>', unsafe_allow_html=True)
    scope, manager, rows = context_selector("coach")
    with st.expander("📋 Coach Overview", expanded=True):
        profile = coach_profile(rows)
        st.markdown(f'<div class="metric-grid"><div class="metric"><div class="metric-label">Early Identity</div><div class="metric-value green">{profile["early_pos"]}</div></div><div class="metric"><div class="metric-label">Best Round</div><div class="metric-value blue">R{profile["best_round"] or "—"}</div></div><div class="metric"><div class="metric-label">Protect</div><div class="metric-value red">R{profile["worst_round"] or "—"}</div></div></div>', unsafe_allow_html=True)
        st.write(f"Use {profile['best_pos']} only as a tiebreaker between similarly ranked players. In Round {profile['worst_round'] or '—'}, slow down and follow the highest remaining ADP tier.")
    with st.expander("🎯 Player Fit", expanded=False):
        cols = st.columns(3)
        teams = cols[0].number_input("Teams", 8, 16, 10, 1, key="fit_teams")
        slot = cols[1].number_input("Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="fit_slot")
        rnd = cols[2].number_input("Round", 1, 16, 1, 1, key="fit_round")
        overall = (int(rnd) - 1) * int(teams) + int(slot) if int(rnd) % 2 else int(rnd) * int(teams) - int(slot) + 1
        fits = player_fit(overall, int(rnd)).head(12)
        if fits.empty:
            st.info("No verified ADP options matched this pick.")
        else:
            best = fits.iloc[0]
            st.markdown(f'<div class="report"><div class="report-title">Best Available At Pick {overall}</div><div class="report-answer">{best["player_name"]}</div><div class="report-note">{best["position"]} · ESPN ADP {best["adp"]:.1f} · {best["availability"]}</div></div>', unsafe_allow_html=True)
            for _, player in fits.iterrows():
                st.markdown(f'<div class="player-card"><div class="pos">{player["position"]}</div><div><div class="player">{player["player_name"]}</div><div class="meta">ESPN ADP {player["adp"]:.1f} · {player["availability"]}</div></div><div class="tag">{player["fit"]}</div></div>', unsafe_allow_html=True)
    with st.expander("🗺️ Draft Plan", expanded=False):
        teams = st.number_input("League Size", 8, 16, 10, 1, key="plan_teams")
        slot = st.number_input("Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="plan_slot")
        plan = build_plan(int(slot), int(teams), 16)
        for _, pick in plan.iterrows():
            st.markdown(f'<div class="player-card"><div class="pos">R{int(pick["Round"])}</div><div><div class="player">{pick["Player"]} ({pick["Pos"]})</div><div class="meta">Pick {int(pick["Pick"])} · Alternatives: {pick["Alternatives"] or "—"}</div></div><div class="tag">ADP {pick["ADP"]:.1f}</div></div>', unsafe_allow_html=True)

elif page == "Live Draft":
    st.markdown('<div class="hero"><div class="kicker">🧩 Live Draft</div><div class="hero-title">Who Should You Take Now?</div><div class="hero-sub">Set the current overall pick. The app never invents a draft position.</div></div>', unsafe_allow_html=True)
    teams = st.number_input("Teams", 8, 16, 10, 1, key="live_teams")
    slot = st.number_input("Your Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="live_slot")
    current_pick = st.number_input("Current Overall Pick", 1, int(teams) * 20, 1, 1, key="live_pick")
    schedule = pd.DataFrame(snake_schedule(int(slot), int(teams), 20))
    future = schedule[schedule["Overall"].ge(int(current_pick))]
    next_pick = int(future.iloc[0]["Overall"]) if not future.empty else None
    picks_until = max(0, next_pick - int(current_pick)) if next_pick is not None else None
    st.markdown(f'<div class="metric-grid"><div class="metric"><div class="metric-label">Current Pick</div><div class="metric-value">{int(current_pick)}</div></div><div class="metric"><div class="metric-label">Your Next Pick</div><div class="metric-value blue">{next_pick or "—"}</div></div><div class="metric"><div class="metric-label">Picks Until You</div><div class="metric-value green">{picks_until if picks_until is not None else "—"}</div></div></div>', unsafe_allow_html=True)
    recommendation_pick = next_pick or int(current_pick)
    rnd = max(1, math.ceil(recommendation_pick / int(teams)))
    fits = player_fit(recommendation_pick, rnd).head(10)
    for _, player in fits.iterrows():
        st.markdown(f'<div class="player-card"><div class="pos">{player["position"]}</div><div><div class="player">{player["player_name"]}</div><div class="meta">ESPN ADP {player["adp"]:.1f} · {player["availability"]}</div></div><div class="tag">{player["fit"]}</div></div>', unsafe_allow_html=True)

elif page == "Grade Draft":
    st.markdown('<div class="hero"><div class="kicker">📝 Grade Draft</div><div class="hero-title">Grade Your Draft</div><div class="hero-sub">Enter your picks. Premium rounds count more heavily.</div></div>', unsafe_allow_html=True)
    teams = st.number_input("Teams", 8, 16, 10, 1, key="grade_teams")
    slot = st.number_input("Your Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="grade_slot")
    draft = st.data_editor(pd.DataFrame(columns=["Round", "Player", "Pos", "ADP"]), num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("Grade This Draft", use_container_width=True):
        if draft.empty:
            st.warning("Add drafted players first.")
        else:
            draft["Round"] = pd.to_numeric(draft["Round"], errors="coerce")
            draft["ADP"] = pd.to_numeric(draft["ADP"], errors="coerce")
            schedule = {x["Round"]: x["Overall"] for x in snake_schedule(int(slot), int(teams), 20)}
            draft["Pick"] = draft["Round"].map(schedule)
            draft["Value"] = draft["Pick"] - draft["ADP"]
            draft["Score"] = (72 + 1.15 * draft["Value"].clip(-25, 25)).clip(25, 98)
            weights = draft["Round"].map({1: 1, 2: .92, 3: .84, 4: .74, 5: .64, 6: .55}).fillna(.3)
            valid = draft.dropna(subset=["Score"])
            score = float(np.average(valid["Score"], weights=weights.loc[valid.index])) if not valid.empty else np.nan
            grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 50 else "F"
            st.markdown(f'<div class="report"><div class="report-title">Draft Grade</div><div class="report-answer">{grade}</div><div class="report-note">{score:.1f}/100 · Premium rounds count most.</div></div>', unsafe_allow_html=True)
            st.dataframe(draft, use_container_width=True, hide_index=True)

else:
    st.markdown('<div class="hero"><div class="kicker">🏛️ Shiva League History</div><div class="hero-title">Search Historical Drafts</div><div class="hero-sub">Filter by league, current manager and season.</div></div>', unsafe_allow_html=True)
    scope, manager, rows = context_selector("history")
    seasons = sorted(rows["season"].dropna().astype(int).unique(), reverse=True)
    season = st.selectbox("Season", ["All Seasons"] + [str(x) for x in seasons])
    search = st.text_input("Search Player", placeholder="Optional player name")
    result = rows.copy()
    if season != "All Seasons":
        result = result[result["season"].eq(int(season))]
    if search.strip():
        result = result[result["player_name"].str.contains(search.strip(), case=False, na=False)]
    cols = [c for c in ["season", "league_name", "round", "overall_pick", "player_name", "position", "position_draft_rank", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played"] if c in result.columns]
    st.dataframe(result[cols].sort_values(["season", "round", "overall_pick"], ascending=[False, True, True]), use_container_width=True, hide_index=True)
