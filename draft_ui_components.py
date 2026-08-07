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
    """Readable, high-contrast mobile-first visual system for the full Shiva app."""
    st.markdown(
        """
<style>
:root{
  --shiva-bg:#090b0d;
  --shiva-surface:#15191d;
  --shiva-surface-2:#1b2026;
  --shiva-border:#313944;
  --shiva-text:#f8fafc;
  --shiva-muted:#aeb6c1;
  --shiva-green:#39ff53;
  --shiva-blue:#6aa8ff;
  --shiva-red:#ff6570;
  --shiva-orange:#ffb84d;
}

html,body,.stApp{background:var(--shiva-bg)!important;color:var(--shiva-text)!important}
.block-container{max-width:540px!important;padding:12px 14px 64px!important}
p,li,label,[data-testid="stCaptionContainer"]{font-size:15px!important;line-height:1.45!important}
[data-testid="stCaptionContainer"]{color:var(--shiva-muted)!important}

.app-title{font-size:22px!important;letter-spacing:.01em!important;margin:6px 0 9px!important}
.nav-label{font-size:11px!important;color:#98a1ac!important;margin:6px 0 5px!important}
.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_history button{
  min-height:82px!important;
  padding:7px 4px!important;
  border:1px solid transparent!important;
  border-radius:14px!important;
  font-size:11px!important;
  line-height:1.12!important;
  color:#c2c8d0!important;
}
.st-key-nav_intel button p,.st-key-nav_coach button p,.st-key-nav_mock button p,.st-key-nav_history button p{
  font-size:11px!important;line-height:1.12!important
}
.st-key-nav_intel button p::first-line,.st-key-nav_coach button p::first-line,.st-key-nav_mock button p::first-line,.st-key-nav_history button p::first-line{
  font-size:30px!important;line-height:1.2!important
}
.st-key-nav_intel button[kind="primary"],.st-key-nav_coach button[kind="primary"],.st-key-nav_mock button[kind="primary"],.st-key-nav_history button[kind="primary"]{
  background:linear-gradient(180deg,rgba(57,255,83,.13),rgba(57,255,83,.04))!important;
  border-color:rgba(57,255,83,.48)!important;
  box-shadow:0 0 22px rgba(57,255,83,.13)!important;
}

.stButton button{
  min-height:54px!important;
  border-radius:14px!important;
  font-size:15px!important;
  letter-spacing:.01em!important;
  border:1px solid #3a424d!important;
  background:linear-gradient(180deg,#252b32,#1c2127)!important;
  box-shadow:0 5px 16px rgba(0,0,0,.22)!important;
}
.stButton button:hover{border-color:#697483!important;transform:translateY(-1px)}
.stButton button[kind="primary"]{
  background:linear-gradient(135deg,#39ff53,#20d83b)!important;
  color:#071008!important;
  border-color:#59ff6e!important;
  box-shadow:0 8px 24px rgba(57,255,83,.2)!important;
}
.stButton button[kind="primary"] p{color:#071008!important;font-weight:1000!important}

[data-baseweb="select"]>div,[data-testid="stNumberInput"]>div>div,[data-testid="stTextInput"] input{
  min-height:52px!important;
  border-radius:14px!important;
  font-size:15px!important;
  background:#171c22!important;
  border:1px solid #39414c!important;
}
[data-testid="stExpander"]{
  border-radius:16px!important;
  border:1px solid #343d48!important;
  background:#12161a!important;
  margin:10px 0!important;
}
[data-testid="stExpander"] summary{font-size:15px!important;font-weight:900!important;padding:4px 2px!important}

.hero{
  padding:18px!important;
  border-radius:20px!important;
  background:linear-gradient(145deg,#202730,#13171b)!important;
  border:1px solid #3b4552!important;
  box-shadow:0 10px 30px rgba(0,0,0,.28)!important;
}
.kicker{font-size:12px!important;letter-spacing:.1em!important}
.hero-title{font-size:28px!important;line-height:1.08!important;margin-top:7px!important}
.hero-sub{font-size:15px!important;line-height:1.5!important;color:#bac2cc!important}

.metric-grid{gap:10px!important}
.metric{padding:14px!important;min-height:92px!important;border-radius:16px!important;background:#171c21!important}
.metric-label{font-size:11px!important;color:#9ea7b2!important}
.metric-value{font-size:23px!important;margin-top:15px!important}
.player-card,.support-row{padding:14px!important;margin:9px 0!important;border-radius:16px!important;gap:11px!important;background:#171c21!important}
.player,.support-name{font-size:16px!important;line-height:1.25!important}
.meta,.support-meta{font-size:13px!important;line-height:1.45!important;color:#aeb6c1!important}
.tag,.support-rank{font-size:12px!important}
.pos,.support-year{font-size:13px!important}
.report{padding:18px!important;border-radius:18px!important;border-left-width:7px!important;background:linear-gradient(145deg,#151b18,#101412)!important}
.report-title{font-size:13px!important;letter-spacing:.05em!important}
.report-answer{font-size:34px!important;line-height:1.08!important;margin-top:9px!important}
.report-note{font-size:15px!important;line-height:1.5!important;margin-top:10px!important}

/* Draft command bar */
.draft-command{background:linear-gradient(145deg,#182027,#11161b)!important;border:1px solid #3b4652!important;border-radius:16px!important;padding:12px!important;margin:5px 0 14px!important;box-shadow:0 8px 24px rgba(0,0,0,.24)!important}
.draft-command-grid{gap:9px!important}
.draft-command-cell{background:#10151a!important;border:1px solid #2d3742!important;border-radius:11px!important;padding:8px!important}
.draft-command-label{font-size:10px!important;color:#8f99a5!important}
.draft-command-value{font-size:14px!important;margin-top:4px!important}
.draft-command-roster{font-size:13px!important;margin-top:10px!important;padding-top:9px!important;color:var(--shiva-green)!important}

/* Today's Draft Edge */
.edge-label{font-size:13px!important;margin:16px 0 8px!important}
.edge-grid{gap:10px!important}
.edge-card{padding:14px!important;border-radius:16px!important;background:linear-gradient(145deg,#1a2026,#12171b)!important;box-shadow:0 6px 18px rgba(0,0,0,.2)!important}
.edge-kind{font-size:11px!important}.edge-title{font-size:17px!important;margin-top:8px!important}.edge-text{font-size:14px!important;line-height:1.45!important;margin-top:7px!important;color:#c2c9d1!important}

/* Mock draft — override the older tiny type scale */
.mock-topbar{gap:9px!important;margin:10px 0!important}
.mock-chip{padding:11px!important;border-radius:14px!important;background:#171d23!important;border-color:#3b4551!important}
.mock-chip-label{font-size:10px!important;color:#98a2ae!important}
.mock-chip-value{font-size:18px!important;margin-top:5px!important}
.mock-section-title{font-size:16px!important;margin:18px 0 8px!important}
.mock-subtle{font-size:13px!important;line-height:1.45!important;color:#aeb6c1!important}
.mock-list-head{font-size:10px!important;padding:9px 8px!important;grid-template-columns:38px minmax(0,1fr) 52px 58px!important;border-radius:14px 14px 0 0!important}
.mock-rank{font-size:13px!important}
.mock-player-name{font-size:15px!important;line-height:1.2!important}
.mock-player-meta{font-size:12px!important;line-height:1.35!important;margin-top:4px!important}
.mock-pos{font-size:11px!important;padding:6px 7px!important;min-width:40px!important;border-radius:9px!important}
.mock-rec{gap:10px!important;padding:4px 0 10px!important}
.mock-rec-card{flex:0 0 164px!important;padding:12px!important;border-radius:15px!important;background:#171d23!important}
.mock-roster-row{grid-template-columns:42px minmax(0,1fr)!important;gap:9px!important;padding:10px 0!important}
.mock-roster-slot{font-size:11px!important}.mock-roster-name{font-size:14px!important}
.mock-history{font-size:13px!important;line-height:1.4!important;padding:9px 0!important}
.mock-board-head{font-size:11px!important;min-height:44px!important}
.mock-board-cell{min-height:80px!important;padding:8px!important}
.mock-pick-no{font-size:10px!important}.mock-pick-player{font-size:12px!important;line-height:1.2!important}.mock-pick-meta{font-size:10px!important;line-height:1.25!important}
.mock-board-legend{gap:8px!important;margin:10px 0!important}.mock-legend-item{font-size:11px!important;padding:6px 9px!important}

/* Make Streamlit control labels, tabs, segmented controls and radio text readable */
[data-testid="stWidgetLabel"] p,[data-baseweb="tab"] p,[role="radiogroup"] label p,[data-testid="stSegmentedControl"] button p{font-size:14px!important}
[data-testid="stSegmentedControl"] button{min-height:46px!important;padding:7px 9px!important}
[data-testid="stProgress"] p{font-size:13px!important}

@media(max-width:430px){
  .block-container{padding:10px 12px 58px!important}
  .edge-grid{grid-template-columns:1fr!important}
  .draft-command-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  .hero-title{font-size:26px!important}
  .report-answer{font-size:30px!important}
  .mock-rec-card{flex-basis:156px!important}
}

@media(max-width:350px){
  div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel){flex-wrap:wrap!important;gap:5px!important}
  div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel)>div{flex:0 0 calc(50% - 3px)!important;width:calc(50% - 3px)!important}
  .st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_history button{min-height:70px!important}
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
        "blue": "#6aa8ff",
        "red": "#ff6570",
        "orange": "#ffb84d",
    }.get(str(card.get("tone")), "#39ff53")
    return (
        f'<div class="edge-card" style="border-top:4px solid {tone}">'
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
