# Jyoti Vedic AI

A mobile-first Vedic birth-chart and Panchanga application. This repository is open-source and the local-first implementation is being developed on the `client-side-engine-poc` branch.

## Zero-hosting setup

This branch is designed so calculations happen on the user's own device. It does not need a Jyoti backend, paid compute server, Cloudflare, Render, Vercel, or another cloud-hosting account.

- **Android:** the app packages the website, JavaScript engine and Swiss Ephemeris WebAssembly file inside the APK. Chart calculations run on the phone.
- **Website:** a downloadable offline ZIP includes the same local calculation engine. Start it on a computer using the included launcher; it opens on `127.0.0.1`, which means the website is served only by that computer.
- **Public URL:** not included. A public website address necessarily requires a machine or service to serve the files. This project intentionally does not set one up.
- **Birth privacy:** chart and Panchanga calculations do not send birth details to a Jyoti server. Optional place search sends only the search text to OpenStreetMap Nominatim; enter coordinates manually to avoid that request.
- **Offline use:** once the APK is installed, chart calculations do not need internet. The offline website ZIP also calculates locally when launched on the same computer.

The APK is the recommended Android install. Do not open the website's `index.html` directly from a ZIP or file manager: browser security restrictions can block WebAssembly modules and service workers on `file://`. Use the included launcher.

## Downloadable offline website

The GitHub Actions workflow builds **Jyoti-Vedic-AI-Offline-Website.zip** automatically on pushes to this branch.

To build it yourself (Node.js 22+ and Python 3.8+):

```bash
npm install --no-audit --no-fund
npm run build:client
python3 scripts/create_offline_web_package.py
```

The ZIP is created at `dist/Jyoti-Vedic-AI-Offline-Website.zip`. Extract it, then:
- Windows: double-click `START-JYOTI-WINDOWS.bat`
- macOS/Linux: run `./START-JYOTI-MAC-LINUX.sh`
- Any supported desktop: run `python3 start.py`

The launcher binds only to `127.0.0.1` and does not expose the website to your local network or the public internet. Python 3.8+ is required.

## Build and test the local engine

Requires Node.js 22+:

```bash
npm install --no-audit --no-fund
npm run test:client
npm run build:client
npm run test:browser
```

The calculation engine uses `@swisseph/browser` with its built-in Moshier ephemeris mode. Vedic sign, nakshatra, divisional-chart, Vimshottari and Panchanga rules are implemented in `web/engine/vedic-core.js`; the browser API adapter is in `web/engine/index.js`.

## Android APK

The Android workflow builds the local WebAssembly bundle, copies it into Android assets and compiles the debug APK:

```bash
python3 scripts/sync_android_assets.py
```

The APK workflow is available in the repository's **Actions** tab. Build success confirms packaging and compilation; a physical-device or emulator runtime test is still required before calling the APK release-ready.

## Scope and verification

Features in the local-first prototype:
- D1/Rashi placements, ascendant, whole-sign houses, nakshatra/pada and Vimshottari Mahadasha.
- Birth Panchanga: Vara, Tithi, Nakshatra, Yoga and Karana.
- Daily sunrise-based Panchanga and a timeline of tithi, nakshatra, yoga and karana changes from sunrise to the next sunrise.
- D1 plus 15 standard divisional charts (D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45 and D60).
- IANA timezone handling and a bundled coordinate-to-timezone boundary dataset.
- Mobile-first interface, South Indian-style D1 chart, divisional-chart selector and JSON export.

The browser engine has passed unit tests, a Chromium WebAssembly smoke test and a limited parity test against the pinned Python engine (one birth-chart fixture and selected daily Panchanga dates/locations). In the sample, sunrise differed by 79 seconds from the Python reference, inside the current 180-second test tolerance. This is a regression check, not universal astronomical accuracy certification. More multi-location/date checks and Android runtime testing remain before production release. See [the validation protocol](docs/accuracy-validation.md) and [the local-first architecture](docs/zero-hosting-architecture.md).

The local-first branch is experimental. **The `main` branch has not been migrated** and still contains the original FastAPI-backed implementation. No production deployment or public website URL has been created.

## Legacy API

The original Python API remains in the repository as a reference/fallback for parity tests. The local-first Android APK and offline website package do not require it.

## Licence

This project is AGPL-3.0-or-later. It integrates `vedic-calc` (AGPL-3.0-or-later) and Swiss Ephemeris, which is dual-licensed under AGPL or a professional licence; this repository uses the AGPL route. `@photostructure/tz-lookup` is CC0-1.0. Preserve upstream notices and provide corresponding source as required by the applicable licence when redistributing. Review all transitive dependency notices before public launch. This is an engineering summary, not legal advice.
