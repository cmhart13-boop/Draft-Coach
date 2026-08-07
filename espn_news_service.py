from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("shiva.espn_news")
ESPN_RSS_URL = "https://www.espn.com/espn/rss/nfl/news"
ESPN_JSON_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=20"
USER_AGENT = "Mozilla/5.0 (compatible; ShivaDraft/1.0; +https://streamlit.app)"
CACHE_PATH = Path(__file__).resolve().parent / "espn_news_cache.json"
MEDIA_NS = "http://search.yahoo.com/mrss/"


def _request(url: str, accept: str, timeout: int = 12) -> tuple[bytes, str, int]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            status = int(getattr(response, "status", 200))
            content_type = str(response.headers.get("Content-Type", ""))
            LOGGER.info("ESPN request ok url=%s status=%s content_type=%s bytes=%s", url, status, content_type, len(body))
            return body, content_type, status
    except urllib.error.HTTPError as exc:
        preview = exc.read(500).decode("utf-8", errors="replace") if exc.fp else ""
        LOGGER.exception("ESPN HTTP error url=%s status=%s content_type=%s preview=%r", url, exc.code, exc.headers.get("Content-Type", "") if exc.headers else "", preview)
        raise
    except Exception:
        LOGGER.exception("ESPN request failed url=%s", url)
        raise


def _rss_thumbnail(item: ET.Element) -> str:
    candidates: list[str] = []
    for tag in [
        f"{{{MEDIA_NS}}}thumbnail",
        f"{{{MEDIA_NS}}}content",
        "thumbnail",
        "image",
        "enclosure",
    ]:
        for node in item.findall(tag):
            url = str(node.attrib.get("url") or "").strip()
            if url:
                candidates.append(url)
            if node.text and str(node.text).strip().startswith("http"):
                candidates.append(str(node.text).strip())
    return next((url for url in candidates if url.startswith("http")), "")


def _parse_rss(payload: bytes) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        LOGGER.exception("ESPN RSS XML parse failed preview=%r", payload[:500].decode("utf-8", errors="replace"))
        raise
    stories: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        def text(tag: str) -> str:
            node = item.find(tag)
            return (node.text or "").strip() if node is not None else ""
        title = text("title")
        link = text("link")
        description = text("description")
        published = text("pubDate")
        if title and link:
            stories.append({
                "title": title,
                "description": description,
                "link": link,
                "published": published,
                "thumbnail": _rss_thumbnail(item),
                "source": "ESPN RSS",
            })
    return stories


def _json_thumbnail(article: dict[str, Any]) -> str:
    images = article.get("images") or []
    if isinstance(images, list):
        ranked = sorted(
            [img for img in images if isinstance(img, dict)],
            key=lambda img: (int(img.get("width") or 0) * int(img.get("height") or 0)),
            reverse=True,
        )
        for image in ranked:
            url = str(image.get("url") or image.get("href") or "").strip()
            if url.startswith("http"):
                return url
    return ""


def _parse_json(payload: bytes) -> list[dict[str, str]]:
    data = json.loads(payload.decode("utf-8", errors="replace"))
    stories: list[dict[str, str]] = []
    for article in data.get("articles", []) or []:
        links = article.get("links") or {}
        web = links.get("web") or {} if isinstance(links, dict) else {}
        link = str(web.get("href") or "") if isinstance(web, dict) else ""
        title = str(article.get("headline") or "").strip()
        if title and link:
            stories.append({
                "title": title,
                "description": str(article.get("description") or "").strip(),
                "link": link,
                "published": str(article.get("published") or article.get("lastModified") or "").strip(),
                "thumbnail": _json_thumbnail(article),
                "source": "ESPN JSON",
            })
    return stories


def _write_cache(stories: list[dict[str, str]], source: str) -> None:
    if not stories:
        return
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "stories": stories,
    }
    try:
        CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        LOGGER.exception("Could not write ESPN cache path=%s", CACHE_PATH)


def _read_cache() -> list[dict[str, str]]:
    if not CACHE_PATH.exists():
        return []
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        stories = list(data.get("stories", []) or [])
        for story in stories:
            if isinstance(story, dict):
                story.setdefault("thumbnail", "")
        return stories
    except Exception:
        LOGGER.exception("Could not read ESPN cache path=%s", CACHE_PATH)
        return []


def fetch_espn_news(limit: int = 8) -> list[dict[str, str]]:
    """Server-side ESPN fetch. RSS first, ESPN JSON second, last-good local cache last."""
    try:
        payload, content_type, status = _request(ESPN_RSS_URL, "application/rss+xml, application/xml, text/xml, */*")
        if status == 200:
            stories = _parse_rss(payload)
            if stories:
                _write_cache(stories, "ESPN RSS")
                return stories[:limit]
            LOGGER.warning("ESPN RSS returned zero parsed stories content_type=%s", content_type)
    except Exception:
        pass

    try:
        payload, content_type, status = _request(ESPN_JSON_URL, "application/json,text/plain,*/*")
        if status == 200:
            stories = _parse_json(payload)
            if stories:
                _write_cache(stories, "ESPN JSON")
                return stories[:limit]
            LOGGER.warning("ESPN JSON returned zero parsed stories content_type=%s", content_type)
    except Exception:
        pass

    cached = _read_cache()
    if cached:
        LOGGER.warning("Serving last-good ESPN cache with %s stories", len(cached))
        return cached[:limit]
    return []
