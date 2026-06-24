# eigencircuits - build & design plan

A modern, mathematics-tailored SciGen, delivered as a paper-generating website.
This plan folds together two inputs:

1. `MATHGEN_SPEC.md` (v1.0) - the engine design, structural anatomy, and per-field lexicon seeds. (The product name there, "MathGen", is superseded: this project is **eigencircuits**.)
2. `research/01..04-*.md` - a fresh four-cluster sweep of recent arXiv math (all 32 categories) producing broader, current vocabulary and many more title/abstract frames to expand each bank.

Where the spec and the session decisions disagreed on stack, the session decisions win and are recorded below.

---

## 1. What this is

SciGen (Stribling, Krohn, Aguayo, 2005) generated grammatically correct but meaningless CS papers from a hand-written CFG. eigencircuits is a mathematics-tailored reimagining: a website where a click produces a complete, typeset arXiv-style math paper - title, authors and affiliations, abstract, MSC classes, multi-section body with definitions / lemmas / theorems / proofs / displayed equations / remarks / examples, acknowledgments, and references - all internally coherent to one secretly chosen subfield.

The output should read as syntactically and stylistically indistinguishable from a real arXiv paper to a non-expert, and amusingly hollow to an expert. It does not state true theorems. The craft is in perfect imitation of form.

**What lifts it above a plain CFG** (all from the spec, Part II): subfield typing, variable binding & capture, weighted productions, structural macros, and seeded determinism. Binding is the core coherence mechanism: the paper's central object ("a smooth projective variety $X$") is chosen once and reused verbatim in title, abstract, theorems, and proofs.

---

## 2. Locked decisions

| Decision          | Value                                                                                                                 | Source                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Product name      | **eigencircuits**                                                                                                     | this session (overrides "MathGen") |
| Engine language   | **Python** (port of spec Part II)                                                                                     | session answer                     |
| Hosting           | **Cloudflare Python Worker** exposing `generate(seed)`                                                                | session answer                     |
| Frontend          | **Vite + React + TypeScript** SPA                                                                                     | spec §5.1 + session ("modern FE")  |
| On-page render    | **KaTeX** preview (instant, offline)                                                                                  | spec §2 + session                  |
| PDF export        | **Client-side WASM LaTeX → PDF** (SwiftLaTeX) from engine `.tex`; plus `.tex` download                                | session answer                     |
| Subfield handling | Coherent, auto-random; "reveal subfield" affordance; no manual picker for v1                                          | spec §2                            |
| Output realism    | Well-formed, plausible, meaningless by design                                                                         | spec §2                            |
| Reproducibility   | Seeded PRNG; seed shown and shareable via URL                                                                         | spec §2, §4.7                      |
| Repo hygiene      | No AI fingerprints: no `CLAUDE.md`/`.claude/` committed, no co-authorship trailers, no em-dashes in copy/code/commits | standing preference                |
| Git identity      | Personal (Sean Reid), remote via `github-personal` host                                                               | standing preference                |

### 2.1 The one architectural shift from the spec

The spec was "pure client-side, no backend, zero runtime cost." We are adding a Python Worker because Python is the chosen engine language and the requested home for the core logic. Consequences, all manageable:

- The grammar engine is pure, dependency-light Python, so Pyodide on Workers stays small. Cold-start latency is the main risk (see §10).
- The engine still emits a structured `PaperModel` (JSON), not a string. The Worker returns `PaperModel` + a compilable `.tex`. The FE renders the model with KaTeX and compiles the `.tex` to PDF in-browser on demand.
- The spec's KaTeX-validity unit test (which assumed a JS engine) moves to a small Node test harness in the web app that validates a corpus of engine-emitted equations against `katex.renderToString({throwOnError:true})` in CI. See §8.

Determinism, binding, scopes, and the `PaperModel` contract are unchanged in spirit; only the host language changes.

---

## 3. Architecture

A clean monorepo (pnpm workspaces + a Python package), production-grade from the start.

