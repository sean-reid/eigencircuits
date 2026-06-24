"""Lexicon data schema.

A :class:`SubfieldLexicon` is pure data describing one arXiv subject class: the
word banks the grammar draws from while a paper is locked to it, the preferred
math symbols, and a signature displayed-equation motif. Field modules under
``lexicon/fields`` return one of these; they contain no logic.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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

# Roles passed to a subfield's equation motif, mapping a role name (such as
# ``mainObject``) to the math symbol allocated for it.
SymRoles = Mapping[str, str]


@dataclass(frozen=True)
class SubfieldLexicon:
    code: str  # e.g. "math.NT"
    name: str  # e.g. "Number Theory"
    weight: float  # unnormalized selection weight
    banks: Mapping[str, Sequence[str]]
    symbols: Sequence[str]  # KaTeX-safe math symbols, e.g. ["p", "\\zeta(s)", ...]
    eqn_motif: Callable[[SymRoles], str]  # signature displayed formula
    adjacent: Sequence[str] = field(default_factory=tuple)  # codes for ~10% cross-listing

    def bank(self, name: str) -> Sequence[str]:
        try:
            return self.banks[name]
        except KeyError as exc:
            raise KeyError(f"{self.code} has no bank {name!r}") from exc
