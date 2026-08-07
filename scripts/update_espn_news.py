from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "espn_news_cache.json"
USER_AGENT = "Mozilla/5.0 ShivaDraft/1.0"
ESPN_JSON = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=12"
GOOGLE_RSS = (
    "https://news.google.com/rss/search?"
    + urllib.parse.urlencode(
        {
            "q": "site:espn.com/nfl OR site:espn.com/fantasy/football ESPN NFL fantasy football",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )
)


def fetch(url: str, accept: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()


def from_espn_json() -> list[dict[str, str]]:
    payload = fetch(ESPN_JSON, "application/json")
    data = json.loads(payload.decode("utf-8", errors="replace"))
    stories: list[dict[str, str]] = []
    for article in data.get("articles", []) or []:
        title = str(article.get("headline") or article.get("title") or "").strip()
        summary = str(article.get("description") or "").strip()
        link = ""
        links = article.get("links") or {}
        if isinstance(links, dict):
            web = links.get("web") or {}
            if isinstance(web, dict):
                link = str(web.get("href") or "").strip()
        if title and link:
            stories.append({"title": title, "link": link, "summary": summary, "source": "ESPN"})
        if len(stories) >= 4:
            break
    return stories


def from_google_rss() -> list[dict[str, str]]:
    payload = fetch(GOOGLE_RSS, "application/rss+xml, application/xml, text/xml")
    root = ET.fromstring(payload)
    stories: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        title_node = item.find("title")
        link_node = item.find("link")
        title = (title_node.text or "").strip() if title_node is not None else ""
        link = (link_node.text or "").strip() if link_node is not None else ""
        if title.lower().endswith(" - espn"):
            title = title[:-7].strip()
        if title and link:
            stories.append({"title": title, "link": link, "summary": "", "source": "ESPN via Google News"})
        if len(stories) >= 4:
            break
    return stories


def main() -> None:
    stories: list[dict[str, str]] = []
    source = ""
    try:
        stories = from_espn_json()
        source = "ESPN JSON"
    except Exception as exc:
        print(f"ESPN JSON failed: {exc}")

    if not stories:
        try:
            stories = from_google_rss()
            source = "Google News ESPN-only RSS"
        except Exception as exc:
            print(f"Google News fallback failed: {exc}")

    if not stories:
        raise SystemExit("No ESPN headlines could be fetched; preserving previous cache if one exists.")

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "stories": stories[:4],
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(stories[:4])} stories to {CACHE_PATH}")


if __name__ == "__main__":
    main()
