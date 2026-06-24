"""Theme initialization.

Establishes a paper's identity before any text is produced: the locked subfield,
its central objects and notation (bound once at paper scope and reused for
coherence), the immutable house style, and the front matter (authors, MSC codes,
keywords).
"""

from __future__ import annotations

import unicodedata

from .lexicon.fields.registry import weighted_fields
from .lexicon.global_bank import (
    AGENCIES,
    FIRST_NAMES,
    INITIALS,
    INSTITUTIONS,
    SURNAMES,
)
from .lexicon.schema import SubfieldLexicon
from .rng import Rng
from .types import Author, BoundValue, GenContext, PaperStyle


def select_field(rng: Rng) -> SubfieldLexicon:
    return rng.pick_weighted(weighted_fields())


def init_theme(ctx: GenContext) -> None:
    """Bind the central objects, adjectives, method, and related result."""
    f = ctx.field
    ctx.bind("mainObject", BoundValue(rng_choice(ctx, "objects")), "paper")
    ctx.symbols.get("mainObject", ctx.rng)  # fix the main symbol deterministically
    ctx.bind("mainAdj", BoundValue(rng_choice(ctx, "props")), "paper")
    ctx.bind("mainAdj2", BoundValue(rng_choice(ctx, "props")), "paper")
    if ctx.rng.chance(0.5):
        ctx.bind("secondObject", BoundValue(rng_choice(ctx, "objects")), "paper")
        ctx.symbols.get("secondObject", ctx.rng)
    ctx.bind("method", BoundValue(rng_choice(ctx, "methods")), "paper")
    ctx.bind("method2", BoundValue(rng_choice(ctx, "methods")), "paper")
    ctx.bind("relResult", BoundValue(rng_choice(ctx, "namedResults")), "paper")
    ctx.bind("invariant", BoundValue(rng_choice(ctx, "invariants")), "paper")
    ctx.bind("gloss", BoundValue(rng_choice(ctx, "objectGloss")), "paper")
    ctx.bind("relName", BoundValue(ctx.rng.choice(SURNAMES)), "paper")
    _ = f  # field is read through ctx in the helpers


def rng_choice(ctx: GenContext, bank: str) -> str:
    return ctx.rng.choice(ctx.field.bank(bank))


def make_style(rng: Rng) -> PaperStyle:
    length_class = rng.pick_weighted([(1.5, "note"), (5.0, "standard"), (3.5, "long")])
    numbering = "section" if length_class != "note" or rng.chance(0.5) else "doc"
    citations = "alpha" if rng.chance(0.5) else "numeric"
    caps = "title" if rng.chance(0.5) else "sentence"
    return PaperStyle(
        numbering=numbering,
        citations=citations,
        caps=caps,
        length_class=length_class,
    )


def person_name(rng: Rng) -> str:
    # One surname per author. (Joining two surnames with an en-dash reads as a
    # compound eponym, not a person.) Genuinely hyphenated surnames already
    # exist in the bank, e.g. "Harish-Chandra".
    surname = rng.choice(SURNAMES)
    given = rng.choice(INITIALS) if rng.chance(0.4) else rng.choice(FIRST_NAMES)
    return f"{given} {surname}"


def make_authors(rng: Rng) -> tuple[list[Author], list[str]]:
    count = rng.pick_weighted([(3.0, 1), (4.0, 2), (3.0, 3), (1.0, 4)])
    n_aff = rng.int_in_range(1, min(2, count))
    affiliations = [_affiliation(rng) for _ in range(n_aff)]
    # Email domain follows the affiliation, so address and email agree.
    domains = [_domain_for(a) for a in affiliations]
    authors: list[Author] = []
    for _ in range(count):
        name = person_name(rng)
        aff = rng.int_in_range(0, n_aff - 1)
        authors.append(Author(name=name, affiliation=aff, email=_email(name, domains[aff])))
    return authors, affiliations


_AFF_STOPWORDS = frozenset(
    [
        "university",
        "institute",
        "of",
        "mathematics",
        "department",
        "school",
        "faculty",
        "national",
        "technical",
        "centre",
        "center",
        "research",
        "sciences",
        "mathematical",
        "geometry",
        "and",
        "theory",
        "state",
        "statistics",
        "advanced",
        "for",
        "des",
        "etudes",
        "scientifiques",
        "college",
        "sorbonne",
        "royal",
    ]
)


