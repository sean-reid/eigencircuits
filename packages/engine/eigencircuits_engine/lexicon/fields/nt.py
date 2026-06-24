"""math.NT - Number Theory.

Seed from the build spec, expanded with the algebra/number-theory research
dossier.
"""

from __future__ import annotations

from ..schema import SubfieldLexicon

NT = SubfieldLexicon(
    code="math.NT",
    name="Number Theory",
    weight=10.0,
    banks={
        "objects": [
            "prime",
            "$L$-function",
            "modular form",
            "elliptic curve",
            "Galois representation",
            "Dirichlet character",
            "cusp form",
            "ideal class",
            "Dedekind zeta function",
            "Eisenstein series",
            "automorphic form",
            "lattice",
            "Diophantine equation",
            "abelian variety",
            "Hecke eigenform",
            "Selmer group",
            "newform",
            "Shimura variety",
            "Maass form",
            "number field",
        ],
        "props": [
            "$p$-adic",
            "cyclotomic",
            "totally real",
            "supersingular",
            "ordinary",
            "ramified",
            "unramified",
            "primitive",
            "cuspidal",
            "automorphic",
            "monogenic",
            "squarefree",
            "integral",
            "crystalline",
            "semistable",
            "geometrically irreducible",
        ],
        "spaces": [
            "number field",
            "local field",
            "ring of integers",
            "adele ring",
            "Hecke algebra",
            "Selmer group",
            "Galois group",
            "class group",
            "Tate--Shafarevich group",
            "modular curve",
            "Iwasawa algebra",
        ],
        "maps": [
            "Frobenius",
            "Hecke operator",
            "reduction modulo $p$",
            "base change",
            "the regulator map",
            "the cyclotomic character",
            "the Artin map",
            "specialization",
        ],
        "invariants": [
            "rank",
            "conductor",
            "discriminant",
            "regulator",
            "class number",
            "Iwasawa $\\lambda$-invariant",
            "analytic rank",
            "root number",
            "$p$-adic valuation",
            "central value",
        ],
        "namedResults": [
            "the Riemann Hypothesis",
            "the Birch--Swinnerton-Dyer conjecture",
            "the Sato--Tate conjecture",
            "the Bombieri--Vinogradov theorem",
            "the Keating--Snaith conjecture",
            "the Rudnick--Sarnak density conjecture",
            "Langlands functoriality",
            "the Iwasawa Main Conjecture",
            "the Bloch--Kato conjecture",
            "the $abc$ conjecture",
            "Serre's modularity conjecture",
        ],
        "methods": [
            "the circle method",
            "a sieve argument",
            "$p$-adic interpolation",
            "the trace formula",
            "modularity lifting",
            "the theory of newforms",
            "Iwasawa-theoretic techniques",
            "an analysis of the associated $L$-function",
            "a descent argument",
            "the large sieve",
        ],
        "objectGloss": [
            "encodes deep arithmetic information",
            "governs the distribution of primes",
            "arises naturally in the Langlands program",
            "controls the arithmetic of the associated motive",
            "is central to modern number theory",
        ],
    },
    # Object-naming symbols only: plain letters suitable for "let X be ...".
    # Specific notation (zeta, L-functions, fields) lives in the equations.
    # Object-naming letters only. No "p" (clashes with the prime index p in
    # T_p, a_p, \pmod p) and no "N" (clashes with counting functions N(x)).
    symbols=[
        "E",
        "K",
        "F",
        "f",
        "\\chi",
        "\\rho",
        "\\pi",
        "A",
        "V",
        "X",
    ],
    eqn_motif=lambda roles: (
        r"L(s,\chi) = \sum_{n \ge 1} \frac{\chi(n)}{n^{s}} "
        r"= \prod_{p} \bigl(1 - \chi(p) p^{-s}\bigr)^{-1}"
    ),
    msc=["11F11", "11G05", "11M06", "11R23", "11F33", "11G40"],
    adjacent=["math.AG", "math.RT"],
)
