#!/usr/bin/env python3
"""Copy the canonical mobile PWA assets from web/ to Vercel's public/ folder."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "web"
DESTINATION = ROOT / "public"
ASSETS = (
    "index.html",
    "styles.css",
    "app.js",
    "config.js",
    "sw.js",
    "manifest.webmanifest",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
    "apple-touch-icon.png",
)


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    missing = [name for name in ASSETS if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"Missing PWA asset(s): {', '.join(missing)}")
    for name in ASSETS:
        shutil.copy2(SOURCE / name, DESTINATION / name)
    print(f"Synced {len(ASSETS)} PWA assets from web/ to public/.")


if __name__ == "__main__":
    main()
