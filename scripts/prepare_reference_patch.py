from pathlib import Path

path = Path("scripts/patch_reference_mock_ui.py")
text = path.read_text()

# Keep backslash-n escapes literal inside the generated Python source.
text = text.replace("new_available = '''", "new_available = r'''", 1)
text = text.replace("new_board = '''", "new_board = r'''", 1)

# re.sub treats backslashes in a string replacement specially. Use callable
# replacements so generated f-strings retain literal backslash-n sequences.
replacements = {
    'text = re.sub(r"def _css\\(\\) -> None:.*?\\n\\ndef _state_key\\(\\)", new_css + "\\n\\ndef _state_key()", text, flags=re.S)':
        'text = re.sub(r"def _css\\(\\) -> None:.*?\\n\\ndef _state_key\\(\\)", lambda _m: new_css + "\\n\\ndef _state_key()", text, flags=re.S)',
    'text = re.sub(r"def _render_recommendations\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_available", new_recs + "\\n\\ndef _render_available", text, flags=re.S)':
        'text = re.sub(r"def _render_recommendations\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_available", lambda _m: new_recs + "\\n\\ndef _render_available", text, flags=re.S)',
    'text = re.sub(r"def _render_available\\(state: dict\\[str, Any\\], history: pd.DataFrame, weekly: pd.DataFrame\\) -> None:.*?\\n\\ndef _render_queue", new_available + "\\n\\ndef _render_queue", text, flags=re.S)':
        'text = re.sub(r"def _render_available\\(state: dict\\[str, Any\\], history: pd.DataFrame, weekly: pd.DataFrame\\) -> None:.*?\\n\\ndef _render_queue", lambda _m: new_available + "\\n\\ndef _render_queue", text, flags=re.S)',
    'text = re.sub(r"def _render_queue\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_roster", new_queue + "\\n\\ndef _render_roster", text, flags=re.S)':
        'text = re.sub(r"def _render_queue\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_roster", lambda _m: new_queue + "\\n\\ndef _render_roster", text, flags=re.S)',
    'text = re.sub(r"def _render_roster\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_recent", new_roster + "\\n\\ndef _render_recent", text, flags=re.S)':
        'text = re.sub(r"def _render_roster\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_recent", lambda _m: new_roster + "\\n\\ndef _render_recent", text, flags=re.S)',
    'text = re.sub(r"def _render_recent\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_board", new_recent + "\\n\\ndef _render_board", text, flags=re.S)':
        'text = re.sub(r"def _render_recent\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_board", lambda _m: new_recent + "\\n\\ndef _render_board", text, flags=re.S)',
    'text = re.sub(r"def _render_board\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_ask_shiva", new_board + "\\n\\ndef _render_ask_shiva", text, flags=re.S)':
        'text = re.sub(r"def _render_board\\(state: dict\\[str, Any\\]\\) -> None:.*?\\n\\ndef _render_ask_shiva", lambda _m: new_board + "\\n\\ndef _render_ask_shiva", text, flags=re.S)',
    'text = re.sub(r"def render_mock_draft_room\\(.*\\Z", new_render, text, flags=re.S)':
        'text = re.sub(r"def render_mock_draft_room\\(.*\\Z", lambda _m: new_render, text, flags=re.S)',
}
for old, new in replacements.items():
    text = text.replace(old, new)

path.write_text(text)
print("Reference UI generator escape handling prepared.")
