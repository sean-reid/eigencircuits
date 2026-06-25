"""Top-level generation: assemble a :class:`PaperModel` from the grammar.

Document structure, counters, and section scopes are managed here in Python;
the grammar supplies the prose for each block. The result is a typed tree, ready
for rendering or LaTeX export.
"""

from __future__ import annotations

import secrets
import unicodedata
from dataclasses import asdict
from typing import Any

from . import GRAMMAR_VERSION
from .grammar import GRAMMAR
from .interpreter import expand
from .lexicon.fields.registry import BY_CODE
from .lexicon.global_bank import (
    HEDGES,
    INITIALS,
    INVARIANT_PREDICATES,
    JOURNALS,
    PROOF_CLOSERS,
    PROOF_CONNECTIVES,
    PROOF_OPENERS,
    PUBLISHERS,
    SURNAMES,
)
from .lexicon.schema import SubfieldLexicon
from .postprocess import cap_first, finalize, pluralize, titlecase
from .rng import Rng, format_seed, parse_seed
from .symbols import SymbolAllocator
from .theme import (
    init_theme,
    make_authors,
    make_funding,
    make_keywords,
    make_msc,
    make_style,
    select_field,
)
from .types import (
    NT,
    Block,
    EnvBlock,
    EquationBlock,
    GenContext,
    PaperModel,
    PaperStyle,
    Para,
    ProofBlock,
    Reference,
    Scope,
    SectionModel,
)


def generate(seed: str | int | None = None, subfield: str | None = None) -> PaperModel:
    seed_int = parse_seed(seed) if seed is not None else secrets.randbits(32)
    rng = Rng(seed_int)
    field = BY_CODE[subfield] if subfield is not None else select_field(rng)
    style = make_style(rng)
    ctx = _make_context(rng, field, style)
    init_theme(ctx)

    title = _title(ctx)
    abstract = finalize(expand(NT("Abstract"), ctx))
    authors, affiliations = make_authors(rng)
    msc_primary, msc_secondary = make_msc(rng, field)
    keywords = make_keywords(rng, field)

    # Build the bibliography first so the body can cite real labels.
    references = _build_bibliography(ctx)
    ctx.cite_labels = [r.label for r in references]

    core_count = {
        "note": rng.int_in_range(2, 3),
        "standard": rng.int_in_range(4, 5),
        "long": rng.int_in_range(6, 8),
    }[style.length_class]
    has_prelim = style.length_class != "note" and rng.chance(0.85)
    has_final = rng.chance(0.6)

    # Plan the section headings up front so the introduction's outline is
    # accurate and no two headings collide.
    headings = _plan_headings(ctx, core_count, has_prelim, has_final)
    outline = _outline(headings)

    sections: list[SectionModel] = []
    cursor = 0
    sections.append(_intro_section(ctx, headings[cursor], outline))
    cursor += 1
    if has_prelim:
        sections.append(_prelim_section(ctx, headings[cursor]))
        cursor += 1
    for _ in range(core_count):
        sections.append(_core_section(ctx, headings[cursor]))
        cursor += 1
    if has_final:
        sections.append(_final_section(ctx, headings[cursor]))
        cursor += 1

    acknowledgments = _acknowledgments(ctx, len(authors))
    funding = make_funding(rng)

    return PaperModel(
        seed=format_seed(seed_int),
        grammar_version=GRAMMAR_VERSION,
        subfield=field.code,
        title=title,
        authors=authors,
        affiliations=affiliations,
        abstract=abstract,
        msc_primary=msc_primary,
        msc_secondary=msc_secondary,
        keywords=keywords,
        sections=sections,
        references=references,
        style=style,
        acknowledgments=acknowledgments,
        funding=funding,
    )


def to_dict(model: PaperModel) -> dict[str, Any]:
    return asdict(model)


def front_matter(seed: str | int | None = None, subfield: str | None = None) -> dict[str, Any]:
    """Just the title, authors, and abstract -- cheap enough to scan the whole
    corpus for search. Consumes randomness in the same order as ``generate`` up
    to the authors, so the title/abstract match the full paper exactly."""
    seed_int = parse_seed(seed) if seed is not None else secrets.randbits(32)
    rng = Rng(seed_int)
    field = BY_CODE[subfield] if subfield is not None else select_field(rng)
    style = make_style(rng)
    ctx = _make_context(rng, field, style)
    init_theme(ctx)
    title = _title(ctx)
    abstract = finalize(expand(NT("Abstract"), ctx))
    authors, _ = make_authors(rng)
    return {"title": title, "abstract": abstract, "authors": [a.name for a in authors]}


