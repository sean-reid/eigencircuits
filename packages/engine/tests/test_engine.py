from __future__ import annotations

import re

import pytest

from eigencircuits_engine.examples import (
    EXAMPLE_FIELD,
    EXAMPLE_GRAMMAR,
    EXAMPLE_STYLE,
    demo_paper,
)
from eigencircuits_engine.interpreter import expand, make_context, realize
from eigencircuits_engine.postprocess import finalize, is_math_balanced
from eigencircuits_engine.rng import format_seed
from eigencircuits_engine.types import NT

FORBIDDEN = ("None", "undefined", "nan", "NaN")
SEEDS = [format_seed(i * 2654435761 & 0xFFFFFFFF) for i in range(400)]


def test_same_seed_is_identical() -> None:
    for seed in ("demo", "abc123", "0"):
        assert demo_paper(seed) == demo_paper(seed)


def test_distinct_seeds_vary() -> None:
    outputs = {demo_paper(s) for s in SEEDS[:50]}
    assert len(outputs) > 10


@pytest.mark.parametrize("seed", SEEDS[:120])
def test_output_is_well_formed(seed: str) -> None:
    text = demo_paper(seed)
    assert text
    assert is_math_balanced(text)
    for token in FORBIDDEN:
        assert token not in text
    assert "  " not in text
    assert not re.search(r"\s[,.;:]", text)
    assert not re.search(r"([,.;:]){2,}", text)


@pytest.mark.parametrize("seed", SEEDS[:120])
def test_central_object_is_coherent(seed: str) -> None:
    # The object bound at paper scope must reappear: it is referenced in the
    # title, the abstract, and the theorem.
    ctx = make_context(int(seed, 36), EXAMPLE_FIELD, EXAMPLE_GRAMMAR, EXAMPLE_STYLE)
    text = finalize(expand(NT("Paper"), ctx))
    bound = ctx.scopes[0].vars["mainObject"].text
    assert text.lower().count(bound.lower()) >= 2


def test_recursive_rule_terminates() -> None:
    # 'Chain' is left-recursive with a marked terminal option; every seed must
    # halt and produce a non-empty string within the depth budget.
    for seed in SEEDS:
        out = realize(EXAMPLE_GRAMMAR, EXAMPLE_FIELD, EXAMPLE_STYLE, seed, start="Chain")
        assert out
