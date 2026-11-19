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
DASHA_BOUNDARY_TOLERANCE_DAYS = 3.0
VIMSHOTTARI_ORDER = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
REFERENCE_DASHA_YEAR_DAYS = 365.25  # Shared year basis to isolate D1-derived dasha math
NAKSHATRA_SPAN = 360.0 / 27.0
ASCENDANT_TOLERANCE = 0.15
PANCHANGA_BOUNDARY_TOLERANCE = 0.02
PANCHANGA_ANGLE_TOLERANCE = 0.10


@dataclass(frozen=True)
class Fixture:
    label: str
    birth_date: date
    birth_time: time
    timezone: str
    latitude: float
    longitude: float
    fold: int | None = None


FIXTURES = (
    Fixture("Mumbai 1990", date(1990, 3, 15), time(10, 30), "Asia/Kolkata", 19.0760, 72.8777),
    Fixture("Karmala 1996", date(1996, 7, 4), time(9, 10), "Asia/Kolkata", 18.4040, 75.1950),
    Fixture("New York 1988", date(1988, 6, 15), time(12, 0), "America/New_York", 40.7128, -74.0060),
    Fixture("Jamnagar 2026", date(2026, 1, 2), time(17, 40), "Asia/Kolkata", 22.4707, 70.0577),
    # Post-1945 standardized India Standard Time (+05:30).
    Fixture("Kolkata 1946", date(1946, 1, 15), time(12, 0), "Asia/Kolkata", 22.5726, 88.3639),
    # Non-hour civil offset (+05:45).
    Fixture("Kathmandu 2000", date(2000, 6, 1), time(8, 25), "Asia/Kathmandu", 27.7172, 85.3240),
    # Southern hemisphere summer time and near the end of the DE421 time span.
    Fixture("Sydney 2050", date(2050, 2, 15), time(7, 35), "Australia/Sydney", -33.8688, 151.2093),
    # Date-line / large positive UTC offset; local midnight maps to the previous UTC date.
    Fixture("Auckland 2001", date(2001, 1, 1), time(0, 30), "Pacific/Auckland", -36.8509, 174.7645),
    # Second occurrence of a repeated wall-clock time when DST ends.
    Fixture("New York DST fold", date(2025, 11, 2), time(1, 30), "America/New_York", 40.7128, -74.0060, fold=1),
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


def crossed_equal_varga_boundary(
    reference_sign: str,
    reference_degree: float,
    swiss_sign: str,
    swiss_degree: float,
    division: int,
) -> bool:
    """True when two close D1 positions straddle a standard equal-varga part.

    A discrete divisional sign can differ even when two continuous D1
    longitudes agree within a few thousandths of a degree. That is an
    expected boundary-sensitive result, not necessarily a formula error.
    D30 uses unequal divisions and is intentionally excluded here.
    """
    if division == 30 or reference_sign != swiss_sign:
        return False
    part_size = 30.0 / division
    reference_part = min(int(float(reference_degree) / part_size), division - 1)
    swiss_part = min(int(float(swiss_degree) / part_size), division - 1)
    return reference_part != swiss_part


def calculate_fixture(fixture: Fixture, verbose: bool = True) -> tuple[bool, list[str]]:
    # Lazy imports give a useful error when optional dependencies are absent.
    from jyotishganit import calculate_birth_chart
    from jyotishganit.components.panchanga import create_panchanga, get_lunar_phase, lunar_longitude, solar_longitude
    from jyotishganit.core.astronomical import get_timescale as jg_get_timescale
    from jyotishganit.core.constants import NAKSHATRAS as JG_NAKSHATRAS, TITHI_NAMES as JG_TITHI_NAMES, YOGA_NAMES as JG_YOGA_NAMES
    from vedic_calc import calculate_chart, calculate_dasha, calculate_panchanga
    from vedic_calc.chart.divisional import calculate_divisional_chart
    from vedic_calc.core.constants import Ayanamsa, Planet

    from app.timezones import resolve_local_birth

    local_birth, utc_birth, offset_hours = resolve_local_birth(
        fixture.birth_date, fixture.birth_time, fixture.timezone, fixture.fold
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

    # Birth-time Panchanga cross-check. The second engine computes the five
    # limbs through its separate Skyfield helper functions; the production
    # result comes from the Swiss Ephemeris panchanga module.
    panchanga_reference_time = jg_get_timescale().utc(
        utc_birth.year, utc_birth.month, utc_birth.day,
        utc_birth.hour, utc_birth.minute, utc_birth.second,
    )
    reference_panchanga = create_panchanga(
        local_naive, offset_hours, float(reference_chart.ayanamsa.value)
    )
    reference_phase = float(get_lunar_phase(panchanga_reference_time)) % 360.0
    reference_moon_tropical = float(lunar_longitude(panchanga_reference_time))
    reference_sun_tropical = float(solar_longitude(panchanga_reference_time))
    reference_moon_sidereal = (
        reference_moon_tropical - float(reference_chart.ayanamsa.value)
    ) % 360.0
    reference_sun_sidereal = (
        reference_sun_tropical - float(reference_chart.ayanamsa.value)
    ) % 360.0
    reference_yoga_longitude = (
        reference_sun_sidereal + reference_moon_sidereal
    ) % 360.0

    reference_panchanga_numbers = {
        "tithi": JG_TITHI_NAMES.index(reference_panchanga.tithi) + 1,
        "nakshatra": JG_NAKSHATRAS.index(reference_panchanga.nakshatra) + 1,
        "yoga": JG_YOGA_NAMES.index(reference_panchanga.yoga) + 1,
        "karana": int(reference_phase / 6.0) + 1,
    }
    swiss_panchanga = calculate_panchanga(
        year=local_birth.year,
        month=local_birth.month,
        day=local_birth.day,
        latitude=fixture.latitude,
        longitude=fixture.longitude,
        timezone_offset=offset_hours,
        ayanamsa=Ayanamsa.TRUE_CHITRAPAKSHA,
        hour=local_birth.hour,
        minute=local_birth.minute,
    )
    swiss_phase = (
        float(swiss_chart.planets[Planet.MOON].longitude)
        - float(swiss_chart.planets[Planet.SUN].longitude)
    ) % 360.0
    swiss_moon_sidereal = float(swiss_chart.planets[Planet.MOON].longitude)
    swiss_yoga_longitude = (
        float(swiss_chart.planets[Planet.SUN].longitude) + swiss_moon_sidereal
    ) % 360.0

    def distance_to_boundary(angle: float, width: float) -> float:
        remainder = float(angle) % width
        return min(remainder, width - remainder)

    panchanga_checks = (
        ("Tithi", reference_panchanga_numbers["tithi"], int(swiss_panchanga.tithi_number), reference_phase, swiss_phase, 12.0),
        ("Nakshatra", reference_panchanga_numbers["nakshatra"], int(swiss_panchanga.nakshatra.value), reference_moon_sidereal, swiss_moon_sidereal, NAKSHATRA_SPAN),
        ("Yoga", reference_panchanga_numbers["yoga"], int(swiss_panchanga.yoga_number), reference_yoga_longitude, swiss_yoga_longitude, NAKSHATRA_SPAN),
        ("Karana", reference_panchanga_numbers["karana"], int(swiss_panchanga.karana_number), reference_phase, swiss_phase, 6.0),
    )
    panchanga_boundary_sensitive = 0
    panchanga_mismatches = 0
    panchanga_angular_differences: dict[str, float] = {}
    for label, reference_number, swiss_number, reference_angle, swiss_angle, segment_width in panchanga_checks:
        angular_difference = circular_difference(reference_angle, swiss_angle)
        panchanga_angular_differences[label] = angular_difference
        if reference_number != swiss_number:
            near_boundary = (
                distance_to_boundary(reference_angle, segment_width) <= PANCHANGA_BOUNDARY_TOLERANCE
                or distance_to_boundary(swiss_angle, segment_width) <= PANCHANGA_BOUNDARY_TOLERANCE
            )
            if near_boundary and angular_difference <= PANCHANGA_ANGLE_TOLERANCE:
                panchanga_boundary_sensitive += 1
            else:
                panchanga_mismatches += 1
                failures.append(
                    f"birth Panchanga {label} mismatch: "
                    f"Skyfield={reference_number}, Swiss={swiss_number}; "
                    f"angle Δ={angular_difference:.6f}°"
                )

    expected_vara = local_naive.strftime("%A")
    reference_vara = str(reference_panchanga.vaara).split()[0]
    swiss_vara = str(swiss_panchanga.vara).split()[0]
    if reference_vara != expected_vara or swiss_vara != expected_vara:
        panchanga_mismatches += 1
        failures.append(
            f"birth Panchanga Vara mismatch: date={expected_vara}, "
            f"Skyfield={reference_panchanga.vaara}, Swiss={swiss_panchanga.vara}"
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
        boundary_sensitive = 0
        for name in (*CLASSICAL_PLANETS, *NODES):
            reference_sign = reference_divisional_planets.get(name)
            swiss_sign = swiss_divisional_planets.get(name)
            if reference_sign is None or swiss_sign is None:
                failures.append(f"{chart_key.upper()} missing divisional placement for {name}")
                mismatches += 1
            elif reference_sign != swiss_sign:
                ref_position = ref_planets[name]
                swiss_position = swiss_chart.planets[enum_planets[name]]
                if crossed_equal_varga_boundary(
                    str(ref_position.sign).title(),
                    float(ref_position.sign_degrees),
                    swiss_position.sign.name.title(),
                    float(swiss_position.degree_in_sign),
                    division,
                ):
                    boundary_sensitive += 1
                else:
                    failures.append(
                        f"{chart_key.upper()} {name} sign mismatch: "
                        f"Skyfield={reference_sign}, Swiss={swiss_sign}"
                    )
                    mismatches += 1

        reference_div_asc = str(reference_division.ascendant.sign).title()
        swiss_div_asc = swiss_division.ascendant_sign.name.title()
        if reference_div_asc != swiss_div_asc:
            if crossed_equal_varga_boundary(
                str(reference_chart.d1_chart.houses[0].sign).title(),
                float(reference_chart.d1_chart.houses[0].sign_degrees),
                swiss_chart.ascendant.sign.name.title(),
                float(swiss_chart.ascendant.degree_in_sign),
                division,
            ):
                boundary_sensitive += 1
            else:
                failures.append(
                    f"{chart_key.upper()} ascendant sign mismatch: "
                    f"Skyfield={reference_div_asc}, Swiss={swiss_div_asc}"
                )
                mismatches += 1
        divisional_results[chart_key.upper()] = {
            "mismatches": mismatches,
            "boundary_sensitive": boundary_sensitive,
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
    # Both derived reference and Swiss schedule use 365.25-day years here.
    # This normalizes the year convention so we are checking Moon-derived
    # balance and lord sequencing, not two different definitions of a year.
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
        print(f"\n[{fixture.label}] {local_naive.isoformat()} {fixture.timezone} (UTC{offset_hours:+g}, fold={fixture.fold})")
        print(f"  UTC: {utc_birth.isoformat()}")
        print(f"  Ayanamsa: Skyfield={jg_ayanamsa:.6f}°  Swiss={se_ayanamsa:.6f}°  Δ={ayanamsa_diff:.6f}°")
        print(f"  Ascendant: Skyfield={reference_asc:.6f}°  Swiss={swiss_asc:.6f}°  Δ={asc_diff:.6f}°")
        print(
            f"  Birth Panchanga: {4 - panchanga_mismatches}/{4} limb indices match; "
            f"{panchanga_boundary_sensitive} boundary-sensitive; "
            f"max angular Δ={max(panchanga_angular_differences.values()):.6f}°"
        )
        for name in (*CLASSICAL_PLANETS, *NODES):
            if name in diffs:
                print(f"  {name:<8} Δ={diffs[name]:.6f}°")
        for chart_name, stats in sorted(divisional_results.items()):
            print(
                f"  {chart_name:<4} {stats['placements_checked']} sign placements checked; "
                f"{stats['mismatches']} substantive mismatch(es), "
                f"{stats['boundary_sensitive']} boundary-sensitive"
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
