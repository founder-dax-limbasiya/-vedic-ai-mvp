from __future__ import annotations

import os
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import generate_chart, generate_daily_panchanga
from .location_timezone import timezone_at
from .place_search import PlaceSearchUnavailable, search_places
from .schemas import ChartRequest, DailyPanchangaRequest
from .timezones import (
    AmbiguousLocalTimeError,
    NonexistentLocalTimeError,
    TimezoneInputError,
    resolve_local_birth,
)

app = FastAPI(
    title="Vedic AI API",
    version="0.1.0",
    description="Calculation API for a privacy-first Vedic astrology PWA.",
)

origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, object]:
    try:
        import vedic_calc  # noqa: F401
        engine_ready = True
    except ImportError:
        engine_ready = False
    return {
        "status": "ok" if engine_ready else "degraded",
        "api": "vedic-ai-api",
        "calculation_engine_installed": engine_ready,
        "birth_profiles_persisted": False,
    }


@app.get("/v1/timezones")
def timezones(q: str = "") -> dict[str, list[str]]:
    query = q.strip().lower()
    zones = sorted(available_timezones())
    if query:
        zones = [zone for zone in zones if query in zone.lower()]
    return {"timezones": zones}


@app.post("/v1/chart")
def create_chart(payload: ChartRequest) -> dict[str, object]:
    try:
        birth_zone = ZoneInfo(payload.timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_timezone", "message": "Unknown IANA timezone. Example: Asia/Kolkata"}) from exc
    if payload.birth_date > datetime.now(birth_zone).date():
        raise HTTPException(status_code=422, detail={"code": "future_birth_date", "message": "Birth date cannot be in the future."})
    try:
        local_birth, utc_birth, offset_hours = resolve_local_birth(
            payload.birth_date, payload.birth_time, payload.timezone, payload.fold
        )
    except AmbiguousLocalTimeError as exc:
        raise HTTPException(status_code=422, detail={"code": "ambiguous_local_time", "message": str(exc)}) from exc
    except NonexistentLocalTimeError as exc:
        raise HTTPException(status_code=422, detail={"code": "nonexistent_local_time", "message": str(exc)}) from exc
    except TimezoneInputError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_timezone", "message": str(exc)}) from exc

    try:
        result = generate_chart(payload, local_birth, utc_birth, offset_hours)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"code": "engine_unavailable", "message": str(exc)}) from exc
    except Exception as exc:  # Keep implementation details and birth inputs out of client errors.
        raise HTTPException(status_code=422, detail={"code": "calculation_failed", "message": "The chart could not be calculated for these inputs. Check the date, time and location."}) from exc
    return result


@app.post("/v1/panchanga")
def daily_panchanga(payload: DailyPanchangaRequest) -> dict[str, object]:
    """Calculate the five Panchanga limbs at local sunrise for a place/date."""
    try:
        # Resolve the offset for local noon; ordinary DST transitions occur
        # before sunrise, so this is also the sunrise offset for normal civil days.
        _, _, offset_hours = resolve_local_birth(
            payload.calendar_date, time(12, 0), payload.timezone
        )
    except (TimezoneInputError, NonexistentLocalTimeError, AmbiguousLocalTimeError) as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_local_date", "message": str(exc)},
        ) from exc

    try:
        result = generate_daily_panchanga(
            payload.calendar_date,
            payload.latitude,
            payload.longitude,
            offset_hours,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "engine_unavailable", "message": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "panchanga_calculation_failed", "message": "The Panchanga could not be calculated for this place and date."},
        ) from exc

    return {
        **result,
        "timezone": payload.timezone,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
    }


@app.get("/v1/places")
def places(q: str) -> dict[str, object]:
    """One-shot user-triggered place lookup; this is not autocomplete."""
    try:
        return {"places": search_places(q), "attribution": "© OpenStreetMap contributors"}
    except PlaceSearchUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/place-timezone")
def place_timezone(latitude: float, longitude: float) -> dict[str, str]:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise HTTPException(status_code=422, detail="Latitude or longitude is out of range")
    try:
        return {"timezone": timezone_at(latitude, longitude)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
