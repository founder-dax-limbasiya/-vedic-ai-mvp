# Jyoti: client-side calculation architecture

## Goal

Keep both the website/PWA and Android APK usable without a Jyoti-operated calculation API or a paid compute server. The user's browser or Android device performs chart calculations locally after the public static app assets have loaded.

A website still needs a place to serve static files. GitHub Pages can serve the public website as a static site; this is not an API or calculation server. The APK bundles the same web assets and WebAssembly engine. Calculations do not send the birth details to a Jyoti backend.

## Shared calculation engine

- `@swisseph/browser` supplies Swiss Ephemeris calculations through WebAssembly.
- Built-in Moshier ephemeris avoids the need to fetch ephemeris files for the baseline calculation.
- `web/engine/vedic-core.js` contains the pure Vedic calculation rules ported from the pinned `vedic-calc` library: sign/nakshatra mapping, divisional charts, Vimshottari Mahadasha and Panchanga indices.
- `web/engine/index.js` adapts the ephemeris to the app's current result shape and provides local time-zone conversion, sunrise/sunset estimation and transition calculations.
- The exact same browser bundle is intended for the PWA and Android WebView APK.

## Migration safety

This is a proof-of-concept branch. The current FastAPI/Python API, Render Blueprint, existing website, and APK workflow on `main` remain unchanged. Do not remove the API or switch the production UI until the local engine has passed:
1. Browser/WebAssembly initialization tests.
2. Golden chart parity checks against the pinned Python engine for multiple places, dates and ayanamsas.
3. Sunrise/sunset and daily Panchanga parity checks.
4. Transition timing checks, including day-boundary and DST cases.
5. Android WebView testing using the packaged assets.

## Accuracy and limitations to verify

The browser adapter uses the built-in Moshier ephemeris mode. The current Python deployment can use Swiss Ephemeris data files or fall back to Moshier. Results must be compared before replacing the Python backend. Sunrise/sunset is currently found by searching for the Sun's apparent-altitude crossing because the browser wrapper does not currently expose the same `rise_trans` method used by the Python engine. The calculated crossing therefore remains provisional until parity tests pass.

## Hosting and connectivity

- Website: static website hosting only; no Jyoti calculation API.
- Android: PWA assets and WASM engine packaged inside the APK.
- Runtime calculation: local to the user's device.
- Internet is needed to open/download the website and receive updates. The APK can calculate offline after installation, subject to browser/WebView storage and file availability.
- Optional place search may still call a third-party public geocoding service. Manual coordinates remain a privacy-preserving fallback.

## Licensing

This codebase already uses AGPL-3.0-or-later and the selected `@swisseph/browser` package is also AGPL-3.0. Preserve upstream copyright and licence notices, and include the corresponding source when distributing or offering the network-accessible website. Review Swiss Ephemeris licensing obligations before changing the project's licence or distribution model.
