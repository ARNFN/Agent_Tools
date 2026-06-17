import os

import httpx

from tool.current_time.qweather_auth import get_auth_headers

DEFAULT_GEO_PATH = "/geo/v2/city/lookup"
DEFAULT_WEATHER_PATH = "/v7/weather/now"


def _get_host() -> str:
    host = os.getenv("QWEATHER_HOST", "").strip().rstrip("/")
    if not host:
        raise ValueError(
            "QWEATHER_HOST is not configured. "
            "请在和风控制台-设置中查看你的 API Host（形如 xxx.qweatherapi.com）并写入 .env"
        )
    if not host.startswith("http"):
        host = f"https://{host}"
    return host


def qweather_get(path: str, params: dict | None = None) -> dict:
    host = _get_host()
    url = f"{host}{path}"
    headers = get_auth_headers()

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params or {}, headers=headers)
        resp.raise_for_status()
        return resp.json()
