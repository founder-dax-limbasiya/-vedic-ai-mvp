# Internet deployment (Render)

Vedic AI runs as one public FastAPI web service. The same HTTPS origin serves the website/PWA and all calculation API routes; no Vercel or separate frontend host is needed.

## Deploy

1. Create a free account at https://render.com/ and connect the GitHub account that owns this repository.
2. Open https://dashboard.render.com/blueprints and choose **New Blueprint Instance**.
3. Select `founder-dax-limbasiya/-vedic-ai-mvp`, branch `main`, and confirm the `render.yaml` Blueprint.
4. Render creates the web service named `jyoti-vedic-ai-api` and gives it the public URL `https://jyoti-vedic-ai-api.onrender.com`.
5. Wait until the first deploy is marked **Live**. Check `/health`; it should report `calculation_engine_installed: true`.

The Blueprint builds from the repository root, installs the pinned open-source calculation engine and offline timezone data, copies the PWA files into `public/`, and starts Uvicorn on Render's assigned port.

## Free-tier behavior

Render's free web services are public over HTTPS, but they spin down after 15 minutes without traffic. The next request wakes the service; Render says this can take about a minute. Free services also have monthly included usage limits and may restart. This is fine for a beta/test app, but not an always-on uptime promise. See [Render's free service limits](https://render.com/docs/free).

## APK

The Android APK bundles the mobile frontend. Its API base is `https://jyoti-vedic-ai-api.onrender.com`, so birth-chart, timezone, place-search and Panchanga calculations run over the internet on Render. It does not use Vercel. If Render assigns a different URL, update `VEDIC_API_BASE` in the Android APK workflow/build environment and rebuild.

## Verify

- `/` — mobile web app
- `/health` — API and calculation-engine health
- `/docs` — FastAPI API docs
- `/v1/timezones?q=Asia` — timezone search

Test chart generation and daily Panchanga from both a browser and the Android APK after the Render service is live.

## Privacy and licensing

The API does not persist birth profiles. Birth date/time and coordinates are processed to calculate the requested chart. Optional Nominatim birthplace search remains disabled unless a real identifying `NOMINATIM_USER_AGENT` is configured. The project is AGPL-3.0-or-later; retain the source link and licence notices.
