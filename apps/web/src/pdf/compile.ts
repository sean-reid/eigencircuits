/**
 * Browser-side LaTeX -> PDF compilation, backed by a single shared pdfTeX
 * engine. The engine is loaded lazily on first use and reused across pages;
 * compiles are serialized because the worker handles one job at a time.
 */
import { PdfTeXEngine, type CompileResult } from './PdfTeXEngine';

/**
 * Where the engine fetches its format file and TeX packages. We self-host a
 * harvested subset on our own origin (served by the API under `/texlive/`),
 * so there is no third-party runtime dependency. A global override lets the
 * harvest tooling point the engine at a local TeX Live mirror.
 */
const TEXLIVE_ENDPOINT: string =
  (globalThis as { __TEXLIVE_ENDPOINT__?: string }).__TEXLIVE_ENDPOINT__ ??
  `${(import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'}/texlive/`;

let engine: PdfTeXEngine | undefined;
let loading: Promise<PdfTeXEngine> | undefined;
let queue: Promise<unknown> = Promise.resolve();

async function getEngine(): Promise<PdfTeXEngine> {
  if (engine) return engine;
  if (!loading) {
    loading = (async () => {
      const e = new PdfTeXEngine();
      await e.loadEngine();
      e.setTexliveEndpoint(TEXLIVE_ENDPOINT);
      engine = e;
      return e;
    })().catch((err) => {
      loading = undefined;
      throw err;
    });
  }
  return loading;
}

/** Run `fn` after any in-flight compile completes, so jobs never overlap. */
function enqueue<T>(fn: () => Promise<T>): Promise<T> {
  const run = queue.then(fn, fn);
  // Keep the chain alive even if a job rejects.
  queue = run.then(
    () => undefined,
    () => undefined,
  );
  return run;
}

/**
 * Compile a full LaTeX document to a PDF. Resolves with the pdfTeX status, log,
 * and (on success) the PDF bytes. A single pass is sufficient: generated papers
 * carry no `\ref`/`\cite`, so there are no cross-references to resolve.
 */
export function compilePdf(tex: string): Promise<CompileResult> {
  return enqueue(async () => {
    const e = await getEngine();
    e.writeMemFSFile('main.tex', tex);
    e.setEngineMainFile('main.tex');
    return e.compileLaTeX();
  });
}

// A minimal document exercising every package in the real preamble, so warming
// it pre-fetches the engine, the format file, and the shared package/font set.
const WARM_TEX = String.raw`\documentclass[11pt]{amsart}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{stmaryrd}
\begin{document}
\(\llbracket x \rrbracket \in \mathbb{Z}\)
\end{document}`;

let prewarmed = false;

/**
 * Load the engine and warm the shared package cache in the background, so the
 * first real "View PDF" is fast. Best-effort and idempotent: failures are
 * swallowed (the PDF page surfaces real errors on demand).
 */
export function prewarmPdfEngine(): void {
  if (prewarmed) return;
  prewarmed = true;
  const start = () => {
    enqueue(async () => {
      const e = await getEngine();
      e.writeMemFSFile('warm.tex', WARM_TEX);
      e.setEngineMainFile('warm.tex');
      return e.compileLaTeX();
    }).catch(() => undefined);
  };
  if (typeof requestIdleCallback === 'function') requestIdleCallback(start, { timeout: 4000 });
  else setTimeout(start, 1500);
}
