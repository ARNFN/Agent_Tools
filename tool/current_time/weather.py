from tool.current_time.location_provider import resolve_location_query
from tool.current_time.qweather_client import DEFAULT_WEATHER_PATH, qweather_get


def get_weather(location: str | None = None) -> dict:
    loc_info = resolve_location_query(location)
    loc_id = loc_info.get("id")
    loc_name = loc_info.get("name") or loc_info.get("adm2") or "unknown"

    if not loc_id:
        if loc_info.get("lat") and loc_info.get("lon"):
            from tool.current_time.location_provider import _qweather_reverse_geo
            try:
                enriched = _qweather_reverse_geo(loc_info["lon"], loc_info["lat"])
                loc_id = enriched.get("id")
                loc_name = enriched.get("name") or loc_name
            except Exception:
                raise ValueError(
                    f"Cannot fetch weather: no QWeather location ID for {loc_name}. "
                    "QWeather API may be unavailable."
                )
        else:
            raise ValueError(f"Cannot fetch weather: insufficient location data for {loc_name}")

    weather_data = qweather_get(
        DEFAULT_WEATHER_PATH,
        params={"location": loc_id, "lang": "zh"},
    )
    if weather_data.get("code") != "200":
        raise ValueError(f"Weather lookup failed: {weather_data.get('code')}")

    now = weather_data.get("now", {})
    return {
        "location": loc_name,
        "location_id": loc_id,
        "text": now.get("text"),
        "temp": now.get("temp"),
        "feels_like": now.get("feelsLike"),
        "humidity": now.get("humidity"),
        "wind_dir": now.get("windDir"),
        "wind_scale": now.get("windScale"),
        "update_time": weather_data.get("updateTime"),
    }
