"""A small, self-contained example field and grammar.

This is not the production grammar (the 32 subfields arrive later); it exists to
exercise every engine feature, document the authoring API, and give the CLI a
smoke target. It already shows the coherence mechanism: the central object is
bound once and reused across the title, abstract, and theorem.
"""

from __future__ import annotations

from .builder import (
    article,
    bind,
    choice,
    eqn,
    lit,
    nt,
    pick,
    plural,
    quiet,
    ref,
    refnum,
    seq,
    sym,
    titlecase,
)
from .interpreter import realize
from .lexicon.schema import SubfieldLexicon
from .types import Grammar, PaperStyle

EXAMPLE_FIELD = SubfieldLexicon(
    code="math.XX",
    name="Example",
    weight=1.0,
    banks={
        "objects": [
            "variety",
            "scheme",
            "moduli space",
            "vector bundle",
            "lattice",
            "manifold",
        ],
        "props": [
            "smooth",
            "projective",
            "irreducible",
            "proper",
            "normal",
            "reduced",
        ],
        "invariants": ["cohomology", "Betti numbers", "degree", "genus", "Euler characteristic"],
        "methods": [
            "a descent argument",
            "deformation theory",
            "an inductive construction",
            "spectral techniques",
        ],
    },
    symbols=["X", "Y", "Z", "M", "\\mathcal{F}", "\\mathcal{L}"],
    inline_eqns=[
        r"\dim H^{1}(XSYM) = 2",
        r"XSYM \cong ASYM",
        r"\deg XSYM = 3",
    ],
    display_eqns=[
        r"\chi(XSYM) = \sum_{i \ge 0} (-1)^i \dim H^i(XSYM)",
        r"0 \to ASYM \to XSYM \to \mathcal{Q} \to 0",
    ],
)

EXAMPLE_STYLE = PaperStyle(
    numbering="section", citations="numeric", caps="title", length_class="note"
)

_central = seq(ref("mainAdj"), lit(" "), ref("mainObject"))

EXAMPLE_GRAMMAR: Grammar = {
    "Paper": seq(
        quiet(bind("mainObject", pick("objects"), "paper")),
        quiet(bind("mainAdj", pick("props"), "paper")),
        nt("Title"),
        lit("\n\n"),
        nt("Abstract"),
        lit("\n\n"),
        nt("Theorem"),
    ),
    "Title": titlecase(
        choice(
            [
                (3, seq(lit("on the "), pick("invariants"), lit(" of "), article(_central))),
                (2, seq(lit("a note on "), plural(_central))),
            ]
        )
    ),
    "Abstract": seq(
        lit("We study "),
        plural(ref("mainObject")),
        lit(" "),
        sym("mainObject"),
        lit(". By "),
        pick("methods"),
        lit(", we prove that every "),
        _central,
        lit(" satisfies "),
        eqn("cohomDim"),
        lit("."),
    ),
    "Theorem": seq(
        lit("Theorem "),
        refnum("thm", "main"),
        lit(". Let "),
        sym("mainObject"),
        lit(" be "),
        article(_central),
        lit(". Then "),
        eqn("isoNatural"),
        lit("."),
    ),
    # A deliberately recursive rule, used to verify depth-bounded termination.
    "Chain": choice(
        [
            (3, seq(pick("props"), lit(" and "), nt("Chain"))),
            (1, pick("props")),
        ],
        terminal=1,
    ),
}


def demo_paper(seed: int | str) -> str:
    return realize(EXAMPLE_GRAMMAR, EXAMPLE_FIELD, EXAMPLE_STYLE, seed, start="Paper")
