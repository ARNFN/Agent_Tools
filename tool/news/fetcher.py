from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from tool.news.feeds import get_feed_urls

TZ_UTC8 = timezone(timedelta(hours=8))


def _is_today(entry, today: datetime.date) -> bool:
    published = None
    if entry.get("published"):
        try:
            published = parsedate_to_datetime(entry["published"])
        except (TypeError, ValueError):
            pass
    if published is None and entry.get("updated"):
        try:
            published = parsedate_to_datetime(entry["updated"])
        except (TypeError, ValueError):
            pass
    if published is None:
        return False
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    local_date = published.astimezone(TZ_UTC8).date()
    return local_date == today


def _parse_entry(entry, feed_meta: dict) -> dict:
    return {
        "title": entry.get("title", ""),
        "link": entry.get("link", ""),
        "summary": entry.get("summary", ""),
        "published": entry.get("published") or entry.get("updated", ""),
        "source": feed_meta["name"],
        "category": feed_meta["category"],
        "lang": feed_meta["lang"],
    }


def fetch_news(
    category: str | None = None,
    lang: str | None = None,
    count: int = 10,
) -> list[dict]:
    today = datetime.now(TZ_UTC8).date()
    feed_urls = get_feed_urls(category=category, lang=lang)
    articles = []

    with httpx.Client(timeout=20, follow_redirects=True) as client:
        for feed_meta in feed_urls:
            try:
                resp = client.get(feed_meta["url"])
                resp.raise_for_status()
                parsed = feedparser.parse(resp.text)
            except Exception:
                continue

            for entry in parsed.entries:
                if not _is_today(entry, today):
                    continue
                articles.append(_parse_entry(entry, feed_meta))

    articles.sort(key=lambda a: a.get("published", ""), reverse=True)
    return articles[:count]
