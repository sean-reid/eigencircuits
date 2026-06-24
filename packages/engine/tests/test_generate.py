from __future__ import annotations

import re

import pytest

from eigencircuits_engine.generate import generate, to_dict
from eigencircuits_engine.postprocess import is_math_balanced
from eigencircuits_engine.rng import format_seed
from eigencircuits_engine.types import EquationBlock, PaperModel

# "None"/"undefined" would betray a formatting bug; "n^{1}" an exponent bug.
# (Plain "nan" is avoided here because it is a substring of "discriminant".)
FORBIDDEN = ("None", "undefined", "n^{1}")
SEEDS = [format_seed(i * 2654435761 & 0xFFFFFFFF) for i in range(120)]

_MATH = re.compile(r"\$([^$]{1,16})\$")


def _all_text(model: PaperModel) -> list[str]:
    parts = [model.title, model.abstract]
    for section in model.sections:
        parts.append(section.heading)
        for block in section.blocks:
            parts.append(block.tex if isinstance(block, EquationBlock) else block.text)
    parts.extend(r.text for r in model.references)
    if model.acknowledgments:
        parts.append(model.acknowledgments)
    return parts


def _inline_symbols(text: str) -> set[str]:
    return set(_MATH.findall(text))


def test_same_seed_is_identical() -> None:
    for seed in ("alpha", "m4", "0"):
        assert to_dict(generate(seed)) == to_dict(generate(seed))


def test_structure() -> None:
    from eigencircuits_engine.lexicon.fields.registry import BY_CODE

    model = generate("m4")
    assert model.sections[0].heading == "Introduction"
    assert all(s.blocks for s in model.sections)
    assert 12 <= len(model.references) <= 25
    assert model.subfield in BY_CODE
    assert model.seed == "m4"


def test_length_varies() -> None:
    sizes = {len(generate(s).sections) for s in SEEDS}
    assert max(sizes) - min(sizes) >= 3


@pytest.mark.parametrize("seed", SEEDS[:80])
def test_well_formed(seed: str) -> None:
    for text in _all_text(generate(seed)):
        assert is_math_balanced(text), text
        for token in FORBIDDEN:
            assert token not in text, (token, text)
        assert "  " not in text, text
        assert not re.search(r"\s[,.;]", text), text


@pytest.mark.parametrize("seed", SEEDS[:80])
def test_central_object_coherent(seed: str) -> None:
    # Coherence shows up as shared notation: the main symbol bound for the
    # paper appears in the abstract and again in the body.
    model = generate(seed)
    abstract_syms = _inline_symbols(model.abstract)
    body_syms: set[str] = set()
    for section in model.sections:
        for block in section.blocks:
            if not isinstance(block, EquationBlock):
                body_syms |= _inline_symbols(block.text)
    assert abstract_syms & body_syms, (abstract_syms, body_syms)
