"""The authored grammar: sentence-level nonterminals.

Document structure (sections, counters, block assembly) lives in
``generate.py``; this module supplies the prose. Everything reads bound values
from paper scope, so the central object, its symbol, the method, and the related
named result stay consistent across the title, abstract, and body.
"""

from __future__ import annotations

from .builder import (
    article,
    cap,
    choice,
    cite,
    eqn,
    lit,
    nt,
    opt,
    pick,
    plural,
    ref,
    seq,
    sym,
)
from .types import Grammar

# Reusable phrase fragments built from the paper-scope bindings.
_central = seq(ref("mainAdj"), lit(" "), ref("mainObject"))
_central2 = seq(ref("mainAdj2"), lit(" "), ref("mainObject"))
_a_central = article(_central)
_plural_central = plural(_central)
_sym = sym("mainObject")  # the main object's symbol as inline math

# Short, varied inline relations. The long field signature is reserved for the
# occasional displayed equation, so it never spams the prose.
_inline_eqn = choice(
    [
        (3, eqn("estimate")),
        (3, eqn("bigO")),
        (3, eqn("cohomDim")),
        (2, eqn("congr")),
        (2, eqn("eigen")),
    ]
)
_iso_eqn = eqn("iso")
_map_eqn = eqn("map")
_display_eqn = choice(
    [
        (1, eqn("field", True)),
        (2, eqn("exactSeq", True)),
        (2, eqn("sum", True)),
        (2, eqn("eigen", True)),
        (2, eqn("cohomDim", True)),
        (1, eqn("estimate", True)),
    ]
)

