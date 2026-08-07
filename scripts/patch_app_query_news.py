from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ROUTER = ROOT / "shiva_query_router.py"

text = APP.read_text(encoding="utf-8")

# Keep the deterministic data router as the evidence layer, but make ChatGPT the
# conversational Ask Shiva response layer.
if "from shiva_chatgpt_service import ask_shiva_via_chatgpt\n" not in text:
    text = text.replace(
        "from shiva_query_router import run_shiva_query\n",
        "from shiva_query_router import run_shiva_query\nfrom shiva_chatgpt_service import ask_shiva_via_chatgpt\n",
    )

old_submit = '''    if submitted:\n        if prompt.strip():\n            st.session_state["shiva_report_dynamic"] = run_shiva_query(prompt, history, roi, rankings, weekly)\n        else:\n            st.warning("Type a report request first.")\n'''

new_submit = '''    if submitted:\n        if prompt.strip():\n            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n            if not api_key:\n                st.error("Ask Shiva is ready to use ChatGPT, but OPENAI_API_KEY has not been added to this app's Streamlit secrets yet.")\n            else:\n                try:\n                    with st.spinner("Shiva is analyzing the verified data..."):\n                        st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                            question=prompt,\n                            history=history,\n                            roi=roi,\n                            rankings=rankings,\n                            weekly=weekly,\n                            api_key=api_key,\n                        )\n                except Exception as exc:\n                    st.error(f"Ask Shiva could not reach ChatGPT right now: {exc}")\n        else:\n            st.warning("Type a question first.")\n'''

if old_submit in text:
    text = text.replace(old_submit, new_submit)
elif "ask_shiva_via_chatgpt(" not in text:
    raise RuntimeError("Could not locate the Ask Shiva submit block to replace safely.")

APP.write_text(text, encoding="utf-8")

# Preserve the weekly-data player-name preference used by the deterministic evidence layer.
router = ROUTER.read_text(encoding="utf-8")
router = router.replace(
    'name_col = _column(weekly, "player_name", "player_display_name", "name", "player")',
    'name_col = _column(weekly, "player_display_name", "player_name", "name", "player")',
)
ROUTER.write_text(router, encoding="utf-8")

print("Patched app.py so Ask Shiva uses ChatGPT over verified local evidence")
