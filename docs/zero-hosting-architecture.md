# Jyoti: local-first, zero-hosting architecture

## Decision

Jyoti's local-first Android app and downloadable website calculate on the user's own device. Neither needs a Jyoti backend, paid compute server, or cloud-hosting account.

- **Android:** the website UI, JavaScript engine and WebAssembly binary are included in the APK. Calculations run locally after installation.
- **Offline website:** a ZIP contains the static website and local engine. Its included launcher starts a small HTTP server bound to `127.0.0.1` on the user's computer. This is a local device process, not cloud hosting.
- **Public website URL:** intentionally not provided. A public URL requires some machine/service to host and serve files. No Cloudflare, Render, Vercel or other host is configured.
- **Birth data:** no Jyoti calculation API call is made. Chart inputs are processed in the browser/app.
- **Optional place search:** sends only the search query to OpenStreetMap Nominatim. Manual latitude/longitude entry avoids that request.
- **Time zones:** a bundled coordinate boundary lookup is used. Results can be approximate near time-zone borders; verify historical local civil time.

## Website package

Build order:

1. Install pinned JavaScript dependencies.
2. Build `web/engine.bundle.js` and copy `web/swisseph.wasm`.
3. Run `scripts/create_offline_web_package.py`.
4. Distribute `dist/Jyoti-Vedic-AI-Offline-Website.zip`.

The package includes `start.py`, Windows and macOS/Linux launchers, attribution notices and the website assets. It requires Python 3.8+ on the desktop computer. The launcher binds to loopback only and automatically opens the browser. Direct `file://` opening is not supported because browsers restrict WebAssembly modules and service workers on file URLs.

The separate GitHub Actions workflow builds and uploads the ZIP artifact. Artifact retention is temporary; the package is a build output, not a permanent public website address.

## Calculation engine

- `@swisseph/browser` runs Swiss Ephemeris through WebAssembly using its built-in Moshier ephemeris mode.
- `web/engine/vedic-core.js` implements Vedic sign/nakshatra, divisional-chart, Vimshottari and Panchanga rules from the pinned `vedic-calc` version.
- `web/engine/index.js` provides device-local chart, daily Panchanga, sunrise-to-next-sunrise transitions and coordinate-to-time-zone functionality.
- `scripts/build_client_engine.mjs` builds the bundle and copies the WASM binary.

## Verification and known limitations

The Chromium browser test passed:
- six pure calculation unit tests;
- actual browser WebAssembly initialization and calculation;
- one sample chart compared with the pinned Python engine (9 planets, ascendant, 12 houses, 16 divisional charts, Mahadasha and birth Panchanga);
- all nine Mahadasha lord, start-date, end-date and duration values in that fixture;
- a daily Panchanga and transition comparison for a selected test date/location;
- website UI flow for chart, daily Panchanga and transition rendering;
- zero outbound browser requests during that calculation flow using manual coordinates.

The sample daily sunrise differed by 79 seconds from the Python reference, within the current 180-second test tolerance. The browser wrapper uses a local solar-altitude search rather than the same Python `rise_trans` routine. This sunrise approximation needs more multi-location/date verification. The current checks are regression tests, not a complete accuracy certification.

The APK workflow previously completed at commit `8e99cee927824da12275dada8beba0e9ef2ac637`. That verifies APK packaging and compilation, not runtime behaviour on a physical Android device or emulator. The offline website ZIP also needs its first completed CI build and end-to-end launcher test before being treated as release-ready.

The `client-side-engine-poc` branch remains experimental. The `main` branch, original FastAPI backend and server-backed UI have not been migrated. The backend is retained as a reference for regression checks; no hosted deployment is part of this plan.

## Privacy and offline behaviour

- Birth chart, divisional chart, Mahadasha and Panchanga calculations run locally.
- The APK bundles the calculation engine and does not require a network connection for those calculations after installation.
- The offline website runs on the computer's loopback address with its own included assets.
- Place search is optional and external; manual coordinates work without it.
- No login, database, cloud sync, payments, ads or analytics are included in this prototype.

## Licensing

The project is AGPL-3.0-or-later. The selected `@swisseph/browser` package is AGPL-3.0; `@photostructure/tz-lookup` is CC0-1.0. Preserve upstream notices and provide corresponding source as required by AGPL when distributing the APK or website package. Review all transitive dependency notices before public launch. This is an engineering summary, not legal advice.
