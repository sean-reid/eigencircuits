"""The interpreter: realize a :data:`GNode` tree to text.

This is the only place randomness is consumed. It threads the generation
context, enforces a depth budget so recursive rules terminate, binds and reads
back values for coherence, and avoids immediate lexical repetition.
"""

from __future__ import annotations

from .equations import build_eqn
from .lexicon.schema import SubfieldLexicon
from .postprocess import cap_first, finalize, lower_first, pluralize, titlecase, with_article
from .rng import Rng, parse_seed
from .symbols import SymbolAllocator
from .types import (
    NT,
    Bind,
    BoundValue,
    Choice,
    Cite,
    Eqn,
    GenContext,
    GNode,
    Grammar,
    Lit,
    Opt,
    PaperStyle,
    Pick,
    Ref,
    RefNum,
    Rep,
    Scope,
    Seq,
    Sym,
    Xform,
)

SOFT_MAX_DEPTH = 25
HARD_MAX_DEPTH = 400
RECENT_MEMORY = 6
PICK_RETRIES = 8


class GenerationError(RuntimeError):
    """Raised when the grammar cannot be realized (a bug in the grammar)."""


def expand(node: GNode, ctx: GenContext) -> str:
    if isinstance(node, Lit):
        return node.value

    if isinstance(node, NT):
        ctx.depth += 1
        if ctx.depth > HARD_MAX_DEPTH:
            raise GenerationError(f"hard depth limit exceeded at {node.name!r}")
        try:
            target = ctx.grammar.get(node.name)
            if target is None:
                raise GenerationError(f"undefined nonterminal {node.name!r}")
            return expand(target, ctx)
        finally:
            ctx.depth -= 1

    if isinstance(node, Seq):
        return "".join(expand(child, ctx) for child in node.children)

    if isinstance(node, Choice):
        return expand(_choose(node, ctx), ctx)

    if isinstance(node, Opt):
        return expand(node.node, ctx) if ctx.rng.chance(node.p) else ""

    if isinstance(node, Rep):
        return _expand_rep(node, ctx)

    if isinstance(node, Pick):
        text = _pick_bank(ctx, node.bank)
        if node.bound is not None:
            ctx.bind(node.bound, BoundValue(text), "nearest")
        return text

    if isinstance(node, Bind):
        text = expand(node.node, ctx)
        ctx.bind(node.name, BoundValue(text), node.scope)
        return text

    if isinstance(node, Ref):
        found = ctx.lookup(node.name)
        if found is not None:
            return found.text
        if node.fallback is not None:
            return expand(node.fallback, ctx)
        raise GenerationError(f"reference to unbound name {node.name!r}")

    if isinstance(node, Xform):
        return _apply_xform(node.op, expand(node.node, ctx))

    if isinstance(node, Eqn):
        return build_eqn(ctx, node.motif, node.display)

    if isinstance(node, Sym):
        # Symbols appear in prose, so emit them as inline math ("$X$").
        return f"${ctx.symbols.get(node.role, ctx.rng)}$"

    if isinstance(node, RefNum):
        return _refnum(ctx, node)

    if isinstance(node, Cite):
        return _cite(ctx, node)

    raise GenerationError(f"unknown node {node!r}")


def _choose(node: Choice, ctx: GenContext) -> GNode:
    if ctx.depth >= SOFT_MAX_DEPTH and node.terminal is not None:
        return node.options[node.terminal][1]
    return ctx.rng.pick_weighted(node.options)


def _expand_rep(node: Rep, ctx: GenContext) -> str:
    count = ctx.rng.int_in_range(node.lo, node.hi)
    if count <= 0:
        return ""
    parts = [expand(node.node, ctx) for _ in range(count)]
    if count == 1:
        return parts[0]
    return expand(node.sep, ctx).join(parts)


def _pick_bank(ctx: GenContext, bank: str) -> str:
    items = ctx.field.banks.get(bank) or ctx.extra.get(bank)
    if not items:
        raise GenerationError(f"empty or unknown bank {bank!r} in {ctx.field.code}")
    recent = ctx.recent.setdefault(bank, [])
    selected = ctx.rng.choice(items)
    tries = 0
    while selected in recent and tries < PICK_RETRIES and len(items) > len(recent):
        selected = ctx.rng.choice(items)
        tries += 1
    recent.append(selected)
    if len(recent) > RECENT_MEMORY:
        recent.pop(0)
    return selected


def _apply_xform(op: str, text: str) -> str:
    if op == "cap":
        return cap_first(text)
    if op == "lower":
        return lower_first(text)
    if op == "titlecase":
        return titlecase(text)
    if op == "plural":
        return pluralize(text)
    if op == "article":
        return with_article(text)
    if op == "quiet":
        return ""
    raise GenerationError(f"unknown transform {op!r}")


def _refnum(ctx: GenContext, node: RefNum) -> str:
    if node.key is not None and node.key in ctx.refs:
        return ctx.refs[node.key]
    ctx.counters[node.counter] = ctx.counters.get(node.counter, 0) + 1
    label = _format_number(ctx, node.counter, ctx.counters[node.counter])
    if node.counter == "eq":
        label = f"({label})"
    if node.key is not None:
        ctx.refs[node.key] = label
    return label


def _cite(ctx: GenContext, node: Cite) -> str:
    labels = ctx.cite_labels
    if not labels:
        return ""
    k = ctx.rng.int_in_range(node.lo, min(node.hi, len(labels)))
    chosen: list[str] = []
    guard = 0
    while len(chosen) < k and guard < 50:
        candidate = ctx.rng.choice(labels)
        if candidate not in chosen:
            chosen.append(candidate)
        guard += 1
    chosen.sort(key=lambda s: (len(s), s))
    return "[" + ", ".join(chosen) + "]"


def _format_number(ctx: GenContext, counter: str, value: int) -> str:
    if ctx.style.numbering == "section" and counter != "sec":
        return f"{ctx.counters.get('sec', 0)}.{value}"
    return str(value)


def make_context(
    seed: int,
    field: SubfieldLexicon,
    grammar: Grammar,
    style: PaperStyle,
) -> GenContext:
    return GenContext(
        rng=Rng(seed),
        field=field,
        grammar=grammar,
        style=style,
        symbols=SymbolAllocator(field.symbols),
        scopes=[Scope("paper")],
        counters={"thm": 0, "eq": 0, "sec": 0},
        refs={},
    )


def realize(
    grammar: Grammar,
    field: SubfieldLexicon,
    style: PaperStyle,
    seed: int | str,
    start: str = "Paper",
) -> str:
    """Expand ``start`` to a finalized string. Used for tests and examples."""
    ctx = make_context(parse_seed(seed), field, grammar, style)
    return finalize(expand(NT(start), ctx))
