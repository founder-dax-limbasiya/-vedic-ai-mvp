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
from datetime import date, datetime, time, timedelta
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
DASHA_BOUNDARY_TOLERANCE_DAYS = 2.0
VIMSHOTTARI_ORDER = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
REFERENCE_DASHA_YEAR_DAYS = 365.25636
NAKSHATRA_SPAN = 360.0 / 27.0
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
    from vedic_calc import calculate_chart, calculate_dasha
    from vedic_calc.chart.divisional import calculate_divisional_chart
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

    # Compare every standard divisional chart exposed by both engines.
    # These are discrete sign placements, so there is no angular tolerance:
    # each planet and the divisional ascendant must land in the same sign.
    divisional_results: dict[str, dict[str, int]] = {}
    for chart_key, reference_division in sorted(reference_chart.divisional_charts.items()):
        division = int(chart_key.lower().removeprefix("d"))
        swiss_division = calculate_divisional_chart(swiss_chart, division)

        reference_divisional_planets: dict[str, str] = {}
        for house in reference_division.houses:
            for occupant in house.occupants:
                reference_divisional_planets[str(occupant.celestial_body)] = str(occupant.sign).title()

        swiss_divisional_planets = {
            planet.name.title(): sign.name.title()
            for planet, sign in swiss_division.planets.items()
        }
        mismatches = 0
        for name in (*CLASSICAL_PLANETS, *NODES):
            reference_sign = reference_divisional_planets.get(name)
            swiss_sign = swiss_divisional_planets.get(name)
            if reference_sign is None or swiss_sign is None:
                failures.append(f"{chart_key.upper()} missing divisional placement for {name}")
                mismatches += 1
            elif reference_sign != swiss_sign:
                failures.append(
                    f"{chart_key.upper()} {name} sign mismatch: "
                    f"Skyfield={reference_sign}, Swiss={swiss_sign}"
                )
                mismatches += 1

        reference_div_asc = str(reference_division.ascendant.sign).title()
        swiss_div_asc = swiss_division.ascendant_sign.name.title()
        if reference_div_asc != swiss_div_asc:
            failures.append(
                f"{chart_key.upper()} ascendant sign mismatch: "
                f"Skyfield={reference_div_asc}, Swiss={swiss_div_asc}"
            )
            mismatches += 1
        divisional_results[chart_key.upper()] = {
            "mismatches": mismatches,
            "placements_checked": len(CLASSICAL_PLANETS) + len(NODES) + 1,
        }

    # Derive the reference Mahadasha schedule from the independent JPL
    # engine's own D1 Moon longitude. Do not consume jyotishganit's built-in
    # dasha dates here: its current Vimshottari helper obtains the Moon through
    # Skyfield's default ecliptic_latlon() frame, while its D1 path uses the
    # true ecliptic/equinox-of-date helper. That frame mismatch shifts the
    # dasha balance even though the D1 positions agree.
    reference_moon = next(
        planet for planet in reference_chart.d1_chart.planets
        if planet.celestial_body == "Moon"
    )
    reference_moon_lon = (
        SIGN_INDEX[str(reference_moon.sign).strip().lower()] * 30.0
        + float(reference_moon.sign_degrees)
    ) % 360.0
    reference_nakshatra_index = int(reference_moon_lon / NAKSHATRA_SPAN)
    reference_nakshatra_progress = reference_moon_lon % NAKSHATRA_SPAN
    reference_starting_lord = VIMSHOTTARI_ORDER[
        reference_nakshatra_index % len(VIMSHOTTARI_ORDER)
    ]
    reference_sequence = list(VIMSHOTTARI_ORDER)
    start_index = reference_sequence.index(reference_starting_lord)
    reference_sequence = reference_sequence[start_index:] + reference_sequence[:start_index]

    elapsed_fraction = reference_nakshatra_progress / NAKSHATRA_SPAN
    reference_first_duration_days = (
        VIMSHOTTARI_YEARS[reference_starting_lord] * REFERENCE_DASHA_YEAR_DAYS
    )
    reference_start = local_naive - timedelta(
        days=reference_first_duration_days * elapsed_fraction
    )
    reference_mahadashas = []
    current_reference_start = reference_start
    for lord in reference_sequence:
        duration_days = VIMSHOTTARI_YEARS[lord] * REFERENCE_DASHA_YEAR_DAYS
        current_reference_end = current_reference_start + timedelta(days=duration_days)
        reference_mahadashas.append({
            "lord": lord,
            "start": current_reference_start,
            "end": current_reference_end,
        })
        current_reference_start = current_reference_end

    # Compare the nine Mahadasha lords and their start/end boundaries.
    # The reference uses a sidereal year (365.25636 days); vedic-calc uses
    # 365.25 days, so allow a documented 2-day screening window.
    swiss_mahadashas = [
        period for period in calculate_dasha(swiss_chart, levels=1)
        if period.level == "mahadasha"
    ]
    swiss_dasha_lords = [period.lord.name.title() for period in swiss_mahadashas]
    reference_dasha_lords = [period["lord"] for period in reference_mahadashas]
    dasha_max_boundary_difference = 0.0
    dasha_sequence_matches = reference_dasha_lords == swiss_dasha_lords
    if not dasha_sequence_matches:
        failures.append(
            f"Mahadasha lord sequence mismatch: "
            f"Skyfield-D1={reference_dasha_lords}, Swiss={swiss_dasha_lords}"
        )
    elif len(reference_dasha_lords) != 9 or len(swiss_mahadashas) != 9:
        failures.append("Expected nine Mahadasha periods from each engine")
    else:
        for reference_period, swiss_period in zip(reference_mahadashas, swiss_mahadashas):
            lord = reference_period["lord"]
            start_delta = abs(
                (reference_period["start"] - swiss_period.start).total_seconds()
            ) / 86400.0
            end_delta = abs(
                (reference_period["end"] - swiss_period.end).total_seconds()
            ) / 86400.0
            dasha_max_boundary_difference = max(
                dasha_max_boundary_difference, start_delta, end_delta
            )
            if start_delta > DASHA_BOUNDARY_TOLERANCE_DAYS:
                failures.append(
                    f"{lord} Mahadasha start differs by {start_delta:.3f} days "
                    f"(limit {DASHA_BOUNDARY_TOLERANCE_DAYS:.1f})"
                )
            if end_delta > DASHA_BOUNDARY_TOLERANCE_DAYS:
                failures.append(
                    f"{lord} Mahadasha end differs by {end_delta:.3f} days "
                    f"(limit {DASHA_BOUNDARY_TOLERANCE_DAYS:.1f})"
                )

    if verbose:
        print(f"\n[{fixture.label}] {local_naive.isoformat()} {fixture.timezone} (UTC{offset_hours:+g})")
        print(f"  UTC: {utc_birth.isoformat()}")
        print(f"  Ayanamsa: Skyfield={jg_ayanamsa:.6f}°  Swiss={se_ayanamsa:.6f}°  Δ={ayanamsa_diff:.6f}°")
        print(f"  Ascendant: Skyfield={reference_asc:.6f}°  Swiss={swiss_asc:.6f}°  Δ={asc_diff:.6f}°")
        for name in (*CLASSICAL_PLANETS, *NODES):
            if name in diffs:
                print(f"  {name:<8} Δ={diffs[name]:.6f}°")
        for chart_name, stats in sorted(divisional_results.items()):
            print(
                f"  {chart_name:<4} {stats['placements_checked']} sign placements checked; "
                f"{stats['mismatches']} mismatch(es)"
            )
        print(
            f"  Mahadasha: sequence {'MATCH' if dasha_sequence_matches else 'MISMATCH'}; "
            f"max boundary Δ={dasha_max_boundary_difference:.3f} days "
            f"(limit {DASHA_BOUNDARY_TOLERANCE_DAYS:.1f} days)"
        )
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