```
eigencircuits/
  README.md
  PLAN.md
  research/                      # the four-cluster dossier (source for lexicon expansion)
  packages/
    engine/                      # the Python grammar engine (the core IP)
      pyproject.toml
      eigencircuits_engine/
        __init__.py
        types.py                 # GNode, GenContext, BoundValue, PaperModel, PaperStyle, EqnMotif
        rng.py                   # seeded PRNG (mulberry32-equivalent) + pick_weighted, int_in_range
        builder.py               # lit, nt, seq, choice, opt, rep, pick, bind, ref, xform, eqn, sym
        interpreter.py           # expand(node, ctx) -> str; depth control; scope stack; the only RNG consumer
        symbols.py               # SymbolAllocator (non-colliding math symbols per role)
        theme.py                 # init_theme(ctx): subfield draw, central objects, style, authors, MSC
        equations.py             # build_eqn(ctx, motif, display) -> KaTeX/LaTeX string
        postprocess.py           # spacing, a/an, sentence caps, $ balance, irregular plurals, en-dashes
        generate.py              # generate(seed?) -> PaperModel
        grammar/                 # the authored grammar (data + thin builders)
          structure.py           # Paper, Section, Intro move sequence, environments, Proof
          titles.py abstracts.py theorems.py proofs.py references.py closing.py
          __init__.py            # assembles the grammar map
        lexicon/
          schema.py              # SubfieldLexicon, BankName
          global_bank.py         # cross-field nouns/adjs/verbs, names, journals, agencies (spec §3.2-3.4)
          fields/                # one module per subfield -> SubfieldLexicon
            nt.py ag.py co.py dg.py pr.py ap.py rt.py fa.py ds.py ca.py gt.py at.py
            oa.py qa.py sg.py ac.py ra.py kt.py ct.py lo.py mg.py sp.py na.py oc.py
            st.py mp.py gr.py cv.py gn.py it.py ho.py gm.py
            registry.py          # code -> SubfieldLexicon, with selection weights
      tests/                     # pytest: determinism, coherence, well-formedness, termination
    latex/                       # shared LaTeX preamble/templates used by toLatex (kept language-neutral)
  apps/
    worker/                      # Cloudflare Python Worker
      wrangler.toml
      src/entry.py               # GET /generate?seed= -> { model, tex }; GET /health
      tests/
    web/                         # Vite + React + TS SPA
      index.html
      src/
        main.tsx App.tsx
        state/store.ts           # Zustand
        api/client.ts            # calls Worker /generate
        render/                  # Paper.tsx, Math.tsx (KaTeX), Section.tsx, TheoremBlock.tsx, References.tsx
        pdf/                     # SwiftLaTeX WASM integration: compile .tex -> PDF
        ui/                      # Toolbar.tsx, SubfieldReveal.tsx
        export/                  # download .tex, .html, permalink
        styles/                  # paper.css (LaTeX article look), app.css
        types/paperModel.ts      # TS mirror of the engine PaperModel contract
      tests/                     # vitest (rendering) + katex-validity harness
      tests-e2e/                 # Playwright user-story tests
```

The `PaperModel` JSON is the contract between engine, Worker, and FE. The TS type in `web/src/types/paperModel.ts` mirrors the Python dataclasses in `engine/types.py`; a generated JSON Schema keeps them in sync (checked in CI).

---

## 4. The engine (port of spec Part II)

### 4.1 GNode algebra (Python dataclasses)

Same algebra as spec §4.2, expressed as a tagged union of frozen dataclasses: `Lit, NT, Seq, Choice, Opt, Rep, Pick, Bind, Ref, Xform, Eqn, Sym, RefNum`. A thin builder API (`builder.py`) keeps authored grammar readable: `lit`, `nt`, `seq(*nodes)`, `choice([(w, node), ...])`, `opt(p, node)`, `rep(min, max, sep, node)`, `pick(bank)`, `pick_bound(name, bank)`, `bind(name, node, scope=...)`, `ref(name)`, `cap`, `article`, `plural`, `eqn(motif, display=...)`, `sym(role)`.

### 4.2 Context & binding (the coherence mechanism, spec §4.3)

`GenContext` threads: the seeded `rng`; the locked `field` lexicon; a stack of `scopes` (paper at the bottom); a `SymbolAllocator`; counters (`thm`, `eq`, `sec`); a `refs` map (crossref key -> rendered number); and an immutable `PaperStyle`.

- `bind(name, node, scope)` evaluates `node` once, stores the `BoundValue`, returns its text.
- `ref(name)` walks the scope stack and returns the stored text verbatim, so the same phrase reappears.
- `sym(role)` returns the allocated math symbol for a bound object, allocating on first use so prose and equations agree and symbols never collide.
- Scope lifetimes: `paper` holds the 1-2 central objects, method, related named result, and symbol assignments; `section`/`local` hold transient proof objects so they do not leak.

### 4.3 Theme initializer (spec §4.4)

`init_theme(ctx)` runs before any text: weighted subfield draw -> load lexicon; bind central objects (+symbols) and 1-3 props; bind a method and a related named result; fix `PaperStyle` (numbering, citation style, capitalization, length class); generate authors, affiliations, MSC codes, keywords; init counters. A ~10% cross-listing allowance lets `pick` occasionally borrow from one adjacent field.

