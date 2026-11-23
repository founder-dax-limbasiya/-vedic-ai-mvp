#!/usr/bin/env python3
"""Create a self-contained, local-server-ready Jyoti website ZIP."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DIST = ROOT / "dist"
PACKAGE = DIST / "Jyoti-Vedic-AI-Offline-Website"
ARCHIVE = DIST / "Jyoti-Vedic-AI-Offline-Website.zip"

REQUIRED = (
    "index.html", "styles.css", "app-local.js", "engine.bundle.js",
    "swisseph.wasm", "config.js", "sw.js", "manifest.webmanifest",
    "icon.svg", "icon-192.png", "icon-512.png",
    "icon-maskable-512.png", "apple-touch-icon.png",
)
EXTRA = ("start.py", "START-JYOTI-WINDOWS.bat", "START-JYOTI-MAC-LINUX.sh",
         "README-OFFLINE.txt", "LICENSE", "NOTICE.md")

README = """JYOTI VEDIC AI — OFFLINE WEBSITE PACKAGE

START:
  Windows: double-click START-JYOTI-WINDOWS.bat
  macOS/Linux: run ./START-JYOTI-MAC-LINUX.sh
  Or run: python3 start.py

The launcher starts a small server on YOUR OWN DEVICE and opens the website
at http://127.0.0.1:8787 (or the next free local port). It does not upload
files or start a cloud server. Keep the terminal window open while using it;
press Ctrl+C to stop.

REQUIREMENT:
  Python 3.8 or newer installed on your computer.

OFFLINE:
  Birth chart and Panchanga calculations run locally in your browser using
  the included WebAssembly engine. No Jyoti API/server is contacted.
  Optional place search requires internet and sends the search text to
  OpenStreetMap. Enter latitude/longitude manually for offline use.

ANDROID:
  Use the separate Android APK. Opening index.html directly from a ZIP/file
  manager is not supported because browsers restrict WebAssembly modules and
  service workers on file:// URLs.

LICENCE:
  This project and the included Swiss Ephemeris browser engine are AGPL.
  Keep the included LICENSE and NOTICE files with redistributed copies.
"""

def main() -> None:
    missing = [name for name in REQUIRED if not (WEB / name).is_file()]
    if missing:
        raise SystemExit("Missing built website assets: " + ", ".join(missing))

    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)

    for name in REQUIRED:
        shutil.copy2(WEB / name, PACKAGE / name)
    for name in EXTRA:
        source = ROOT / name
        if not source.is_file():
            raise SystemExit(f"Missing package helper or notice: {name}")
        shutil.copy2(source, PACKAGE / name)

    DIST.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(DIST))
    print(f"Created {ARCHIVE} ({ARCHIVE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
