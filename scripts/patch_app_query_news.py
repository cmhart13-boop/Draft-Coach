from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ROUTER = ROOT / "shiva_query_router.py"

text = APP.read_text(encoding="utf-8")

# Ensure os is available for environment-secret fallback.
if "import os\n" not in text:
    text = text.replace("import math\n", "import math\nimport os\n")

# Keep the deterministic data router as the evidence layer, but make ChatGPT the
# conversational Ask Shiva response layer.
if "from shiva_chatgpt_service import ask_shiva_via_chatgpt\n" not in text:
    text = text.replace(
        "from shiva_query_router import run_shiva_query\n",
        "from shiva_query_router import run_shiva_query\nfrom shiva_chatgpt_service import ask_shiva_via_chatgpt\n",
    )

old_block = '''    if submitted:\n        if prompt.strip():\n            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n            if not api_key:\n                st.error("Ask Shiva is ready to use ChatGPT, but OPENAI_API_KEY has not been added to this app's Streamlit secrets yet.")\n            else:\n                try:\n                    with st.spinner("Shiva is analyzing the verified data..."):\n                        st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                            question=prompt,\n                            history=history,\n                            roi=roi,\n                            rankings=rankings,\n                            weekly=weekly,\n                            api_key=api_key,\n                        )\n                except Exception as exc:\n                    st.error(f"Ask Shiva could not reach ChatGPT right now: {exc}")\n        else:\n            st.warning("Type a question first.")\n'''

new_block = '''    # Prefer a server-side secret. For immediate testing, allow a session-only key\n    # entry without ever writing the credential to GitHub or disk.\n    configured_api_key = (\n        str(os.environ.get("OPENAI_API_KEY", "")).strip()\n        or str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n        or str(st.session_state.get("shiva_openai_api_key", "")).strip()\n    )\n\n    if not configured_api_key:\n        with st.expander("Connect ChatGPT", expanded=True):\n            entered_key = st.text_input(\n                "OpenAI API key",\n                type="password",\n                placeholder="sk-...",\n                help="Used only for this browser session. For permanent use, add OPENAI_API_KEY in Streamlit Cloud Secrets.",\n                key="shiva_openai_api_key_input",\n            )\n            if entered_key.strip():\n                st.session_state["shiva_openai_api_key"] = entered_key.strip()\n                configured_api_key = entered_key.strip()\n                st.success("ChatGPT connected for this session.")\n\n    if submitted:\n        if not prompt.strip():\n            st.warning("Type a question first.")\n        elif not configured_api_key:\n            st.error("ChatGPT needs an OpenAI API key. Add it above once, or set OPENAI_API_KEY in Streamlit Cloud Secrets for permanent use.")\n        else:\n            try:\n                with st.spinner("Shiva is asking ChatGPT and checking the verified data..."):\n                    st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                        question=prompt,\n                        history=history,\n                        roi=roi,\n                        rankings=rankings,\n                        weekly=weekly,\n                        api_key=configured_api_key,\n                    )\n            except Exception as exc:\n                st.error(f"ChatGPT connection failed: {exc}")\n'''

if old_block in text:
    text = text.replace(old_block, new_block)
elif "configured_api_key = (" not in text:
    raise RuntimeError("Could not locate the current Ask Shiva ChatGPT block to replace safely.")

APP.write_text(text, encoding="utf-8")

# Preserve the weekly-data player-name preference used by the deterministic evidence layer.
router = ROUTER.read_text(encoding="utf-8")
router = router.replace(
    'name_col = _column(weekly, "player_name", "player_display_name", "name", "player")',
    'name_col = _column(weekly, "player_display_name", "player_name", "name", "player")',
)
ROUTER.write_text(router, encoding="utf-8")

print("Patched Ask Shiva with environment/secrets/session API-key support")
