"""Builder API.

Thin constructors over the :data:`GNode` algebra so authored grammar reads
naturally. Lists are normalized to the tuples the frozen dataclasses expect.
"""

from __future__ import annotations

from collections.abc import Sequence

from .types import (
    NT,
    Bind,
    Choice,
    Cite,
    Eqn,
    GNode,
    Lit,
    Opt,
    Pick,
    Ref,
    RefNum,
    Rep,
    Seq,
    Sym,
    Xform,
)


def lit(value: str) -> Lit:
    return Lit(value)


def nt(name: str) -> NT:
    return NT(name)


def seq(*children: GNode) -> Seq:
    return Seq(tuple(children))


def choice(options: Sequence[tuple[float, GNode]], terminal: int | None = None) -> Choice:
    return Choice(tuple(options), terminal)


def opt(p: float, node: GNode) -> Opt:
    return Opt(p, node)


def rep(lo: int, hi: int, sep: GNode, node: GNode) -> Rep:
    return Rep(lo, hi, sep, node)


def pick(bank: str) -> Pick:
    return Pick(bank)


def pick_bound(name: str, bank: str) -> Pick:
    return Pick(bank, bound=name)


def bind(name: str, node: GNode, scope: str = "nearest") -> Bind:
    return Bind(name, node, scope)


def ref(name: str, fallback: GNode | None = None) -> Ref:
    return Ref(name, fallback)


def cap(node: GNode) -> Xform:
    return Xform("cap", node)


def lower(node: GNode) -> Xform:
    return Xform("lower", node)


def titlecase(node: GNode) -> Xform:
    return Xform("titlecase", node)


def plural(node: GNode) -> Xform:
    return Xform("plural", node)


def article(node: GNode) -> Xform:
    return Xform("article", node)


def quiet(node: GNode) -> Xform:
    """Evaluate ``node`` for its side effects (such as binding) but emit nothing."""
    return Xform("quiet", node)


def eqn(motif: str, display: bool = False) -> Eqn:
    return Eqn(motif, display)


def sym(role: str) -> Sym:
    return Sym(role)


def refnum(counter: str, key: str | None = None) -> RefNum:
    return RefNum(counter, key)


def cite(lo: int = 1, hi: int = 2) -> Cite:
    return Cite(lo, hi)
