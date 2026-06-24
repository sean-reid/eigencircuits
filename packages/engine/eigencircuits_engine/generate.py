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
from .lexicon.global_bank import (
    HEDGES,
    INITIALS,
    JOURNALS,
    PROOF_CONNECTIVES,
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

_PROOF_OPENS = (
    "We argue by induction on the relevant invariant.",
    "The proof relies on the construction introduced above.",
    "We may assume without loss of generality that the normalization holds.",
    "Fix the data as above.",
)
_PROOF_CLOSES = (
    "This completes the proof.",
    "as desired.",
    "which is what we wanted.",
    "The result now follows.",
)


def generate(seed: str | int | None = None) -> PaperModel:
    seed_int = parse_seed(seed) if seed is not None else secrets.randbits(32)
    rng = Rng(seed_int)
    field = select_field(rng)
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
        "note": rng.int_in_range(1, 2),
        "standard": rng.int_in_range(3, 4),
        "long": rng.int_in_range(5, 7),
    }[style.length_class]
    has_prelim = style.length_class != "note" and rng.chance(0.85)

    sections: list[SectionModel] = [_intro_section(ctx, core_count, has_prelim)]
    if has_prelim:
        sections.append(_prelim_section(ctx))
    for _ in range(core_count):
        sections.append(_core_section(ctx))
    if rng.chance(0.6):
        sections.append(_final_section(ctx))

    acknowledgments = _acknowledgments(ctx)
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


def _intro_section(ctx: GenContext, core_count: int, has_prelim: bool) -> SectionModel:
    number = _start_section(ctx, "Introduction")
    blocks: list[Block] = []

    opener = expand(NT("IntroContext"), ctx)
    if ctx.rng.chance(0.85):
        opener += " " + expand(NT("IntroPriorWork"), ctx)
    if ctx.rng.chance(0.7):
        opener += " " + expand(NT("IntroGap"), ctx)
    blocks.append(Para(finalize(opener)))
    blocks.append(Para(finalize(expand(NT("IntroThisPaper"), ctx))))

    blocks.append(
        EnvBlock(
            env="Theorem",
            number="A",
            name="Main Theorem" if ctx.rng.chance(0.3) else None,
            text=finalize(expand(NT("TheoremStmt"), ctx)),
        )
    )
    blocks.append(Para(finalize(expand(NT("IntroStrategy"), ctx))))
    blocks.append(Para(_outline(ctx, core_count, has_prelim)))

    ctx.pop_scope()
    return SectionModel(number=number, heading="Introduction", blocks=blocks)


def _prelim_section(ctx: GenContext) -> SectionModel:
    heading = cap_first(f"Preliminaries on {pluralize(ctx.rng.choice(ctx.field.bank('objects')))}")
    number = _start_section(ctx, heading)
    blocks: list[Block] = [_env(ctx, "Definition", "DefinitionStmt")]
    if ctx.rng.chance(0.7):
        blocks.append(_env(ctx, "Remark", "RemarkStmt"))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


def _core_section(ctx: GenContext) -> SectionModel:
    heading = _core_heading(ctx)
    number = _start_section(ctx, heading)
    blocks: list[Block] = []
    if ctx.rng.chance(0.45):
        blocks.append(_env(ctx, "Definition", "DefinitionStmt"))
        if ctx.rng.chance(0.4):
            blocks.append(Para(finalize(expand(NT("RemarkStmt"), ctx))))
    for i in range(ctx.rng.int_in_range(1, 3)):
        _theorem_like(ctx, blocks)
        if i == 0 and ctx.rng.chance(0.3):
            blocks.append(_env(ctx, "Corollary", "CorollaryStmt"))
    if ctx.rng.chance(0.55):
        equation = _display_equation(ctx)
        if equation is not None:
            blocks.append(equation)
    if ctx.rng.chance(0.4):
        blocks.append(_env(ctx, "Example", "ExampleStmt"))
    if ctx.rng.chance(0.5):
        blocks.append(_env(ctx, "Remark", "RemarkStmt"))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


