"""Adapter around existing Vedic calculation code; no planetary maths here."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any

import swisseph as swe

from .schemas import ChartRequest

_ENGINE_LOCK = RLock()  # Swiss Ephemeris exposes process-global sidereal settings.
_AYANAMSA_NAMES = {
    "lahiri": "LAHIRI",
    "raman": "RAMAN",
    "kp": "KP",
    "true_chitrapaksha": "TRUE_CHITRAPAKSHA",
}
_PLANET_SWISS_IDS = {
    "SUN": swe.SUN,
    "MOON": swe.MOON,
    "MARS": swe.MARS,
    "MERCURY": swe.MERCURY,
    "JUPITER": swe.JUPITER,
    "VENUS": swe.VENUS,
    "SATURN": swe.SATURN,
    "RAHU": swe.MEAN_NODE,
}


def _ephemeris_name(return_flags: int) -> str:
    if return_flags & swe.FLG_JPLEPH:
        return "JPL"
    if return_flags & swe.FLG_SWIEPH:
        return "Swiss Ephemeris"
    if return_flags & swe.FLG_MOSEPH:
        return "Moshier analytical fallback"
    return "Unknown"


def _julian_day_utc(utc_dt: datetime) -> float:
    utc = utc_dt.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0
    return swe.julday(utc.year, utc.month, utc.day, hour)


def _enum_label(value: Any) -> str:
    """Format enum names for display, including compound Sanskrit names."""
    return str(value.name).replace("_", " ").title()


def _position_payload(name: str, position: Any, retrograde: bool | None) -> dict[str, Any]:
    nak = position.nakshatra_info
    return {
        "planet": name.title(),
        "longitude": round(float(position.longitude), 6),
        "sign": _enum_label(position.sign),
        "degree_in_sign": round(float(position.degree_in_sign), 4),
        "nakshatra": _enum_label(nak.nakshatra),
        "pada": int(nak.pada),
        "nakshatra_lord": _enum_label(nak.lord),
        "retrograde": bool(position.is_retrograde if retrograde is None else retrograde),
    }


def generate_chart(
    request: ChartRequest,
    local_birth: datetime,
    utc_birth: datetime,
    timezone_offset: float,
) -> dict[str, Any]:
    """Call the reused engine and add explicit ephemeris/speed diagnostics."""
    try:
        from vedic_calc import calculate_chart, calculate_dasha, calculate_panchanga
        from vedic_calc.chart.divisional import calculate_divisional_chart
        from vedic_calc.core.constants import Ayanamsa, Planet
    except ImportError as exc:
        raise RuntimeError(
            "The pinned vedic-calc dependency is not installed. Run `pip install -e api`."
        ) from exc

    ayanamsa = Ayanamsa[_AYANAMSA_NAMES[request.ayanamsa]]
    # Keep sidereal-mode changes, chart generation and diagnostics in one
    # critical section because pyswisseph maintains process-global settings.
    with _ENGINE_LOCK:
        chart = calculate_chart(
            year=local_birth.year,
            month=local_birth.month,
            day=local_birth.day,
            hour=local_birth.hour,
            minute=local_birth.minute,
            second=local_birth.second,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone_offset=timezone_offset,
            ayanamsa=ayanamsa,
        )
        jd_ut = _julian_day_utc(utc_birth)
        retrograde_by_planet: dict[str, bool] = {"KETU": True}
        ephemeris_by_planet: dict[str, str] = {}
        for planet_name, swiss_id in _PLANET_SWISS_IDS.items():
            _, source_flags = swe.calc_ut(jd_ut, swiss_id, 0)
            speed_values, speed_flags = swe.calc_ut(jd_ut, swiss_id, swe.FLG_SPEED)
            retrograde_by_planet[planet_name] = float(speed_values[3]) < 0.0
            ephemeris_by_planet[planet_name] = _ephemeris_name(source_flags)
            if _ephemeris_name(speed_flags) != ephemeris_by_planet[planet_name]:
                ephemeris_by_planet[planet_name] += " (speed-source differs)"

        retrograde_by_planet["RAHU"] = True

        planets = []
        for planet_enum, position in chart.planets.items():
            name = planet_enum.name
            planets.append(_position_payload(name, position, retrograde_by_planet.get(name)))
        planets.sort(key=lambda item: [
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
        ].index(item["planet"]))

        houses = [
            {
                "house": int(house.house_number),
                "sign": _enum_label(house.sign),
                "lord": _enum_label(house.lord),
            }
            for house in chart.houses
        ]
        ascendant = _position_payload("ASCENDANT", chart.ascendant, False)
        panchanga = calculate_panchanga(
            year=local_birth.year,
            month=local_birth.month,
            day=local_birth.day,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone_offset=timezone_offset,
            ayanamsa=ayanamsa,
            hour=local_birth.hour,
            minute=local_birth.minute,
        )
        panchanga_payload = {
            "vara": panchanga.vara,
            "tithi_number": int(panchanga.tithi_number),
            "tithi_name": panchanga.tithi_name,
            "nakshatra": _enum_label(panchanga.nakshatra),
            "yoga_number": int(panchanga.yoga_number),
            "yoga_name": panchanga.yoga_name,
            "karana_number": int(panchanga.karana_number),
            "karana_name": panchanga.karana_name,
            "sunrise_local": panchanga.sunrise.isoformat() if panchanga.sunrise else None,
            "sunset_local": panchanga.sunset.isoformat() if panchanga.sunset else None,
            "calculation_time": "Exact local birth time",
        }
        dashas = calculate_dasha(chart, levels=1)
        dasha_payload = [
            {
                "lord": period.lord.name.title(),
                "start_local": period.start.isoformat(),
                "end_local": period.end.isoformat(),
                "duration_years": round(float(period.duration_years), 4),
            }
            for period in dashas
            if period.level == "mahadasha"
        ]

        # Generate the 15 standard divisional charts supported by the
        # pinned engine. D1 is added from the already-calculated birth chart.
        divisional_payload: dict[str, Any] = {
            "D1": {
                "division": 1,
                "name": "Rasi",
                "ascendant_sign": _enum_label(chart.ascendant.sign),
                "planets": [
                    {"planet": planet.name.title(), "sign": _enum_label(position.sign)}
                    for planet, position in sorted(
                        chart.planets.items(), key=lambda item: item[0].value
                    )
                ],
            }
        }
        standard_divisions = (2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)
        for division in standard_divisions:
            varga = calculate_divisional_chart(chart, division)
            divisional_payload[f"D{division}"] = {
                "division": int(varga.division),
                "name": str(varga.name),
                "ascendant_sign": _enum_label(varga.ascendant_sign),
                "planets": [
                    {"planet": planet.name.title(), "sign": _enum_label(sign)}
                    for planet, sign in sorted(
                        varga.planets.items(), key=lambda item: item[0].value
                    )
                ],
            }

    return {
        "calculation": {
            "engine": "vedic-calc",
            "engine_commit": "620d54560ee7e108496495eeb17054a52630a0bf",
            "ephemeris_by_planet": ephemeris_by_planet,
            "retrograde_speed_flag": "SEFLG_SPEED",
            "disclaimer": "Ephemeris source is reported per planet. If Moshier appears, Swiss Ephemeris data files were unavailable for that body and its analytical fallback was used.",
        },
        "birth": {
            "local_datetime": local_birth.isoformat(),
            "utc_datetime": utc_birth.isoformat(),
            "timezone": request.timezone,
            "utc_offset_hours": timezone_offset,
            "latitude": request.latitude,
            "longitude": request.longitude,
        },
        "settings": {
            "ayanamsa": request.ayanamsa,
            "house_system": "Whole Sign",
        },
        "ayanamsa_degrees": round(float(chart.ayanamsa_degrees), 6),
        "ascendant": ascendant,
        "planets": planets,
        "houses": houses,
        "birth_panchanga": panchanga_payload,
        "vimshottari_mahadashas": dasha_payload,
        "divisional_charts": divisional_payload,
    }


def generate_daily_panchanga(
    calendar_date: Any,
    latitude: float,
    longitude: float,
    timezone_offset: float,
) -> dict[str, Any]:
    """Calculate daily Panchanga at local sunrise under the shared ephemeris lock."""
    try:
        from vedic_calc import calculate_panchanga
        from vedic_calc.core.constants import Ayanamsa
    except ImportError as exc:
        raise RuntimeError("The pinned vedic-calc dependency is not installed.") from exc

    with _ENGINE_LOCK:
        panchanga = calculate_panchanga(
            year=calendar_date.year,
            month=calendar_date.month,
            day=calendar_date.day,
            latitude=latitude,
            longitude=longitude,
            timezone_offset=timezone_offset,
            ayanamsa=Ayanamsa.LAHIRI,
        )
        return {
            "date": calendar_date.isoformat(),
            "utc_offset_hours": timezone_offset,
            "ayanamsa": "lahiri",
            "calculation_time": "Local sunrise" if panchanga.sunrise else "Solar-noon fallback (sunrise unavailable)",
            "vara": panchanga.vara,
            "tithi_number": int(panchanga.tithi_number),
            "tithi_name": panchanga.tithi_name,
            "nakshatra": panchanga.nakshatra.name.title(),
            "yoga_number": int(panchanga.yoga_number),
            "yoga_name": panchanga.yoga_name,
            "karana_number": int(panchanga.karana_number),
            "karana_name": panchanga.karana_name,
            "sunrise_local": panchanga.sunrise.isoformat() if panchanga.sunrise else None,
            "sunset_local": panchanga.sunset.isoformat() if panchanga.sunset else None,
        }