GRAMMAR: Grammar = {
    # ------------------------------------------------------------------ titles
    "Title": choice(
        [
            (3, seq(lit("on the "), ref("invariant"), lit(" of "), _a_central)),
            (2, seq(ref("invariant"), lit(" of "), _plural_central)),
            (
                2,
                seq(
                    lit("on "),
                    plural(ref("mainObject")),
                    lit(" with "),
                    pick("props"),
                    lit(" "),
                    pick("invariants"),
                ),
            ),
            (1, seq(lit("a note on "), _plural_central)),
            (2, seq(ref("invariant"), lit(" for "), _plural_central)),
            (2, seq(_plural_central, lit(" and "), plural(pick("objects")))),
            (1, seq(lit("towards "), ref("relResult"), lit(" for "), plural(ref("mainObject")))),
            (2, seq(plural(ref("mainObject")), lit(" via "), ref("method"))),
            (1, seq(article(seq(pick("props"), lit(" approach"))), lit(" to "), ref("relResult"))),
        ]
    ),
    # --------------------------------------------------------------- abstract
    "Abstract": seq(
        nt("AbstractTopic"),
        lit(" "),
        nt("AbstractMethod"),
        lit(" "),
        nt("AbstractResult"),
        opt(0.75, seq(lit(" "), nt("AbstractApplication"))),
        opt(0.65, seq(lit(" "), nt("AbstractPositioning"))),
    ),
    "AbstractTopic": choice(
        [
            (3, seq(lit("we study "), _plural_central, lit(" "), _sym, lit("."))),
            (
                2,
                seq(
                    lit("let "),
                    _sym,
                    lit(" be "),
                    _a_central,
                    lit(". we are concerned with the "),
                    ref("invariant"),
                    lit(" of "),
                    _sym,
                    lit("."),
                ),
            ),
            (
                1,
                seq(
                    cap(article(_central)),
                    lit(" "),
                    _sym,
                    lit(", going back to "),
                    pick("names"),
                    lit(", "),
                    ref("gloss"),
                    lit("."),
                ),
            ),
        ]
    ),
    "AbstractMethod": choice(
        [
            (
                3,
                seq(
                    lit("Our approach combines "),
                    ref("method"),
                    lit(" with "),
                    pick("methods"),
                    lit("."),
                ),
            ),
            (2, seq(lit("The argument relies on "), ref("method"), lit("."))),
            (1, seq(lit("Building on "), ref("method"), lit(", we proceed as follows."))),
        ]
    ),
    "AbstractResult": choice(
        [
            (
                3,
                seq(
                    lit("we prove that every "), _central, lit(" satisfies "), _inline_eqn, lit(".")
                ),
            ),
            (
                3,
                seq(
                    lit("we show that the "),
                    ref("invariant"),
                    lit(" of "),
                    _sym,
                    lit(" is "),
                    pick("props"),
                    lit("."),
                ),
            ),
            (
                2,
                seq(
                    lit("our main result asserts that "),
                    _sym,
                    lit(" admits "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit("."),
                ),
            ),
        ]
    ),
    "AbstractApplication": choice(
        [
            (
                2,
                seq(
                    lit("as an application, we deduce "),
                    ref("relResult"),
                    lit(" for "),
                    plural(ref("mainObject")),
                    lit("."),
                ),
            ),
            (
                2,
                seq(lit("this settles a question of "), pick("names"), lit(" in the affirmative.")),
            ),
            (1, seq(lit("in particular, "), _sym, lit(" is "), pick("props"), lit("."))),
        ]
    ),
    "AbstractPositioning": choice(
        [
            (
                2,
                seq(
                    lit("this extends earlier work of "),
                    pick("names"),
                    lit(" and "),
                    pick("names"),
                    lit("."),
                ),
            ),
            (1, seq(lit("along the way, we give a new proof of "), ref("relResult"), lit("."))),
        ]
    ),
    # --------------------------------------------------- theorem environments
    # The central object is introduced in the abstract and the intro; body
    # statements mostly refer to it by symbol or "as above" rather than
    # restating the full "{adj} {object}" phrase, as real papers do.
    "TheoremStmt": choice(
        [
            (
                3,
                seq(
                    lit("Suppose that "),
                    nt("Hypothesis"),
                    lit(". Then "),
                    nt("Conclusion"),
                    opt(0.35, seq(lit(", and moreover "), nt("Conclusion"))),
                    lit("."),
                ),
            ),
            (3, seq(lit("With the notation above, "), nt("Conclusion"), lit("."))),
            (2, seq(lit("Let "), _sym, lit(" be as above. Then "), nt("Conclusion"), lit("."))),
            (2, seq(lit("If "), nt("Hypothesis"), lit(", then "), nt("Conclusion"), lit("."))),
            (
                1,
                seq(
                    lit("Let "),
                    _sym,
                    lit(" be "),
                    _a_central,
                    lit(". Then "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
            (
                1,
                seq(
                    lit("Assume "),
                    nt("Hypothesis"),
                    lit(". Then the following are equivalent: (1) "),
                    nt("Conclusion"),
                    lit("; (2) "),
                    nt("Conclusion"),
                    lit("; (3) "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
        ]
    ),
    "LemmaStmt": choice(
        [
            (3, seq(lit("With the notation above, "), _inline_eqn, lit("."))),
            (2, seq(lit("We have "), _inline_eqn, lit("."))),
            (2, seq(lit("Suppose that "), nt("Hypothesis"), lit(". Then "), _inline_eqn, lit("."))),
            (
                2,
                seq(
                    lit("For every "),
                    pick("objects"),
                    lit(" there exists "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit(" such that "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
            (
                1,
                seq(
                    lit("Let "),
                    _sym,
                    lit(" be "),
                    _a_central,
                    lit(". Then "),
                    _inline_eqn,
                    lit("."),
                ),
            ),
        ]
    ),
    "DefinitionStmt": choice(
        [
            (
                3,
                seq(
                    lit("We say that "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit(" is "),
                    pick("props"),
                    lit(" if "),
                    nt("Condition"),
                    lit("."),
                ),
            ),
            (
                2,
                seq(
                    lit("Recall that "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit(" is said to be "),
                    pick("props"),
                    lit(" if "),
                    nt("Condition"),
                    lit("."),
                ),
            ),
        ]
    ),
    "CorollaryStmt": choice(
        [
            (2, seq(lit("Under the hypotheses above, "), nt("Conclusion"), lit("."))),
            (1, seq(lit("In particular, "), _sym, lit(" is "), pick("props"), lit("."))),
        ]
    ),
    "RemarkStmt": choice(
        [
            (2, seq(lit("Note that "), nt("Conclusion"), lit("."))),
            (
                2,
                seq(
                    lit("When "),
                    _sym,
                    lit(" is "),
                    pick("props"),
                    lit(", this recovers the classical result of "),
                    pick("names"),
                    lit("."),
                ),
            ),
            (1, seq(lit("It is natural to ask whether "), nt("Conclusion"), lit("."))),
            (
                1,
                seq(
                    lit("This was first observed in "),
                    cite(1, 1),
                    lit("; see also "),
                    cite(1, 2),
                    lit("."),
                ),
            ),
        ]
    ),
    # ------------------------------------------------------------- clauses
    "Conclusion": choice(
        [
            (
                3,
                seq(lit("the "), pick("invariants"), lit(" of "), _sym, lit(" is "), pick("props")),
            ),
            (
                2,
                seq(_sym, lit(" is "), pick("props"), lit(" if and only if it is "), pick("props")),
            ),
            (
                2,
                seq(
                    lit("there exists "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit(" such that "),
                    _inline_eqn,
                    lit(" holds"),
                ),
            ),
            (1, seq(lit("there is a natural isomorphism "), _iso_eqn)),
            (
                1,
                seq(
                    plural(ref("mainObject")), lit(" are classified by their "), pick("invariants")
                ),
            ),
            (2, seq(lit("the "), pick("invariants"), lit(" of "), _sym, lit(" is finite"))),
            (2, seq(_sym, lit(" is determined by its "), pick("invariants"))),
            (2, seq(_sym, lit(" admits "), article(seq(pick("props"), lit(" "), pick("objects"))))),
            (
                2,
                seq(
                    lit("the "),
                    pick("invariants"),
                    lit(" of "),
                    _sym,
                    lit(" coincides with the "),
                    pick("invariants"),
                    lit(" of "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                ),
            ),
            (
                2,
                seq(
                    lit("every "),
                    pick("props"),
                    lit(" "),
                    pick("objects"),
                    lit(" arises from "),
                    _sym,
                ),
            ),
            (1, seq(_sym, lit(" is "), pick("props"))),
            (
                1,
                seq(
                    lit("the natural map "),
                    _map_eqn,
                    lit(" is "),
                    choice(
                        [(1, lit("surjective")), (1, lit("injective")), (1, lit("an isomorphism"))]
                    ),
                ),
            ),
            (
                1,
                seq(
                    lit("the "),
                    pick("invariants"),
                    lit(" of "),
                    _sym,
                    lit(" does not depend on the choice of "),
                    pick("objects"),
                ),
            ),
        ]
    ),
    "Hypothesis": choice(
        [
            (1, seq(_sym, lit(" is "), _a_central)),
            (3, seq(_sym, lit(" is "), pick("props"), lit(" and "), pick("props"))),
            (2, seq(_sym, lit(" is "), pick("props"))),
            (
                2,
                seq(
                    lit("the "),
                    ref("invariant"),
                    lit(" of "),
                    _sym,
                    lit(" is "),
                    choice([(1, lit("finite")), (1, lit("nonzero")), (1, lit("bounded"))]),
                ),
            ),
            (1, seq(_inline_eqn, lit(" holds"))),
        ]
    ),
    # Used only inside definitions, so the condition refers to the object being
    # defined ("it"/"its"), never the paper's main object.
    "Condition": choice(
        [
            (3, seq(lit("it is "), pick("props"), lit(" and "), pick("props"))),
            (
                2,
                seq(
                    lit("its "),
                    pick("invariants"),
                    choice(
                        [(1, lit(" vanishes")), (1, lit(" is finite")), (1, lit(" is trivial"))]
                    ),
                ),
            ),
            (2, seq(lit("it is "), pick("props"))),
            (2, seq(lit("it admits "), article(seq(pick("props"), lit(" "), pick("objects"))))),
            (1, seq(lit("the associated "), pick("objects"), lit(" is "), pick("props"))),
            (1, seq(_inline_eqn, lit(" holds"))),
        ]
    ),
    # --------------------------------------------------------------- proofs
    "ProofStep": choice(
        [
            (3, seq(pick("connectives"), lit(" "), nt("Conclusion"), lit("."))),
            (2, seq(lit("By "), pick("namedResults"), lit(", "), nt("Conclusion"), lit("."))),
            (2, seq(lit("Applying "), pick("methods"), lit(", we obtain "), _inline_eqn, lit("."))),
            (2, seq(lit("By "), cite(1, 1), lit(", "), nt("Conclusion"), lit("."))),
            (1, seq(lit("As shown in "), cite(1, 1), lit(", "), nt("Conclusion"), lit("."))),
            (1, seq(lit("A short computation gives "), _inline_eqn, lit("."))),
            (1, seq(lit("After a harmless reduction, we may assume "), nt("Conclusion"), lit("."))),
            (1, seq(lit("It remains to verify that "), nt("Conclusion"), lit("."))),
        ]
    ),
    # ------------------------------------------------------- introduction moves
    "IntroContext": choice(
        [
            (3, seq(lit("Let "), _sym, lit(" be "), _a_central, lit("."))),
            (
                2,
                seq(
                    cap(article(_central)),
                    lit(", going back to "),
                    pick("names"),
                    lit(", "),
                    ref("gloss"),
                    lit("."),
                ),
            ),
        ]
    ),
    "IntroPriorWork": seq(
        lit("The study of "),
        plural(ref("mainObject")),
        choice(
            [
                (1, lit(" has been extensively developed in recent years")),
                (1, lit(" has attracted considerable attention")),
            ]
        ),
        choice(
            [
                (2, seq(lit("; see "), cite(2, 3), lit(" and the references therein."))),
                (
                    2,
                    seq(
                        lit("; see, for instance, the work of "),
                        pick("names"),
                        lit(" and "),
                        pick("names"),
                        lit(" "),
                        cite(1, 2),
                        lit("."),
                    ),
                ),
            ]
        ),
    ),
    "IntroGap": choice(
        [
            (
                2,
                seq(
                    lit("Despite these advances, it remains a delicate problem to determine the "),
                    ref("invariant"),
                    lit(" of "),
                    _sym,
                    lit("."),
                ),
            ),
            (1, seq(lit("However, little is known beyond the "), pick("props"), lit(" case."))),
        ]
    ),
    "IntroThisPaper": choice(
        [
            (
                3,
                seq(
                    lit("In this paper, we "),
                    choice([(1, lit("determine")), (1, lit("compute")), (1, lit("investigate"))]),
                    lit(" the "),
                    ref("invariant"),
                    lit(" of "),
                    _plural_central,
                    lit("."),
                ),
            ),
            (2, seq(lit("In this paper, we prove that "), nt("Conclusion"), lit("."))),
            (
                2,
                seq(
                    lit("The aim of this note is to "),
                    choice([(1, lit("classify")), (1, lit("describe"))]),
                    lit(" "),
                    _plural_central,
                    lit("."),
                ),
            ),
        ]
    ),
    "IntroStrategy": seq(
        lit("The key ingredient is "),
        ref("method"),
        lit(", which we combine with "),
        pick("methods"),
        lit("."),
    ),
    "ExampleStmt": choice(
        [
            (
                2,
                seq(
                    lit("Let "),
                    _sym,
                    lit(" be "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                    lit(". Then "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
            (
                1,
                seq(
                    lit("Consider "), _a_central, lit(". In this case "), nt("Conclusion"), lit(".")
                ),
            ),
        ]
    ),
    "ConjectureStmt": choice(
        [
            (2, seq(lit("We conjecture that "), nt("Conclusion"), lit("."))),
            (
                2,
                seq(
                    lit("We expect that, if "),
                    nt("Hypothesis"),
                    lit(", then "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
            (1, seq(lit("It is natural to conjecture that "), nt("Conclusion"), lit("."))),
        ]
    ),
    "ClosingRemark": choice(
        [
            (
                2,
                seq(
                    lit("It would be interesting to "),
                    choice([(1, lit("determine")), (1, lit("decide")), (1, lit("know"))]),
                    lit(" whether "),
                    nt("Conclusion"),
                    lit("."),
                ),
            ),
            (
                2,
                seq(
                    lit("We expect that "),
                    nt("Conclusion"),
                    lit(", though we have not been able to prove this."),
                ),
            ),
            (2, seq(lit("A natural question is whether "), nt("Conclusion"), lit("."))),
            (2, seq(lit("It remains open whether "), nt("Conclusion"), lit("."))),
            (1, seq(lit("We conjecture that "), nt("Conclusion"), lit("."))),
            (1, seq(lit("Our methods should extend to "), plural(pick("objects")), lit("."))),
            (
                2,
                seq(
                    lit("As an application, we deduce "),
                    ref("relResult"),
                    lit(" for "),
                    plural(ref("mainObject")),
                    lit("."),
                ),
            ),
            (1, seq(lit("We hope to return to these questions in future work."))),
            (
                1,
                seq(
                    lit("Finally, we note that the "),
                    pick("invariants"),
                    lit(" of "),
                    _sym,
                    lit(" remains poorly understood."),
                ),
            ),
        ]
    ),
    "DisplayEqn": _display_eqn,
    # Bibliography titles: on-theme but drawn freshly so they vary entry to entry.
    "RefTitle": choice(
        [
            (
                3,
                seq(
                    lit("on the "),
                    pick("invariants"),
                    lit(" of "),
                    article(seq(pick("props"), lit(" "), pick("objects"))),
                ),
            ),
            (
                2,
                seq(
                    pick("invariants"),
                    lit(" of "),
                    plural(seq(pick("props"), lit(" "), pick("objects"))),
                ),
            ),
            (
                2,
                seq(
                    pick("invariants"),
                    lit(" for "),
                    plural(seq(pick("props"), lit(" "), pick("objects"))),
                ),
            ),
            (1, seq(lit("a note on "), plural(pick("objects")))),
            (2, seq(plural(pick("objects")), lit(" and "), plural(pick("objects")))),
        ]
    ),
}
