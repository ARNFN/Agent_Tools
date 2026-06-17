"""Location providers: Windows GPS, IP geolocation, QWeather reverse lookup."""

import ctypes
import json
import locale
import math
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from tool.current_time.qweather_client import DEFAULT_GEO_PATH, qweather_get

_DEBUG_LOG = str(Path(__file__).resolve().parents[2] / "debug-c1ddd0.log")
_WIN_LOCATION_PS1 = Path(__file__).resolve().parent / "_win_location.ps1"

# region agent log
def _dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    entry = {
        "sessionId": "c1ddd0",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# endregion

GEOID_COUNTRY: dict[int, str] = {
    45: "中国",
    244: "美国",
    242: "日本",
    119: "韩国",
    225: "英国",
    84: "德国",
    74: "法国",
}

IP_API_URL = "http://ip-api.com/json/"


def _build_geo_lookup_params(location: str, number: int) -> dict:
    params = {"location": location, "number": number, "lang": "zh"}
    geo_range = os.getenv("QWEATHER_GEO_RANGE", "").strip().lower()
    if geo_range:
        params["range"] = geo_range
    return params


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def get_system_region() -> dict[str, Any]:
    tz = datetime.now().astimezone().tzinfo
    tz_key = getattr(tz, "key", None) or str(tz)
    lang, _ = locale.getlocale(locale.LC_CTYPE) or (None, None)
    country = None
    geo_id = None

    if sys.platform == "win32":
        try:
            geo_id = ctypes.windll.kernel32.GetUserGeoID(16)
            country = GEOID_COUNTRY.get(geo_id)
        except Exception as exc:
            _dbg("H1", "location_provider.py", "system_geo_failed", {"error": str(exc)})

    result = {
        "source": "system",
        "name": None,
        "country": country,
        "geo_id": geo_id,
        "locale": lang,
        "tz": tz_key,
        "utc_offset": datetime.now().astimezone().strftime("%z"),
    }
    _dbg("H1", "location_provider.py", "system_region", result)
    return result


def get_windows_location() -> dict[str, Any] | None:
    """Windows System.Device.Location GPS/Wi-Fi positioning (~10-100m accuracy)."""
    if sys.platform != "win32" or not _WIN_LOCATION_PS1.exists():
        return None

    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(_WIN_LOCATION_PS1),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        line = (proc.stdout or "").strip()
        if not line or line == "UNKNOWN":
            _dbg("H3", "location_provider.py", "windows_gps_unknown", {"stderr": proc.stderr[:200]})
            return None

        parts = line.split(",")
        if len(parts) < 2:
            return None

        lat = float(parts[0])
        lon = float(parts[1])
        accuracy = float(parts[2]) if len(parts) > 2 else None
        result = {
            "source": "windows_gps",
            "lat": lat,
            "lon": lon,
            "accuracy_m": accuracy,
        }
        _dbg("H3", "location_provider.py", "windows_gps", result)
        return result
    except Exception as exc:
        _dbg("H3", "location_provider.py", "windows_gps_failed", {"error": str(exc)})
        return None


def get_ip_region() -> dict[str, Any]:
    with httpx.Client(timeout=10) as client:
        resp = client.get(IP_API_URL, params={"lang": "zh-CN"})
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "success":
        raise ValueError(f"IP lookup failed: {data.get('message', 'unknown')}")

    result = {
        "source": "ip",
        "name": data.get("city"),
        "id": None,
        "lat": float(data.get("lat", 0)),
        "lon": float(data.get("lon", 0)),
        "adm2": data.get("city"),
        "adm1": data.get("regionName"),
        "country": data.get("country"),
        "tz": data.get("timezone"),
        "utc_offset": None,
        "ip": data.get("query"),
    }
    _dbg("H2", "location_provider.py", "ip_region", {
        "city": result["name"],
        "adm1": result["adm1"],
        "lat": result["lat"],
        "lon": result["lon"],
    })
    return result


def _qweather_city_lookup(query: str) -> dict[str, Any]:
    data = qweather_get(
        DEFAULT_GEO_PATH,
        params=_build_geo_lookup_params(query, 10),
    )
    if data.get("code") != "200" or not data.get("location"):
        raise ValueError(f"QWeather lookup failed: {data.get('code')}")
    loc = data["location"][0]
    return _format_qweather_loc(loc, source="qweather")


def _pick_nearest_location(candidates: list[dict], lat: float, lon: float) -> dict:
    best = None
    best_dist = float("inf")
    for loc in candidates:
        try:
            loc_lat = float(loc.get("lat", 0))
            loc_lon = float(loc.get("lon", 0))
        except (TypeError, ValueError):
            continue
        dist = _haversine_km(lat, lon, loc_lat, loc_lon)
        if dist < best_dist:
            best_dist = dist
            best = loc
    if best is None:
        raise ValueError("No valid location candidates")
    _dbg("H4", "location_provider.py", "nearest_pick", {
        "picked": best.get("name"),
        "distance_km": round(best_dist, 3),
        "candidate_count": len(candidates),
    })
    return best


def _qweather_reverse_geo(lon: float, lat: float) -> dict[str, Any]:
    """Reverse geocode with nearest-district matching. QWeather accepts lon,lat with 2 decimal places."""
    query = f"{lon:.2f},{lat:.2f}"
    data = qweather_get(
        DEFAULT_GEO_PATH,
        params=_build_geo_lookup_params(query, 20),
    )
    if data.get("code") != "200" or not data.get("location"):
        raise ValueError(f"QWeather reverse geo failed: {data.get('code')}")

    loc = _pick_nearest_location(data["location"], lat, lon)
    result = _format_qweather_loc(loc, source="qweather")
    result["input_lat"] = lat
    result["input_lon"] = lon
    result["query_coord"] = query
    return result


def _format_qweather_loc(loc: dict, source: str) -> dict[str, Any]:
    return {
        "source": source,
        "name": loc.get("name"),
        "id": loc.get("id"),
        "lat": loc.get("lat"),
        "lon": loc.get("lon"),
        "adm2": loc.get("adm2"),
        "adm1": loc.get("adm1"),
        "country": loc.get("country"),
        "tz": loc.get("tz"),
        "utc_offset": loc.get("utcOffset"),
        "rank": loc.get("rank"),
        "type": loc.get("type"),
    }


def _resolve_from_coords(
    lat: float,
    lon: float,
    chain_prefix: list[str],
    extra: dict | None = None,
) -> dict[str, Any]:
    try:
        result = _qweather_reverse_geo(lon, lat)
        result["fallback_chain"] = chain_prefix + ["qweather"]
        if extra:
            result.update(extra)
        _dbg("H5", "location_provider.py", "resolved", {
            "source": result["source"],
            "name": result["name"],
            "input_lat": lat,
            "input_lon": lon,
            "chain": result["fallback_chain"],
        })
        return result
    except Exception as exc:
        _dbg("H5", "location_provider.py", "coord_resolve_failed", {"error": str(exc), "lat": lat, "lon": lon})
        raise


def resolve_auto_region() -> dict[str, Any]:
    """
    Auto-detect region with fallback chain:
    1. Windows GPS (System.Device.Location) — highest district precision
    2. IP geolocation + QWeather reverse geo
    3. IP-only or system-only if APIs unavailable
    """
    system = get_system_region()

    win_loc = get_windows_location()
    if win_loc:
        try:
            return _resolve_from_coords(
                win_loc["lat"],
                win_loc["lon"],
                ["system", "windows_gps"],
                extra={"accuracy_m": win_loc.get("accuracy_m")},
            )
        except Exception:
            pass

    ip_data: dict[str, Any] | None = None
    try:
        ip_data = get_ip_region()
    except Exception as exc:
        _dbg("H2", "location_provider.py", "ip_failed", {"error": str(exc)})

    if ip_data and ip_data.get("lon") and ip_data.get("lat"):
        try:
            result = _resolve_from_coords(
                float(ip_data["lat"]),
                float(ip_data["lon"]),
                ["system", "ip"],
                extra={"ip": ip_data.get("ip")},
            )
            return result
        except Exception:
            ip_data["fallback_chain"] = ["system", "ip"]
            ip_data["system_tz"] = system.get("tz")
            ip_data["system_locale"] = system.get("locale")
            ip_data["lat"] = str(ip_data["lat"])
            ip_data["lon"] = str(ip_data["lon"])
            return ip_data

    system["fallback_chain"] = ["system"]
    _dbg("H4", "location_provider.py", "resolved", {"source": "system"})
    return system


def resolve_location_query(location: str | None) -> dict[str, Any]:
    if location:
        try:
            return _qweather_city_lookup(location)
        except Exception as exc:
            _dbg("H5", "location_provider.py", "named_lookup_failed", {"location": location, "error": str(exc)})
            raise
    return resolve_auto_region()