def _ascii(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    return "".join(c for c in folded if c.isascii() and c.isalpha())


def _domain_for(affiliation: str) -> str:
    tokens = [_ascii(t).lower() for t in affiliation.replace(",", " ").split()]
    candidates = [t for t in tokens if t and t not in _AFF_STOPWORDS]
    key = max(candidates, key=len) if candidates else "math"
    return f"math.{key}.edu"


def _email(name: str, domain: str) -> str:
    surname = name.split()[-1].split("--")[-1]
    handle = _ascii(surname).lower() or "author"
    return f"{handle}@{domain}"


# Generated-institution parts, mixed with the real ones in INSTITUTIONS.
_AFF_CITIES = (
    "Aarhus",
    "Geneva",
    "Heidelberg",
    "Lyon",
    "Trieste",
    "Uppsala",
    "Kanazawa",
    "Coimbra",
    "Wrocław",
    "Nijmegen",
    "Adelaide",
    "Tbilisi",
    "Haifa",
    "Bilbao",
    "Bergen",
    "Ghent",
    "Lund",
    "Graz",
    "Bristol",
    "Sheffield",
    "Nantes",
    "Rennes",
    "Bologna",
    "Padua",
    "Turin",
    "Valencia",
    "Granada",
    "Porto",
    "Lisbon",
    "Tartu",
    "Vilnius",
    "Kraków",
    "Poznań",
    "Brno",
    "Debrecen",
    "Cluj",
    "Belgrade",
    "Sofia",
    "Sendai",
    "Nagoya",
    "Hsinchu",
    "Daejeon",
    "Pohang",
    "Hangzhou",
    "Nanjing",
    "Chennai",
    "Pune",
    "Bengaluru",
    "Cape Town",
    "Nairobi",
    "Montevideo",
    "Bogotá",
    "Santiago",
    "Córdoba",
    "Guadalajara",
    "Auckland",
    "Wellington",
    "Reykjavík",
    "Ann Arbor",
    "Boulder",
    "Davis",
    "Madison",
    "Eugene",
    "Storrs",
    "Stony Brook",
)
_AFF_TEMPLATES = (
    "University of {city}",
    "{city} Center for Mathematical Sciences",
    "Department of Mathematics, University of {city}",
    "Mathematical Institute, {city}",
    "Centre for Geometry and Number Theory, {city}",
    "{city} Research Institute for Mathematical Sciences",
    "Faculty of Mathematics, {city} State University",
    "School of Mathematics and Statistics, University of {city}",
    "Technical University of {city}",
    "National Institute of Mathematics, {city}",
)


def _affiliation(rng: Rng) -> str:
    if rng.chance(0.5):
        return rng.choice(INSTITUTIONS)
    return rng.choice(_AFF_TEMPLATES).format(city=rng.choice(_AFF_CITIES))


def make_msc(rng: Rng, field: SubfieldLexicon) -> tuple[str, list[str]]:
    codes = list(field.msc) or ["00A05"]
    primary = codes[0]
    rest = codes[1:]
    n = min(len(rest), rng.int_in_range(1, 2))
    secondary = _sample(rng, rest, n)
    return primary, secondary


def make_keywords(rng: Rng, field: SubfieldLexicon) -> list[str]:
    # Keywords are noun terms (objects, invariants, qualifiers); not methods, and
    # math is kept intact ("$p$-adic", "$L$-function") as in real papers.
    pool: list[str] = []
    for bank in ("objects", "invariants", "props"):
        pool.extend(field.bank(bank))
    count = rng.int_in_range(4, 6)
    return _sample(rng, pool, min(count, len(pool)))


def make_funding(rng: Rng) -> str | None:
    if not rng.chance(0.6):
        return None
    return f"This work was partially supported by {_funding_clause(rng)}."


def _funding_clause(rng: Rng) -> str:
    """A funding phrase whose grant code matches the agency's real format."""
    agency = rng.choice(AGENCIES)
    if agency == "NSF":
        return f"NSF grant DMS-{rng.int_in_range(1700000, 2499999)}"
    if agency == "ERC":
        return (
            "the European Research Council under grant agreement no. "
            f"{rng.int_in_range(640000, 949999)}"
        )
    if agency == "EPSRC":
        return f"EPSRC grant EP/{chr(rng.int_in_range(78, 90))}{rng.int_in_range(100000, 999999)}/1"
    if agency == "DFG":
        return f"the DFG (project number {rng.int_in_range(100000, 499999)})"
    if agency == "JSPS":
        return (
            f"JSPS KAKENHI grant JP{rng.int_in_range(18, 24):02d}K{rng.int_in_range(10000, 99999)}"
        )
    if agency == "NSERC":
        return f"NSERC (RGPIN-{rng.int_in_range(2016, 2024)}-{rng.int_in_range(100000, 699999)})"
    return f"the Simons Foundation (grant {rng.int_in_range(300000, 899999)})"


def _sample(rng: Rng, pool: list[str], n: int) -> list[str]:
    chosen: list[str] = []
    guard = 0
    while len(chosen) < n and guard < 200:
        candidate = rng.choice(pool)
        if candidate not in chosen:
            chosen.append(candidate)
        guard += 1
    return chosen
