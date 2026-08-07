from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
REQ = ROOT / "requirements.txt"

MARKER = "# ============================================================\n# LIVE ESPN NFL NEWS FEED\n# ============================================================"

NEWS_BLOCK = r'''# ============================================================
# LIVE ESPN FANTASY NEWS — DIRECT ESPN SITE API
# No RSS, no feedparser.
# ============================================================
import json
import urllib.request
from html import escape

st.markdown("---")
st.header("📰 Live ESPN Fantasy News Stream")

@st.cache_data(ttl=300, show_spinner=False)
def load_espn_news_api() -> list[dict]:
    """Fetch current ESPN NFL/fantasy-relevant news from ESPN's public site JSON API."""
    api_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=12"
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            news_data = json.loads(response.read().decode("utf-8"))
        articles = news_data.get("articles", []) or []
        return articles[:4]
    except Exception:
        return []

articles = load_espn_news_api()
news_cols = st.columns(4)

if articles:
    for idx, article in enumerate(articles[:4]):
        with news_cols[idx]:
            title = escape(str(article.get("headline", "Fantasy Football Update")))
            description = escape(str(article.get("description", "Click below to read the full fantasy breakdown.")))

            links_dict = article.get("links", {}) or {}
            web_links = links_dict.get("web", {}) if isinstance(links_dict, dict) else {}
            article_url = web_links.get("href", "https://www.espn.com/fantasy/football/") if isinstance(web_links, dict) else "https://www.espn.com/fantasy/football/"
            article_url = escape(str(article_url), quote=True)

            short_description = description[:110] + ("..." if len(description) > 110 else "")

            st.markdown(
                f"""
                <div style="background-color:#262730;padding:15px;border-radius:8px;min-height:220px;display:flex;flex-direction:column;justify-content:space-between;border:1px solid #464855;">
                    <div>
                        <h4 style="color:#FF4B4B;margin:0 0 10px 0;font-size:16px;font-weight:800;line-height:1.3;">{title}</h4>
                        <p style="color:#F0F2F6;font-size:13px;line-height:1.4;font-weight:500;">{short_description}</p>
                    </div>
                    <a href="{article_url}" target="_blank" rel="noopener noreferrer" style="background-color:#FF4B4B;color:white!important;text-align:center;padding:8px 12px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:12px;margin-top:10px;display:block;">READ FULL ARTICLE</a>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("Unable to refresh live news feed articles from ESPN.")
'''

text = APP.read_text(encoding="utf-8")
if MARKER not in text:
    raise SystemExit("ESPN news marker not found in app.py")

prefix = text.split(MARKER, 1)[0].rstrip() + "\n\n"
APP.write_text(prefix + NEWS_BLOCK, encoding="utf-8")

if REQ.exists():
    lines = [line for line in REQ.read_text(encoding="utf-8").splitlines() if line.strip().lower() != "feedparser"]
    REQ.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

# Remove the legacy RSS/cache implementation so there is only one news path.
for relative in [
    "feedparser.py",
    "espn_news_cache.json",
    "scripts/update_espn_news.py",
    ".github/workflows/update-espn-news.yml",
]:
    path = ROOT / relative
    if path.exists():
        path.unlink()

print("Patched app.py to direct ESPN JSON API and removed RSS/feedparser legacy files.")
