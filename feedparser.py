from __future__ import annotations

"""Small ESPN-hardened feed parser used by the Streamlit app.

The app imports ``feedparser`` and calls ``feedparser.parse(url)``.  Streamlit
Cloud can occasionally get an empty result when the third-party feedparser
package performs a direct fetch against ESPN.  This local compatibility module
keeps the same tiny interface the app uses, but performs the network request
with normal browser headers and falls back to ESPN's public NFL news JSON feed.

It intentionally returns only the fields the app consumes: title, link,
summary and an ``entries`` attribute.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
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
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()


def _text(node: ET.Element | None, tag: str) -> str:
    if node is None:
        return ""
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _parse_rss_bytes(payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    entries: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        summary = _text(item, "description")
        if title and link:
            entries.append({"title": title, "link": link, "summary": summary})
    return entries


def _parse_espn_json(payload: bytes) -> list[dict[str, str]]:
    data: dict[str, Any] = json.loads(payload.decode("utf-8", errors="replace"))
    entries: list[dict[str, str]] = []
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
        if title and link:
            entries.append({"title": title, "link": link, "summary": summary})
    return entries


def parse(url: str, *args: Any, **kwargs: Any) -> SimpleNamespace:
    """Return a feedparser-like object with ``entries``.

    Try the requested ESPN RSS URL first, then ESPN's alternate RSS feed, then
    ESPN's public NFL news JSON service.  A failed source never prevents the
    next source from being attempted.
    """
    tried: list[str] = []
    urls = [url] + [candidate for candidate in ESPN_RSS_FALLBACKS if candidate != url]

    for candidate in urls:
        try:
            tried.append(candidate)
            payload = _fetch(candidate, "application/rss+xml, application/xml, text/xml, */*;q=0.8")
            entries = _parse_rss_bytes(payload)
            if entries:
                return SimpleNamespace(entries=entries, bozo=False, href=candidate)
        except Exception:
            continue

    try:
        tried.append(ESPN_NFL_JSON)
        payload = _fetch(ESPN_NFL_JSON, "application/json, text/plain, */*")
        entries = _parse_espn_json(payload)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=ESPN_NFL_JSON)
    except Exception:
        pass

    return SimpleNamespace(entries=[], bozo=True, href=url, tried=tried)
