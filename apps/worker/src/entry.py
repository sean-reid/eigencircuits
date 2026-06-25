"""Cloudflare Python Worker exposing the eigencircuits generator.

The worker is the single origin. It answers the JSON API and hands everything
else to the static-asset binding:

    GET /health|/generate|/archive|/list|/search|/abs -> JSON API
    GET /texlive/...   -> self-hosted TeX Live mirror (static asset; the
                          required `fileid` header is set by assets/_headers)
    everything else    -> the built SPA, with client-side routes resolved by
                          single-page-application not-found handling

The ``eigencircuits_engine`` package is vendored next to this file at deploy
time (see wrangler.toml); it is pure Python and runs under Pyodide.
"""

import datetime as dt
import json
from urllib.parse import parse_qs, urlparse

from workers import Response

from eigencircuits_engine import GRAMMAR_VERSION
from eigencircuits_engine import corpus
from eigencircuits_engine.generate import generate, to_dict
from eigencircuits_engine.latex import to_latex


def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def _int(params: dict, key: str, default: int) -> int:
    try:
        return int(params.get(key, [str(default)])[0])
    except (TypeError, ValueError):
        return default

_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=31536000, immutable",
}


def _json(body: dict, status: int = 200) -> Response:
    return Response(json.dumps(body, ensure_ascii=False), status=status, headers=_HEADERS)


async def on_fetch(request, env) -> Response:
    route = urlparse(request.url)
    params = parse_qs(route.query)
    if route.path == "/health":
        return _json({"ok": True, "grammarVersion": GRAMMAR_VERSION})
    if route.path == "/generate":
        seed = params.get("seed", [None])[0]
        model = generate(seed)
        body = {"model": to_dict(model), "tex": to_latex(model)}
        headers = dict(_HEADERS)
        if seed is None:
            headers["Cache-Control"] = "no-store"
        return Response(json.dumps(body, ensure_ascii=False), headers=headers)
    if route.path == "/archive":
        return _json(corpus.archive_payload(_today()))
    if route.path == "/list":
        cat = params.get("cat", ["math.NT"])[0]
        period = params.get("period", ["recent"])[0]
        skip = max(0, _int(params, "skip", 0))
        show = min(2000, max(1, _int(params, "show", 50)))
        return _json(corpus.list_payload(_today(), cat, period, skip, show))
    if route.path == "/search":
        query = params.get("q", [""])[0]
        cat = params.get("cat", [""])[0]
        skip = max(0, _int(params, "skip", 0))
        show = min(500, max(1, _int(params, "show", 50)))
        return _json(corpus.search_payload(_today(), query, cat, skip, show))
    if route.path == "/abs":
        payload = corpus.abs_payload(_today(), params.get("id", [""])[0])
        return _json(payload, status=200) if payload else _json({"error": "not found"}, 404)
    # Static assets: the SPA, the vendored pdfTeX engine, and the TeX Live
    # mirror under /texlive/. The assets binding applies _headers and resolves
    # unknown paths to index.html (single-page-application not-found handling).
    return await env.ASSETS.fetch(request)
