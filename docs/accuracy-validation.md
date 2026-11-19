# Independent calculation validation

## Reference engines

The production chart adapter uses the pinned `vedic-calc` library on Swiss Ephemeris. This optional validation tool compares it with `jyotishganit==0.1.7`, a separate MIT-licensed Python project using Skyfield and JPL DE421.

The reference package is not installed in normal runtime deployments. It is isolated in the optional `accuracy` dependency group because its JPL ephemeris and Hipparcos catalogue data are only needed for development validation.

## Run the check

From the repository root:

```bash
pip install -e './api[accuracy]'
python tools/cross_validate.py
```

The first run downloads JPL DE421 and a Hipparcos catalogue file. Allow enough disk space and network access. The GitHub Actions workflow caches the downloaded files for later runs.

## Hipparcos catalogue source

Skyfield normally requests `hip_main.dat` from CDS/VizieR. A Skyfield maintainer issue reported that the CDS host was unavailable; the issue author reported success using a dated Internet Archive copy of that same CDS catalogue. This harness therefore uses the archived capture from 2025-06-27 by default; set `HIPPARCOS_CATALOG_URL` to a verified compatible HTTP(S) mirror to override it.

- Skyfield issue: https://github.com/skyfielders/python-skyfield/issues/1155
- Archived catalogue capture: https://web.archive.org/web/20250627160000if_/https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat

The Hipparcos mission catalogue is a historical fixed catalogue. The archive is used to make the optional independent check repeatable; it is not used by the production Vedic API.

## Conventions being aligned

- Both engines receive the same local civil birth date/time, numeric UTC offset resolved from the same IANA timezone, latitude and longitude.
- Both are set to True Chitra Paksha / True Chitrapaksha.
- Both use a whole-sign D1/Rashi chart.
- Both use mean lunar nodes (Rahu/Ketu).
- Longitudes are compared as circular angles, not ordinary linear differences.
- The independent engine uses apparent positions and DE421 JPL data; the app engine uses Swiss Ephemeris. Small differences can arise from ephemeris source, barycentre/body model, apparent-coordinate implementation and precise ayanamsa realization.

## Initial engineering tolerances

The harness uses these maximum absolute angular differences as screening thresholds:

| Output | Limit |
|---|---:|
| Ayanamsa value | 0.05° |
| Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn | 0.10° |
| Rahu and Ketu | 0.15° |
| Ascendant | 0.15° |

These are screening thresholds for gross disagreements, not an accuracy certification or astrological truth claim. If a fixture fails, investigate time conversion, ayanamsa, coordinate frame, ephemeris source and body/node conventions before changing any threshold. Do not simply widen tolerances to make CI green.

## Divisional chart comparison

The harness compares 15 standard divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60). For each fixture, it checks the discrete sign assigned to each of the nine planets and the ascendant.

A small D1 longitude difference can place two engines' values on opposite sides of an equal-varga subdivision boundary. The resulting D-chart sign can therefore differ even when the underlying D1 values are close. For the equal divisions, the harness detects this exact case and reports it separately as **boundary-sensitive** rather than treating it as a substantive calculation disagreement. D30 has unequal traditional segments, so it is not included in that equal-boundary classification. All such cases remain visible in the run output; the tolerance is not widened to hide them.

This check compares discrete sign placements, not every divisional longitude, bhava or school-specific varga interpretation.

## Vimshottari Mahadasha comparison

The independent JPL engine's built-in Vimshottari helper is **not** used as the comparison target. Code inspection shows it gets the Moon with Skyfield's default `ecliptic_latlon()`, while the JPL engine's D1 chart path uses its explicit true ecliptic/equinox-of-date frame conversion. Those are different coordinate frames; its own Dasha helper can therefore produce a different birth-nakshatra balance from its own D1 Moon placement.

To avoid comparing one engine's D1 output against a different coordinate path inside that same engine, the harness derives the reference Vimshottari schedule from the JPL engine's D1 Moon position. It applies the standard 27 equal nakshatra divisions and nine-lord sequence. Both schedules use a common 365.25-day year basis to isolate the Moon-derived starting balance and lord sequence from a small difference in year-length convention.

The three-day Mahadasha boundary limit is a screening threshold, not a licence to ignore larger discrepancies. The harness reports the maximum boundary difference for every fixture. This validates Mahadasha lord order and boundary timing only; it does not validate antardasha/pratyantardasha or an astrological interpretation.

## Latest measured result — 2026-11-19

GitHub Actions run [44538678440](https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44538678440) passed all 9 fixtures:

1. Mumbai 1990
2. Karmala 1996
3. New York 1988
4. Jamnagar 2026
5. Kolkata 1946
6. Kathmandu 2000
7. Sydney 2050
8. Auckland 2001 (local midnight falls on the previous UTC date)
9. New York DST fold 2025 (second 01:30 occurrence)

| Compared output | Maximum observed difference | Screening limit |
|---|---:|---:|
| Ayanamsa | 0.004565° | 0.05° |
| Ascendant | 0.077954° | 0.15° |
| Nine planetary longitudes, including mean nodes | 0.007220° | 0.10° classical planets / 0.15° nodes |
| Mahadasha boundary timing | 2.324 days | 3 days |

Across the 9 fixtures, all 15 vargas were checked for nine planets and the ascendant (1,350 discrete sign placements). There were **zero substantive mismatches** and **one boundary-sensitive D24 placement** (Auckland 2001). The nine Mahadasha lord sequences matched.

These results apply only to the listed fixtures and exact pinned engine versions/settings. They are not a universal astronomical accuracy certification and do not validate every era, latitude, time, divisional longitude or traditional rule.

## Not covered by this check

- Birth-time or daily Panchanga values and transitions.
- Antardasha, pratyantardasha and deeper Dasha boundaries.
- Retrograde station-time edge cases.
- Shadbala, yogas, doshas, compatibility, muhurta or interpretation text.
- Unknown or approximate birth times.
