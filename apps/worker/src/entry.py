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
import re
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

# The corpus is a function of the current date, so date-dependent endpoints must
# revalidate often; a paper (by id) and a seeded generation are immutable.
_FRESH = "public, max-age=300, stale-while-revalidate=86400"
_IMMUTABLE = "public, max-age=31536000, immutable"
_NOSTORE = "no-store"
_SEED_RE = re.compile(r"^[0-9a-z]{1,16}$", re.IGNORECASE)


def _headers(cache: str) -> dict:
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": cache,
    }


def _json(body: dict, status: int = 200, cache: str = _FRESH) -> Response:
    return Response(json.dumps(body, ensure_ascii=False), status=status, headers=_headers(cache))


async def on_fetch(request, env) -> Response:
    route = urlparse(request.url)
    params = parse_qs(route.query)
    if route.path == "/health":
        return _json({"ok": True, "grammarVersion": GRAMMAR_VERSION}, cache=_NOSTORE)
    if route.path == "/generate":
        seed = params.get("seed", [None])[0]
        if seed is not None and not _SEED_RE.match(seed):
            return _json({"error": "invalid seed"}, status=400, cache=_NOSTORE)
        model = generate(seed)
        body = {"model": to_dict(model), "tex": to_latex(model)}
        return _json(body, cache=_IMMUTABLE if seed else _NOSTORE)
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
        if payload:
            return _json(payload, cache=_IMMUTABLE)
        return _json({"error": "not found"}, status=404, cache=_NOSTORE)
    if route.path.startswith("/texlive/"):
        # Serve a TeX file. A missing file would otherwise fall through to the
        # SPA's index.html (single-page-application not-found handling), and the
        # pdfTeX engine would ingest HTML as a .tex/.vf/.cfg file. Detect that
        # fallback (text/html on a /texlive path) and report the file absent;
        # the engine negative-caches a 301 and proceeds.
        asset = await env.ASSETS.fetch(request)
        content_type = asset.headers.get("content-type") or ""
        if "text/html" in content_type:
            return Response("Not found", status=301)
        return asset
    # Everything else is the SPA; unknown paths resolve to index.html.
    return await env.ASSETS.fetch(request)
