from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from draft_decision_engine import build_today_edge, canonical_draft_state


def shared_draft_state(rankings: pd.DataFrame) -> dict[str, Any]:
    """Return the single app-facing draft state, preserving the live mock object by reference."""
    raw = st.session_state.get("mock_draft_state_v2") or st.session_state.get("draft_state") or {}
    canonical = canonical_draft_state(raw, rankings)
    st.session_state["draft_state"] = canonical
    return canonical


def _render_premium_global_css() -> None:
    """Large, touch-first, high-contrast visual system designed for a phone screen."""
    st.markdown(
        """
<style>
:root{
  --shiva-bg:#07090b;
  --shiva-surface:#14191f;
  --shiva-surface-2:#1b222a;
  --shiva-border:#34404d;
  --shiva-text:#f8fafc;
  --shiva-muted:#b3bdc8;
  --shiva-green:#39ff53;
  --shiva-blue:#64a8ff;
  --shiva-red:#ff6874;
  --shiva-orange:#ffb84d;
}

html,body,.stApp{
  background:radial-gradient(circle at 50% -10%,#121923 0,#090c10 34%,#07090b 72%)!important;
  color:var(--shiva-text)!important;
}
.block-container{max-width:680px!important;padding:14px 16px 80px!important}

/* Phone-first readable baseline. Never let important text fall back to tiny Streamlit defaults. */
p,li,label,[data-testid="stCaptionContainer"],.stMarkdown,.stMarkdown p{
  font-size:18px!important;
  line-height:1.5!important;
}
[data-testid="stCaptionContainer"]{color:var(--shiva-muted)!important;font-size:16px!important}
h1{font-size:36px!important} h2{font-size:30px!important} h3{font-size:24px!important}
.app-title{font-size:28px!important;font-weight:1000!important;margin:8px 0 12px!important}
.nav-label{font-size:14px!important;color:#aab4bf!important;margin:8px 0 8px!important;letter-spacing:.08em!important}

/* NAVIGATION: force a 2x2 grid so labels/icons can be large and all four remain visible. */
div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel){
  display:flex!important;
  flex-wrap:wrap!important;
  gap:10px!important;
  width:100%!important;
  margin-bottom:8px!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel)>div{
  flex:0 0 calc(50% - 5px)!important;
  width:calc(50% - 5px)!important;
  min-width:0!important;
}
.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_history button{
  width:100%!important;
  min-height:102px!important;
  padding:10px 8px!important;
  border:1px solid #303944!important;
  border-radius:20px!important;
  background:linear-gradient(145deg,#171d23,#0f1317)!important;
  box-shadow:0 8px 24px rgba(0,0,0,.24)!important;
  color:#d6dce3!important;
  font-size:15px!important;
  font-weight:1000!important;
  line-height:1.18!important;
  white-space:pre-line!important;
  text-align:center!important;
}
.st-key-nav_intel button p,.st-key-nav_coach button p,.st-key-nav_mock button p,.st-key-nav_history button p{
  white-space:pre-line!important;
  text-align:center!important;
  line-height:1.18!important;
  margin:0!important;
  color:inherit!important;
  font-size:15px!important;
  font-weight:1000!important;
}
.st-key-nav_intel button p::first-line,.st-key-nav_coach button p::first-line,.st-key-nav_mock button p::first-line,.st-key-nav_history button p::first-line{
  font-size:38px!important;
  line-height:1.25!important;
}
.st-key-nav_intel button[kind="primary"],.st-key-nav_coach button[kind="primary"],.st-key-nav_mock button[kind="primary"],.st-key-nav_history button[kind="primary"]{
  background:linear-gradient(145deg,rgba(57,255,83,.18),rgba(21,62,31,.35))!important;
  border-color:rgba(57,255,83,.72)!important;
  box-shadow:0 0 0 1px rgba(57,255,83,.12),0 0 28px rgba(57,255,83,.18)!important;
  color:#fff!important;
}

/* All controls should feel like native phone controls, not tiny web widgets. */
.stButton button{
  min-height:60px!important;
  border-radius:16px!important;
  padding:10px 14px!important;
  font-size:18px!important;
  font-weight:950!important;
  letter-spacing:.01em!important;
  border:1px solid #414d5a!important;
  background:linear-gradient(180deg,#28313a,#1b2229)!important;
  color:#fff!important;
  box-shadow:0 7px 20px rgba(0,0,0,.28)!important;
}
.stButton button p{font-size:18px!important;font-weight:950!important}
.stButton button:hover{border-color:#748191!important;transform:translateY(-1px)}
.stButton button[kind="primary"]{
  background:linear-gradient(135deg,#46ff5d,#23d83c)!important;
  color:#061108!important;
  border-color:#70ff81!important;
  box-shadow:0 10px 28px rgba(57,255,83,.24)!important;
}
.stButton button[kind="primary"] p{color:#061108!important}

[data-baseweb="select"]>div,
[data-testid="stNumberInput"]>div>div,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea{
  min-height:58px!important;
  border-radius:16px!important;
  font-size:18px!important;
  line-height:1.45!important;
  background:#151b21!important;
  border:1px solid #414d59!important;
  color:#fff!important;
}
[data-testid="stTextArea"] textarea{min-height:112px!important;padding:14px!important}
[data-testid="stTextInput"] input{padding:0 14px!important}
[data-testid="stWidgetLabel"] p{font-size:17px!important;font-weight:850!important}

[data-testid="stExpander"]{
  border-radius:18px!important;
  border:1px solid #394552!important;
  background:linear-gradient(145deg,#12171c,#0e1216)!important;
  margin:12px 0!important;
  overflow:hidden!important;
}
[data-testid="stExpander"] summary{font-size:18px!important;font-weight:950!important;padding:8px 5px!important}

/* Hero / section surfaces */
.hero{
  padding:22px!important;
  margin:14px 0 16px!important;
  border-radius:24px!important;
  background:linear-gradient(145deg,#222c36,#12171d)!important;
  border:1px solid #44515f!important;
  box-shadow:0 14px 36px rgba(0,0,0,.32)!important;
}
.kicker{font-size:15px!important;letter-spacing:.09em!important;color:var(--shiva-green)!important}
.hero-title{font-size:36px!important;line-height:1.08!important;margin-top:9px!important;font-weight:1000!important}
.hero-sub{font-size:18px!important;line-height:1.5!important;color:#c1cad4!important;margin-top:10px!important}

/* Metrics and player/supporting rows */
.metric-grid{display:grid!important;grid-template-columns:1fr 1fr!important;gap:12px!important;margin:14px 0!important}
.metric{padding:18px!important;min-height:112px!important;border-radius:18px!important;background:linear-gradient(145deg,#182027,#11171c)!important;border:1px solid #37434f!important}
.metric-label{font-size:13px!important;color:#a5afbb!important;letter-spacing:.06em!important}
.metric-value{font-size:28px!important;margin-top:18px!important;line-height:1.1!important}
.player-card,.support-row{padding:17px!important;margin:11px 0!important;border-radius:18px!important;gap:13px!important;background:linear-gradient(145deg,#171f26,#11171c)!important;border:1px solid #35414d!important}
.player,.support-name{font-size:19px!important;line-height:1.28!important;font-weight:1000!important}
.meta,.support-meta{font-size:16px!important;line-height:1.45!important;color:#b4bec9!important;margin-top:5px!important}
.tag,.support-rank{font-size:15px!important}.pos,.support-year{font-size:15px!important}

/* Shiva answers should be visually dominant. */
.report{
  padding:22px!important;
  border-radius:22px!important;
  border:1px solid #34523d!important;
  border-left:8px solid var(--shiva-green)!important;
  background:linear-gradient(145deg,#142018,#0d1310)!important;
  box-shadow:0 10px 30px rgba(0,0,0,.25)!important;
}
.report-title{font-size:16px!important;letter-spacing:.05em!important;color:#d8f8dd!important}
.report-answer{font-size:36px!important;line-height:1.12!important;margin-top:11px!important;color:var(--shiva-green)!important}
.report-note{font-size:18px!important;line-height:1.55!important;margin-top:12px!important;color:#e2e8ee!important}

/* Draft command bar: always readable, never a tiny strip. */
.draft-command{background:linear-gradient(145deg,#19242d,#10161c)!important;border:1px solid #42505e!important;border-radius:20px!important;padding:14px!important;margin:8px 0 16px!important;box-shadow:0 10px 28px rgba(0,0,0,.28)!important}
.draft-command-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important}
.draft-command-cell{background:#0e1419!important;border:1px solid #303c47!important;border-radius:14px!important;padding:11px!important;min-width:0!important}
.draft-command-label{font-size:12px!important;color:#9ca7b3!important;letter-spacing:.07em!important;text-transform:uppercase!important}
.draft-command-value{font-size:18px!important;line-height:1.25!important;margin-top:5px!important;color:#fff!important;font-weight:1000!important;white-space:normal!important}
.draft-command-roster{font-size:17px!important;line-height:1.4!important;margin-top:12px!important;padding-top:11px!important;color:var(--shiva-green)!important;border-top:1px solid #34404b!important;font-weight:950!important}

/* TODAY'S DRAFT EDGE: full-width cards by design. No three-column squeeze anywhere. */
.edge-label{font-size:16px!important;margin:20px 0 10px!important;color:var(--shiva-green)!important;letter-spacing:.08em!important}
.edge-grid{display:grid!important;grid-template-columns:1fr!important;gap:12px!important;width:100%!important}
.edge-card{padding:18px!important;border-radius:20px!important;background:linear-gradient(145deg,#1a222a,#11171c)!important;border:1px solid #3b4753!important;box-shadow:0 8px 24px rgba(0,0,0,.24)!important}
.edge-kind{font-size:14px!important;font-weight:1000!important;letter-spacing:.055em!important}.edge-title{font-size:22px!important;line-height:1.2!important;margin-top:9px!important;font-weight:1000!important}.edge-text{font-size:17px!important;line-height:1.5!important;margin-top:8px!important;color:#ccd4dc!important}

/* Mock draft — large enough to use during a timed pick on a phone. */
.mock-topbar{gap:10px!important;margin:12px 0!important;grid-template-columns:1fr 1fr!important}
.mock-chip{padding:14px!important;border-radius:16px!important;background:#171f27!important;border-color:#40505e!important;min-height:88px!important}
.mock-chip-label{font-size:12px!important;color:#a0abb7!important}.mock-chip-value{font-size:22px!important;line-height:1.15!important;margin-top:7px!important}
.mock-section-title{font-size:20px!important;margin:22px 0 10px!important}.mock-subtle{font-size:16px!important;line-height:1.5!important;color:#b6c0ca!important}
.mock-list-head{font-size:12px!important;padding:11px 8px!important;grid-template-columns:42px minmax(0,1fr) 58px 64px!important;border-radius:16px 16px 0 0!important}
.mock-rank{font-size:15px!important}.mock-player-name{font-size:18px!important;line-height:1.25!important}.mock-player-meta{font-size:15px!important;line-height:1.4!important;margin-top:5px!important}
.mock-pos{font-size:13px!important;padding:7px 8px!important;min-width:44px!important;border-radius:10px!important}
.mock-rec{gap:11px!important;padding:5px 0 12px!important}.mock-rec-card{flex:0 0 190px!important;padding:15px!important;border-radius:18px!important;background:#171f27!important}
.mock-roster-row{grid-template-columns:48px minmax(0,1fr)!important;gap:10px!important;padding:12px 0!important}.mock-roster-slot{font-size:13px!important}.mock-roster-name{font-size:17px!important}
.mock-history{font-size:16px!important;line-height:1.45!important;padding:11px 0!important}
.mock-board-head{font-size:13px!important;min-height:48px!important}.mock-board-cell{min-height:86px!important;padding:9px!important}.mock-pick-no{font-size:11px!important}.mock-pick-player{font-size:14px!important;line-height:1.25!important}.mock-pick-meta{font-size:12px!important;line-height:1.3!important}
.mock-board-legend{gap:9px!important;margin:12px 0!important}.mock-legend-item{font-size:13px!important;padding:7px 10px!important}

[data-baseweb="tab"] p,[role="radiogroup"] label p,[data-testid="stSegmentedControl"] button p{font-size:16px!important}
[data-testid="stSegmentedControl"] button{min-height:52px!important;padding:9px 11px!important}
[data-testid="stProgress"] p{font-size:16px!important}

/* Streamlit often gives columns widths that are too narrow on mobile. Keep important rows spacious. */
@media(max-width:760px){
  .block-container{max-width:100%!important;padding:12px 14px 72px!important}
  .hero-title{font-size:34px!important}
  .report-answer{font-size:34px!important}
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_command_bar(rankings: pd.DataFrame) -> dict[str, Any]:
    _render_premium_global_css()
    state = shared_draft_state(rankings)
    counts = state.get("roster_counts", {})
    active = bool(state.get("drafted_players")) or state.get("status") in {"active", "complete"}
    fmt = f"{state['teams']}-Team • {state['scoring']} • Pick {state['draft_position']}"
    if active:
        cells = [
            ("FORMAT", fmt),
            ("ROUND", state.get("current_pick_label") or "—"),
            ("NEXT PICK", state.get("next_user_pick_label") or "—"),
            ("ON CLOCK", f"Team {state.get('current_team', '—')}"),
        ]
    else:
        cells = [("FORMAT", fmt)]
    cell_html = "".join(
        f'<div class="draft-command-cell"><div class="draft-command-label">{html.escape(str(label))}</div><div class="draft-command-value">{html.escape(str(value))}</div></div>'
        for label, value in cells
    )
    roster = f"RB {counts.get('RB', 0)} | WR {counts.get('WR', 0)} | QB {counts.get('QB', 0)} | TE {counts.get('TE', 0)}"
    st.markdown(
        f'<div class="draft-command"><div class="draft-command-grid">{cell_html}</div><div class="draft-command-roster">MY ROSTER: {html.escape(roster)}</div></div>',
        unsafe_allow_html=True,
    )
    return state


def _card(card: dict[str, Any]) -> str:
    tone = {
        "green": "#39ff53",
        "blue": "#64a8ff",
        "red": "#ff6874",
        "orange": "#ffb84d",
    }.get(str(card.get("tone")), "#39ff53")
    return (
        f'<div class="edge-card" style="border-top:5px solid {tone}">'
        f'<div class="edge-kind" style="color:{tone}">{html.escape(str(card.get("icon") or ""))} {html.escape(str(card.get("kind") or "DRAFT EDGE"))}</div>'
        f'<div class="edge-title">{html.escape(str(card.get("title") or ""))}</div>'
        f'<div class="edge-text">{html.escape(str(card.get("text") or ""))}</div>'
        '</div>'
    )


def render_today_edge(rankings: pd.DataFrame, roi: pd.DataFrame, state: dict[str, Any]) -> None:
    cards = build_today_edge(rankings, roi, state, max_cards=6)
    st.markdown('<div class="edge-label">TODAY\'S DRAFT EDGE</div>', unsafe_allow_html=True)
    if not cards:
        st.caption("Draft-edge cards will appear when current ADP and comparable historical rows support them.")
        return
    st.markdown('<div class="edge-grid">' + "".join(_card(c) for c in cards[:3]) + '</div>', unsafe_allow_html=True)
    if len(cards) > 3:
        with st.expander("See More Insights", expanded=False):
            st.markdown('<div class="edge-grid">' + "".join(_card(c) for c in cards[3:]) + '</div>', unsafe_allow_html=True)
