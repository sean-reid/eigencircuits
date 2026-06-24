"""Core types: the grammar node algebra, generation context, and paper model.

A grammar is a mapping from nonterminal names to :data:`GNode` expansion trees.
The node algebra is a tagged union of frozen dataclasses; the interpreter
dispatches on the concrete type. The engine emits a :class:`PaperModel` (a typed
tree), not a raw string, so presentation and export stay independent of
generation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field as dfield

from .lexicon.schema import SubfieldLexicon
from .rng import Rng
from .symbols import SymbolAllocator

# --------------------------------------------------------------------------- #
# Grammar node algebra
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Lit:
    """A literal terminal."""

    value: str


@dataclass(frozen=True)
class NT:
    """A reference to another nonterminal."""

    name: str


@dataclass(frozen=True)
class Seq:
    """Concatenation of child nodes."""

    children: tuple[GNode, ...]


@dataclass(frozen=True)
class Choice:
    """Weighted alternation.

    ``terminal`` is the index of the lowest-recursion option, chosen when the
    depth budget is exhausted so that every recursive rule can terminate.
    """

    options: tuple[tuple[float, GNode], ...]
    terminal: int | None = None


@dataclass(frozen=True)
class Opt:
    """Include ``node`` with probability ``p``."""

    p: float
    node: GNode


@dataclass(frozen=True)
class Rep:
    """Repeat ``node`` between ``lo`` and ``hi`` times, joined by ``sep``."""

    lo: int
    hi: int
    sep: GNode
    node: GNode


@dataclass(frozen=True)
class Pick:
    """Draw a term from the locked subfield bank, optionally binding it."""

    bank: str
    bound: str | None = None


@dataclass(frozen=True)
class Bind:
    """Evaluate ``node`` once and store the result under ``name``."""

    name: str
    node: GNode
    scope: str = "nearest"  # 'paper' | 'section' | 'local' | 'nearest'


@dataclass(frozen=True)
class Ref:
    """Emit a previously bound value, expanding ``fallback`` if unset."""

    name: str
    fallback: GNode | None = None


@dataclass(frozen=True)
class Xform:
    """Post-process the text produced by ``node``."""

    op: str  # 'cap' | 'lower' | 'titlecase' | 'plural' | 'article'
    node: GNode


@dataclass(frozen=True)
class Eqn:
    """Invoke the equation sub-grammar."""

    motif: str
    display: bool = False


@dataclass(frozen=True)
class Sym:
    """Emit the math symbol allocated for ``role``."""

    role: str


@dataclass(frozen=True)
class RefNum:
    """Emit or look up a cross-reference number."""

    counter: str  # 'thm' | 'eq' | 'sec'
    key: str | None = None


@dataclass(frozen=True)
class Cite:
    """Emit a citation drawn from the generated bibliography labels."""

    lo: int = 1
    hi: int = 2


GNode = Lit | NT | Seq | Choice | Opt | Rep | Pick | Bind | Ref | Xform | Eqn | Sym | RefNum | Cite

Grammar = dict[str, GNode]


# --------------------------------------------------------------------------- #
# Generation context
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BoundValue:
    text: str
    is_plural: bool = False


@dataclass
class Scope:
    kind: str  # 'paper' | 'section' | 'local'
    vars: dict[str, BoundValue] = dfield(default_factory=dict)


@dataclass(frozen=True)
class PaperStyle:
    numbering: str  # 'section' | 'doc'
    citations: str  # 'alpha' | 'numeric'
    caps: str  # 'title' | 'sentence'
    length_class: str  # 'note' | 'standard' | 'long'


@dataclass
class GenContext:
    rng: Rng
    field: SubfieldLexicon
    grammar: Grammar
    style: PaperStyle
    symbols: SymbolAllocator
    scopes: list[Scope]
    counters: dict[str, int]
    refs: dict[str, str]
    depth: int = 0
    recent: dict[str, list[str]] = dfield(default_factory=dict)
    extra: dict[str, Sequence[str]] = dfield(default_factory=dict)  # global banks (names, ...)
    cite_labels: list[str] = dfield(default_factory=list)  # bibliography labels for citations

    def push_scope(self, kind: str) -> None:
        self.scopes.append(Scope(kind))

    def pop_scope(self) -> None:
        self.scopes.pop()

    def bind(self, name: str, value: BoundValue, scope: str) -> None:
        self._target_scope(scope).vars[name] = value

    def lookup(self, name: str) -> BoundValue | None:
        for scope in reversed(self.scopes):
            found = scope.vars.get(name)
            if found is not None:
                return found
        return None

    def _target_scope(self, scope: str) -> Scope:
        if scope == "paper":
            return self.scopes[0]
        if scope == "section":
            for s in reversed(self.scopes):
                if s.kind == "section":
                    return s
            return self.scopes[0]
        return self.scopes[-1]


# --------------------------------------------------------------------------- #
# Paper model (engine output)
# --------------------------------------------------------------------------- #


@dataclass
class Author:
    name: str
    affiliation: int
    email: str | None = None


@dataclass
class Para:
    text: str
    kind: str = "para"


@dataclass
class EnvBlock:
    env: str  # 'Definition' | 'Theorem' | 'Proposition' | 'Lemma' | ...
    number: str
    text: str
    name: str | None = None
    kind: str = "env"


@dataclass
class ProofBlock:
    text: str
    kind: str = "proof"


@dataclass
class EquationBlock:
    tex: str
    number: str | None = None
    kind: str = "equation"


Block = Para | EnvBlock | ProofBlock | EquationBlock


@dataclass
class Reference:
    label: str
    text: str


@dataclass
class SectionModel:
    number: str
    heading: str
    blocks: list[Block]


@dataclass
class PaperModel:
    seed: str
    grammar_version: int
    subfield: str
    title: str
    authors: list[Author]
    affiliations: list[str]
    abstract: str
    msc_primary: str
    msc_secondary: list[str]
    keywords: list[str]
    sections: list[SectionModel]
    references: list[Reference]
    style: PaperStyle
    acknowledgments: str | None = None
    funding: str | None = None