### 4.4 Structural macros (spec §4.5)

`Paper` is a `seq` of macros gated by `PaperStyle.lengthClass`: TitleBlock, AuthorBlock, Abstract, MSCBlock, optional Contents, Introduction (an ordered, mostly-optional move sequence: context -> prior work -> gap -> this paper -> main result env -> corollary -> proof strategy -> outline), optional Preliminaries, 1-K CoreSections (definition, 1-3 theorem-likes each with a proof, remark, example, displayed eqn), optional final remarks, optional acknowledgments and funding, References, optional appendix, author addresses.

### 4.5 Equation sub-grammar (spec §4.9)

`build_eqn(ctx, motif, display)` builds a KaTeX/LaTeX string from the locked field's symbol bank and signature `eqn_motif`, substituting bound symbols where roles match. Prefer the field's signature formula ~40% of the time; otherwise a generic motif specialized with field symbols. Stay inside a known KaTeX-safe palette (see §8 and spec Appendix B gotchas).

### 4.6 Determinism (spec §4.7)

A small seedable PRNG (mulberry32-equivalent in Python), never the stdlib global RNG. Seed is shown in the UI and encoded in the URL (`?seed=`). Same seed + same `GRAMMAR_VERSION` yields a byte-identical paper. Bump `GRAMMAR_VERSION` when rules change.

### 4.7 Recursion & shaping (spec §4.6)

Depth counter with `MAX_DEPTH` (~25) and per-rule caps; on overflow, `choice` collapses to a marked terminal option. Anti-repetition LRU per bank. A light post-pass fixes spacing, sentence caps, a/an, double spaces, and `$...$` balance.

---

## 5. Lexicon: merging spec seeds with the research dossier

Each subfield module returns a `SubfieldLexicon` (spec §5.3 schema): banks for `objects`, `props`, `spaces`, `maps`, `invariants`, `namedResults`, `methods`, `objectGloss`; a `symbols` list; a signature `eqn_motif(SymRoles) -> str`; and `adjacent` codes for cross-listing.

Build procedure per field:

1. Start from the spec §3.11 seed (~8-15 items per bank) - the source of truth for the signature equation motif and core symbols.
2. Expand each bank to ~25-40 items using the matching cluster file in `research/`:
   - `01-algebra-number-theory.md` -> NT, AG, RT, RA, AC, QA, KT, GR
   - `02-analysis.md` -> AP, CA, FA, CV, SP, OA, MP, DS
   - `03-geometry-topology.md` -> DG, GT, AT, SG, MG, GN, CT
   - `04-discrete-probability-applied.md` -> CO, PR, ST, OC, NA, IT, LO
3. Pull title frames and abstract sentence templates from both the spec (§3.5, §3.6) and the research files (each cluster contributed 15-25 title patterns and 10-15 abstract patterns) into the shared grammar, tagged by field where field-specific.
4. Keep lexicon modules data-only (no logic) so non-programmers can extend them later (spec Appendix B).

Selection weights follow spec §3.1 (large active fields high; GM and HO near-zero with special expository templates). Global cross-field banks, the ~150 surname bank, eponym machinery, journals, and funding agencies come from spec §3.2-3.4 and §3.10.

---

## 6. Rendering and export

The engine emits `PaperModel` (typed tree). Presentation is separate.

- **KaTeX preview** (`render/Math.tsx`): `katex.renderToString(tex, { displayMode, throwOnError:false, output:'htmlAndMathml' })`. `paper.css` evokes a LaTeX `article`: Latin Modern / STIX serif, justified text, centered bold title, run-in bold theorem headers with italic statements, flush-right numbered equations, ruled References with hanging indent. Mobile-responsive (max-width column, fluid on small screens) per standing preference.
- **PDF** (`pdf/`): SwiftLaTeX WASM compiles the engine's `.tex` to a real PDF in-browser, on demand (lazy-loaded so it does not bloat first paint). This is the authentic arXiv-look output.
- **`.tex` download**: `\documentclass{article}` with `amsmath, amsthm, amssymb`, `\newtheorem` declarations, title/author/abstract, sections, environments, equations, and `thebibliography`. Compiles under pdfLaTeX. Produced by the engine (`toLatex`) so the Worker can return it directly.
- **`.html` download** and **permalink** (`?seed=`).

---

## 7. Worker API contract

- `GET /generate?seed=<base36>` -> `{ model: PaperModel, tex: string }`. Omitting `seed` generates a fresh random seed and returns it inside `model.seed`.
- `GET /health` -> `{ ok: true, grammarVersion }`.
- CORS locked to the web app origin. Response cached by seed (immutable given `GRAMMAR_VERSION`).

