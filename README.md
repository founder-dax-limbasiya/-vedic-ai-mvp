# Vedic AI — MVP starter

A mobile-first, privacy-conscious Vedic birth-chart PWA with a Python API. “Jyoti” is a working title only; no trademark/name clearance has been performed.

## Current scope
- Vedic birth chart integration through the open-source `vedic-calc` library.
- D1 / Rashi placements, ascendant, whole-sign houses, nakshatra/pada and Vimshottari Mahadasha.
- Birth-time Panchanga: Vara, Tithi, Nakshatra, Yoga and Karana, plus local sunrise/sunset.
- D1 plus 15 standard divisional charts: D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60.
- IANA timezone handling, including ambiguous and nonexistent local birth times.
- Offline coordinate-to-IANA-timezone lookup using a pinned boundary dataset.
- Swiss Ephemeris speed diagnostics for retrograde status and per-planet source reporting.
- Mobile-first installable PWA with a divisional-chart selector, JSON export and Android/iOS app icons.
- No account database, saved birth profiles, payments, ads, analytics, or AI interpretations in this starter.

## Licence
This project is AGPL-3.0-or-later. It integrates `vedic-calc` (AGPL-3.0-or-later) and Swiss Ephemeris, which is dual-licensed under AGPL or a professional licence. This repository chooses the AGPL route. Network users must be offered the complete corresponding source under the licence terms. This is an engineering assessment, not legal advice. Review all transitive dependencies and notices before public launch.

## Run locally
Requires Python 3.12+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e './api[geo]'
uvicorn app.main:app --app-dir api --host 0.0.0.0 --port 8000
```

Serve the `web/` directory using a static host. Set the API URL in `web/config.js` when the API is not at `http://127.0.0.1:8000`.

To run the full test suite (including the real-engine chart/Panchanga smoke test and offline timezone dataset):

```bash
pip install -e './api[test,geo]'
python -m unittest discover -s api/tests -v
```

To run the optional independent D1/varga/Mahadasha comparison (downloads/caches the JPL and Hipparcos reference data):

```bash
pip install -e './api[accuracy]'
python tools/cross_validate.py
```

## Verification status
GitHub Actions installed the pinned `vedic-calc` engine and offline timezone data, generated a real sample chart with 9 planetary placements, 12 houses, 9 Mahadasha periods, 16 chart entries (D1 + 15 standard vargas) and birth-time Panchanga, then passed all 17 Python tests and the PWA JavaScript/config checks.

The separate MIT-licensed JPL/Skyfield DE421 vs Swiss Ephemeris cross-check passed all 9 sample births: Mumbai 1990, Karmala 1996, New York 1988, Jamnagar 2026, Kolkata 1946, Kathmandu 2000, Sydney 2050, Auckland 2001 and the second occurrence of a New York DST-fold time in 2025. Maximum measured D1 differences were 0.004565° for ayanamsa, 0.077954° for ascendant and 0.007220° across the nine planetary longitudes. All 15 vargas across 9 fixtures (1,350 discrete planet/ascendant sign checks) had zero substantive mismatches; one D24 sign placement was flagged as boundary-sensitive because the two close D1 inputs fell on opposite sides of a division boundary. Mahadasha lord sequences matched, with a maximum date-boundary difference of 2.324 days using a common 365.25-day year basis and a documented three-day screening limit.

The JPL reference Mahadasha schedule is derived from that engine's D1 Moon position because its built-in Dasha helper uses a different ecliptic-coordinate path. These are regression checks on a finite sample, not universal astronomical accuracy certification. Birth-time Panchanga is integration-tested but is not yet cross-validated against independent Panchanga references. See [the validation protocol](docs/accuracy-validation.md) and [GitHub Actions](https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions).

## Deployment
See [the closed-beta deployment guide](docs/deployment.md) for Render API and Cloudflare Pages setup. No public deployment has been performed yet.

## Beta deployment only
- Static PWA: Cloudflare Pages, output directory `web/`, no build command.
- API: Render free service is for closed beta/testing only; free services can sleep and have ephemeral filesystems.
- Set `SOURCE_URL` in `web/config.js` to this public repository before enabling public access.
- Configure exact `FRONTEND_ORIGINS` and a real `NOMINATIM_USER_AGENT` before enabling the optional place search.
- Do not enable public Nominatim search on multiple workers/replicas until its per-process in-memory rate limit/cache is replaced with a shared one.

## Reference
Pinned engine source: https://github.com/atolat/vedic-calc/tree/620d54560ee7e108496495eeb17054a52630a0bf
