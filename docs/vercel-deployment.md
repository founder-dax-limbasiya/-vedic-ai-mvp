# Vercel deployment

Vedic AI is a single Vercel project: FastAPI handles the calculation routes and Vercel's `public/` directory serves the mobile PWA from the same origin.

## Project layout

- Root `pyproject.toml` installs the pinned calculation engine and offline timezone dependencies.
- `tool.vercel.entrypoint = "api.app.main:app"` points Vercel at the existing FastAPI instance.
- `tool.vercel.scripts.build` runs `scripts/sync_vercel_public.py`, which copies the canonical assets from `web/` into `public/`.
- `vercel.json` selects Mumbai (`bom1`) and a 60-second function maximum for the chart API.
- `web/config.js` uses the local API for localhost development and same-origin routes in hosted environments.

No database, saved birth-profile storage, AI provider key, or payment secret is required for this calculation-only MVP.

## Git integration

The Vercel project is linked to `founder-dax-limbasiya/-vedic-ai-mvp` on `main`. Pushes to the production branch trigger deployment.

## Optional place search

Public Nominatim search remains disabled unless `NOMINATIM_USER_AGENT` is configured. Do not enable it with a fake contact address or before reviewing the public Nominatim usage policy. Manual coordinates and offline timezone lookup remain available.

## Smoke tests

After deployment, check:

- `/` — mobile PWA loads.
- `/health` — `calculation_engine_installed` is true.
- `/docs` — FastAPI documentation loads.
- `/v1/timezones?q=Asia` — timezone lookup responds.
- Submit a known test chart, then use the daily Panchanga and transition timing actions.

Vercel Hobby is suitable for a small closed beta, not a production uptime promise. Monitor function duration and build output size before opening access broadly.

## Source and licence

The complete corresponding source and licence are available at https://github.com/founder-dax-limbasiya/-vedic-ai-mvp. The project uses AGPL-3.0-or-later components, so network-use source obligations remain applicable.
