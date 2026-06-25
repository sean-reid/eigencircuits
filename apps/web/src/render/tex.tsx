import katex from 'katex';
import { Fragment, type ReactNode } from 'react';

const _katexCache = new Map<string, string>();

function katexHtml(tex: string, displayMode: boolean): string {
  const key = `${displayMode ? 'D' : 'I'}|${tex}`;
  let html = _katexCache.get(key);
  if (html === undefined) {
    html = katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      output: 'htmlAndMathml',
      strict: false,
    });
    _katexCache.set(key, html);
  }
  return html;
}

type Token =
  | { type: 'text'; value: string }
  | { type: 'math'; value: string; display: boolean }
  | { type: 'emph' | 'bold'; value: string };

const MACROS: { name: string; type: 'emph' | 'bold' }[] = [
  { name: '\\emph{', type: 'emph' },
  { name: '\\textbf{', type: 'bold' },
];

/**
 * Read a balanced `{...}` body starting just after the opening brace at `start`.
 * `$...$` spans are treated as opaque so braces inside math (e.g. `\mathcal{C}`)
 * do not affect nesting. Returns the inner text and the index past the close.
 */
function readBraces(text: string, start: number): { inner: string; end: number } {
  let depth = 1;
  let inMath = false;
  let i = start;
  for (; i < text.length; i++) {
    const c = text.charAt(i);
    if (c === '$') inMath = !inMath;
    else if (!inMath && c === '{') depth++;
    else if (!inMath && c === '}') {
      depth--;
      if (depth === 0) break;
    }
  }
  return { inner: text.slice(start, i), end: i + 1 };
}

/**
 * Split prose into text / math / emphasis tokens. Macros are matched before
 * math so `\emph{...}` whose body contains `$...$` stays intact; the body is
 * tokenized recursively at render time.
 */
function tokenize(text: string): Token[] {
  const out: Token[] = [];
  let buf = '';
  const flush = () => {
    if (buf) out.push({ type: 'text', value: buf });
    buf = '';
  };
  let i = 0;
  while (i < text.length) {
    const c = text.charAt(i);
    if (c === '$') {
      const display = text.startsWith('$$', i);
      const delim = display ? '$$' : '$';
      const end = text.indexOf(delim, i + delim.length);
      if (end === -1) {
        buf += text.slice(i);
        break;
      }
      flush();
      out.push({ type: 'math', value: text.slice(i + delim.length, end), display });
      i = end + delim.length;
      continue;
    }
    const macro = c === '\\' ? MACROS.find((m) => text.startsWith(m.name, i)) : undefined;
    if (macro) {
      const { inner, end } = readBraces(text, i + macro.name.length);
      flush();
      out.push({ type: macro.type, value: inner });
      i = end;
      continue;
    }
    buf += c;
    i++;
  }
  flush();
  return out;
}

/** Turn LaTeX dashes into typographic en/em dashes. */
function dashes(text: string): string {
  return text.replace(/---/g, '—').replace(/--/g, '–');
}

function render(text: string, key: string): ReactNode[] {
  return tokenize(text).map((tok, idx) => {
    const k = `${key}-${idx}`;
    switch (tok.type) {
      case 'text':
        return <Fragment key={k}>{dashes(tok.value)}</Fragment>;
      case 'math':
        return (
          <span
            key={k}
            className={tok.display ? 'math-display' : 'math-inline'}
            dangerouslySetInnerHTML={{ __html: katexHtml(tok.value, tok.display) }}
          />
        );
      case 'emph':
        return <em key={k}>{render(tok.value, k)}</em>;
      case 'bold':
        return <strong key={k}>{render(tok.value, k)}</strong>;
    }
  });
}

/** Inline prose that may contain math and `\emph{}`/`\textbf{}` markup. */
export function InlineText({ text }: { text: string }): ReactNode {
  return <>{render(text, 't')}</>;
}

/** A standalone displayed equation (bare LaTeX, no delimiters). */
export function DisplayMath({ tex }: { tex: string }): ReactNode {
  return <span dangerouslySetInnerHTML={{ __html: katexHtml(tex, true) }} />;
}
