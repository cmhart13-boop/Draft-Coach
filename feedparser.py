from __future__ import annotations

"""ESPN-hardened compatibility feed parser for the Streamlit app.

This module exposes a tiny ``parse(url)`` interface compatible with the way
``app.py`` uses feedparser.  It tries multiple ESPN transports and finally a
Google News RSS query restricted to ESPN.com so the UI still receives ESPN
article headlines when Streamlit Cloud cannot fetch ESPN's RSS directly.
"""

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from types import SimpleNamespace
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1 ShivaDraft/1.0"
)

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


def _fetch(url: str, accept: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.espn.com/",
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
        if not title or not link or link in seen:
            continue
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
        if not link:
            link = str(article.get("link") or "").strip()
        if title and link and link not in seen:
            seen.add(link)
            entries.append({"title": title, "link": link, "summary": summary})
    return entries


class _ESPNLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[dict[str, str]] = []
        self._href = ""
        self._text_parts: list[str] = []
        self._in_anchor = False
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href") or ""
        if "/nfl/story/_/id/" in href or "/fantasy/football/story/_/id/" in href:
            self._href = href
            self._text_parts = []
            self._in_anchor = True

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self._text_parts.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._in_anchor:
            return
        title = re.sub(r"\s+", " ", " ".join(self._text_parts)).strip()
        href = self._href
        if href.startswith("/"):
            href = "https://www.espn.com" + href
        if title and href and href not in self._seen and len(title) > 12:
            self._seen.add(href)
            self.entries.append({"title": title, "link": href, "summary": ""})
        self._href = ""
        self._text_parts = []
        self._in_anchor = False


def _parse_espn_html(payload: bytes) -> list[dict[str, str]]:
    parser = _ESPNLinkParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return parser.entries


def _parse_google_news(payload: bytes) -> list[dict[str, str]]:
    entries = _parse_rss_bytes(payload)
    cleaned: list[dict[str, str]] = []
    for item in entries:
        title = re.sub(r"\s+-\s+ESPN$", "", item["title"], flags=re.I).strip()
        cleaned.append({"title": title, "link": item["link"], "summary": item.get("summary", "")})
    return cleaned


def parse(url: str, *args: Any, **kwargs: Any) -> SimpleNamespace:
    tried: list[str] = []

    # 1) Requested ESPN RSS feed, then alternate ESPN RSS feed.
    urls = [url] + [candidate for candidate in ESPN_RSS_FALLBACKS if candidate != url]
    for candidate in urls:
        try:
            tried.append(candidate)
            payload = _fetch(candidate, "application/rss+xml, application/xml, text/xml, */*;q=0.8")
            entries = _parse_rss_bytes(payload)
            if entries:
                return SimpleNamespace(entries=entries, bozo=False, href=candidate)
        except Exception:
            pass

    # 2) ESPN's public NFL JSON news service.
    try:
        tried.append(ESPN_NFL_JSON)
        payload = _fetch(ESPN_NFL_JSON, "application/json, text/plain, */*")
        entries = _parse_espn_json(payload)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=ESPN_NFL_JSON)
    except Exception:
        pass

    # 3) Scrape ESPN's NFL homepage for direct ESPN article links.
    try:
        tried.append(ESPN_NFL_PAGE)
        payload = _fetch(ESPN_NFL_PAGE, "text/html,application/xhtml+xml,*/*;q=0.8")
        entries = _parse_espn_html(payload)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=ESPN_NFL_PAGE)
    except Exception:
        pass

    # 4) Final transport fallback: Google News RSS restricted to ESPN.com.
    #    Headlines remain ESPN articles; Google only provides the RSS transport.
    try:
        tried.append(GOOGLE_ESPN_RSS)
        payload = _fetch(GOOGLE_ESPN_RSS, "application/rss+xml, application/xml, text/xml, */*")
        entries = _parse_google_news(payload)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=GOOGLE_ESPN_RSS)
    except Exception:
        pass

    return SimpleNamespace(entries=[], bozo=True, href=url, tried=tried)
