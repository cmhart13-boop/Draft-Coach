from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ROUTER = ROOT / "shiva_query_router.py"

text = APP.read_text(encoding="utf-8")

if "import os\n" not in text:
    text = text.replace("import math\n", "import math\nimport os\n")

if "from shiva_chatgpt_service import ask_shiva_via_chatgpt\n" not in text:
    text = text.replace(
        "from shiva_query_router import run_shiva_query\n",
        "from shiva_query_router import run_shiva_query\nfrom shiva_chatgpt_service import ask_shiva_via_chatgpt\n",
    )

current_block = '''    if submitted:\n        if prompt.strip():\n            try:\n                api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n            except Exception:\n                api_key = ""\n            try:\n                with st.spinner("Shiva is analyzing the verified data..."):\n                    st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                        question=prompt,\n                        history=history,\n                        roi=roi,\n                        rankings=rankings,\n                        weekly=weekly,\n                        api_key=api_key or None,\n                    )\n            except Exception:\n                # Last-resort verified local engine: Ask Shiva must never die on the user.\n                st.session_state["shiva_report_dynamic"] = run_shiva_query(\n                    prompt, history, roi, rankings, weekly\n                )\n        else:\n            st.warning("Type a question first.")\n'''

replacement = '''    try:\n        secret_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n    except Exception:\n        secret_key = ""\n    configured_api_key = (\n        str(os.environ.get("OPENAI_API_KEY", "")).strip()\n        or secret_key\n        or str(st.session_state.get("shiva_openai_api_key", "")).strip()\n    )\n\n    if not configured_api_key:\n        with st.expander("Connect ChatGPT", expanded=True):\n            entered_key = st.text_input(\n                "OpenAI API key",\n                type="password",\n                placeholder="sk-...",\n                help="Used only for this browser session. For permanent use, add OPENAI_API_KEY in Streamlit Cloud Secrets.",\n                key="shiva_openai_api_key_input",\n            )\n            if entered_key.strip():\n                st.session_state["shiva_openai_api_key"] = entered_key.strip()\n                configured_api_key = entered_key.strip()\n                st.success("ChatGPT connected for this session.")\n\n    if submitted:\n        if not prompt.strip():\n            st.warning("Type a question first.")\n        elif not configured_api_key:\n            st.error("ChatGPT needs an OpenAI API key. Add it above once, or set OPENAI_API_KEY in Streamlit Cloud Secrets for permanent use.")\n        else:\n            try:\n                with st.spinner("Shiva is asking ChatGPT and checking the verified data..."):\n                    st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                        question=prompt,\n                        history=history,\n                        roi=roi,\n                        rankings=rankings,\n                        weekly=weekly,\n                        api_key=configured_api_key,\n                    )\n            except Exception as exc:\n                st.error(f"ChatGPT connection failed: {exc}")\n'''

if current_block in text:
    text = text.replace(current_block, replacement)
elif "configured_api_key = (" not in text:
    raise RuntimeError("Could not locate the current Ask Shiva block safely.")

APP.write_text(text, encoding="utf-8")

router = ROUTER.read_text(encoding="utf-8")
router = router.replace(
    'name_col = _column(weekly, "player_name", "player_display_name", "name", "player")',
    'name_col = _column(weekly, "player_display_name", "player_name", "name", "player")',
)
ROUTER.write_text(router, encoding="utf-8")

print("Ask Shiva patched with environment, Streamlit secret, and session key support")
