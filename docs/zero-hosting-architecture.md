# Jyoti: local-first calculation architecture

## Decision

Jyoti's website and Android app share a calculation engine that runs on the user's device. Chart calculations do not call a Jyoti API or require a paid compute server.

- Website: static files + browser WebAssembly. A static host is still needed to deliver the site.
- Android: the same web UI, JavaScript bundle and WebAssembly binary are packaged into the APK. Calculation works locally after installation.
- Birth data: sent to no Jyoti server for chart calculation.
- Optional place lookup: sends only the search query to OpenStreetMap Nominatim. Users can enter coordinates manually and calculate without this request.
- Time-zone selection: browser's IANA zone list plus a bundled coordinate boundary lookup. The coordinate lookup can be approximate near borders; verify historical local civil time for the birth date.

## Calculation engine

- `@swisseph/browser` runs Swiss Ephemeris through WebAssembly, using its built-in Moshier ephemeris mode.
- `web/engine/vedic-core.js` ports the Vedic sign/nakshatra, divisional-chart, Vimshottari and Panchanga rules from the pinned `vedic-calc` version.
- `web/engine/index.js` provides the device-local API for birth charts, daily Panchanga, sunrise-to-next-sunrise transitions and coordinate-to-time-zone lookup.
- `scripts/build_client_engine.mjs` creates `web/engine.bundle.js` and copies `web/swisseph.wasm`.

## Current verification

The real-browser CI run at commit `40f715337fb95e6037c53e8361d7accf64c5bf7f` passed:
- six pure calculation unit tests;
- real Chromium WebAssembly initialization and calculation;
- a sample chart checked against the pinned Python engine (9 planets, ascendant, 12 houses, 16 divisional charts, Mahadasha and birth Panchanga);
- all nine Mahadasha lord, start-date, end-date and duration values against the Python reference;
- a daily Panchanga and transition comparison for one test date/location;
- website UI flow for chart, daily Panchanga and transition rendering;
- zero outbound browser requests during calculation.

The daily sunrise in the sample differed by 79 seconds from the Python reference, inside the current 180-second test tolerance. Sunrise and sunset are found through a local solar-altitude search because the browser wrapper does not expose the same `rise_trans` routine as the Python package. That approximation needs more multi-location/date verification before a production migration. The current sample is one chart birth and one daily Panchanga date across Jamnagar/Mumbai, so it is a useful regression gate, not a complete accuracy certification.

The APK build workflow also completed successfully at commit `8e99cee927824da12275dada8beba0e9ef2ac637`. This proves the APK packages the local assets and compiles; it is not yet a physical-device or Android-emulator runtime test.

This is still an experimental branch. The current `main` branch, Render Blueprint, Python API and server-backed production UI have not been changed. Do not remove the fallback backend or switch production until the broader parity suite and Android runtime test pass.

## Static website hosting

The static website still needs a public host, but it does not need a calculation API. Recommended option: Cloudflare Pages Free, with no Pages Functions.

Current Cloudflare documentation (checked 23 November 2026) lists 500 builds/month and one concurrent build on the Free plan. Pages static asset requests are free and unlimited when the request does not invoke Pages Functions. Limits and plan terms can change; this is not a lifetime guarantee.

GitHub Pages is deliberately not the recommended production host for a SaaS: GitHub says Pages is not intended or allowed as free hosting for an online business or commercial SaaS.

### Connect the repository in Cloudflare Pages

1. In Cloudflare Dashboard, open **Workers & Pages → Create application → Pages → Connect to Git**.
2. Authorize GitHub and select `founder-dax-limbasiya/-vedic-ai-mvp`.
3. Set the production branch to `main` after the local-first branch has been reviewed and merged.
4. Use these build settings:
   - Framework preset: **None**
   - Root directory: `/`
   - Build command: `npm install --no-audit --no-fund && npm run build:client`
   - Build output directory: `web`
5. Save and deploy. Cloudflare Pages serves the generated static bundle from its `pages.dev` address. No API token needs to be pasted into source code or chat.

Cloudflare Git integration can auto-deploy after each push to the selected production branch. It also supports preview deployments for branches; keep previews disabled or use them only for testing until the feature branch is ready.

## Offline and privacy behaviour

- After initial website load, the service worker caches the app shell, browser bundle and WASM asset. Subsequent calculations can run offline as long as the browser has retained the cache.
- The APK bundles the same assets, so calculations do not depend on connectivity after installation.
- Place search is an optional external lookup; manual coordinates work without it.
- No login, cloud sync, database, payments, ads or analytics are included.

## Licensing

The project is AGPL-3.0-or-later. The selected `@swisseph/browser` package is AGPL-3.0; `@photostructure/tz-lookup` is CC0-1.0. Preserve upstream notices and provide the corresponding source as required by AGPL when distributing the APK or offering the website over a network. Review all transitive dependency notices before public launch. This is an engineering summary, not legal advice.
