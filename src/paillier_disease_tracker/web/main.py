from __future__ import annotations

import argparse
import socket
import threading
import time
import webbrowser

import uvicorn


def _is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def _pick_port(host: str, preferred: int, max_attempts: int = 20) -> int:
    if _is_port_free(host, preferred):
        return preferred

    for offset in range(1, max_attempts + 1):
        candidate = preferred + offset
        if _is_port_free(host, candidate):
            return candidate

    raise RuntimeError("No free port found near preferred port")


def _browser_url(host: str, port: int) -> str:
    browser_host = host
    if host in {"0.0.0.0", "::"}:
        browser_host = "127.0.0.1"
    return f"http://{browser_host}:{port}/"


def _open_browser(url: str, delay: float) -> None:
    def _open() -> None:
        webbrowser.open(url)

    timer = threading.Timer(delay, _open)
    timer.daemon = True
    timer.start()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paillier Disease Tracker Web")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--open-delay", type=float, default=0.8)
    parser.add_argument("--log-level", default="info")
    parser.add_argument("--no-auto-port", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    host = args.host
    port = args.port
    if not args.no_auto_port:
        port = _pick_port(host, port)

    if not args.no_browser:
        _open_browser(_browser_url(host, port), args.open_delay)

    uvicorn.run(
        "paillier_disease_tracker.web.app:app",
        host=host,
        port=port,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
