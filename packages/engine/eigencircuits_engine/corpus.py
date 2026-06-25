"""The shared, deterministic corpus.

Every visitor sees the same papers: an arXiv-style identifier maps to a fixed
seed and subject, so the engine regenerates the identical paper on demand. The
set of papers that "exists" is a pure function of the current date -- each day
contributes ~30-50 papers with a stable per-month sequence number -- so a new
batch appears automatically every day, with no database.
"""

from __future__ import annotations

import datetime as dt
import functools
import zlib
from dataclasses import dataclass

from .generate import front_matter, generate, to_dict
from .latex import to_latex
from .lexicon.fields.registry import BY_CODE, FIELDS

CORPUS_DAYS = 90
RECENT_DAYS = 5


def _h(text: str) -> int:
    return zlib.crc32(text.encode("utf-8"))


def _unit(text: str) -> float:
    return _h(text) / 0x100000000


@dataclass(frozen=True)
class Entry:
    id: str
    date: dt.date
    primary: str
    crosslist: tuple[str, ...]
    seed: int


# Real arXiv categories outside the math archive that math papers cross-list to.
_EXTERNAL_NAMES = {
    "cs.DM": "Discrete Mathematics",
    "cs.IT": "Information Theory",
    "cs.NA": "Numerical Analysis",
    "math-ph": "Mathematical Physics",
    "stat.ML": "Machine Learning",
}


def _name(code: str) -> str:
    field = BY_CODE.get(code)
    if field is not None:
        return field.name
    return _EXTERNAL_NAMES.get(code, code)


def _papers_on(day: dt.date) -> int:
    return 30 + _h(f"count:{day.isoformat()}") % 21  # 30..50


def _month_offset(day: dt.date) -> int:
    """Papers dated earlier in the same month, so a paper's sequence number is a
    stable function of its day regardless of the corpus window."""
    total = 0
    cursor = day.replace(day=1)
    while cursor < day:
        total += _papers_on(cursor)
        cursor += dt.timedelta(days=1)
    return total


def _weighted_subject(ident: str) -> str:
    total = sum(f.weight for f in FIELDS)
    target = _unit(f"subj:{ident}") * total
    upto = 0.0
    for f in FIELDS:
        upto += f.weight
        if target < upto:
            return f.code
    return FIELDS[-1].code


def _crosslist(primary: str, ident: str) -> tuple[str, ...]:
    adjacent = list(BY_CODE[primary].adjacent)
    if not adjacent or _unit(f"xl:{ident}") < 0.5:
        return ()
    count = 1 if _unit(f"xn:{ident}") < 0.8 else 2
    chosen: list[str] = []
    for i in range(count):
        code = adjacent[_h(f"xc:{ident}:{i}") % len(adjacent)]
        if code != primary and code not in chosen:
            chosen.append(code)
    return tuple(chosen)


def build_manifest(today: dt.date, days: int = CORPUS_DAYS) -> list[Entry]:
    entries: list[Entry] = []
    day = today - dt.timedelta(days=days - 1)
    while day <= today:
        base = _month_offset(day)
        for k in range(_papers_on(day)):
            seq = base + k + 1
            ident = f"{day.year % 100:02d}{day.month:02d}.{seq:05d}"
            primary = _weighted_subject(ident)
            entries.append(
                Entry(ident, day, primary, _crosslist(primary, ident), _h(ident) & 0xFFFFFFFF)
            )
        day += dt.timedelta(days=1)
    return entries


def recent_dates(manifest: list[Entry], n: int = RECENT_DAYS) -> list[dt.date]:
    return sorted({e.date for e in manifest}, reverse=True)[:n]


def for_category(manifest: list[Entry], cat: str) -> list[Entry]:
    return [e for e in manifest if e.primary == cat or cat in e.crosslist]


# --------------------------------------------------------------------------- #
# Payloads (JSON-ready) consumed by the server / worker
# --------------------------------------------------------------------------- #


def _comments(ident: str) -> str:
    pages = 6 + _h(f"pp:{ident}") % 35
    figures = _h(f"fg:{ident}") % 6
    return f"{pages} pages" + (f", {figures} figures" if figures else "")


