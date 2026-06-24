"""Lexicon data schema.

A :class:`SubfieldLexicon` is pure data describing one arXiv subject class: the
word banks the grammar draws from while a paper is locked to it, the preferred
math symbols, and pools of authentic inline and displayed formulas. Field
modules under ``lexicon/fields`` return one of these; they contain no logic.

Equation templates are LaTeX with two sentinel tokens (no ``str.format``, so
literal braces are safe): ``XSYM`` is replaced by the paper's main symbol and
``ASYM`` by another field symbol.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

# Banks every subfield is expected to provide.
FIELD_BANKS: tuple[str, ...] = (
    "objects",
    "props",
    "spaces",
    "maps",
    "invariants",
    "namedResults",
    "methods",
    "objectGloss",
)


@dataclass(frozen=True)
class SubfieldLexicon:
    code: str  # e.g. "math.NT"
    name: str  # e.g. "Number Theory"
    weight: float  # unnormalized selection weight
    banks: Mapping[str, Sequence[str]]
    symbols: Sequence[str]  # object-naming symbols, e.g. ["E", "K", "\\rho", ...]
    inline_eqns: Sequence[str]  # short formulas for prose
    display_eqns: Sequence[str]  # larger formulas set off on their own line
    msc: Sequence[str] = field(default_factory=tuple)  # MSC 2020 codes, primary first
    adjacent: Sequence[str] = field(default_factory=tuple)  # codes for ~10% cross-listing

    def bank(self, name: str) -> Sequence[str]:
        try:
            return self.banks[name]
        except KeyError as exc:
            raise KeyError(f"{self.code} has no bank {name!r}") from exc
