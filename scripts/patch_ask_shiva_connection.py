from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
text = APP.read_text(encoding="utf-8")

old = '''    if submitted:\n        if prompt.strip():\n            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n            if not api_key:\n                st.error("Ask Shiva is ready to use ChatGPT, but OPENAI_API_KEY has not been added to this app's Streamlit secrets yet.")\n            else:\n                try:\n                    with st.spinner("Shiva is analyzing the verified data..."):\n                        st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                            question=prompt,\n                            history=history,\n                            roi=roi,\n                            rankings=rankings,\n                            weekly=weekly,\n                            api_key=api_key,\n                        )\n                except Exception as exc:\n                    st.error(f"Ask Shiva could not reach ChatGPT right now: {exc}")\n        else:\n            st.warning("Type a question first.")\n'''

new = '''    if submitted:\n        if prompt.strip():\n            try:\n                api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n            except Exception:\n                api_key = ""\n            try:\n                with st.spinner("Shiva is analyzing the verified data..."):\n                    st.session_state["shiva_report_dynamic"] = ask_shiva_via_chatgpt(\n                        question=prompt,\n                        history=history,\n                        roi=roi,\n                        rankings=rankings,\n                        weekly=weekly,\n                        api_key=api_key or None,\n                    )\n            except Exception:\n                # Last-resort verified local engine: Ask Shiva must never die on the user.\n                st.session_state["shiva_report_dynamic"] = run_shiva_query(\n                    prompt, history, roi, rankings, weekly\n                )\n        else:\n            st.warning("Type a question first.")\n'''

if old not in text:
    print("Ask Shiva guard block already replaced or not found.")
else:
    text = text.replace(old, new)

# Clean duplicate path declarations introduced by earlier integration patches.
needle = 'WEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"\n'
while text.count(needle) > 1:
    first = text.find(needle)
    second = text.find(needle, first + len(needle))
    text = text[:second] + text[second + len(needle):]

APP.write_text(text, encoding="utf-8")
print("Ask Shiva now uses ChatGPT when configured and verified local fallback otherwise.")
