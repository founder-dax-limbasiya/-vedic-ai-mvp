# Current build status

Last checked: 2026-11-19

## Implemented

- Mobile-first installable PWA shell with chart input, result display and JSON export.
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

Latest fully green workflow for the above verification: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44502080104

## Not yet verified / not done

- Planetary positions, ascendant, nakshatra, divisional charts and dashas have not yet been cross-validated against two independent, convention-matched astrology engines/reference datasets.
- Retrograde status uses a separate `SEFLG_SPEED` call to correct an upstream issue, but exact station-time edge cases still need dedicated fixture validation.
- No public deployment has been performed.
- AI interpretations, accounts, cloud sync, payments, paid reports, analytics and multilingual content are not implemented.
- No complete SBOM or formal legal review has been completed.

## Release blockers

1. Validate reference birth charts against at least two independent calculators/reference datasets; explicitly align ayanamsa, node type, house system, time handling and ephemeris source.
2. Add known fixtures for historical timezones, date-line boundaries, unknown/approximate birth times and near-stationary retrograde planets.
3. Generate and review an SBOM and all source/data licence notices, especially AGPL and timezonefinder-data ODbL obligations.
4. Before public AGPL network deployment, provide the complete corresponding source and keep `SOURCE_URL` accurate in `web/config.js`.
5. Add API rate limits, shared Nominatim throttle/cache for multi-instance deployments, error monitoring and abuse controls before expanding beyond a closed beta.
6. Validate user demand and repeat use before implementing subscriptions or expanding into other astrology traditions.
