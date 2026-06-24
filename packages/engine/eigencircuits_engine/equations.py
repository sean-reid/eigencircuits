"""Equation sub-grammar.

Draws authentic formulas from the locked subfield's inline/display pools, with
per-paper anti-repetition so the same formula does not recur. Templates carry
the sentinel tokens ``XSYM`` (main symbol) and ``ASYM`` (another symbol). A
generic, parametrized motif set is the fallback for fields without pools.
"""

from __future__ import annotations

from collections.abc import Callable

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
    # Shape-specific slots (a natural isomorphism / a natural map) must keep
    # their form, so they bypass the free-form formula pools.
    pool = ctx.field.display_eqns if display else ctx.field.inline_eqns
    if motif in ("iso", "map"):
        body = _generic(ctx, motif, ctx.symbols.assigned())
    elif pool:
        body = _fill(ctx, _draw(ctx, list(pool), "__eqd__" if display else "__eqi__"))
    else:
        body = _generic(ctx, motif, ctx.symbols.assigned())
    body = body.strip("$").strip()
    return f"$$ {body} $$" if display else f"${body}$"


def _draw(ctx: GenContext, pool: list[str], key: str) -> str:
    """Pick a template not used yet in this paper; reset the memory if exhausted.

    De-duplication is on the raw template, so each structural shape appears at
    most once per paper while the randomized fill varies it from paper to paper.
    """
    used = ctx.recent.setdefault(key, [])
    for _ in range(10):
        choice = pool[ctx.rng.int_in_range(0, len(pool) - 1)]
        if choice not in used:
            used.append(choice)
            return choice
    used.clear()
    return pool[ctx.rng.int_in_range(0, len(pool) - 1)]


_PRIMES = (2, 3, 5, 7, 11, 13)


def _fill(ctx: GenContext, template: str) -> str:
    """Substitute symbols (XSYM/ASYM/BSYM) and randomized numeric tokens.

    Each token gets a single value per call, so repeated tokens in one formula
    stay consistent while the formula varies across papers.
    """
    rng = ctx.rng
    x = ctx.symbols.get("mainObject", ctx.rng)
    others = [s for s in ctx.field.symbols if s != x] or ["Y", "Z"]
    body = template.replace("XSYM", x)
    if "ASYM" in body:
        body = body.replace("ASYM", others[rng.int_in_range(0, len(others) - 1)])
    if "BSYM" in body:
        rest = [s for s in others if s + "$" not in body] or others
        body = body.replace("BSYM", rest[rng.int_in_range(0, len(rest) - 1)])
    tokens: dict[str, Callable[[], int]] = {
        "@K@": lambda: rng.int_in_range(2, 6),
        "@I@": lambda: rng.int_in_range(1, 3),
        "@N@": lambda: rng.int_in_range(2, 9),
        "@P@": lambda: _PRIMES[rng.int_in_range(0, len(_PRIMES) - 1)],
        "@R@": lambda: rng.int_in_range(0, 3),
        "@C@": lambda: rng.int_in_range(2, 5),
    }
    for token, make in tokens.items():
        if token in body:
            body = body.replace(token, str(make()))
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
    if motif == "map":
        return rf"{x} \to {b}" if b != x else rf"{x} \to H^{{1}}({x})"
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
