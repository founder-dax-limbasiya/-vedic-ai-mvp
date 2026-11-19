# Current build status

Last checked: 2026-11-19

## Implemented

- Mobile-first installable PWA with chart input, result display, JSON export and raster app icons for Android/iOS installation.
- FastAPI endpoints for health, IANA timezone list, chart generation, optional one-shot place search, and coordinate-to-timezone lookup.
- Birthplace-local date/time conversion using IANA timezone history; nonexistent DST times are rejected and ambiguous DST times require the user to choose an occurrence.
- Future birth dates are rejected using the birth-place timezone.
- Offline coordinate-to-timezone lookup using `timezonefinder>=9.2,<10` and pinned `timezonefinder-data==4.2026.6`.
- Integration adapter calls pinned `vedic-calc` `calculate_chart()` and `calculate_dasha()`; no chart formulas have been reimplemented in the app.
- Independent Swiss Ephemeris speed calls use `SEFLG_SPEED` for retrograde labels and report per-planet ephemeris source.
- No account database, saved birth profiles, payments, report purchasing or AI interpretation provider.

## Verified in GitHub Actions

- Pinned `vedic-calc` Git commit installed successfully from GitHub.
- Optional timezonefinder engine and pinned boundary dataset installed successfully.
- 16 Python tests passed, including a real end-to-end chart generation test, coordinate-to-timezone test for Jamnagar, retrograde speed-flag check, API validation and DST edge cases.
- `node --check` passed for PWA app, config and service-worker scripts.
- PWA manifest JSON and Python `pyproject.toml` parsed successfully.
- Independent MIT-licensed JPL/Skyfield DE421 vs Swiss Ephemeris validation passed on 4 sample D1 charts (Mumbai 1990, Karmala 1996, New York 1988, Jamnagar 2026).
- Maximum measured angular differences across the 4 fixtures: ayanamsa 0.003434°, ascendant 0.002613°, planetary longitude 0.003613°. The starting limits were 0.05°, 0.15° and 0.10° respectively for ayanamsa, ascendant and classical planet longitudes (nodes 0.15°).

Accuracy workflow: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44504070247
Main tests workflow: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44504070238

## Not yet verified / not done

- Cross-engine checks currently cover only four D1/ascendant/ayanamsa fixtures. They do not prove all historical/future dates or every coordinate, nor validate D2–D60, house-lord interpretation, Shadbala, yogas, panchanga boundaries or Vimshottari start/end periods.
- Retrograde status uses a separate `SEFLG_SPEED` call to correct an upstream issue, but near-stationary edge cases still need dedicated fixtures.
- No public deployment has been performed.
- AI interpretations, accounts, cloud sync, payments, paid reports, analytics and multilingual content are not implemented.
- No complete SBOM or formal legal review has been completed.

## Release blockers

1. Expand the D1 comparison with more eras, latitudes, timezones, date-line cases and birth times near midnight; add a third independent source/reference where practical.
2. Validate divisional charts D2–D60, dashas and panchanga transitions with convention-matched fixtures.
3. Add known fixtures for historical timezones, date-line boundaries, unknown/approximate birth times and near-stationary retrograde planets.
4. Generate and review an SBOM and all source/data licence notices, especially AGPL and timezonefinder-data ODbL obligations.
5. Before public AGPL network deployment, provide the complete corresponding source and keep `SOURCE_URL` accurate in `web/config.js`.
6. Add API rate limits, shared Nominatim throttle/cache for multi-instance deployments, error monitoring and abuse controls before expanding beyond a closed beta.
7. Validate user demand and repeat use before implementing subscriptions or expanding into other astrology traditions.
