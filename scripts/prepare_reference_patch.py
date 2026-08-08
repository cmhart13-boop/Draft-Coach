from pathlib import Path

path = Path("scripts/patch_reference_mock_ui.py")
text = path.read_text()
text = text.replace("new_available = '''", "new_available = r'''", 1)
text = text.replace("new_board = '''", "new_board = r'''", 1)
path.write_text(text)
print("Reference UI generator escape handling prepared.")
