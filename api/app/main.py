from __future__ import annotations

import os
from zoneinfo import available_timezones

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import generate_chart
from .location_timezone import timezone_at
from .place_search import PlaceSearchUnavailable, search_places
from .schemas import ChartRequest
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
