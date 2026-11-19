"""Resolve local civil birth times safely using the IANA timezone database."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class TimezoneInputError(ValueError):
    """Invalid IANA timezone or local wall-clock time."""


class AmbiguousLocalTimeError(TimezoneInputError):
    """A wall-clock time occurred twice and the user must choose a fold."""


class NonexistentLocalTimeError(TimezoneInputError):
    """A wall-clock time was skipped during a timezone transition."""


def resolve_local_birth(
    birth_date: date,
    birth_time: time,
    timezone_name: str,
    fold: int | None = None,
) -> tuple[datetime, datetime, float]:
    """Return (local aware, UTC aware, offset hours) for a birthplace time.

    `fold=0` selects the first occurrence and `fold=1` the second occurrence
    when clocks move backward. Nonexistent spring-forward times are rejected.
    """
    if birth_time.tzinfo is not None:
        raise TimezoneInputError("birth_time must be a local wall-clock time without a UTC offset")
    if fold not in (None, 0, 1):
        raise TimezoneInputError("fold must be 0, 1, or omitted")
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise TimezoneInputError("Unknown IANA timezone. Example: Asia/Kolkata") from exc

    wall = datetime.combine(birth_date, birth_time.replace(tzinfo=None))
    valid: dict[int, datetime] = {}
    for candidate_fold in (0, 1):
        candidate = wall.replace(tzinfo=zone, fold=candidate_fold)
        round_trip = candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
        if round_trip == wall:
            valid[candidate_fold] = candidate

    if not valid:
        raise NonexistentLocalTimeError(
            "That local time did not occur because the clocks moved forward. Check the birth time."
        )

    offsets = {candidate.utcoffset() for candidate in valid.values()}
    ambiguous = len(offsets) > 1
    if ambiguous and fold is None:
        raise AmbiguousLocalTimeError(
            "That local time occurred twice because the clocks moved backward. Choose the first or second occurrence."
        )

    chosen_fold = fold if fold is not None else next(iter(valid))
    if chosen_fold not in valid:
        chosen_fold = next(iter(valid))
    local_aware = valid[chosen_fold]
    utc_aware = local_aware.astimezone(timezone.utc)
    offset = local_aware.utcoffset()
    if offset is None:
        raise TimezoneInputError("Could not resolve UTC offset for this birth time")
    return local_aware, utc_aware, offset.total_seconds() / 3600.0
