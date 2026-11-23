# Vedic AI — MVP starter

A mobile-first, privacy-conscious Vedic birth-chart PWA with a Python API. “Jyoti” is a working title only; no trademark/name clearance has been performed.

## Current scope
- Vedic birth chart integration through the open-source `vedic-calc` library.
- D1 / Rashi placements, ascendant, whole-sign houses, nakshatra/pada and Vimshottari Mahadasha.
- Birth-time Panchanga: Vara, Tithi, Nakshatra, Yoga and Karana, plus local sunrise/sunset.
- Daily sunrise-based Panchanga lookup by date, plus a chronological timeline of exact tithi, nakshatra, yoga and karana changes from sunrise to next sunrise.
- D1 plus 15 standard divisional charts: D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60.
- IANA timezone handling, including ambiguous and nonexistent local birth times.
- Offline coordinate-to-IANA-timezone lookup using a pinned boundary dataset.
- Swiss Ephemeris speed diagnostics for retrograde status and per-planet source reporting.
- Mobile-first installable PWA with a hand-crafted editorial Jyotish interface, South Indian-style D1 Rashi chart, divisional-chart selector, Panchanga transition timeline and JSON export.
- No account database, saved birth profiles, payments, ads, analytics, or AI interpretations in this starter.


## Local-first prototype (feature branch)

The `client-side-engine-poc` branch contains an experimental shared browser/Android calculation engine. Birth charts, divisional charts, Mahadasha and Panchanga are calculated on the user's device using Swiss Ephemeris WebAssembly; there is no Jyoti calculation API call in this prototype. The current `main` branch remains the original FastAPI-backed implementation until the local engine has broader parity and Android runtime verification.

Build the local calculation bundle (Node.js 22+):

```bash
npm install --no-audit --no-fund
npm run test:client
npm run build:client
```

Serve `web/` with a static web server after building. For Cloudflare Pages, use build command `npm install --no-audit --no-fund && npm run build:client` and output directory `web`. The APK workflow runs the same build step and packages the bundle and WASM binary into Android assets. See [the local-first architecture and validation notes](docs/zero-hosting-architecture.md).

Optional place search uses OpenStreetMap Nominatim; manual coordinates avoid that network request. Coordinate-to-time-zone lookup is bundled locally.

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

### API endpoints
- `POST /v1/chart` — birth chart, birth-time Panchanga, D1 + 15 standard vargas, Mahadasha.
- `POST /v1/panchanga` — daily Panchanga at local sunrise for a date, timezone and coordinates.
- `POST /v1/panchanga/transitions` — tithi, nakshatra, yoga and karana change times between sunrise and the next sunrise.
- `GET /v1/timezones` — IANA timezone search.
- `GET /v1/places` — optional, one-shot birthplace search (requires an identifying Nominatim User-Agent).
- `GET /v1/place-timezone` — offline coordinate-to-IANA-timezone lookup.

To run the full test suite (including real-engine chart/Panchanga integration and offline timezone dataset):

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
The latest completed feature-code run passed all **20 Python tests**, including the real-engine Jamnagar sunrise-to-sunrise Panchanga transition test, JavaScript syntax checks, and manifest/config parsing: [GitHub Actions](https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/45053224077).

The separate MIT-licensed JPL/Skyfield DE421 vs Swiss Ephemeris cross-check passed all 9 sample births: Mumbai 1990, Karmala 1996, New York 1988, Jamnagar 2026, Kolkata 1946, Kathmandu 2000, Sydney 2050, Auckland 2001 and the second occurrence of a New York DST-fold time in 2025. The latest run compared birth-time Panchanga limb indices and reported 9/9 fixtures passed. Maximum measured D1 differences were 0.004565° for ayanamsa, 0.077954° for ascendant and 0.007220° across the nine planetary longitudes. All 15 vargas across 9 fixtures (1,350 discrete planet/ascendant sign checks) had zero substantive mismatches; one D24 placement was flagged as boundary-sensitive because the two close D1 inputs fell on opposite sides of a division boundary. Mahadasha lord sequences matched, with a maximum date-boundary difference of 2.324 days using a common 365.25-day year basis and a documented three-day screening limit: [independent accuracy workflow](https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/45053023891).

These are regression checks on a finite sample, not universal astronomical accuracy certification. Daily Panchanga transition timestamps use the pinned library's sunrise-to-next-sunrise routine and are integration-tested, but are not yet independently cross-validated against another Panchanga reference implementation. See [the validation protocol](docs/accuracy-validation.md).

## Deployment
The app is designed as a single-origin Render web service: FastAPI serves both the calculation API and the mobile PWA. The repository includes `render.yaml` for a one-click Blueprint setup. See [the deployment guide](docs/deployment.md).

## Beta deployment notes
- Render's free web service sleeps after 15 minutes without traffic and may take about a minute to wake; this is suitable for testing, not an always-on production promise.
- Hosted browser requests use same-origin API routes. The Android APK calls the same Render API over the internet.
- Optional Nominatim birthplace search remains disabled until a real identifying `NOMINATIM_USER_AGENT` is configured.
- Do not enable public Nominatim search on multiple workers/replicas until its per-process in-memory rate limit/cache is replaced with a shared one.

## Reference
Pinned engine source: https://github.com/atolat/vedic-calc/tree/620d54560ee7e108496495eeb17054a52630a0bf
