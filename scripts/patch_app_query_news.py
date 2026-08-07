from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ROUTER = ROOT / "shiva_query_router.py"
text = APP.read_text(encoding="utf-8")

text = text.replace(
    "from shiva_engine import build_history_frame, run_shiva_query\n",
    "from shiva_engine import build_history_frame\nfrom shiva_query_router import run_shiva_query\nfrom espn_news_service import fetch_espn_news\n",
)

text = text.replace(
    'BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"\n',
    'BIRTH_DATES_PATH = APP_DIR / "player_birth_dates.csv"\nWEEKLY_PATH = APP_DIR / "player_weekly_master_2014_2025.csv.gz"\n',
)

needle = '''@st.cache_data(show_spinner=False)\ndef load_births() -> pd.DataFrame:\n    if not BIRTH_DATES_PATH.exists():\n        return pd.DataFrame(columns=["name_key", "birth_date"])\n    df = pd.read_csv(BIRTH_DATES_PATH)\n    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")\n    return df.dropna(subset=["name_key", "birth_date"]).drop_duplicates("name_key")\n\nroi = load_roi()\nrankings = load_rankings()\nbirths = load_births()\n'''
replacement = '''@st.cache_data(show_spinner=False)\ndef load_births() -> pd.DataFrame:\n    if not BIRTH_DATES_PATH.exists():\n        return pd.DataFrame(columns=["name_key", "birth_date"])\n    df = pd.read_csv(BIRTH_DATES_PATH)\n    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")\n    return df.dropna(subset=["name_key", "birth_date"]).drop_duplicates("name_key")\n\n@st.cache_data(show_spinner=False)\ndef load_weekly() -> pd.DataFrame:\n    if not WEEKLY_PATH.exists():\n        return pd.DataFrame()\n    return pd.read_csv(WEEKLY_PATH, low_memory=False, compression="gzip")\n\nroi = load_roi()\nrankings = load_rankings()\nbirths = load_births()\nweekly = load_weekly()\n'''
if needle in text:
    text = text.replace(needle, replacement)

text = text.replace(
    'run_shiva_query(prompt, history, roi, rankings)',
    'run_shiva_query(prompt, history, roi, rankings, weekly)',
)

marker = "# ============================================================\n# LIVE ESPN FANTASY NEWS — DIRECT ESPN SITE API\n"
if marker in text:
    prefix = text.split(marker, 1)[0].rstrip() + "\n\n"
    news = r'''# ============================================================
# LIVE ESPN FANTASY NEWS — SERVER-SIDE SERVICE + LAST-GOOD CACHE
# ============================================================
from html import escape

st.markdown("---")
st.markdown(
    """
    <div style="margin:8px 0 12px 0;">
      <div style="color:#31f22f;font-size:11px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase;">📰 LIVE ESPN NFL NEWS</div>
      <div style="color:#fff;font-size:24px;font-weight:1000;line-height:1.05;margin-top:5px;">Fantasy-Relevant Headlines</div>
    </div>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=600, show_spinner=False)
def load_espn_news_backend() -> list[dict[str, str]]:
    return fetch_espn_news(limit=8)

articles = load_espn_news_backend()
if articles:
    for row_start in range(0, min(len(articles), 8), 2):
        news_cols = st.columns(2)
        for col_index, article in enumerate(articles[row_start:row_start + 2]):
            with news_cols[col_index]:
                title = escape(str(article.get("title") or "ESPN NFL Update"))
                description = escape(str(article.get("description") or ""))
                published = escape(str(article.get("published") or ""))
                article_url = escape(str(article.get("link") or "https://www.espn.com/nfl/"), quote=True)
                short_description = description[:150] + ("..." if len(description) > 150 else "")
                st.markdown(
                    f"""
                    <div style="background:linear-gradient(145deg,#202126,#151518);border:1px solid #34343a;border-radius:16px;padding:14px;min-height:220px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 8px 24px rgba(0,0,0,.22);margin-bottom:10px;">
                      <div>
                        <div style="color:#31f22f;font-size:9px;font-weight:1000;letter-spacing:.08em;text-transform:uppercase;margin-bottom:7px;">ESPN NFL</div>
                        <div style="color:#fff;font-size:14px;font-weight:950;line-height:1.25;">{title}</div>
                        <div style="color:#a7a8ad;font-size:10px;margin-top:7px;">{published}</div>
                        <div style="color:#d4d4d7;font-size:11px;line-height:1.4;margin-top:9px;">{short_description}</div>
                      </div>
                      <a href="{article_url}" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:14px;padding:11px 8px;border-radius:10px;background:#31f22f;color:#071007!important;text-decoration:none;text-align:center;font-size:10px;font-weight:1000;letter-spacing:.04em;">OPEN ON ESPN</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info("ESPN news could not be refreshed and no last-good cached headlines are available yet. The backend logs contain the request/parsing failure details.")
'''
    text = prefix + news

APP.write_text(text, encoding="utf-8")

router = ROUTER.read_text(encoding="utf-8")
router = router.replace(
    'name_col = _column(weekly, "player_name", "player_display_name", "name", "player")',
    'name_col = _column(weekly, "player_display_name", "player_name", "name", "player")',
)
ROUTER.write_text(router, encoding="utf-8")
print("Patched app.py plus detailed weekly player-name resolution")
