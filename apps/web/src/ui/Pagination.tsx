import type { ReactNode } from 'react';

interface Props {
  total: number;
  skip: number;
  show: number;
  onPage: (skip: number) => void;
}

/**
 * Windowed page links in arXiv's "[from-to]" style. Shows the first, last, and
 * current ± 1 pages with ellipses between, so a listing of thousands does not
 * render hundreds of buttons.
 */
export function Pagination({ total, skip, show, onPage }: Props) {
  const pageCount = Math.ceil(total / show);
  const current = Math.floor(skip / show);

  const wanted = new Set<number>();
  for (const p of [0, 1, current - 1, current, current + 1, pageCount - 2, pageCount - 1]) {
    if (p >= 0 && p < pageCount) wanted.add(p);
  }
  const pages = [...wanted].sort((a, b) => a - b);

  const items: ReactNode[] = [];
  let prev = -1;
  for (const p of pages) {
    if (p - prev > 1) items.push(<span key={`gap-${p}`}>…</span>);
    const from = p * show;
    const to = Math.min(from + show, total);
    items.push(
      p === current ? (
        <span key={p} className="range current">
          {from + 1}-{to}
        </span>
      ) : (
        <button key={p} className="range linklike" onClick={() => onPage(from)}>
          [{from + 1}-{to}]
        </button>
      ),
    );
    prev = p;
  }

  return (
    <div className="pagination">
      <span>Total of {total} entries</span>
      {pageCount > 1 && <> : {items}</>}
    </div>
  );
}