The FE can also keep a thin client-side fallback path (call the Worker; if offline, show a friendly state). Generation is fast and deterministic, so caching by `seed` is trivial.

---

## 8. Testing and CI

Comprehensive pipeline (standing preference): lint, types, unit, e2e, build, visual regression, perf, security.

Engine (pytest, `packages/engine/tests`):

- **Determinism**: `generate(seed)` twice yields identical `PaperModel`.
- **Coherence**: the `mainObject` phrase and its symbol appear in title or abstract and in >=1 theorem; the locked field's banks supply >=90% of content words (instrument `pick`).
- **Well-formedness**: balanced `$...$`/`$$...$$`; no empty nonterminal; no literal `None`/`nan`/`undefined`; no doubled punctuation; correct a/an.
- **Termination**: halts within `MAX_DEPTH` for 10^4 random seeds.

KaTeX validity (Node harness in `apps/web`, runs in CI): generate a corpus of equations from the engine (via the Worker or a fixture dump) and assert each parses under `katex.renderToString({throwOnError:true})`. This replaces the spec's in-engine KaTeX test now that the engine is Python.

Web:

- **vitest**: rendering components from fixed `PaperModel` fixtures.
- **Playwright e2e** (`tests-e2e`, mapped to user stories, shipped with features): generate a paper; reseed via URL and confirm reproducibility; reveal subfield; download `.tex`; compile PDF; toggle typography and dark mode; mobile viewport (375/768/1024). Capture and visually review screenshots of every state (standing preference).

`.tex` acceptance: a CI job compiles a sample export under pdfLaTeX (texlive in CI) to prove authenticity.

Definition of done: `dev` and `build` succeed; all suites pass; 20 random papers are coherent, varied, KaTeX-valid, spanning multiple subfields; any paper's `.tex` compiles under pdfLaTeX.

---

## 9. Milestones (atomic commits; push at milestone boundaries)

1. **M0 - Repo & CI scaffold.** Monorepo, git identity, lint/format/type configs, empty CI green. Move `research/` under `docs/` if preferred. (no app behavior yet)
2. **M1 - Engine core.** `types/rng/builder/interpreter/symbols`; determinism, well-formedness, termination tests green.
3. **M2 - Theme + math.NT end-to-end.** `init_theme`, NT lexicon (seed + research expansion), titles/abstracts/theorems/proofs grammar, `toLatex`; coherence test green; a believable NT `PaperModel`.
4. **M3 - Worker + web render.** Python Worker `/generate`; React paper view with KaTeX; toolbar, seed/URL, reveal; KaTeX-validity harness green; first Playwright story.
5. **M4 - PDF + export.** SwiftLaTeX WASM PDF; `.tex`/`.html` download; permalink; pdfLaTeX CI compile.
6. **M5 - All 32 fields.** Fill `lexicon/fields/*` (seed + research), weighted draw, cross-listing.
7. **M6 - Polish & audit.** Paper CSS fidelity, anti-repetition and frequency tuning vs real arXiv feel, mobile pass, accessibility, full multi-agent audit (UX/code/perf/security) per standing preference.

Stretch (spec §5.9): dev "lock to subfield" picker, length slider, TikZ-CD / SVG commutative-diagram generator, referee-report generator, BibTeX export, seed gallery, daily-paper permalink.

---

## 10. Open risks and decisions

- **Pyodide cold start on Workers.** The engine is small and pure-Python, which helps, but first-request latency needs measurement. Mitigations: keep dependencies at zero, cache responses by seed, consider Worker warming, or fall back to a tiny compiled path if latency is unacceptable. Decide after M3 with real numbers.
- **Python/TS contract drift.** Mitigated by generating a JSON Schema from the engine `PaperModel` and validating the TS type against it in CI.
- **SwiftLaTeX bundle size.** Lazy-load the WASM compiler so it never affects first paint; KaTeX covers the instant preview.
- **Equation safety.** Constrain motifs to a KaTeX-safe macro palette; the CI KaTeX harness is the gate (spec Appendix B lists the unsupported-macro traps).

---

## 11. Provenance

Engine design, structural anatomy, and per-field seed lexicons: `MATHGEN_SPEC.md` v1.0 (Parts I-III). Vocabulary expansion, title/abstract frame banks, and current-trend terminology: the four-cluster arXiv sweep in `research/`. Stack reconciliation (Python engine + Cloudflare Worker + React FE + KaTeX preview + WASM PDF) and the eigencircuits name: this session.
