from __future__ import annotations

import base64
import math
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from shiva_engine import build_history_frame
from shiva_query_router import run_shiva_query
from shiva_chatgpt_service import ask_shiva_via_chatgpt
from espn_news_service import fetch_espn_news
from mock_draft_ui import render_mock_draft_room

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"
WEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"
SPLASH_PATH = APP_DIR / "shiva_splash_screen.jpeg"

st.set_page_config(
    page_title="Shiva Draft Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "shiva_splash_seen" not in st.session_state:
    st.session_state.shiva_splash_seen = True
    if SPLASH_PATH.exists():
        splash_b64 = base64.b64encode(SPLASH_PATH.read_bytes()).decode("ascii")
        st.markdown(
            f"""
<style>
#shiva-startup-splash{{position:fixed;inset:0;z-index:2147483647;background:#06168f;display:flex;align-items:center;justify-content:center;overflow:hidden;pointer-events:none;animation:shivaSplashShell 2.8s cubic-bezier(.22,.8,.24,1) forwards}}
#shiva-startup-splash .splash-phone{{position:absolute;inset:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:#06168f}}
#shiva-startup-splash img{{width:100%;height:100%;object-fit:cover;object-position:center center;transform-origin:center center;animation:shivaSplashImage 2.8s cubic-bezier(.22,.8,.24,1) forwards}}
#shiva-startup-splash .splash-glow{{position:absolute;inset:-18%;background:radial-gradient(circle at 50% 48%,rgba(179,255,0,.13),transparent 42%);mix-blend-mode:screen;animation:shivaSplashGlow 2.8s ease-out forwards}}
@keyframes shivaSplashShell{{0%{{opacity:0;visibility:visible}}7%{{opacity:1}}84%{{opacity:1;visibility:visible}}100%{{opacity:0;visibility:hidden}}}}
@keyframes shivaSplashImage{{0%{{transform:translate3d(0,22px,0) scale(1.075);filter:brightness(.82)}}10%{{transform:translate3d(0,0,0) scale(1.025);filter:brightness(1.05)}}72%{{transform:translate3d(0,0,0) scale(1)}}100%{{transform:translate3d(0,-20px,0) scale(1.025);filter:brightness(.92)}}}}
@keyframes shivaSplashGlow{{0%{{opacity:0;transform:scale(.92)}}18%{{opacity:1;transform:scale(1)}}76%{{opacity:.65}}100%{{opacity:0;transform:scale(1.06)}}}}
@media (min-width:700px){{#shiva-startup-splash{{background:#050506}}#shiva-startup-splash .splash-phone{{left:50%;right:auto;width:min(430px,100vw);transform:translateX(-50%);box-shadow:0 0 70px rgba(20,64,255,.24)}}}}
</style>
<div id="shiva-startup-splash" aria-hidden="true"><div class="splash-phone"><img src="data:image/jpeg;base64,{splash_b64}" alt=""/><div class="splash-glow"></div></div></div>
""",
            unsafe_allow_html=True,
        )

st.markdown(
    """
<style>
:root{--bg:#101012;--card:#1c1c1f;--line:#34343a;--muted:#929399;--white:#f7f7f8;--green:#31f22f;--blue:#67a0ff;--red:#ff5c66}
html,body,[class*="css"]{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}.stApp{background:var(--bg);color:var(--white)}.block-container{max-width:430px;padding:10px 12px 60px!important}#MainMenu,footer,header{visibility:hidden}h1,h2,h3,h4,p,label{color:var(--white)!important}.app-title{text-align:center;font-size:18px;font-weight:1000;margin:4px 0 8px}.nav-label{color:#7f8087;font-size:9px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;margin:6px 0 2px}
div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel){display:flex!important;flex-wrap:nowrap!important;gap:2px!important;width:100%!important}div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel)>div{flex:1 1 0!important;width:25%!important;min-width:0!important}.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_history button{width:100%!important;min-width:0!important;min-height:76px!important;padding:3px 1px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:#96979d!important;font-size:9px!important;font-weight:900!important;line-height:1.04!important;white-space:pre-line!important;text-align:center!important}.st-key-nav_intel button p,.st-key-nav_coach button p,.st-key-nav_mock button p,.st-key-nav_history button p{white-space:pre-line!important;text-align:center!important;line-height:1.04!important;margin:0!important;color:inherit!important;font-size:9px!important;font-weight:900!important}.st-key-nav_intel button p::first-line,.st-key-nav_coach button p::first-line,.st-key-nav_mock button p::first-line,.st-key-nav_history button p::first-line{font-size:27px!important;line-height:1.15!important}.st-key-nav_intel button[kind="primary"],.st-key-nav_coach button[kind="primary"],.st-key-nav_mock button[kind="primary"],.st-key-nav_history button[kind="primary"]{color:#fff!important;filter:drop-shadow(0 0 7px rgba(49,242,47,.45))!important}.st-key-nav_intel button[kind="primary"] p::first-line,.st-key-nav_coach button[kind="primary"] p::first-line,.st-key-nav_mock button[kind="primary"] p::first-line,.st-key-nav_history button[kind="primary"] p::first-line{color:var(--green)!important;text-shadow:0 0 7px rgba(49,242,47,.75)!important}
.stButton button{width:100%!important;min-height:48px!important;border-radius:14px!important;border:1px solid var(--line)!important;background:#242429!important;color:#fff!important;font-weight:900!important}[data-baseweb="select"]>div,[data-testid="stNumberInput"]>div>div,[data-testid="stTextInput"] input{background:#20232d!important;border:1px solid #303541!important;border-radius:14px!important;color:#fff!important;min-height:48px!important}[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:16px!important;background:#18181b!important;overflow:hidden!important;margin:10px 0!important}.hero{background:linear-gradient(145deg,#202126,#151518);border:1px solid var(--line);border-radius:20px;padding:17px;margin:10px 0 12px}.kicker{color:var(--green);font-size:10px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase}.hero-title{font-size:24px;font-weight:1000;line-height:1.08;margin-top:7px}.hero-sub{color:var(--muted);font-size:13px;line-height:1.45;margin-top:7px}.metric-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}.metric{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:11px;min-height:78px}.metric-label{color:#85868c;font-size:9px;font-weight:1000;text-transform:uppercase}.metric-value{color:#fff;font-size:19px;font-weight:1000;margin-top:15px}.green{color:var(--green)!important}.blue{color:var(--blue)!important}.red{color:var(--red)!important}.player-card,.support-row{display:grid;grid-template-columns:42px minmax(0,1fr) auto;gap:9px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;margin:7px 0}.pos,.support-year{font-weight:1000;color:var(--green)}.player,.support-name{font-size:13px;font-weight:1000}.meta,.support-meta{font-size:10px;color:var(--muted);line-height:1.35;margin-top:3px}.tag,.support-rank{font-size:10px;font-weight:1000;color:var(--blue);text-align:right}.report{background:#151518;border:1px solid var(--line);border-left:6px solid var(--green);border-radius:16px;padding:16px;margin:12px 0}.report-title{font-size:13px;font-weight:1000;color:#fff}.report-answer{color:var(--green);font-size:30px;font-weight:1000;line-height:1.05;margin-top:8px}.report-note{color:#d0d0d4;font-size:13px;font-weight:700;line-height:1.45;margin-top:8px}.takeaway{background:#171b17;border:1px solid #2c3b2c;border-radius:14px;padding:13px;margin:10px 0}.takeaway b{color:var(--green)!important}
@media(max-width:360px){.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_history button{font-size:8px!important;min-height:70px!important}.st-key-nav_intel button p,.st-key-nav_coach button p,.st-key-nav_mock button p,.st-key-nav_history button p{font-size:8px!important}.st-key-nav_intel button p::first-line,.st-key-nav_coach button p::first-line,.st-key-nav_mock button p::first-line,.st-key-nav_history button p::first-line{font-size:24px!important}}
</style>
""",
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_roi() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("SELECT * FROM draft_roi_scores", con)

@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    df = pd.read_csv(RANKINGS_PATH)
    df["adp"] = pd.to_numeric(df["adp"], errors="coerce")
    df["position_rank"] = pd.to_numeric(df.get("position_rank"), errors="coerce")
    return df.dropna(subset=["player_name", "position", "adp"]).copy()

@st.cache_data(show_spinner=False)
def load_births() -> pd.DataFrame:
    if not BIRTH_DATES_PATH.exists():
        return pd.DataFrame(columns=["name_key", "birth_date"])
    df = pd.read_csv(BIRTH_DATES_PATH)
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    return df.dropna(subset=["name_key", "birth_date"]).drop_duplicates("name_key")

@st.cache_resource(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    """Load only weekly columns used by Shiva/Mock Draft and share one in-memory frame.

    The full compressed master expands dramatically in RAM. Streamlit cache_data also
    serializes/copies the dataframe per session, which can push Community Cloud over its
    memory limit. cache_resource keeps one shared read-only dataframe and usecols avoids
    loading dozens of unused NFL stat columns.
    """
    if not WEEKLY_PATH.exists():
        return pd.DataFrame()
    header = pd.read_csv(WEEKLY_PATH, compression="gzip", nrows=0).columns.tolist()
    wanted = [
        "season", "week", "season_type", "player_id", "player_display_name",
        "player_name", "name", "position", "recent_team", "team",
        "fantasy_points_ppr", "fantasy_points", "targets", "receptions",
        "receiving_yards", "receiving_tds", "carries", "rushing_yards",
        "rushing_tds", "target_share", "red_zone_touches", "attempts",
        "passing_yards", "passing_tds", "interceptions"
    ]
    usecols = [c for c in wanted if c in header]
    return pd.read_csv(
        WEEKLY_PATH,
        compression="gzip",
        usecols=usecols or None,
        low_memory=False,
    )

roi = load_roi()
rankings = load_rankings()
births = load_births()
weekly = load_weekly()
for col in ["season", "round", "overall_pick", "position_draft_rank", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "final_draft_roi"]:
    if col in roi.columns:
        roi[col] = pd.to_numeric(roi[col], errors="coerce")
history = build_history_frame(roi, births)

def current_franchises() -> pd.DataFrame:
    latest = int(roi["season"].max())
    return roi[roi["season"].eq(latest)][["league_name", "team_id", "team_name", "manager_name"]].drop_duplicates(["league_name", "team_id"])

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
    return roi[roi.apply(lambda row: (row["league_name"], row["team_id"]) in keys, axis=1)].copy()

def context_selector(prefix: str) -> tuple[str, str, pd.DataFrame]:
    selector_cols = st.columns(2)
    with selector_cols[0]:
        scope = st.selectbox("League", ["Shiva", "Shiva 2.0", "Combined"], index=2, key=f"{prefix}_scope")
    managers = managers_for(scope)
    default = next((x for x in ["Chris H", "Chris Hart"] if x in managers), managers[0] if managers else "")
    with selector_cols[1]:
        manager = st.selectbox("Manager", managers, index=managers.index(default) if default in managers else 0, key=f"{prefix}_manager")
    return scope, manager, franchise_rows(manager, scope)

def snake_schedule(slot: int, teams: int, rounds: int = 16) -> list[dict[str, int]]:
    return [{"Round": r, "Overall": (r - 1) * teams + slot if r % 2 else r * teams - slot + 1} for r in range(1, rounds + 1)]

def player_fit(overall_pick: int, round_number: int) -> pd.DataFrame:
    pool = rankings.copy()
    before = 5 if round_number <= 3 else 7
    pool = pool[pool["adp"].between(max(1, overall_pick - before), overall_pick + 24)].copy()
    if pool.empty:
        return pool
    pool["distance"] = (pool["adp"] - overall_pick).abs()
    pool["availability"] = np.select([pool["adp"] >= overall_pick, pool["adp"] >= overall_pick - 2], ["Likely Available", "Possible Slide"], default="Longer Shot")
    pool["score"] = 100 - pool["distance"].clip(0, 25) * 3
    if round_number <= 3:
        pool.loc[pool["position"].isin(["RB", "WR"]), "score"] += 10
        pool.loc[pool["position"].eq("QB"), "score"] -= 12
        pool.loc[pool["position"].eq("TE"), "score"] -= 6
    elif round_number <= 6:
        pool.loc[pool["position"].isin(["RB", "WR"]), "score"] += 5
    else:
        pool.loc[pool["position"].isin(["QB", "TE"]), "score"] += 3
    pool["fit"] = np.select([pool["score"] >= 82, pool["score"] >= 70, pool["score"] >= 58], ["Best Available", "Strong Option", "Acceptable"], default="Reach")
    return pool.sort_values(["score", "adp"], ascending=[False, True]).reset_index(drop=True)

def build_plan(slot: int, teams: int = 10, rounds: int = 16) -> pd.DataFrame:
    selected: set[str] = set()
    roster = {"QB": 0, "RB": 0, "WR": 0, "TE": 0}
    output = []
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
        alts = options[options["player_name"].ne(choice["player_name"])].sort_values(["score", "adp"], ascending=[False, True]).head(3)
        output.append({"Round": rnd, "Pick": overall, "Player": str(choice["player_name"]), "Pos": pos, "ADP": float(choice["adp"]), "Alternatives": ", ".join(alts["player_name"].astype(str).tolist())})
    return pd.DataFrame(output)

def coach_profile(rows: pd.DataFrame) -> dict:
    premium = rows[rows["round"].between(1, 8)].copy()
    if premium.empty:
        return {"best_round": None, "worst_round": None, "best_pos": "—", "early_pos": "—"}
    premium["value"] = premium["position_draft_rank"] - premium["position_finish_total"]
    summary = premium.groupby("round").agg(Picks=("player_name", "count"), Value=("value", "mean"))
    eligible = summary[summary["Picks"].ge(max(3, math.ceil(rows["season"].nunique() * .4)))]
    if eligible.empty:
        eligible = summary
    pos_summary = premium.groupby("position").agg(Picks=("player_name", "count"), Value=("value", "mean"))
    early = premium[premium["round"].le(3)]["position"].value_counts()
    return {"best_round": int(eligible["Value"].idxmax()), "worst_round": int(eligible["Value"].idxmin()), "best_pos": str(pos_summary.sort_values(["Value", "Picks"], ascending=[False, False]).index[0]), "early_pos": str(early.index[0]) if not early.empty else "—"}

def render_report(report: dict) -> None:
    title = str(report.get("title") or "🧠 ASK SHIVA GPT").strip()
    answer = str(report.get("answer") or "").strip()
    why = str(
        report.get("why")
        or report.get("takeaway")
        or report.get("note")
        or ""
    ).strip()

    st.markdown(
        f"""
        <div style="background:linear-gradient(145deg,#17181c,#111214);border:1px solid #34363d;border-left:8px solid #31f22f;border-radius:20px;padding:24px 22px;margin:18px 0 14px;box-shadow:0 8px 28px rgba(0,0,0,.25);">
            <div style="color:#d8d8dc;font-size:13px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;margin-bottom:14px;">{title}</div>
            <div style="color:#31f22f;font-size:clamp(30px,8vw,46px);line-height:1.08;font-weight:1000;letter-spacing:-.02em;white-space:pre-wrap;">{answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if why:
        st.markdown(
            f"""
            <div style="background:linear-gradient(145deg,#1a1d1a,#121412);border:1px solid #324232;border-radius:20px;padding:22px;margin:14px 0 22px;">
                <div style="color:#31f22f;font-size:13px;font-weight:1000;letter-spacing:.10em;text-transform:uppercase;margin-bottom:13px;">WHY</div>
                <div style="color:#f5f5f6;font-size:17px;line-height:1.55;font-weight:600;white-space:pre-wrap;">{why}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="app-title">SHIVA DRAFT INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown('<div class="nav-label">Shiva Tools</div>', unsafe_allow_html=True)
TOOLS = [
    ("Shiva Intelligence", "📊\nShiva\nIntelligence", "intel"),
    ("Draft Coach", "📋\nDraft\nCoach", "coach"),
    ("Mock Draft", "🧩\nMock\nDraft", "mock"),
    ("Shiva League History", "🏛️\nLeague\nHistory", "history"),
]
if "page" not in st.session_state:
    st.session_state.page = "Shiva Intelligence"
if st.session_state.page in {"Live Draft", "Grade Draft"}:
    st.session_state.page = "Mock Draft" if st.session_state.page == "Live Draft" else "Shiva Intelligence"
for (name, label, key), col in zip(TOOLS, st.columns(4)):
    with col:
        if st.button(label, key=f"nav_{key}", use_container_width=True, type="primary" if st.session_state.page == name else "secondary"):
            st.session_state.page = name
            st.rerun()
page = st.session_state.page

if page == "Shiva Intelligence":
    st.markdown('<div class="hero"><div class="kicker">📊 Shiva Intelligence</div><div class="hero-title">Ask Shiva GPT</div><div class="hero-sub">Every answer below is calculated from the verified 2014-2025 history, current ESPN ADP, or league draft database. No preset fantasy verdicts.</div></div>', unsafe_allow_html=True)
    with st.form("shiva_intelligence_form", clear_on_submit=False):
        prompt = st.text_input("What do you want to know?", placeholder="Example: What is the average PPG for top 5 RBs since 2019?", key="shiva_prompt_dynamic")
        submitted = st.form_submit_button("ASK SHIVA GPT", use_container_width=True)
    try:
        secret_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        secret_key = ""
    configured_api_key = (
        str(os.environ.get("OPENAI_API_KEY", "")).strip()
        or secret_key
        or str(st.session_state.get("shiva_openai_api_key", "")).strip()
    )

    if not configured_api_key:
        with st.expander("Connect ChatGPT", expanded=True):
            entered_key = st.text_input(
                "OpenAI API key",
                type="password",
                placeholder="sk-...",
                help="Used only for this browser session. For permanent use, add OPENAI_API_KEY in Streamlit Cloud Secrets.",
                key="shiva_openai_api_key_input",
            )
            if entered_key.strip():
                st.session_state["shiva_openai_api_key"] = entered_key.strip()
                configured_api_key = entered_key.strip()
                st.success("Shiva GPT connected for this session.")

    if submitted:
        if not prompt.strip():
            st.warning("Type a question first.")
        elif not configured_api_key:
            st.error("ChatGPT needs an OpenAI API key. Add it above once, or set OPENAI_API_KEY in Streamlit Cloud Secrets for permanent use.")
        else:
            try:
                with st.spinner("Shiva GPT is analyzing the verified data..."):
                    st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(
                        question=prompt,
                        history=history,
                        roi=roi,
                        rankings=rankings,
                        weekly=weekly,
                        api_key=configured_api_key,
                    )
            except Exception as exc:
                st.error(f"ChatGPT connection failed: {exc}")
    report = st.session_state.get("shiva_report_dynamic")
    if report:
        render_report(report)

elif page == "Draft Coach":
    st.markdown('<div class="hero"><div class="kicker">📋 Draft Coach</div><div class="hero-title">Build Your 2026 Draft</div><div class="hero-sub">Coach Overview, Player Fit and Draft Plan all live here.</div></div>', unsafe_allow_html=True)
    scope, manager, rows = context_selector("coach")
    with st.expander("📋 Coach Overview", expanded=True):
        profile = coach_profile(rows)
        st.markdown(f'<div class="metric-grid"><div class="metric"><div class="metric-label">Early Identity</div><div class="metric-value green">{profile["early_pos"]}</div></div><div class="metric"><div class="metric-label">Best Round</div><div class="metric-value blue">R{profile["best_round"] or "—"}</div></div><div class="metric"><div class="metric-label">Protect</div><div class="metric-value red">R{profile["worst_round"] or "—"}</div></div></div>', unsafe_allow_html=True)
        st.write(f"Use {profile['best_pos']} only as a tiebreaker between similarly ranked players. In Round {profile['worst_round'] or '—'}, slow down and follow the highest remaining ADP tier.")
    with st.expander("🎯 Player Fit", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            teams = st.number_input("Teams", 8, 16, 10, 1, key="fit_teams")
        with cols[1]:
            slot = st.number_input("Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="fit_slot")
        with cols[2]:
            rnd = st.number_input("Round", 1, 16, 1, 1, key="fit_round")
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
        plan_cols = st.columns(2)
        with plan_cols[0]:
            teams = st.number_input("League Size", 8, 16, 10, 1, key="plan_teams")
        with plan_cols[1]:
            slot = st.number_input("Draft Slot", 1, int(teams), min(4, int(teams)), 1, key="plan_slot")
        for _, pick in build_plan(int(slot), int(teams), 16).iterrows():
            st.markdown(f'<div class="player-card"><div class="pos">R{int(pick["Round"])}</div><div><div class="player">{pick["Player"]} ({pick["Pos"]})</div><div class="meta">Pick {int(pick["Pick"])} · Alternatives: {pick["Alternatives"] or "—"}</div></div><div class="tag">ADP {pick["ADP"]:.1f}</div></div>', unsafe_allow_html=True)

elif page == "Mock Draft":
    # One centralized draft state powers both Players and Draft Board views.
    try:
        secret_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        secret_key = ""
    mock_api_key = (
        str(os.environ.get("OPENAI_API_KEY", "")).strip()
        or secret_key
        or str(st.session_state.get("shiva_openai_api_key", "")).strip()
    )
    render_mock_draft_room(
        rankings=rankings,
        weekly=weekly,
        history=history,
        roi=roi,
        db_path=DB_PATH,
        ask_shiva_func=ask_shiva_via_chatgpt,
        api_key=mock_api_key or None,
    )

else:
    st.markdown('<div class="hero"><div class="kicker">🏛️ Shiva League History</div><div class="hero-title">Search Historical Drafts</div><div class="hero-sub">Filter by league, current manager and season.</div></div>', unsafe_allow_html=True)
    scope, manager, rows = context_selector("history")
    history_cols = st.columns(2)
    seasons = sorted(rows["season"].dropna().astype(int).unique(), reverse=True)
    with history_cols[0]:
        season = st.selectbox("Season", ["All Seasons"] + [str(x) for x in seasons])
    with history_cols[1]:
        search = st.text_input("Search Player", placeholder="Optional player name")
    result = rows.copy()
    if season != "All Seasons":
        result = result[result["season"].eq(int(season))]
    if search.strip():
        result = result[result["player_name"].str.contains(search.strip(), case=False, na=False)]
    for _, pick in result.sort_values(["season", "round", "overall_pick"], ascending=[False, True, True]).head(200).iterrows():
        st.markdown(f'<div class="player-card"><div class="pos">R{int(pick["round"])}</div><div><div class="player">{pick["player_name"]} ({pick["position"]})</div><div class="meta">{int(pick["season"])} · {pick["league_name"]} · Pick {int(pick["overall_pick"])} · Final {pick["position_finish_total"]}</div></div><div class="tag">{float(pick["ppg"]):.1f} PPG</div></div>', unsafe_allow_html=True)

# ============================================================
# LIVE ESPN FANTASY NEWS — SERVER-SIDE SERVICE + LAST-GOOD CACHE
# ============================================================
from html import escape

st.markdown("---")
st.markdown(
    """
    <div style="margin:8px 0 12px 0;">
      <div style="color:#31f22f;font-size:11px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;">📰 LIVE ESPN NFL NEWS</div>
      <div style="color:#fff;font-size:24px;font-weight:1000;line-height:1.05;margin-top:5px;">Fantasy-Relevant Headlines</div>
    </div>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=600, show_spinner=False)
def load_espn_news_backend() -> list[dict[str, str]]:
    return fetch_espn_news(limit=8)

articles = load_espn_news_backend()
if articles:
    for row_start in range(0, min(len(articles), 8), 2):
        news_cols = st.columns(2)
        for col_index, article in enumerate(articles[row_start:row_start + 2]):
            with news_cols[col_index]:
                title = escape(str(article.get("title") or "ESPN NFL Update"))
                description = escape(str(article.get("description") or ""))
                published = escape(str(article.get("published") or ""))
                article_url = escape(str(article.get("link") or "https://www.espn.com/nfl/"), quote=True)
                thumbnail = escape(str(article.get("thumbnail") or ""), quote=True)
                short_description = description[:135] + ("..." if len(description) > 135 else "")
                image_html = (
                    f'<div style="width:100%;height:112px;overflow:hidden;border-radius:12px;margin-bottom:11px;background:#101114;">'
                    f'<img src="{thumbnail}" alt="" loading="lazy" referrerpolicy="no-referrer" '
                    f'style="width:100%;height:100%;object-fit:cover;display:block;" />'
                    f'</div>'
                    if thumbnail else
                    '<div style="height:54px;border-radius:12px;margin-bottom:11px;background:linear-gradient(135deg,#202f42,#141922);display:flex;align-items:center;justify-content:center;color:#31f22f;font-size:22px;font-weight:1000;">ESPN</div>'
                )
                st.markdown(
                    f"""
                    <div style="background:linear-gradient(145deg,#202126,#151518);border:1px solid #34343a;border-radius:16px;padding:12px;min-height:290px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 8px 24px rgba(0,0,0,.22);margin-bottom:10px;overflow:hidden;">
                      <div>
                        {image_html}
                        <div style="color:#31f22f;font-size:9px;font-weight:1000;letter-spacing:.08em;text-transform:uppercase;margin-bottom:7px;">ESPN NFL</div>
                        <div style="color:#fff;font-size:14px;font-weight:950;line-height:1.25;">{title}</div>
                        <div style="color:#a7a8ad;font-size:10px;margin-top:7px;">{published}</div>
                        <div style="color:#d4d4d7;font-size:11px;line-height:1.4;margin-top:9px;">{short_description}</div>
                      </div>
                      <a href="{article_url}" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:14px;padding:11px 8px;border-radius:10px;background:#31f22f;color:#071007!important;text-decoration:none;text-align:center;font-size:10px;font-weight:1000;letter-spacing:.04em;">OPEN ON ESPN</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info("ESPN news could not be refreshed and no last-good cached headlines are available yet. The backend logs contain the request/parsing failure details.")