def _item_number(ctx: GenContext) -> str:
    ctx.counters["item"] = ctx.counters.get("item", 0) + 1
    n = ctx.counters["item"]
    if ctx.style.numbering == "section":
        return f"{ctx.counters['sec']}.{n}"
    return str(n)


def _eq_number(ctx: GenContext) -> str:
    ctx.counters["eq"] = ctx.counters.get("eq", 0) + 1
    n = ctx.counters["eq"]
    if ctx.style.numbering == "section":
        return f"{ctx.counters['sec']}.{n}"
    return str(n)


# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #


def _make_context(rng: Rng, field: SubfieldLexicon, style: PaperStyle) -> GenContext:
    return GenContext(
        rng=rng,
        field=field,
        grammar=GRAMMAR,
        style=style,
        symbols=SymbolAllocator(field.symbols),
        scopes=[Scope("paper")],
        counters={"item": 0, "eq": 0, "sec": 0},
        refs={},
        extra={
            "names": SURNAMES,
            "connectives": PROOF_CONNECTIVES,
            "hedges": HEDGES,
            "invariantProps": INVARIANT_PREDICATES,
        },
    )


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


def _start_section(ctx: GenContext, heading: str) -> str:
    ctx.counters["sec"] += 1
    if ctx.style.numbering == "section":
        ctx.counters["item"] = 0
        ctx.counters["eq"] = 0
    ctx.push_scope("section")
    return str(ctx.counters["sec"])


def _intro_section(ctx: GenContext, heading: str, outline: str) -> SectionModel:
    number = _start_section(ctx, heading)
    blocks: list[Block] = []

    opener = expand(NT("IntroContext"), ctx)
    if ctx.rng.chance(0.85):
        opener += " " + expand(NT("IntroPriorWork"), ctx)
    if ctx.rng.chance(0.7):
        opener += " " + expand(NT("IntroGap"), ctx)
    blocks.append(Para(finalize(opener)))
    blocks.append(Para(finalize(expand(NT("IntroThisPaper"), ctx))))

    # A normal numbered theorem (amsthm renders it "Theorem 1.1"), optionally
    # named, so later "by Theorem 1.1" references resolve in the compiled PDF.
    main_number = _item_number(ctx)
    blocks.append(
        EnvBlock(
            env="Theorem",
            number=main_number,
            name="Main Theorem" if ctx.rng.chance(0.3) else None,
            text=finalize(expand(NT("TheoremStmt"), ctx)),
        )
    )
    ctx.int_refs.append(f"Theorem {main_number}")
    if ctx.rng.chance(0.35):
        blocks.append(Para("We also obtain the following consequence."))
        blocks.append(_env(ctx, "Corollary", "CorollaryStmt"))
    blocks.append(Para(finalize(expand(NT("IntroStrategy"), ctx))))
    blocks.append(Para(outline))

    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


def _prelim_section(ctx: GenContext, heading: str) -> SectionModel:
    number = _start_section(ctx, heading)
    blocks: list[Block] = [_env(ctx, "Definition", "DefinitionStmt")]
    if ctx.rng.chance(0.7):
        blocks.append(_env(ctx, "Remark", "RemarkStmt"))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


def _core_section(ctx: GenContext, heading: str) -> SectionModel:
    number = _start_section(ctx, heading)
    blocks: list[Block] = []
    if ctx.rng.chance(0.45):
        blocks.append(_env(ctx, "Definition", "DefinitionStmt"))
        if ctx.rng.chance(0.4):
            blocks.append(Para(finalize(expand(NT("RemarkStmt"), ctx))))
    for i in range(ctx.rng.int_in_range(2, 3)):
        _theorem_like(ctx, blocks)
        if i == 0 and ctx.rng.chance(0.35):
            blocks.append(_env(ctx, "Corollary", "CorollaryStmt"))
    if ctx.rng.chance(0.55):
        equation = _display_equation(ctx)
        if equation is not None:
            blocks.append(Para(_fresh(ctx, "__lead__", _EQN_LEADS)))
            blocks.append(equation)
    if ctx.rng.chance(0.4):
        blocks.append(_env(ctx, "Example", "ExampleStmt"))
    if ctx.rng.chance(0.5):
        blocks.append(_env(ctx, "Remark", "RemarkStmt"))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


