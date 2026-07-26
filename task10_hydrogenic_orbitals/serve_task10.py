"""Serve the Task 10 explorer from a deterministic local-only web server."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_DIRECTORY = Path(__file__).resolve().parent / "app"


class Task10RequestHandler(SimpleHTTPRequestHandler):
    """Static handler with strict offline and development-safe headers."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'",
        )
        super().end_headers()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Local interface")
    parser.add_argument("--port", type=int, default=4210, help="TCP port")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    if not 1 <= arguments.port <= 65_535:
        raise SystemExit("--port must be between 1 and 65535")
    handler = partial(Task10RequestHandler, directory=str(APP_DIRECTORY))
    server = ThreadingHTTPServer((arguments.host, arguments.port), handler)
    print(f"Task 10 explorer: http://{arguments.host}:{arguments.port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTask 10 server stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
