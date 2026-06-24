"""Equation sub-grammar.

Draws authentic formulas from the locked subfield's inline/display pools, with
per-paper anti-repetition so the same formula does not recur. Templates carry
the sentinel tokens ``XSYM`` (main symbol) and ``ASYM`` (another symbol). A
generic, parametrized motif set is the fallback for fields without pools.
"""

from __future__ import annotations

from .types import GenContext

GENERIC_MOTIFS: tuple[str, ...] = (
    "estimate",
    "bigO",
    "sum",
    "iso",
    "exactSeq",
    "eigen",
    "cohomDim",
    "congr",
    "limitLaw",
)


def build_eqn(ctx: GenContext, motif: str, display: bool) -> str:
    pool = ctx.field.display_eqns if display else ctx.field.inline_eqns
    if pool:
        body = _fill(ctx, _draw(ctx, list(pool), "__eqd__" if display else "__eqi__"))
    else:
        body = _generic(ctx, motif, ctx.symbols.assigned())
    body = body.strip("$").strip()
    return f"$$ {body} $$" if display else f"${body}$"


def _draw(ctx: GenContext, pool: list[str], key: str) -> str:
    """Pick a template not used yet in this paper; reset the memory if exhausted."""
    used = ctx.recent.setdefault(key, [])
    for _ in range(10):
        choice = pool[ctx.rng.int_in_range(0, len(pool) - 1)]
        if choice not in used:
            used.append(choice)
            return choice
    used.clear()
    return pool[ctx.rng.int_in_range(0, len(pool) - 1)]


def _fill(ctx: GenContext, template: str) -> str:
    x = ctx.symbols.get("mainObject", ctx.rng)
    body = template.replace("XSYM", x)
    if "ASYM" in body:
        syms = [s for s in ctx.field.symbols if s != x] or list(ctx.field.symbols) or ["Y"]
        body = body.replace("ASYM", syms[ctx.rng.int_in_range(0, len(syms) - 1)])
    return body


def _obj(ctx: GenContext, roles: dict[str, str], default: str) -> str:
    return roles.get("mainObject") or (ctx.field.symbols[0] if ctx.field.symbols else default)


def _generic(ctx: GenContext, motif: str, roles: dict[str, str]) -> str:
    x = _obj(ctx, roles, "X")
    syms = list(ctx.field.symbols) or ["X", "Y", "Z"]
    a = syms[ctx.rng.int_in_range(0, len(syms) - 1)]
    b = next((s for s in (syms[ctx.rng.int_in_range(0, len(syms) - 1)],) if s != x), "Y")
    p = ctx.rng.int_in_range(1, 3)
    pw = "" if p == 1 else f"^{{{p}}}"
    if motif == "estimate":
        return rf"\lvert {x} \rvert \le C\, n{pw} \log n"
    if motif == "bigO":
        return rf"a_n = O\!\left(n{pw} \log n\right)"
    if motif == "sum":
        return rf"{x} = \sum_{{n \ge 1}} \frac{{a_n}}{{n^{{s}}}}"
    if motif == "iso":
        return rf"{x} \cong {b}" if b != x else rf"{x} \cong H^{{1}}({x})"
    if motif == "exactSeq":
        return rf"0 \to A \to {x} \to B \to 0"
    if motif == "eigen":
        return rf"T_p {x} = a_p\, {x}"
    if motif == "cohomDim":
        return rf"\dim_{{\mathbb{{Q}}}} H^{{{p}}}({x}) = {ctx.rng.int_in_range(1, 4)}"
    if motif == "congr":
        return r"a_p \equiv p + 1 \pmod{\ell}"
    if motif == "limitLaw":
        return r"\frac{S_n - n\mu}{\sqrt{n}\,\sigma} \Rightarrow \mathcal{N}(0,1)"
    return rf"{x} = {a}"