_FINAL_HEADINGS = ("Concluding remarks", "Final remarks", "Applications", "Further questions")

# Lead-ins so a displayed equation is introduced rather than left floating.
_EQN_LEADS = (
    "We record the following identity.",
    "Recall the following relation.",
    "The main computation is summarized below.",
    "We will make repeated use of the identity below.",
    "It is convenient to record the following.",
    "The starting point is the following relation.",
    "A direct computation yields the following.",
    "The key estimate reads as follows.",
    "We have the following explicit formula.",
    "Recall that one has the following.",
    "The following identity will be used repeatedly.",
    "We summarize the relevant relation below.",
    "This leads to the following expression.",
    "We obtain the following closed form.",
    "The relevant identity is the following.",
    "One verifies the following relation.",
    "We now state the underlying identity.",
    "The proof hinges on the following formula.",
    "We isolate the following relation for later use.",
    "Concretely, we have the following.",
    "It will be useful to recall the following.",
    "The construction yields the following identity.",
    "We collect the relevant formula below.",
    "For convenience we record the following.",
    "The following relation plays a central role.",
    "We shall need the following identity.",
    "This may be rewritten as follows.",
    "The above specializes to the following.",
    "Unwinding the definitions gives the following.",
    "We are led to the following identity.",
    "Our analysis produces the following relation.",
    "The following will be needed in the sequel.",
)


def _final_section(ctx: GenContext, heading: str) -> SectionModel:
    number = _start_section(ctx, heading)
    # Distinct closing sentences (not just non-adjacent): match on the opening
    # words so "It remains open..." cannot appear twice in the same paragraph.
    sentences: list[str] = []
    seen: set[str] = set()
    target = ctx.rng.int_in_range(2, 4)
    tries = 0
    while len(sentences) < target and tries < 24:
        sentence = expand(NT("ClosingRemark"), ctx)
        key = " ".join(sentence.split()[:3]).lower()
        if key not in seen:
            seen.add(key)
            sentences.append(sentence)
        tries += 1
    blocks: list[Block] = [Para(finalize(" ".join(sentences)))]
    if ctx.rng.chance(0.4):
        blocks.append(_env(ctx, "Conjecture", "ConjectureStmt"))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


def _theorem_like(ctx: GenContext, blocks: list[Block]) -> None:
    env = ctx.rng.pick_weighted([(3.0, "Theorem"), (2.0, "Proposition"), (3.0, "Lemma")])
    stmt = "LemmaStmt" if env == "Lemma" else "TheoremStmt"
    number = _item_number(ctx)
    statement = finalize(expand(NT(stmt), ctx))
    # Build the proof before registering this result, so a proof never cites the
    # statement it is proving (only earlier equations and results).
    proof = _proof(ctx)
    blocks.append(EnvBlock(env=env, number=number, text=statement))
    blocks.append(ProofBlock(text=proof))
    ctx.int_refs.append(f"{env} {number}")


def _env(ctx: GenContext, env: str, stmt: str) -> EnvBlock:
    return EnvBlock(
        env=env,
        number=_item_number(ctx),
        text=finalize(expand(NT(stmt), ctx)),
    )


def _proof(ctx: GenContext) -> str:
    parts: list[str] = []
    # Open with a distinct opener (most of the time), not seen yet in this paper.
    if ctx.rng.chance(0.8):
        used = ctx.recent.setdefault("__open__", [])
        for _ in range(6):
            opener = ctx.rng.choice(PROOF_OPENERS)
            if opener not in used:
                used.append(opener)
                parts.append(opener)
                break
    for _ in range(ctx.rng.int_in_range(2, 5)):
        # Sometimes cite an earlier equation or result, as real proofs do.
        if ctx.int_refs and ctx.rng.chance(0.35):
            parts.append(_cross_ref_step(ctx))
        else:
            parts.append(expand(NT("ProofStep"), ctx))
    parts.append(_fresh(ctx, "__close__", PROOF_CLOSERS))
    return finalize(" ".join(parts))


