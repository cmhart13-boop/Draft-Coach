from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
text = APP.read_text(encoding="utf-8")

# 1) Rename the Ask Shiva submit button.
text = text.replace(
    'submitted = st.form_submit_button("Run Report", use_container_width=True)',
    'submitted = st.form_submit_button("Ask ChatGPT", use_container_width=True)',
)

# 2) Replace the old report renderer. Remove Draft Impact and Supporting Data entirely.
old_renderer = '''def render_report(report: dict) -> None:\n    st.markdown(f'<div class="report"><div class="report-title">{report.get("title", "SHIVA REPORT")}</div><div class="report-answer">{report.get("answer", "")}</div><div class="report-note">{report.get("note", "")}</div></div>', unsafe_allow_html=True)\n    takeaway = report.get("takeaway", "")\n    if takeaway:\n        st.markdown(f'<div class="takeaway"><b>🔥 DRAFT IMPACT</b><br>{takeaway}</div>', unsafe_allow_html=True)\n    render_supporting_data(report)\n'''

new_renderer = '''def render_report(report: dict) -> None:\n    answer = str(report.get("answer", "") or "").strip()\n    why = str(\n        report.get("why", "")\n        or report.get("takeaway", "")\n        or report.get("note", "")\n        or ""\n    ).strip()\n\n    st.markdown(\n        f'<div class="report"><div class="report-title">{report.get("title", "SHIVA REPORT")}</div><div class="report-answer">{answer}</div></div>',\n        unsafe_allow_html=True,\n    )\n\n    if why:\n        st.markdown(\n            f'''<div style="background:#171b17;border:1px solid #2c3b2c;border-radius:16px;padding:16px;margin:12px 0;">\n                <div style="color:#31f22f;font-size:12px;font-weight:1000;letter-spacing:.08em;text-transform:uppercase;margin-bottom:9px;">WHY</div>\n                <div style="color:#f7f7f8;font-size:15px;line-height:1.5;font-weight:650;white-space:pre-wrap;">{why}</div>\n            </div>''',\n            unsafe_allow_html=True,\n        )\n'''

if old_renderer in text:
    text = text.replace(old_renderer, new_renderer)
else:
    print("render_report block already updated or did not match exactly.")

# 3) Clean duplicate weekly path declarations if an older integration left any behind.
needle = 'WEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"\n'
while text.count(needle) > 1:
    first = text.find(needle)
    second = text.find(needle, first + len(needle))
    text = text[:second] + text[second + len(needle):]

APP.write_text(text, encoding="utf-8")
print("Ask Shiva layout updated: Ask ChatGPT button, answer-first card, WHY context, no Draft Impact, no Supporting Data.")
