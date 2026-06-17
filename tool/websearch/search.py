import os

from tool.websearch.client import tavily_search

DEFAULT_MAX_RESULTS = 5
MAX_RESULTS_LIMIT = 10


def _get_default_max_results() -> int:
    raw = os.getenv("WEB_SEARCH_MAX_RESULTS", str(DEFAULT_MAX_RESULTS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_RESULTS
    return max(1, min(value, MAX_RESULTS_LIMIT))


def _normalize_result(item: dict) -> dict:
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "snippet": item.get("content", ""),
        "score": item.get("score"),
        "published_date": item.get("published_date"),
    }


def web_search(
    query: str,
    max_results: int | None = None,
    search_depth: str = "basic",
) -> dict:
    query = (query or "").strip()
    if not query:
        raise ValueError("query must not be empty")

    if search_depth not in ("basic", "advanced"):
        raise ValueError("search_depth must be 'basic' or 'advanced'")

    limit = max_results if max_results is not None else _get_default_max_results()
    limit = max(1, min(limit, MAX_RESULTS_LIMIT))

    data = tavily_search(query=query, max_results=limit, search_depth=search_depth)
    results = [_normalize_result(item) for item in data.get("results", [])]

    return {
        "query": query,
        "search_depth": search_depth,
        "result_count": len(results),
        "results": results,
    }
