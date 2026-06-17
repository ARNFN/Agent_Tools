from tool.current_time.location_provider import resolve_location_query


def get_region(location: str | None = None) -> dict:
    return resolve_location_query(location)
