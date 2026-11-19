# Architecture — first release

## Current flow

```text
Android / iOS / desktop browser (PWA)
             |
             | HTTPS JSON, no profile persistence
             v
         FastAPI API
             |
             | IANA timezone -> historical UTC offset
             v
      vedic-calc adapter
             |
             +-- Swiss Ephemeris / Moshier fallback
             +-- D1 chart, nakshatra, whole-sign houses
             +-- Vimshottari dasha periods
             +-- independent speed-flag diagnostic
```

## Separate apps, shared future packages

The portfolio will eventually have separate apps and brands. This first repository slice only contains the Vedic app. Do not add Western, Tarot, Chinese or Numerology screens to this app.

A later monorepo may contain separate apps plus shared typography/accessibility/i18n/auth/payment foundations. Calculation engines and interpretation rules remain isolated by tradition.

## Important technical choices

- `vedic-calc` is called through `api/app/engine.py`; the app does not reimplement its chart mathematics.
- The dependency is pinned to a Git commit; do not float on `main` for reproducible builds.
- `pyswisseph` uses process-global sidereal settings, so chart generation and speed diagnostics are serialized with an `RLock`.
- Each planet's returned ephemeris source is inspected; do not label a Moshier fallback as a Swiss Ephemeris file calculation.
- Retrograde status is recomputed with `SEFLG_SPEED`, as required by the official API documentation. The upstream library currently reads speed without requesting that flag.
- `zoneinfo` resolves the user's local birthplace time using IANA data. Ambiguous and nonexistent clock times are handled explicitly.
- No birth data is written to a database, browser storage, logs, or service-worker cache.

## Known limitations

- The upstream calculation library has known quality gates to address. Its self-consistency tests are not equivalent to independent end-to-end validation.
- Birthplace coordinates and the IANA timezone are entered by the user. An optional place search and timezone-boundary database require a separate licence/operational review.
- Current free Render service behaviour is not suitable for a reliable production system: cold starts and ephemeral filesystem. Keep user data off it.
- AI interpretations and payments are deliberately absent from this first slice.
