from datetime import datetime

from zoneinfo import ZoneInfo



DEFAULT_TZ = "Asia/Shanghai"





def get_current_time(timezone: str = DEFAULT_TZ) -> dict:

    try:

        tz = ZoneInfo(timezone)

    except Exception as exc:

        raise ValueError(f"Invalid timezone: {timezone}") from exc



    now = datetime.now(tz)

    return {

        "timezone": timezone,

        "datetime": now.isoformat(),

        "date": now.strftime("%Y-%m-%d"),

        "time": now.strftime("%H:%M:%S"),

        "weekday": now.strftime("%A"),

        "utc_offset": now.strftime("%z"),

    }


