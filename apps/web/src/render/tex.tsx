import katex from 'katex';
import { Fragment, type ReactNode } from 'react';

function katexHtml(tex: string, displayMode: boolean): string {
  return katex.renderToString(tex, {
    displayMode,
    throwOnError: false,
    output: 'htmlAndMathml',
    strict: false,
  });
}

type Segment = { math: false; value: string } | { math: true; value: string; display: boolean };

/** Split a string into runs of plain text and inline/display math ($...$, $$...$$). */
function splitMath(text: string): Segment[] {
  const out: Segment[] = [];
  let i = 0;
  while (i < text.length) {
    if (text[i] === '$') {
      const display = text.startsWith('$$', i);
      const delim = display ? '$$' : '$';
      const end = text.indexOf(delim, i + delim.length);
      if (end === -1) {
        out.push({ math: false, value: text.slice(i) });
        break;
      }
      out.push({ math: true, value: text.slice(i + delim.length, end), display });
      i = end + delim.length;
    } else {
      const next = text.indexOf('$', i);
      const stop = next === -1 ? text.length : next;
      out.push({ math: false, value: text.slice(i, stop) });
      i = stop;
    }
  }
  return out;
}

const RUN = /\\(emph|textbf)\{([^}]*)\}/g;

/** Render plain prose, honoring `\emph{}`/`\textbf{}` and LaTeX en-dashes. */
function renderProse(text: string, key: string): ReactNode[] {
  const normalized = text.replace(/---/g, '—').replace(/--/g, '–');
  const nodes: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  RUN.lastIndex = 0;
  let n = 0;
  while ((m = RUN.exec(normalized)) !== null) {
    if (m.index > last) nodes.push(normalized.slice(last, m.index));
    const inner = m[2];
    nodes.push(
      m[1] === 'emph' ? <em key={`${key}-${n}`}>{inner}</em> : <strong key={`${key}-${n}`}>{inner}</strong>,
    );
    last = m.index + m[0].length;
    n += 1;
  }
  if (last < normalized.length) nodes.push(normalized.slice(last));
  return nodes;
}

/** Inline prose that may contain math. */
export function InlineText({ text }: { text: string }): ReactNode {
  return splitMath(text).map((seg, idx) =>
    seg.math ? (
      <span
        key={idx}
        className={seg.display ? 'math-display' : 'math-inline'}
        dangerouslySetInnerHTML={{ __html: katexHtml(seg.value, seg.display) }}
      />
    ) : (
      <Fragment key={idx}>{renderProse(seg.value, `t${idx}`)}</Fragment>
    ),
  );
}

/** A standalone displayed equation (bare LaTeX, no delimiters). */
export function DisplayMath({ tex }: { tex: string }): ReactNode {
  return <span dangerouslySetInnerHTML={{ __html: katexHtml(tex, true) }} />;
}
