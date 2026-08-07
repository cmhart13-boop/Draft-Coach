from __future__ import annotations

"""ESPN-compatible feed reader for the Shiva Streamlit app.

Primary path: read a repository-backed cache refreshed by GitHub Actions every
15 minutes. This avoids Streamlit Cloud outbound-network failures entirely.
If the cache is missing, fall back to direct ESPN/Google transports.
"""

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from typing import Any

APP_DIR = Path(__file__).resolve().parent
CACHE_PATH = APP_DIR / "espn_news_cache.json"
USER_AGENT = "Mozilla/5.0 ShivaDraft/1.0"
ESPN_RSS_FALLBACKS = (
    "https://www.espn.com/espn/rss/nfl/news",
    "https://www.espn.com/espn/rss/news",
)
ESPN_NFL_JSON = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=12"
ESPN_NFL_PAGE = "https://www.espn.com/nfl/"
GOOGLE_ESPN_RSS = (
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


def _cache_entries() -> list[dict[str, str]]:
    if not CACHE_PATH.exists():
        return []
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        entries: list[dict[str, str]] = []
        for story in data.get("stories", []) or []:
            title = str(story.get("title") or "").strip()
            link = str(story.get("link") or "").strip()
            summary = str(story.get("summary") or "").strip()
            if title and link:
                entries.append({"title": title, "link": link, "summary": summary})
        return entries
    except Exception:
        return []


def _fetch(url: str, accept: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        return response.read()


def _text(node: ET.Element | None, tag: str) -> str:
    if node is None:
        return ""
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _parse_rss_bytes(payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        summary = _text(item, "description")
        if title and link and link not in seen:
            seen.add(link)
            entries.append({"title": title, "link": link, "summary": summary})
    return entries


def _parse_espn_json(payload: bytes) -> list[dict[str, str]]:
    data: dict[str, Any] = json.loads(payload.decode("utf-8", errors="replace"))
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for article in data.get("articles", []) or []:
        title = str(article.get("headline") or article.get("title") or "").strip()
        summary = str(article.get("description") or "").strip()
        link = ""
        links = article.get("links") or {}
        if isinstance(links, dict):
            web = links.get("web") or {}
            if isinstance(web, dict):
                link = str(web.get("href") or "").strip()
        if title and link and link not in seen:
            seen.add(link)
            entries.append({"title": title, "link": link, "summary": summary})
    return entries


class _ESPNLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[dict[str, str]] = []
        self._href = ""
        self._parts: list[str] = []
        self._in_anchor = False
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href") or ""
        if "/nfl/story/_/id/" in href or "/fantasy/football/story/_/id/" in href:
            self._href = href
            self._parts = []
            self._in_anchor = True

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self._parts.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._in_anchor:
            return
        title = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
        href = self._href
        if href.startswith("/"):
            href = "https://www.espn.com" + href
        if title and href and href not in self._seen and len(title) > 12:
            self._seen.add(href)
            self.entries.append({"title": title, "link": href, "summary": ""})
        self._href = ""
        self._parts = []
        self._in_anchor = False


def parse(url: str, *args: Any, **kwargs: Any) -> SimpleNamespace:
    cached = _cache_entries()
    if cached:
        return SimpleNamespace(entries=cached, bozo=False, href=str(CACHE_PATH))

    for candidate in [url] + [x for x in ESPN_RSS_FALLBACKS if x != url]:
        try:
            entries = _parse_rss_bytes(_fetch(candidate, "application/rss+xml, application/xml, text/xml, */*"))
            if entries:
                return SimpleNamespace(entries=entries, bozo=False, href=candidate)
        except Exception:
            pass

    try:
        entries = _parse_espn_json(_fetch(ESPN_NFL_JSON, "application/json, */*"))
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=ESPN_NFL_JSON)
    except Exception:
        pass

    try:
        parser = _ESPNLinkParser()
        parser.feed(_fetch(ESPN_NFL_PAGE, "text/html, */*").decode("utf-8", errors="replace"))
        if parser.entries:
            return SimpleNamespace(entries=parser.entries, bozo=False, href=ESPN_NFL_PAGE)
    except Exception:
        pass

    try:
        entries = _parse_rss_bytes(_fetch(GOOGLE_ESPN_RSS, "application/rss+xml, application/xml, text/xml, */*"))
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=GOOGLE_ESPN_RSS)
    except Exception:
        pass

    return SimpleNamespace(entries=[], bozo=True, href=url)
