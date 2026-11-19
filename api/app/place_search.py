"""Optional, user-triggered Nominatim search with app-wide throttling and cache.

This is intentionally NOT an autocomplete endpoint. Enable it only after the
application operator configures an identifying User-Agent and agrees to the
public Nominatim usage policy.
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PlaceSearchUnavailable(RuntimeError):
    pass


_CACHE: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0
_CACHE_LIMIT = 256


def search_places(query: str) -> list[dict[str, object]]:
    global _LAST_REQUEST_AT
    cleaned = " ".join(query.split())
    if len(cleaned) < 3:
        raise ValueError("Enter at least 3 characters for a birthplace search")
    if len(cleaned) > 120:
        raise ValueError("Place search is too long")

    user_agent = os.getenv("NOMINATIM_USER_AGENT", "").strip()
    if not user_agent:
        raise PlaceSearchUnavailable(
            "Place search is disabled until the application operator configures NOMINATIM_USER_AGENT. You can enter coordinates manually."
        )

    key = cleaned.casefold()
    with _LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            _CACHE.move_to_end(key)
            return cached

        wait_for = 1.05 - (time.monotonic() - _LAST_REQUEST_AT)
        if wait_for > 0:
            time.sleep(wait_for)

        endpoint = os.getenv(
            "NOMINATIM_SEARCH_URL", "https://nominatim.openstreetmap.org/search"
        )
        url = endpoint + "?" + urlencode(
            {"q": cleaned, "format": "jsonv2", "limit": 5, "addressdetails": 1}
        )
        request = Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
                "Accept-Language": "en",
            },
        )
        _LAST_REQUEST_AT = time.monotonic()
        try:
            with urlopen(request, timeout=10) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PlaceSearchUnavailable("Place search is temporarily unavailable. Enter coordinates manually.") from exc

        results: list[dict[str, object]] = []
        for item in raw:
            try:
                results.append(
                    {
                        "label": str(item["display_name"]),
                        "latitude": float(item["lat"]),
                        "longitude": float(item["lon"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        _CACHE[key] = results
        _CACHE.move_to_end(key)
        while len(_CACHE) > _CACHE_LIMIT:
            _CACHE.popitem(last=False)
        return results
