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
    "sum",
    "integral",
    "exactSeq",
    "eigen",
    "cohomDim",
    "isoNatural",
    "limitLaw",
    "generating",
)


def build_eqn(ctx: GenContext, motif: str, display: bool) -> str:
    roles = ctx.symbols.assigned()
    if motif in ("field", "fieldSignature") or ctx.rng.chance(0.4):
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
    if motif == "estimate":
        p = ctx.rng.int_in_range(1, 3)
        return rf"\left\| {x} \right\| \lesssim {a}^{{-{p}}} \log {a}"
    if motif == "sum":
        return rf"\sum_{{i=1}}^{{n}} {a}_i = {x}"
    if motif == "integral":
        return rf"\int_{{\Omega}} {a}\, d\mu \le C \left\| {x} \right\|"
    if motif == "exactSeq":
        return r"0 \to A \to B \to C \to 0"
    if motif == "eigen":
        return (
            rf"\mathcal{{L}} {x} = \lambda {x}, \qquad \lambda \in \mathrm{{Spec}}(\mathcal{{L}})"
        )
    if motif == "cohomDim":
        return rf"\dim H^{{i}}({x}) = \sum_{{j \ge 0}} (-1)^j b_j"
    if motif == "isoNatural":
        return rf"{x} \cong \mathrm{{Hom}}(A, B)"
    if motif == "limitLaw":
        return r"\frac{S_n - n\mu}{\sqrt{n}\,\sigma} \Rightarrow \mathcal{N}(0,1)"
    if motif == "generating":
        return rf"F({a}) = \sum_{{n \ge 0}} c_n {a}^n"
    return rf"{x} = {a}"
