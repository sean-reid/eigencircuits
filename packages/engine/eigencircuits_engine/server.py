"""A tiny dependency-free HTTP server for local development.

Exposes the same contract as the Cloudflare Worker so the web app can develop
against a real engine without the Pyodide toolchain:

    GET /generate            -> { "model": <PaperModel>, "tex": <str> }
    GET /generate?seed=<s>   -> deterministic for that seed
    GET /health              -> { "ok": true, "grammarVersion": <int> }

Run with:  uv --project packages/engine run python -m eigencircuits_engine.server
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import GRAMMAR_VERSION
from .generate import generate, to_dict
from .latex import to_latex


def _payload(seed: str | None) -> dict[str, object]:
    model = generate(seed)
    return {"model": to_dict(model), "tex": to_latex(model)}


class _Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, object]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (stdlib API name)
        route = urlparse(self.path)
        if route.path == "/health":
            self._send(200, {"ok": True, "grammarVersion": GRAMMAR_VERSION})
            return
        if route.path == "/generate":
            params = parse_qs(route.query)
            seed = params.get("seed", [None])[0]
            self._send(200, _payload(seed))
            return
        self._send(404, {"error": "not found"})

    def log_message(self, *_args: object) -> None:  # quieter console
        pass


def main(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"eigencircuits dev server on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