def _cross_ref_step(ctx: GenContext) -> str:
    conclusion = expand(NT("Conclusion"), ctx)
    refs = ctx.int_refs
    if len(refs) >= 2 and ctx.rng.chance(0.4):
        a = ctx.rng.choice(refs)
        b = ctx.rng.choice(refs)
        for _ in range(4):
            if b != a:
                break
            b = ctx.rng.choice(refs)
        if b != a:
            return f"Combining {a} and {b}, {conclusion}."
    ref = ctx.rng.choice(refs)
    lead = ctx.rng.choice(
        (f"By {ref}, ", f"Using {ref}, ", f"It follows from {ref} that ", f"In view of {ref}, ")
    )
    return f"{lead}{conclusion}."


def _display_equation(ctx: GenContext) -> EquationBlock | None:
    # Avoid emitting the same displayed formula twice in one paper.
    used = ctx.recent.setdefault("__display__", [])
    for _ in range(6):
        tex = expand(NT("DisplayEqn"), ctx).strip().strip("$").strip()
        if tex not in used:
            used.append(tex)
            number = _eq_number(ctx)
            ctx.int_refs.append(f"({number})")
            return EquationBlock(tex=tex, number=number)
    return None


# --------------------------------------------------------------------------- #
# Closing matter
# --------------------------------------------------------------------------- #


def _build_bibliography(ctx: GenContext) -> list[Reference]:
    count = ctx.rng.int_in_range(12, 25)
    raw = [_reference_data(ctx) for _ in range(count)]
    raw.sort(key=lambda r: (r["surnames"][0].lower(), r["year"]))
    refs: list[Reference] = []
    used: dict[str, int] = {}
    for i, r in enumerate(raw, 1):
        label = str(i) if ctx.style.citations == "numeric" else _alpha_key(r, used)
        refs.append(Reference(label=label, text=r["text"]))
    return refs


def _reference_data(ctx: GenContext) -> dict[str, Any]:
    count = ctx.rng.int_in_range(1, 3)
    surnames = [ctx.rng.choice(SURNAMES) for _ in range(count)]
    names = [f"{ctx.rng.choice(INITIALS)} {s}" for s in surnames]
    authors = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    title = cap_first(expand(NT("RefTitle"), ctx))
    kind = ctx.rng.pick_weighted([(6.0, "journal"), (2.0, "book"), (3.0, "arxiv")])
    # The current arXiv identifier scheme (YYMM.NNNNN) dates from 2007.
    year = ctx.rng.int_in_range(2007, 2026) if kind == "arxiv" else ctx.rng.int_in_range(1996, 2026)
    if kind == "journal":
        journal = ctx.rng.choice(JOURNALS)
        vol = ctx.rng.int_in_range(1, 400)
        start = ctx.rng.int_in_range(1, 900)
        end = start + ctx.rng.int_in_range(8, 60)
        text = (
            f"{authors}, \\emph{{{title}}}, {journal} \\textbf{{{vol}}} ({year}), {start}--{end}."
        )
    elif kind == "book":
        text = f"{authors}, \\emph{{{title}}}, {ctx.rng.choice(PUBLISHERS)}, {year}."
    else:
        month = ctx.rng.int_in_range(1, 12)
        number = ctx.rng.int_in_range(1, 99999)
        text = (
            f"{authors}, \\emph{{{title}}}, preprint, "
            f"arXiv:{year % 100:02d}{month:02d}.{number:05d}."
        )
    return {"surnames": surnames, "year": year, "text": text}


def _alpha_key(r: dict[str, Any], used: dict[str, int]) -> str:
    surnames: list[str] = r["surnames"]
    yy = f"{r['year'] % 100:02d}"
    if len(surnames) == 1:
        base = _ascii_letters(surnames[0])[:3].title()
    else:
        base = "".join(_ascii_letters(s)[:1].upper() for s in surnames[:3])
    key = f"{base}{yy}"
    seen = used.get(key, 0)
    used[key] = seen + 1
    return key if seen == 0 else f"{key}{chr(ord('a') + seen - 1)}"


def _ascii_letters(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if c.isascii() and c.isalpha()) or "X"


