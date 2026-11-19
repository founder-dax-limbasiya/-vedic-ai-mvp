#!/usr/bin/env python3
"""Cross-check Vedic chart longitudes against an independent JPL/Skyfield engine.

This is an engineering regression harness, not a claim that either astrology
system predicts real-world events. The two libraries implement similar but
not necessarily identical conventions; read docs/accuracy-validation.md before
changing the comparison thresholds.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

# The official CDS host for Skyfield's Hipparcos file was reported unavailable
# in October 2026. Use a dated Internet Archive capture of the same CDS file
# unless the operator explicitly supplies another verified compatible mirror.
HIPPARCOS_ARCHIVE_URL = (
    "https://web.archive.org/web/20250627160000if_/"
    "https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat"
)


def configure_hipparcos_source() -> str:
    from skyfield.data import hipparcos

    source = os.getenv("HIPPARCOS_CATALOG_URL", HIPPARCOS_ARCHIVE_URL).strip()
    if not source.startswith(("https://", "http://")):
        raise ValueError("HIPPARCOS_CATALOG_URL must be an HTTP(S) URL")
    # jyotishganit's astronomical module imports this same module object, so
    # changing its URL before importing jyotishganit redirects its lazy load.
    hipparcos.URL = source
    return source


SIGN_INDEX = {
    "aries": 0, "taurus": 1, "gemini": 2, "cancer": 3,
    "leo": 4, "virgo": 5, "libra": 6, "scorpio": 7,
    "sagittarius": 8, "capricorn": 9, "aquarius": 10, "pisces": 11,
}

# Initial regression tolerances (degrees), deliberately separate by output.
AYANAMSA_TOLERANCE = 0.05
CLASSICAL_PLANET_TOLERANCE = 0.10
NODE_TOLERANCE = 0.15
ASCENDANT_TOLERANCE = 0.15


@dataclass(frozen=True)
class Fixture:
    label: str
    birth_date: date
    birth_time: time
    timezone: str
    latitude: float
    longitude: float


FIXTURES = (
    Fixture("Mumbai 1990", date(1990, 3, 15), time(10, 30), "Asia/Kolkata", 19.0760, 72.8777),
    Fixture("Karmala 1996", date(1996, 7, 4), time(9, 10), "Asia/Kolkata", 18.4040, 75.1950),
    Fixture("New York 1988", date(1988, 6, 15), time(12, 0), "America/New_York", 40.7128, -74.0060),
    Fixture("Jamnagar 2026", date(2026, 1, 2), time(17, 40), "Asia/Kolkata", 22.4707, 70.0577),
)

CLASSICAL_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NODES = ("Rahu", "Ketu")


def circular_difference(a: float, b: float) -> float:
    """Smallest absolute angular distance in degrees."""
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def position_longitude(position: Any) -> float:
    sign = str(position.sign).strip().lower()
    if sign not in SIGN_INDEX:
        raise ValueError(f"Unknown sign name from reference engine: {position.sign!r}")
    return (SIGN_INDEX[sign] * 30.0 + float(position.sign_degrees)) % 360.0


def calculate_fixture(fixture: Fixture, verbose: bool = True) -> tuple[bool, list[str]]:
    # Lazy imports give a useful error when optional dependencies are absent.
    from jyotishganit import calculate_birth_chart
    from vedic_calc import calculate_chart
    from vedic_calc.core.constants import Ayanamsa, Planet

    from app.timezones import resolve_local_birth

    local_birth, utc_birth, offset_hours = resolve_local_birth(
        fixture.birth_date, fixture.birth_time, fixture.timezone
    )
    local_naive = datetime.combine(fixture.birth_date, fixture.birth_time)

    # Reference A: MIT-licensed Skyfield / JPL DE421 / True Chitra Paksha.
    reference_chart = calculate_birth_chart(
        birth_date=local_naive,
        latitude=fixture.latitude,
        longitude=fixture.longitude,
        timezone_offset=offset_hours,
    )

    # Reference B: pinned Swiss Ephemeris implementation / True Chitrapaksha.
    swiss_chart = calculate_chart(
        year=local_birth.year,
        month=local_birth.month,
        day=local_birth.day,
        hour=local_birth.hour,
        minute=local_birth.minute,
        second=local_birth.second,
        latitude=fixture.latitude,
        longitude=fixture.longitude,
        timezone_offset=offset_hours,
        ayanamsa=Ayanamsa.TRUE_CHITRAPAKSHA,
    )

    failures: list[str] = []
    jg_ayanamsa = float(reference_chart.ayanamsa.value)
    se_ayanamsa = float(swiss_chart.ayanamsa_degrees)
    ayanamsa_diff = abs(jg_ayanamsa - se_ayanamsa)
    if ayanamsa_diff > AYANAMSA_TOLERANCE:
        failures.append(
            f"ayanamsa mismatch {ayanamsa_diff:.6f}° > {AYANAMSA_TOLERANCE:.3f}°"
        )

    ref_planets = {p.celestial_body: p for p in reference_chart.d1_chart.planets}
    enum_planets = {
        "Sun": Planet.SUN, "Moon": Planet.MOON, "Mars": Planet.MARS,
        "Mercury": Planet.MERCURY, "Jupiter": Planet.JUPITER,
        "Venus": Planet.VENUS, "Saturn": Planet.SATURN,
        "Rahu": Planet.RAHU, "Ketu": Planet.KETU,
    }

    diffs: dict[str, float] = {}
    for name in (*CLASSICAL_PLANETS, *NODES):
        if name not in ref_planets or enum_planets[name] not in swiss_chart.planets:
            failures.append(f"missing planet {name}")
            continue
        reference_lon = position_longitude(ref_planets[name])
        swiss_lon = float(swiss_chart.planets[enum_planets[name]].longitude)
        delta = circular_difference(reference_lon, swiss_lon)
        diffs[name] = delta
        limit = NODE_TOLERANCE if name in NODES else CLASSICAL_PLANET_TOLERANCE
        if delta > limit:
            failures.append(f"{name} mismatch {delta:.6f}° > {limit:.3f}°")

    reference_asc = position_longitude(reference_chart.d1_chart.houses[0])
    swiss_asc = float(swiss_chart.ascendant.longitude)
    asc_diff = circular_difference(reference_asc, swiss_asc)
    if asc_diff > ASCENDANT_TOLERANCE:
        failures.append(
            f"ascendant mismatch {asc_diff:.6f}° > {ASCENDANT_TOLERANCE:.3f}°"
        )

    if verbose:
        print(f"\n[{fixture.label}] {local_naive.isoformat()} {fixture.timezone} (UTC{offset_hours:+g})")
        print(f"  UTC: {utc_birth.isoformat()}")
        print(f"  Ayanamsa: Skyfield={jg_ayanamsa:.6f}°  Swiss={se_ayanamsa:.6f}°  Δ={ayanamsa_diff:.6f}°")
        print(f"  Ascendant: Skyfield={reference_asc:.6f}°  Swiss={swiss_asc:.6f}°  Δ={asc_diff:.6f}°")
        for name in (*CLASSICAL_PLANETS, *NODES):
            if name in diffs:
                print(f"  {name:<8} Δ={diffs[name]:.6f}°")
        print("  RESULT: " + ("FAIL" if failures else "PASS"))
        for issue in failures:
            print("    - " + issue)

    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true", help="Print only failing fixture details.")
    args = parser.parse_args()
    try:
        hipparcos_source = configure_hipparcos_source()
        print(f"Hipparcos catalogue source: {hipparcos_source}")
        results = [calculate_fixture(f, verbose=not args.quiet) for f in FIXTURES]
    except ImportError as exc:
        print(
            "Missing optional accuracy dependencies. Install with: "
            "pip install -e './api[accuracy]'",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    except Exception as exc:
        print(f"Cross-validation could not complete: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    passed = sum(1 for ok, _ in results if ok)
    failed = len(results) - passed
    print(f"\nCross-validation summary: {passed}/{len(results)} fixtures passed.")
    if failed:
        return 1
    print(
        "Both engines agree within the documented starting tolerances. "
        "This is a cross-engine regression check, not proof of absolute accuracy."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
