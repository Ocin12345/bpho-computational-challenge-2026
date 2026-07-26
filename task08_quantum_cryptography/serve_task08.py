"""Serve the self-contained Task 8 calculator on localhost."""

from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_DIRECTORY = Path(__file__).resolve().parent / "app"


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must lie within 1 to 65535")
    return port


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=_port, default=8008)
    arguments = parser.parse_args()
    if not APP_DIRECTORY.is_dir():
        raise FileNotFoundError(f"missing Task 8 app directory: {APP_DIRECTORY}")
    handler = functools.partial(SimpleHTTPRequestHandler, directory=APP_DIRECTORY)
    server = ThreadingHTTPServer((arguments.bind, arguments.port), handler)
    print(
        f"Task 8 calculator: http://{arguments.bind}:{arguments.port}/",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
