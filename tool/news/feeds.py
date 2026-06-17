from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FEEDS_PATH = ROOT / "config" / "rss_feeds.yaml"


def load_feeds() -> dict:
    with open(FEEDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_categories() -> list[str]:
    return list(load_feeds().keys())


def get_feed_urls(category: str | None = None, lang: str | None = None) -> list[dict]:
    feeds = load_feeds()
    result = []

    categories = [category] if category else list(feeds.keys())
    for cat in categories:
        if cat not in feeds:
            continue
        cat_feeds = feeds[cat]
        langs = [lang] if lang else list(cat_feeds.keys())
        for lng in langs:
            if lng not in cat_feeds:
                continue
            for entry in cat_feeds[lng]:
                result.append(
                    {
                        "category": cat,
                        "lang": lng,
                        "name": entry["name"],
                        "url": entry["url"],
                    }
                )
    return result
