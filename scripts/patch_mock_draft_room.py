from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

import_line = "from mock_draft_ui import render_mock_draft_room\n"
anchor = "from espn_news_service import fetch_espn_news\n"
if import_line not in text:
    if anchor not in text:
        raise SystemExit("Could not find import anchor in app.py")
    text = text.replace(anchor, anchor + import_line, 1)

start_marker = 'elif page == "Mock Draft":\n'
end_marker = '\nelse:\n    st.markdown(\'<div class="hero"><div class="kicker">🏛️ Shiva League History'
start = text.find(start_marker)
end = text.find(end_marker, start)
if start == -1 or end == -1:
    raise SystemExit(f"Could not locate Mock Draft section boundaries: start={start} end={end}")

replacement = '''elif page == "Mock Draft":
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
'''

text = text[:start] + replacement + text[end:]
path.write_text(text, encoding="utf-8")
print("Mock Draft section integrated with centralized draft engine/UI.")
