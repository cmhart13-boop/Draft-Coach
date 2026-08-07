from pathlib import Path

path = Path("mock_draft_ui.py")
text = path.read_text(encoding="utf-8")

# Streamlit's fragment cadence should use a duration string.  Also make the
# timer patch idempotent so CI can safely run it on an already-integrated app.
text = text.replace("@st.fragment(run_every=1)\n", "@st.fragment(run_every=\"1s\")\n")

if "def _live_timer_fragment() -> None:\n" not in text:
    start = text.find("def _render_timer(state: dict[str, Any]) -> None:\n")
    end = text.find("\ndef _render_controls", start)
    if start == -1 or end == -1:
        raise SystemExit(f"Timer function boundaries not found: {start=} {end=}")
    new = '''@st.fragment(run_every="1s")
def _live_timer_fragment() -> None:
    """Refresh the user clock every second without resetting centralized draft state."""
    state = st.session_state.get(_state_key())
    if not state:
        return
    remain = timer_remaining(state)
    st.progress(remain / max(1, int(state["settings"]["secondsPerPick"])), text=f"⏱️ {remain}s")
    if state["status"] == "active" and not state["paused"] and state["currentTeam"] == state["userTeamId"] and remain <= 0:
        auto_pick_user(state)
        advance_cpu_until_user(state)
        st.session_state[_state_key()] = state
        st.rerun()
'''
    text = text[:start] + new + text[end:]

text = text.replace("    _render_timer(state)\n", "    _live_timer_fragment()\n")
path.write_text(text, encoding="utf-8")
print("Streamlit-compatible live mock draft timer integrated.")
