"""Optional offline coordinate-to-IANA-timezone adapter."""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _finder():
    try:
        from timezonefinder import TimezoneFinder
    except ImportError as exc:
        raise RuntimeError(
            "Offline coordinate-to-timezone lookup is not installed. Install the `geo` extra or enter an IANA timezone manually."
        ) from exc
    return TimezoneFinder()


def timezone_at(latitude: float, longitude: float) -> str:
    zone = _finder().timezone_at(lat=latitude, lng=longitude)
    if not zone:
        raise ValueError("No timezone boundary covers this point. Enter the IANA timezone manually.")
    return zone
