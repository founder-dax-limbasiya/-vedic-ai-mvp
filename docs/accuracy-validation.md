# Independent calculation validation

## Reference engines

The app's production calculation adapter uses the pinned `vedic-calc` library on Swiss Ephemeris. This validation tool optionally compares it with `jyotishganit==0.1.7`, a separate MIT-licensed Python project using Skyfield and JPL DE421.

The reference package is not installed in normal runtime deployments. It is isolated in the optional `accuracy` dependency group because its JPL ephemeris and Hipparcos star-catalogue data are only needed for development validation.

## Run the check

From the repository root:

```bash
pip install -e './api[accuracy]'
python tools/cross_validate.py
```

The first run downloads JPL DE421 and a Hipparcos catalogue file. Allow enough disk space and network access. The GitHub Actions workflow caches the downloaded files for later runs.

## Hipparcos catalogue source

Skyfield normally requests `hip_main.dat` from CDS/VizieR. On October 30, 2026, a Skyfield maintainer issue reported that the CDS host was unavailable. The issue author reported success using a dated Internet Archive copy of that same CDS catalogue. This harness therefore uses the archived capture from 2025-06-27 by default; set `HIPPARCOS_CATALOG_URL` to a verified compatible HTTP(S) mirror to override it.

- Skyfield issue: https://github.com/skyfielders/python-skyfield/issues/1155
- Archived catalogue capture: https://web.archive.org/web/20250627160000if_/https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat

The Hipparcos mission catalogue is a historical fixed catalogue. The archive is used to make the optional independent check repeatable while the primary CDS host is unavailable; it is not used by the production Vedic API.

## Conventions being aligned

- Both engines receive the same local civil birth date/time, numeric UTC offset resolved from the same IANA timezone, latitude and longitude.
- Both are set to True Chitra Paksha / True Chitrapaksha.
- Both use a whole-sign D1/Rashi chart.
- Both use mean lunar nodes (Rahu/Ketu).
- Longitudes are compared as circular angles, not ordinary linear differences.
- The independent engine uses apparent positions and DE421 JPL data; the app engine uses Swiss Ephemeris. Small differences can arise from ephemeris source, barycentre/body model, apparent-coordinate implementation and precise ayanamsa realization.

## Initial engineering tolerances

The harness starts with the following maximum absolute angular differences:

| Output | Limit |
|---|---:|
| Ayanamsa value | 0.05° |
| Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn | 0.10° |
| Rahu and Ketu | 0.15° |
| Ascendant | 0.15° |

These are screening thresholds for gross disagreements, not an accuracy certification or astrological truth claim. If a fixture fails, investigate time conversion, ayanamsa, coordinate frame, ephemeris source and body/node conventions before changing any threshold. Do not simply widen tolerances to make CI green.

## Current scope

This tool compares D1 longitudes, ascendant and ayanamsa only. It does not validate divisional charts, house lord interpretations, shadbala, yogas, doshas, panchanga transitions or dasha period start/end dates. Those need separate convention-matched fixtures before production release.