def _final_section(ctx: GenContext) -> SectionModel:
    heading = ctx.rng.choice(
        ("Concluding remarks", "Final remarks", "Applications", "Further questions")
    )
    number = _start_section(ctx, heading)
    blocks: list[Block] = [Para(finalize(expand(NT("RemarkStmt"), ctx)))]
    if ctx.rng.chance(0.6):
        blocks.append(Para(finalize(expand(NT("AbstractApplication"), ctx))))
    ctx.pop_scope()
    return SectionModel(number=number, heading=heading, blocks=blocks)


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #


def _theorem_like(ctx: GenContext, blocks: list[Block]) -> None:
    env = ctx.rng.pick_weighted([(3.0, "Theorem"), (2.0, "Proposition"), (3.0, "Lemma")])
    stmt = "LemmaStmt" if env == "Lemma" else "TheoremStmt"
    number = _item_number(ctx)
    blocks.append(EnvBlock(env=env, number=number, text=finalize(expand(NT(stmt), ctx))))
    blocks.append(ProofBlock(text=_proof(ctx)))


def _env(ctx: GenContext, env: str, stmt: str) -> EnvBlock:
    return EnvBlock(
        env=env,
        number=_item_number(ctx),
        text=finalize(expand(NT(stmt), ctx)),
    )


def _proof(ctx: GenContext) -> str:
    parts = [ctx.rng.choice(_PROOF_OPENS)]
    for _ in range(ctx.rng.int_in_range(2, 4)):
        parts.append(expand(NT("ProofStep"), ctx))
    parts.append(ctx.rng.choice(_PROOF_CLOSES))
    return finalize(" ".join(parts))


def _display_equation(ctx: GenContext) -> EquationBlock | None:
    # Avoid emitting the same displayed formula twice in one paper.
    used = ctx.recent.setdefault("__display__", [])
    for _ in range(6):
        tex = expand(NT("DisplayEqn"), ctx).strip().strip("$").strip()
        if tex not in used:
            used.append(tex)
            return EquationBlock(tex=tex, number=_eq_number(ctx))
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


def _acknowledgments(ctx: GenContext) -> str | None:
    if not ctx.rng.chance(0.7):
        return None
    thanks = ctx.rng.pick_weighted(
        [(1.0, "thank"), (1.0, "are grateful to"), (1.0, "gratefully acknowledge")]
    )
    extra = ctx.rng.pick_weighted(
        [
            (1.0, "helpful discussions"),
            (1.0, "useful comments"),
            (1.0, "their interest in this work"),
        ]
    )
    name = ctx.rng.choice(SURNAMES)
    return f"The authors {thanks} {name} for {extra}."


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _title(ctx: GenContext) -> str:
    raw = finalize(expand(NT("Title"), ctx))
    return titlecase(raw) if ctx.style.caps == "title" else cap_first(raw)


def _core_heading(ctx: GenContext) -> str:
    inv = ctx.rng.choice(ctx.field.bank("invariants"))
    obj = ctx.rng.choice(ctx.field.bank("objects"))
    template = ctx.rng.pick_weighted(
        [
            (3.0, f"The {inv} of {pluralize(obj)}"),
            (2.0, f"Construction of the {obj}"),
            (2.0, "Proof of the main theorem"),
            (1.0, f"{cap_first(inv)} estimates"),
        ]
    )
    return cap_first(template)


def _outline(ctx: GenContext, core_count: int, has_prelim: bool) -> str:
    parts = ["The paper is organized as follows."]
    sec = 2
    if has_prelim:
        parts.append(f"Section {sec} fixes notation and recalls the necessary background.")
        sec += 1
    parts.append(f"In Section {sec} we prove our main results.")
    if core_count > 1:
        parts.append("The remaining sections develop consequences and worked examples.")
    return finalize(" ".join(parts))
