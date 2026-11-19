# Release gates

The application must not be called production-ready until all gates pass.

1. **Dependency and licence:** pinned engine installs reproducibly; complete notices and source are published; public UI exposes the source link.
2. **Ephemeris:** each body's returned source is recorded; expected ephemeris availability is tested; fallback is disclosed.
3. **Retrograde:** verify speed flag is requested and values are compared to an independent source.
4. **Birth-time correctness:** test historical timezone offsets, DST folds, nonexistent times, leap days, and date-line boundaries.
5. **Reference charts:** compare planetary longitudes, ascendant, nakshatra, pada, houses and dashas against at least two independent, convention-matched references over a diverse fixture set. Record ayanamsa and house settings for every fixture.
6. **Panchanga:** validate birth-time and daily sunrise Panchanga elements, local sunrise/sunset and boundary transitions against independent, convention-matched almanac references for multiple locations, dates and timezone regimes.
7. **Privacy:** confirm no request body logging, database persistence, analytics, service-worker API cache, or third-party call without user action.
8. **Security and abuse:** add rate limits for the calculation API, validate input ranges, test CORS, and review error handling.
9. **User value:** closed beta feedback, repeat use and actual willingness-to-pay test before payment integration.
