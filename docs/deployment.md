# Closed-beta deployment guide

This repo is not deployed yet. These instructions describe a low-cost test setup; they do not certify a production service.

## 1. Deploy the API on Render

The repository includes `render.yaml`. In Render, create a new Blueprint and select:

`founder-dax-limbasiya/-vedic-ai-mvp`

Choose the repository's `main` branch and let Render read the Blueprint. The API service uses the `api/` root and the command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After Render creates the service, copy its HTTPS origin, for example `https://YOUR-SERVICE.onrender.com`.

Set these environment variables in the Render service:

- `FRONTEND_ORIGINS`: the exact HTTPS origin that Cloudflare Pages will serve, e.g. `https://YOUR-PROJECT.pages.dev`.
- `NOMINATIM_USER_AGENT`: optional. Configure a real product identifier and working public contact page before enabling place search, e.g. `JyotiVedicAI/0.1 (+https://YOUR-DOMAIN/contact)`. Leave this unset to keep public Nominatim search disabled.

The free Render plan is for a closed beta only. It may sleep on inactivity and can have cold starts; do not use it for a paid product with uptime promises.

## 2. Point the PWA to the API

Before deploying the static site, edit `web/config.js` and replace the local API origin with the exact Render HTTPS URL:

```js
window.VEDIC_CONFIG = {
  API_BASE: "https://YOUR-SERVICE.onrender.com",
  SOURCE_URL: "https://github.com/founder-dax-limbasiya/-vedic-ai-mvp"
};
```

Keep `SOURCE_URL` pointing to the complete corresponding public source. The project is AGPL-3.0-or-later; network users must be able to access the corresponding source and licence notices. Do not remove the source link.

Commit this configuration change only after you have the final Render service origin. Never put API secrets in `web/config.js`; it is public browser code.

## 3. Deploy the PWA on Cloudflare Pages

Create a Pages project connected to this GitHub repository.

- Production branch: `main`
- Build command: leave blank
- Build output directory: `web`
- Root directory: repository root

After the first deployment, copy the Pages HTTPS origin and put the exact origin in the Render `FRONTEND_ORIGINS` environment variable. Redeploy the API after changing environment variables.

## 4. Smoke-test the closed beta

Open these endpoints in a browser:

- `https://YOUR-SERVICE.onrender.com/health` — should show `calculation_engine_installed: true`.
- `https://YOUR-SERVICE.onrender.com/docs` — FastAPI interactive docs.
- Open the Cloudflare Pages URL on an Android phone, add it to the home screen, and calculate the sample chart in the accuracy test fixtures.

Test a real chart with a known, independently verified birth record before showing it to users. The demo fixture is not an accuracy certification.

## 5. Do not enable public launch yet

Before an open beta or payments:

1. Complete the JPL/Skyfield cross-check and validate against additional convention-matched sources.
2. Add shared rate limiting and caching before running multiple API workers or replicas.
3. Add abuse controls, logging that excludes birth inputs, monitoring, error reporting and backup/recovery plans.
4. Review AGPL and ODbL obligations with qualified counsel and generate a complete software bill of materials.
5. Run real-user onboarding and retention tests. Avoid subscriptions until there is repeat-use value.

## Privacy notes

The current API does not persist birth profiles. It still processes the submitted birth date/time and coordinates. Place search, when enabled, sends the searched place string to the OpenStreetMap Nominatim service and displays attribution. The service worker caches the PWA shell but deliberately does not cache API responses.
