from __future__ import annotations

import pytest

from eigencircuits_engine.generate import generate
from eigencircuits_engine.latex import to_latex
from eigencircuits_engine.rng import format_seed

SEEDS = [format_seed(i * 40503 & 0xFFFFFFFF) for i in range(30)]


@pytest.mark.parametrize("seed", SEEDS)
def test_latex_has_required_structure(seed: str) -> None:
    tex = to_latex(generate(seed))
    for marker in (
        r"\documentclass[11pt]{amsart}",
        r"\title",
        r"\begin{document}",
        r"\maketitle",
        r"\begin{abstract}",
        r"\section{",
        r"\begin{thebibliography}",
        r"\end{document}",
    ):
        assert marker in tex, marker


@pytest.mark.parametrize("seed", SEEDS)
def test_latex_braces_balanced(seed: str) -> None:
    tex = to_latex(generate(seed))
    assert tex.count("{") == tex.count("}")
    assert tex.count(r"\begin{document}") == tex.count(r"\end{document}") == 1
