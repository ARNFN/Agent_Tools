import os

import httpx

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def _get_api_key() -> str:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "TAVILY_API_KEY is not configured. "
            "请在 https://tavily.com 注册并获取 API Key，写入 .env"
        )
    return key


def _get_timeout() -> float:
    raw = os.getenv("WEB_SEARCH_TIMEOUT", "20").strip()
    try:
        return float(raw)
    except ValueError:
        return 20.0


def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> dict:
    api_key = _get_api_key()
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": False,
    }

    with httpx.Client(timeout=_get_timeout()) as client:
        resp = client.post(TAVILY_SEARCH_URL, json=payload)
        resp.raise_for_status()
        return resp.json()
