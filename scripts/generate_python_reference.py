#!/usr/bin/env python3
"""Generate deterministic pinned-Python reference outputs for client parity tests."""
from __future__ import annotations

import json
import sys
from datetime import date, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.engine import (  # noqa: E402
    generate_chart,
    generate_daily_panchanga,
    generate_panchanga_transitions,
)
from app.schemas import ChartRequest  # noqa: E402
from app.timezones import resolve_local_birth  # noqa: E402


def main() -> None:
    request = ChartRequest(
        birth_date=date(1990, 3, 15),
        birth_time=time(10, 30),
        timezone="Asia/Kolkata",
        latitude=19.0760,
        longitude=72.8777,
        ayanamsa="lahiri",
    )
    local_birth, utc_birth, offset = resolve_local_birth(
        request.birth_date, request.birth_time, request.timezone
    )
    chart = generate_chart(request, local_birth, utc_birth, offset)

    panchanga_date = date(2026, 3, 8)
    _, _, panchanga_offset = resolve_local_birth(
        panchanga_date, time(12, 0), "Asia/Kolkata"
    )
    daily = generate_daily_panchanga(
        panchanga_date, 22.4707, 70.0577, panchanga_offset
    )
    transitions = generate_panchanga_transitions(
        panchanga_date, 22.4707, 70.0577, panchanga_offset
    )

    destination = ROOT / "tests" / "python_reference.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps({
            "chart": chart,
            "daily_panchanga": daily,
            "transitions": transitions,
        }, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Wrote pinned Python reference to {destination}")


if __name__ == "__main__":
    main()
