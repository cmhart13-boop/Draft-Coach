from __future__ import annotations

"""ESPN news compatibility layer for the Streamlit app.

The live app already calls ``feedparser.parse(url)``. This local module keeps
that interface but uses multiple live sources so the UI does not go blank when
ESPN blocks a direct Streamlit Cloud request.

Source order:
1. ESPN NFL RSS
2. ESPN general RSS
3. ESPN public NFL news JSON endpoint
4. Google News RSS restricted to ESPN.com NFL/fantasy articles

Only live ESPN article headlines are returned to the app.
"""

import json
import urllib.parse
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

ESPN_NFL_JSON = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=12"
)

GOOGLE_ESPN_QUERY = urllib.parse.quote(
    "site:espn.com NFL fantasy football"
)
GOOGLE_ESPN_RSS = (
    "https://news.google.com/rss/search?q="
    f"{GOOGLE_ESPN_QUERY}&hl=en-US&gl=US&ceid=US:en"
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
        },
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()


def _text(node: ET.Element | None, tag: str) -> str:
    if node is None:
        return ""
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _parse_rss_bytes(payload: bytes, require_espn_source: bool = False) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    entries: list[dict[str, str]] = []

    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        summary = _text(item, "description")

        if require_espn_source:
            source = item.find("source")
            source_name = ((source.text or "") if source is not None else "").strip().lower()
            source_url = ((source.attrib.get("url") or "") if source is not None else "").strip().lower()
            # Google News titles also commonly end in " - ESPN".
            title_is_espn = title.lower().endswith(" - espn")
            if "espn" not in source_name and "espn.com" not in source_url and not title_is_espn:
                continue
            if title_is_espn:
                title = title[:-7].strip()

        if title and link:
            entries.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                }
            )

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
                mobile = links.get("mobile") or {}
                if isinstance(mobile, dict):
                    link = str(mobile.get("href") or "").strip()

        if not link:
            link = str(article.get("link") or "").strip()

        if title and link:
            entries.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                }
            )

    return entries


def parse(url: str, *args: Any, **kwargs: Any) -> SimpleNamespace:
    """Return a feedparser-compatible object containing live ESPN stories."""
    tried: list[str] = []

    # 1-2: ESPN RSS endpoints.
    urls = [url] + [candidate for candidate in ESPN_RSS_FALLBACKS if candidate != url]
    for candidate in urls:
        try:
            tried.append(candidate)
            payload = _fetch(
                candidate,
                "application/rss+xml, application/xml, text/xml, */*;q=0.8",
            )
            entries = _parse_rss_bytes(payload)
            if entries:
                return SimpleNamespace(entries=entries, bozo=False, href=candidate)
        except Exception:
            continue

    # 3: ESPN JSON news service.
    try:
        tried.append(ESPN_NFL_JSON)
        payload = _fetch(ESPN_NFL_JSON, "application/json, text/plain, */*")
        entries = _parse_espn_json(payload)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=ESPN_NFL_JSON)
    except Exception:
        pass

    # 4: Google News as a transport fallback, restricted to ESPN articles.
    # This is still an ESPN-only headline feed; Google only supplies the RSS transport.
    try:
        tried.append(GOOGLE_ESPN_RSS)
        payload = _fetch(
            GOOGLE_ESPN_RSS,
            "application/rss+xml, application/xml, text/xml, */*;q=0.8",
        )
        entries = _parse_rss_bytes(payload, require_espn_source=True)
        if entries:
            return SimpleNamespace(entries=entries, bozo=False, href=GOOGLE_ESPN_RSS)
    except Exception:
        pass

    return SimpleNamespace(entries=[], bozo=True, href=url, tried=tried)
