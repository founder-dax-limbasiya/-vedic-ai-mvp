# Vedic AI — MVP starter

A mobile-first, privacy-conscious Vedic birth-chart PWA with a Python API. “Jyoti” is a working title only; no trademark/name clearance has been performed.

## Current scope
- Vedic birth chart integration through the open-source `vedic-calc` library.
- D1 / Rashi placements, ascendant, whole-sign houses, nakshatra/pada and Vimshottari dasha.
- IANA timezone handling, including ambiguous and nonexistent local birth times.
- Offline coordinate-to-IANA-timezone lookup using a pinned boundary dataset.
- Swiss Ephemeris speed diagnostics for retrograde status and per-planet source reporting.
- Mobile-first installable PWA and FastAPI backend.
- No account database, saved birth profiles, payments, ads, or analytics in this starter.

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

To run the full test suite (including the real-engine smoke test and offline timezone dataset):

```bash
pip install -e './api[test,geo]'
python -m unittest discover -s api/tests -v
```

## Verification status
GitHub Actions has successfully installed the pinned `vedic-calc` engine and offline timezone data, generated a real sample chart with 9 planetary placements, 12 houses and 9 Mahadasha periods, passed all 16 Python tests, and validated the PWA JavaScript and configuration. This is an integration/smoke test, not independent astronomical or astrological accuracy certification. See [the latest workflow runs](https://github.com/founder-dax-limbasiya/-vedic-ai-mvp/actions).

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
