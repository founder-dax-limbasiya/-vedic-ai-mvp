# Current build status

Last checked: 2026-11-19

## Implemented

- Mobile-first installable PWA with chart input, result display, JSON export, Android/iOS raster app icons and a divisional-chart selector.
- FastAPI endpoints for health, IANA timezone list, chart generation, optional one-shot place search, and coordinate-to-timezone lookup.
- Birthplace-local date/time conversion using IANA timezone history; nonexistent DST times are rejected and ambiguous DST times require the user to choose an occurrence.
- Future birth dates are rejected using the birth-place timezone.
- Offline coordinate-to-timezone lookup using `timezonefinder>=9.2,<10` and pinned `timezonefinder-data==4.2026.6`.
- Integration adapter calls pinned `vedic-calc` `calculate_chart()`, `calculate_dasha()` and `calculate_divisional_chart()`; no chart formulas have been reimplemented in the app.
- API returns D1 plus 15 standard divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60), each with nine planetary sign placements and ascendant sign.
- PWA lets users switch between the supported divisional charts.
- Independent Swiss Ephemeris speed calls use `SEFLG_SPEED` for retrograde labels and report per-planet ephemeris source.
- No account database, saved birth profiles, payments, report purchasing or AI interpretation provider.

## Verified in GitHub Actions

- Pinned `vedic-calc` Git commit installed successfully from GitHub.
- Optional timezonefinder engine and pinned boundary dataset installed successfully.
- Real engine smoke test generates 9 planetary placements, 12 houses, 9 Mahadasha periods and 16 chart entries (D1 plus 15 standard vargas).
- Python test suite passed, including the real-engine test, chart adapter response test, coordinate-to-timezone test for Jamnagar, retrograde speed-flag check, API validation and DST edge cases.
- `node --check` passed for PWA app, config and service-worker scripts.
- PWA manifest JSON and Python `pyproject.toml` parsed successfully.
- Independent MIT-licensed JPL/Skyfield DE421 vs Swiss Ephemeris validation passed on 4 sample D1 charts (Mumbai 1990, Karmala 1996, New York 1988, Jamnagar 2026).
- All 15 shared standard divisional charts had zero sign-placement mismatches across the four fixtures (600 planetary/ascendant sign placements).
- Mahadasha lord sequence matched; maximum date-boundary difference was 2.478 days, inside the documented three-day screening limit.

Latest normal tests: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44505640947
Latest independent comparison: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44505569050

## Not yet verified / not done

- Cross-engine checks cover only four D1/varga/Dasha fixtures. They do not prove all historical/future dates or every coordinate, nor validate all boundary cases or interpretation rules.
- Divisional checks compare discrete sign assignments and ascendant signs, not every divisional longitude or all traditional calculation variants.
- Dasha comparison checks Mahadasha sequence and boundaries only; antardasha, pratyantardasha and deeper period boundaries need separate fixtures.
- Retrograde status uses a separate `SEFLG_SPEED` call to correct an upstream issue, but near-stationary edge cases still need dedicated fixtures.
- No public deployment has been performed.
- AI interpretations, accounts, cloud sync, payments, paid reports, analytics and multilingual content are not implemented.
- No complete SBOM or formal legal review has been completed.

## Release blockers

1. Expand D1/varga comparison with more eras, latitudes, timezones, date-line cases and birth times near midnight; add a third independent source/reference where practical.
2. Validate antardashas and panchanga transitions with convention-matched fixtures.
3. Add known fixtures for historical timezones, date-line boundaries, unknown/approximate birth times and near-stationary retrograde planets.
4. Generate and review an SBOM and all source/data licence notices, especially AGPL and timezonefinder-data ODbL obligations.
5. Before public AGPL network deployment, provide the complete corresponding source and keep `SOURCE_URL` accurate in `web/config.js`.
6. Add API rate limits, shared Nominatim throttle/cache for multi-instance deployments, error monitoring and abuse controls before expanding beyond a closed beta.
7. Validate user demand and repeat use before implementing subscriptions or expanding into other astrology traditions.
