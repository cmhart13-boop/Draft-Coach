from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
text = APP.read_text(encoding="utf-8")

# 1) Correct the submit button label everywhere.
for old_label in ["Run Report", "Ask ChatGPT", "ASK CHATGPT", "Ask Shiva GPT"]:
    text = text.replace(
        f'submitted = st.form_submit_button("{old_label}", use_container_width=True)',
        'submitted = st.form_submit_button("ASK SHIVA GPT", use_container_width=True)',
    )

# 2) Replace BOTH the old Supporting Data renderer and report renderer with
# one clean answer + WHY renderer. This removes Draft Impact and View Supporting Data.
new_renderer = '''def render_report(report: dict) -> None:
    title = str(report.get("title") or "🧠 ASK SHIVA GPT").strip()
    answer = str(report.get("answer") or "").strip()
    why = str(
        report.get("why")
        or report.get("takeaway")
        or report.get("note")
        or ""
    ).strip()

    st.markdown(
        f"""
        <div style="background:linear-gradient(145deg,#17181c,#111214);border:1px solid #34363d;border-left:8px solid #31f22f;border-radius:20px;padding:24px 22px;margin:18px 0 14px;box-shadow:0 8px 28px rgba(0,0,0,.25);">
            <div style="color:#d8d8dc;font-size:13px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;margin-bottom:14px;">{title}</div>
            <div style="color:#31f22f;font-size:clamp(30px,8vw,46px);line-height:1.08;font-weight:1000;letter-spacing:-.02em;white-space:pre-wrap;">{answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if why:
        st.markdown(
            f"""
            <div style="background:linear-gradient(145deg,#1a1d1a,#121412);border:1px solid #324232;border-radius:20px;padding:22px;margin:14px 0 22px;">
                <div style="color:#31f22f;font-size:13px;font-weight:1000;letter-spacing:.10em;text-transform:uppercase;margin-bottom:13px;">WHY</div>
                <div style="color:#f5f5f6;font-size:17px;line-height:1.55;font-weight:600;white-space:pre-wrap;">{why}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

'''

pattern = re.compile(
    r'def render_supporting_data\(report: dict\) -> None:.*?(?=st\.markdown\(\'<div class="app-title">)',
    re.DOTALL,
)

if pattern.search(text):
    text = pattern.sub(new_renderer, text, count=1)
else:
    # If Supporting Data was already removed, replace render_report alone.
    render_only = re.compile(
        r'def render_report\(report: dict\) -> None:.*?(?=st\.markdown\(\'<div class="app-title">)',
        re.DOTALL,
    )
    if render_only.search(text):
        text = render_only.sub(new_renderer, text, count=1)
    else:
        raise RuntimeError("Could not locate Ask Shiva report renderer safely.")

# 3) Update the hero copy so the page language matches the feature name.
text = text.replace(
    '<div class="hero-title">Ask Shiva</div>',
    '<div class="hero-title">Ask Shiva GPT</div>',
)

# 4) Normalize success/spinner wording.
text = text.replace("ChatGPT connected for this session.", "Shiva GPT connected for this session.")
text = text.replace("Shiva is asking ChatGPT and checking the verified data...", "Shiva GPT is analyzing the verified data...")

# 5) Clean duplicate weekly path declarations if an older integration left any behind.
needle = 'WEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"\n'
while text.count(needle) > 1:
    first = text.find(needle)
    second = text.find(needle, first + len(needle))
    text = text[:second] + text[second + len(needle):]

APP.write_text(text, encoding="utf-8")
print("Ask Shiva GPT layout updated: correct button, answer-first card, WHY card, no Draft Impact, no Supporting Data.")