def _subjects(entry: Entry) -> dict[str, object]:
    return {
        "primary": entry.primary,
        "primary_name": _name(entry.primary),
        "crosslist": [{"code": c, "name": _name(c)} for c in entry.crosslist],
    }


def listing_entry(entry: Entry, *, abstract: bool = False) -> dict[str, object]:
    model = generate(entry.seed, entry.primary)
    item: dict[str, object] = {
        "id": entry.id,
        "date": entry.date.isoformat(),
        "title": model.title,
        "authors": [a.name for a in model.authors],
        "comments": _comments(entry.id),
        **_subjects(entry),
    }
    if abstract:
        item["abstract"] = model.abstract
    return item


def archive_payload(today: dt.date) -> dict[str, object]:
    manifest = build_manifest(today)
    # Count over the recent window with the same primary-or-crosslist rule the
    # listing uses, so each subject's number equals the "Total of N entries"
    # shown after following its [recent] link.
    window = set(recent_dates(manifest))
    recent = [e for e in manifest if e.date in window]
    counts: dict[str, int] = {}
    for e in recent:
        for code in (e.primary, *e.crosslist):
            counts[code] = counts.get(code, 0) + 1
    subjects = [
        {"code": f.code, "name": f.name, "count": counts.get(f.code, 0)}
        for f in sorted(FIELDS, key=lambda f: f.code)
    ]
    return {
        "archive": "math",
        "subjects": subjects,
        "total": len(recent),
        "recent_dates": [d.isoformat() for d in recent_dates(manifest)],
    }


def list_payload(today: dt.date, cat: str, period: str, skip: int, show: int) -> dict[str, object]:
    manifest = build_manifest(today)
    items = for_category(manifest, cat)
    if period == "recent":
        window = set(recent_dates(manifest))
        items = [e for e in items if e.date in window]
        items.sort(key=lambda e: (e.date, e.id), reverse=True)
    else:  # a YYYY-MM month
        items = [e for e in items if e.date.strftime("%Y-%m") == period]
        items.sort(key=lambda e: e.id)
    total = len(items)
    page = items[skip : skip + show]
    return {
        "cat": cat,
        "name": _name(cat) if cat in BY_CODE else cat,
        "period": period,
        "total": total,
        "skip": skip,
        "show": show,
        "recent_dates": [d.isoformat() for d in recent_dates(manifest)],
        "entries": [listing_entry(e) for e in page],
    }


@functools.lru_cache(maxsize=8192)
def _front(seed: int, primary: str) -> tuple[str, str, str]:
    fm = front_matter(seed, primary)
    return fm["title"], fm["abstract"], " ".join(fm["authors"])


def search_payload(today: dt.date, query: str, cat: str, skip: int, show: int) -> dict[str, object]:
    needle = query.strip().lower()
    matches: list[Entry] = []
    if needle:
        pool = for_category(build_manifest(today), cat) if cat else build_manifest(today)
        for e in pool:
            title, abstract, authors = _front(e.seed, e.primary)
            if needle in f"{title}\n{abstract}\n{authors}".lower():
                matches.append(e)
        matches.sort(key=lambda e: (e.date, e.id), reverse=True)
    total = len(matches)
    return {
        "query": query,
        "cat": cat,
        "total": total,
        "skip": skip,
        "show": show,
        "entries": [listing_entry(e) for e in matches[skip : skip + show]],
    }


def abs_payload(today: dt.date, ident: str) -> dict[str, object] | None:
    entry = next((e for e in build_manifest(today) if e.id == ident), None)
    if entry is None:
        return None
    model = generate(entry.seed, entry.primary)
    tex = to_latex(model)
    hh, mm, ss = (_h(f"t{c}:{ident}") % n for c, n in (("h", 24), ("m", 60), ("s", 60)))
    stamp = f"{entry.date.isoformat()}T{hh:02d}:{mm:02d}:{ss:02d}Z"
    return {
        "id": ident,
        "date": entry.date.isoformat(),
        "comments": _comments(ident),
        "doi": f"10.48550/arXiv.{ident}",
        "submitter": model.authors[0].name,
        "submission": [{"version": 1, "datetime": stamp, "size_kb": len(tex) // 1024 + 1}],
        "msc_primary": model.msc_primary,
        "msc_secondary": model.msc_secondary,
        **_subjects(entry),
        "model": to_dict(model),
        "tex": tex,
    }
