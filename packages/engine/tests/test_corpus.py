from __future__ import annotations

import datetime as dt

from eigencircuits_engine import corpus

TODAY = dt.date(2026, 6, 24)


def test_manifest_is_deterministic() -> None:
    a = corpus.build_manifest(TODAY)
    b = corpus.build_manifest(TODAY)
    assert [e.id for e in a] == [e.id for e in b]
    assert all(e1 == e2 for e1, e2 in zip(a, b, strict=True))


def test_ids_are_unique_and_well_formed() -> None:
    ids = [e.id for e in corpus.build_manifest(TODAY)]
    assert len(ids) == len(set(ids))
    for ident in ids:
        yymm, seq = ident.split(".")
        assert len(yymm) == 4 and yymm.isdigit()
        assert len(seq) == 5 and seq.isdigit()


def test_every_subject_name_resolves() -> None:
    # Regression: cross-lists include real non-math arXiv categories (cs.DM,
    # math-ph, stat.ML, ...). _name must resolve them instead of raising.
    for entry in corpus.build_manifest(TODAY):
        subjects = corpus._subjects(entry)
        assert subjects["primary_name"]
        crosslist = subjects["crosslist"]
        assert isinstance(crosslist, list)
        for cross in crosslist:
            assert cross["name"]


def test_id_reconstruction_matches_manifest() -> None:
    # abs_payload reconstructs an entry directly from its id; it must agree with
    # the manifest for every id, and reject malformed or out-of-window ids.
    manifest = corpus.build_manifest(TODAY)
    for entry in manifest:
        assert corpus._entry_from_id(TODAY, entry.id) == entry
    assert corpus._entry_from_id(TODAY, "9999.99999") is None
    assert corpus._entry_from_id(TODAY, "not-an-id") is None


def test_search_returns_matches() -> None:
    payload = corpus.search_payload(TODAY, "the", "", 0, 25)
    total = payload["total"]
    entries = payload["entries"]
    assert isinstance(total, int) and total > 0
    assert isinstance(entries, list) and len(entries) <= 25


def test_abs_roundtrip_and_missing() -> None:
    first = corpus.build_manifest(TODAY)[0]
    payload = corpus.abs_payload(TODAY, first.id)
    assert payload is not None
    assert payload["id"] == first.id
    assert corpus.abs_payload(TODAY, "9999.99999") is None
    assert corpus.abs_payload(TODAY, "") is None
