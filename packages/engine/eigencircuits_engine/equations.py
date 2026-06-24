"""Equation sub-grammar.

Builds short, balanced, KaTeX-safe formulas from the locked subfield's symbol
bank. A subfield's signature ``eqn_motif`` is preferred about 40% of the time;
otherwise a generic motif is specialized with the field's symbols. Field motifs
return bare LaTeX (no ``$``); this module wraps for inline or display use.
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
    roles = ctx.symbols.assigned()
    if motif in ("field", "fieldSignature"):
        body = ctx.field.eqn_motif(roles).strip()
    else:
        body = _generic(ctx, motif, roles).strip()
    body = body.strip("$").strip()
    return f"$$ {body} $$" if display else f"${body}$"


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
