from datetime import datetime
from zoneinfo import ZoneInfo

NAIROBI = ZoneInfo("Africa/Nairobi")


def ensure_nairobi_aware(dt):
    """
    Ensure a datetime is timezone-aware in Africa/Nairobi.
    If dt is naive, assume it is UTC and convert to Nairobi.
    If dt is aware, convert to Nairobi.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(NAIROBI)
