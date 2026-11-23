#!/usr/bin/env python3
"""Serve the bundled Jyoti site only on this computer (loopback interface)."""
from __future__ import annotations

import functools
import http.server
import socket
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_port() -> int:
    for port in range(8787, 8810):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free local port found between 8787 and 8809.")


def main() -> None:
    port = find_port()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    print("Jyoti Vedic AI is running locally.")
    print(f"Open: {url}")
    print("Only this device can connect. Keep this window open; press Ctrl+C to stop.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Jyoti local website...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