def _acknowledgments(ctx: GenContext, n_authors: int) -> str | None:
    if not ctx.rng.chance(0.7):
        return None
    single = n_authors == 1
    subject = "The author" if single else "The authors"
    verb = ctx.rng.pick_weighted(
        [
            (1.0, "thanks" if single else "thank"),
            (1.0, "is grateful to" if single else "are grateful to"),
            (1.0, "gratefully acknowledges" if single else "gratefully acknowledge"),
        ]
    )
    extra = ctx.rng.pick_weighted(
        [
            (1.0, "helpful discussions"),
            (1.0, "useful comments"),
            (1.0, "their interest in this work"),
            (1.0, "comments on an earlier draft"),
        ]
    )
    name = ctx.rng.choice(SURNAMES)
    return f"{subject} {verb} {name} for {extra}."


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _title(ctx: GenContext) -> str:
    raw = finalize(expand(NT("Title"), ctx))
    return titlecase(raw) if ctx.style.caps == "title" else cap_first(raw)


def _fresh(ctx: GenContext, key: str, pool: tuple[str, ...]) -> str:
    """Pick an item not used yet in this paper under ``key``.

    When the pool is exhausted it resets but keeps the most recent item
    excluded, so the same item never appears twice in a row even across a reset.
    """
    used = ctx.recent.setdefault(key, [])
    candidates = [c for c in pool if c not in used]
    if not candidates:
        used[:] = used[-1:]
        candidates = [c for c in pool if c not in used]
    choice = candidates[ctx.rng.int_in_range(0, len(candidates) - 1)]
    used.append(choice)
    return choice


def _bound(ctx: GenContext, name: str, bank: str) -> str:
    found = ctx.lookup(name)
    return found.text if found is not None else ctx.rng.choice(ctx.field.bank(bank))


def _core_heading(ctx: GenContext) -> str:
    # Headings stay on the paper's topic: mostly the main object and the bound
    # invariant, occasionally a related object for variety.
    main = _bound(ctx, "mainObject", "objects")
    obj = main if ctx.rng.chance(0.7) else ctx.rng.choice(ctx.field.bank("objects"))
    inv = (
        _bound(ctx, "invariant", "invariants")
        if ctx.rng.chance(0.6)
        else ctx.rng.choice(ctx.field.bank("invariants"))
    )
    template = ctx.rng.pick_weighted(
        [
            (3.0, f"The {inv} of {pluralize(obj)}"),
            (2.0, f"Construction of the {obj}"),
            (2.0, "Proof of the main theorem"),
            (2.0, f"Basic properties of {pluralize(obj)}"),
            (1.0, f"{cap_first(inv)} estimates"),
            (1.0, f"Applications to {pluralize(obj)}"),
        ]
    )
    return cap_first(template)


def _plan_headings(
    ctx: GenContext, core_count: int, has_prelim: bool, has_final: bool
) -> list[str]:
    headings = ["Introduction"]
    if has_prelim:
        main = pluralize(_bound(ctx, "mainObject", "objects"))
        prelim = ctx.rng.choice(
            (
                cap_first(f"Preliminaries on {main}"),
                "Notation and conventions",
                cap_first(f"Background on {main}"),
            )
        )
        headings.append(prelim)
    used = {h.lower() for h in headings}
    proof_used = False
    for _ in range(core_count):
        heading = _core_heading(ctx)
        for _retry in range(8):
            clash = heading.lower() in used or (
                heading == "Proof of the main theorem" and proof_used
            )
            if not clash:
                break
            heading = _core_heading(ctx)
        used.add(heading.lower())
        proof_used = proof_used or heading == "Proof of the main theorem"
        headings.append(heading)
    if has_final:
        headings.append(ctx.rng.choice(_FINAL_HEADINGS))
    return headings


def _outline(headings: list[str]) -> str:
    n = len(headings)
    parts = ["The paper is organized as follows."]
    pos = 1
    if n > 1 and headings[1].startswith("Preliminaries"):
        parts.append("Section 2 fixes notation and recalls the necessary background.")
        pos = 2
    has_final = headings[-1] in _FINAL_HEADINGS
    last_core = (n - 1) if has_final else n
    first_core = pos + 1
    if first_core == last_core:
        parts.append(f"In Section {first_core} we prove our main results.")
    elif first_core < last_core:
        parts.append(
            f"Sections {first_core}--{last_core} are devoted to the proofs of our main results."
        )
    if has_final:
        parts.append(f"In Section {n} we discuss applications and open questions.")
    return finalize(" ".join(parts))
