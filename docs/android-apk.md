# Android APK

The Android application is a lightweight WebView wrapper around the mobile-first PWA. It bundles the HTML, CSS, JavaScript, manifest and icons inside the APK, so the app shell opens without a separate frontend deployment.

## API connection

Chart calculations still run on the hosted FastAPI service. The default API origin is `https://jyoti-vedic-ai-api.onrender.com` and can be overridden with `VEDIC_API_BASE` while running `scripts/sync_android_assets.py`.

The WebView uses the local origin `http://localhost:5500` for bundled assets. This matches the development origin already allowed by the API's default CORS configuration. The chart, timezone list, Panchanga, and place lookup therefore require an internet connection and a reachable API deployment.

## Build

From the repository root:

```bash
python scripts/sync_android_assets.py
cd android
gradle :app:assembleDebug
```

The debug APK is written to `android/app/build/outputs/apk/debug/app-debug.apk`. GitHub Actions builds and uploads the same APK as the `jyoti-android-apk` workflow artifact.

This is a debug-signed APK for direct testing, not a Play Store release. A production release needs a protected signing key and a separate release build configuration. Do not commit signing credentials.
