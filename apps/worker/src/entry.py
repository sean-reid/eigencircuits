"""Cloudflare Python Worker exposing the eigencircuits generator.

Routes (same contract as the local dev server):
    GET /generate[?seed=<s>] -> { "model": <PaperModel>, "tex": <str> }
    GET /health              -> { "ok": true, "grammarVersion": <int> }

The ``eigencircuits_engine`` package is vendored next to this file at deploy
time (see wrangler.toml); it is pure Python and runs under Pyodide.
"""

import json
from urllib.parse import parse_qs, urlparse

from workers import Response

from eigencircuits_engine import GRAMMAR_VERSION
from eigencircuits_engine.generate import generate, to_dict
from eigencircuits_engine.latex import to_latex

_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=31536000, immutable",
}


def _json(body: dict, status: int = 200) -> Response:
    return Response(json.dumps(body, ensure_ascii=False), status=status, headers=_HEADERS)


async def on_fetch(request) -> Response:
    route = urlparse(request.url)
    if route.path == "/health":
        return _json({"ok": True, "grammarVersion": GRAMMAR_VERSION})
    if route.path == "/generate":
        seed = parse_qs(route.query).get("seed", [None])[0]
        model = generate(seed)
        # Seeded responses are immutable; a fresh (seedless) one must not cache.
        body = {"model": to_dict(model), "tex": to_latex(model)}
        headers = dict(_HEADERS)
        if seed is None:
            headers["Cache-Control"] = "no-store"
        return Response(json.dumps(body, ensure_ascii=False), headers=headers)
    return _json({"error": "not found"}, status=404)
