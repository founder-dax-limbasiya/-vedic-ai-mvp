#!/usr/bin/env python3
"""Bundle the local-first PWA and WebAssembly engine into the Android WebView app."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "web"
DESTINATION = ROOT / "android" / "app" / "src" / "main" / "assets" / "www"
SOURCE_URL = "https://github.com/founder-dax-limbasiya/-vedic-ai-mvp"
ASSETS = (
    "index.html",
    "styles.css",
    "app.js",
    "app-local.js",
    "engine.bundle.js",
    "swisseph.wasm",
    "sw.js",
    "manifest.webmanifest",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
    "apple-touch-icon.png",
)


def main() -> None:
    missing = [name for name in ASSETS if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"Missing web assets: {', '.join(missing)}")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        shutil.copy2(SOURCE / name, DESTINATION / name)

    (DESTINATION / "config.js").write_text(
        "window.VEDIC_CONFIG = {\n"
        f"  SOURCE_URL: {SOURCE_URL!r}\n"
        "};\n",
        encoding="utf-8",
    )
    print(f"Bundled {len(ASSETS) + 1} PWA files with local WebAssembly calculations; no API origin configured")


if __name__ == "__main__":
    main()
