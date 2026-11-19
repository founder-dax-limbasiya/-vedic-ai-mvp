# Current build status

Last checked: 2026-11-19

## Implemented

- Mobile-first installable PWA with chart input, result display, JSON export, Android/iOS raster app icons, a divisional-chart selector and daily Panchanga panel.
- FastAPI endpoints for health, IANA timezone list, birth-chart generation, daily Panchanga, optional one-shot place search and coordinate-to-timezone lookup.
- Birthplace-local date/time conversion using IANA timezone history; nonexistent DST times are rejected and ambiguous DST times require the user to choose an occurrence.
- Future birth dates are rejected using the birth-place timezone.
- Offline coordinate-to-timezone lookup using `timezonefinder>=9.2,<10` and pinned `timezonefinder-data==4.2026.6`.
- Integration adapter calls pinned `vedic-calc` `calculate_chart()`, `calculate_dasha()`, `calculate_panchanga()` and `calculate_divisional_chart()`; no chart formulas have been reimplemented in the app.
- API returns D1 plus 15 standard divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60), each with nine planetary sign placements and ascendant sign.
- Birth Panchanga at exact local birth time: Vara, Tithi, Nakshatra, Yoga, Karana and local sunrise/sunset.
- Daily Panchanga endpoint `POST /v1/panchanga`: calculates the five limbs at local sunrise for a selected date and birthplace coordinates/timezone; at high latitudes it labels the solar-noon fallback if sunrise cannot be determined.
- Daily Panchanga date picker defaults to the birthplace-local date, not the phone's local date.
- Swiss Ephemeris speed calls use `SEFLG_SPEED` for retrograde labels and report per-planet ephemeris source.
- Service-worker cache is versioned and updated shell assets are activated/claimed.
- No account database, saved birth profiles, payments, report purchasing or AI interpretation provider.

## Verified in GitHub Actions

Latest complete normal test run for the daily Panchanga feature: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44539646399

- Pinned `vedic-calc` Git commit and optional timezonefinder engine/data installed successfully.
- 19 Python tests passed, including real birth chart/Panchanga generation, daily sunrise Panchanga API at Jamnagar, invalid timezone handling, historical Kolkata timezone offset to second precision, coordinate-to-timezone lookup, retrograde speed-flag check and DST edge cases.
- PWA JavaScript syntax, manifest JSON and Python `pyproject.toml` checks passed.

Latest independent comparison: https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions/runs/44539175732

- MIT-licensed JPL/Skyfield DE421 vs Swiss Ephemeris comparison passed 9 sample births: Mumbai 1990, Karmala 1996, New York 1988, Jamnagar 2026, Kolkata 1946, Kathmandu 2000, Sydney 2050, Auckland 2001 and the second New York DST-fold occurrence in 2025.
- Maximum observed differences: ayanamsa 0.004565°, ascendant 0.077954°, nine planetary longitudes 0.007220°.
- All 15 shared divisional charts across 9 fixtures: 1,350 discrete planet/ascendant sign checks, zero substantive mismatches and one boundary-sensitive D24 sign placement.
- Mahadasha lord sequence matched in all 9 fixtures; maximum boundary difference 2.324 days using a common 365.25-day year basis and a three-day screening limit.

## Not yet verified / not done

- Cross-engine checks cover only nine D1/varga/Mahadasha fixtures. They do not prove all historical/future dates, all coordinates or every calculation boundary.
- Divisional checks compare discrete sign assignments and ascendant signs, not every divisional longitude or all traditional calculation variants.
- Dasha comparison checks Mahadasha sequence and boundaries only; antardasha, pratyantardasha and deeper periods need separate fixtures.
- Birth-time and daily Panchanga outputs are real-engine integration-tested but not yet cross-validated against independent Panchanga references.
- Retrograde status uses a separate `SEFLG_SPEED` call to correct an upstream issue, but near-stationary edge cases still need dedicated fixtures.
- No public deployment has been performed.
- AI interpretations, accounts, cloud sync, payments, paid reports, analytics and multilingual content are not implemented.
- No complete SBOM or formal legal review has been completed.

## Historical timezone note

IANA's `Asia/Kolkata` history uses Madras railway time (+05:21:10) for 1870–1941 because Calcutta time varied by institution; it then records wartime daylight-saving periods before returning to +05:30 on 1945-10-15. This is the database's documented best-supported zone history, not a guarantee of the actual clock used by every person in colonial Calcutta. See the [tzdata source notes](https://cr.openjdk.org/~naoto/tz2025b/webrev.00/src/java.base/share/data/tzdata/asia-.html). The test suite checks the historical offset to the second.

## Release blockers

1. Expand D1/varga comparison beyond the current nine fixtures and add a third independent source/reference where practical.
2. Validate birth-time/daily Panchanga elements and transitions against convention-matched references.
3. Validate antardashas and deeper Dasha period boundaries.
4. Add fixtures for unknown/approximate birth times and near-stationary retrograde planets.
5. Generate and review an SBOM and all source/data licence notices, especially AGPL and timezonefinder-data ODbL obligations.
6. Before public AGPL network deployment, provide the complete corresponding source and keep `SOURCE_URL` accurate in `web/config.js`.
7. Add API rate limits, shared Nominatim throttle/cache for multi-instance deployments, error monitoring and abuse controls before expanding beyond a closed beta.
8. Validate user demand and repeat use before implementing subscriptions or expanding into other astrology traditions.
