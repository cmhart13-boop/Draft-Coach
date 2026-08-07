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
    # draft_state is the shared app-facing contract. The live mock remains the source object
    # while it is active; canonical fields are rebuilt on every rerun so all pages see it.
    st.session_state["draft_state"] = canonical
    return canonical


def render_command_bar(rankings: pd.DataFrame) -> dict[str, Any]:
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
        f"""
<style>
.draft-command{{background:#151619;border:1px solid #303238;border-radius:12px;padding:8px;margin:1px 0 10px}}
.draft-command-grid{{display:grid;grid-template-columns:repeat({min(4, len(cells))},minmax(0,1fr));gap:5px}}
.draft-command-cell{{min-width:0}}
.draft-command-label{{color:#777a82;font-size:7px;font-weight:1000;letter-spacing:.08em;text-transform:uppercase}}
.draft-command-value{{color:#f7f7f8;font-size:9px;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}}
.draft-command-roster{{border-top:1px solid #292b31;color:#31f22f;font-size:9px;font-weight:900;margin-top:7px;padding-top:6px}}
@media(max-width:360px){{.draft-command-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style>
<div class="draft-command"><div class="draft-command-grid">{cell_html}</div><div class="draft-command-roster">MY ROSTER: {html.escape(roster)}</div></div>
""",
        unsafe_allow_html=True,
    )
    return state


def _card(card: dict[str, Any]) -> str:
    tone = {
        "green": "#31f22f",
        "blue": "#67a0ff",
        "red": "#ff5c66",
        "orange": "#ffb84d",
    }.get(str(card.get("tone")), "#31f22f")
    return (
        f'<div class="edge-card" style="border-top:3px solid {tone}">'
        f'<div class="edge-kind" style="color:{tone}">{html.escape(str(card.get("icon") or ""))} {html.escape(str(card.get("kind") or "DRAFT EDGE"))}</div>'
        f'<div class="edge-title">{html.escape(str(card.get("title") or ""))}</div>'
        f'<div class="edge-text">{html.escape(str(card.get("text") or ""))}</div>'
        '</div>'
    )


def render_today_edge(rankings: pd.DataFrame, roi: pd.DataFrame, state: dict[str, Any]) -> None:
    cards = build_today_edge(rankings, roi, state, max_cards=6)
    st.markdown(
        """
<style>
.edge-label{color:#31f22f;font-size:10px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;margin:12px 0 6px}
.edge-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}
.edge-card{background:#1b1c20;border:1px solid #32343b;border-radius:12px;padding:10px;min-width:0}
.edge-kind{font-size:8px;font-weight:1000;letter-spacing:.06em}.edge-title{color:#fff;font-size:12px;font-weight:1000;margin-top:6px}.edge-text{color:#b8bac0;font-size:9px;line-height:1.35;margin-top:5px}
@media(max-width:430px){.edge-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.edge-card{padding:8px}.edge-title{font-size:10px}.edge-text{font-size:8px}}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="edge-label">TODAY\'S DRAFT EDGE</div>', unsafe_allow_html=True)
    if not cards:
        st.caption("Draft-edge cards will appear when current ADP and comparable historical rows support them.")
        return
    st.markdown('<div class="edge-grid">' + "".join(_card(c) for c in cards[:3]) + '</div>', unsafe_allow_html=True)
    if len(cards) > 3:
        with st.expander("See More Insights", expanded=False):
            st.markdown('<div class="edge-grid">' + "".join(_card(c) for c in cards[3:]) + '</div>', unsafe_allow_html=True)
