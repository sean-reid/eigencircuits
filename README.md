# eigencircuits

Procedurally generated arXiv-style mathematics papers.

Click generate and you get a complete, typeset paper: a title, authors and
affiliations, an abstract, subject classes, a body of definitions, lemmas,
theorems, proofs and displayed equations, acknowledgments, and references. Every
paper locks to a single (secretly chosen) mathematical subfield, so the
vocabulary, notation, and named results stay internally consistent from the
title through the last proof.

The papers are well-formed and stylistically faithful. They are also
meaningless by design. The point is the imitation of form, not mathematical
truth. It is a descendant of SciGen (2005), retargeted to mathematics with a
much more capable grammar.

## How it works

A seeded, context-sensitive grammar engine drives everything. Unlike a plain
context-free grammar, it binds the paper's central objects once and reuses them
everywhere, weights productions to match the frequencies you see on the real
arXiv, and carries the document skeleton in the grammar itself. A given seed
always reproduces the same paper, which makes results shareable and tests
deterministic.

See [PLAN.md](PLAN.md) for the full design.

## Layout

```
packages/engine   Python grammar engine (the core)
apps/worker        Cloudflare Worker exposing the generator
apps/web           Vite + React frontend with KaTeX preview and PDF export
```

## Development

The engine is Python, managed with [uv](https://docs.astral.sh/uv/). The web app
and worker are TypeScript, managed with [pnpm](https://pnpm.io/).

```bash
# engine
uv --project packages/engine run pytest
uv --project packages/engine run ruff check .

# workspace
pnpm install
pnpm dev          # run the web app
pnpm test         # run JS/TS tests
pnpm lint
```

## License

MIT. See [LICENSE](LICENSE).
