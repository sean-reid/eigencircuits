import { memo } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { fetchAbs, fetchList } from '../api/client';
import { useAsync } from '../api/useAsync';
import { prewarmPdfEngine } from '../pdf/compile';
import { InlineText } from '../render/tex';
import { Pagination } from '../ui/Pagination';
import type { ListEntry } from '../types/api';
import { downloadTex, formatMonth } from '../util/format';

const PER_PAGE = [25, 50, 100, 250];

function Subjects({ entry }: { entry: ListEntry }) {
  return (
    <span className="subjects">
      <span className="subject-primary">
        {entry.primary_name} ({entry.primary})
      </span>
      {entry.crosslist.map((c) => (
        <span key={c.code}>
          ; {c.name} ({c.code})
        </span>
      ))}
    </span>
  );
}

export const EntryRow = memo(function EntryRow({ entry, n }: { entry: ListEntry; n: number }) {
  const onTex = () => {
    void fetchAbs(entry.id).then((r) => downloadTex(entry.id, r.tex));
  };
  return (
    <li className="entry" value={n}>
      <div className="entry-id">
        <span className="entry-num">[{n}]</span>{' '}
        <Link to={`/abs/${entry.id}`} className="arxiv-id">
          eiGen:{entry.id}
        </Link>{' '}
        <span className="formats">
          [
          <Link to={`/pdf/${entry.id}`} onMouseEnter={prewarmPdfEngine} onFocus={prewarmPdfEngine}>
            pdf
          </Link>
          , <Link to={`/html/${entry.id}`}>html</Link>,{' '}
          <button className="linklike" onClick={onTex}>
            tex
          </button>
          ]
        </span>
      </div>
      <div className="entry-title">
        <span className="label">Title:</span> <InlineText text={entry.title} />
      </div>
      <div className="entry-authors">
        <span className="label">Authors:</span> {entry.authors.join(', ')}
      </div>
      {entry.comments && (
        <div className="entry-comments">
          <span className="label">Comments:</span> {entry.comments}
        </div>
      )}
      <div className="entry-subjects">
        <span className="label">Subjects:</span> <Subjects entry={entry} />
      </div>
    </li>
  );
});

export function ListPage() {
  const { cat = '', period = 'recent' } = useParams();
  const [params, setParams] = useSearchParams();
  const skip = Math.max(0, Number(params.get('skip') ?? '0') || 0);
  const show = Math.min(2000, Math.max(1, Number(params.get('show') ?? '50') || 50));
  const { data, error, loading } = useAsync(
    () => fetchList(cat, period, skip, show),
    [cat, period, skip, show],
  );

  if (loading) return <p className="status">Loading…</p>;
  if (error || !data) return <p className="status error">Could not load listing: {error}</p>;

  const setPage = (nextSkip: number, nextShow: number) => {
    setParams({ skip: String(nextSkip), show: String(nextShow) });
  };

  // arXiv lists papers whose primary subject is this category, then a separate
  // "Cross-lists" section for papers primarily in another category. Numbering
  // is continuous across both sections.
  const primaries = data.entries.filter((e) => e.primary === cat);
  const crosses = data.entries.filter((e) => e.primary !== cat);

  const renderEntries = (entries: ListEntry[], startN: number) => (
    <ol className="entries" start={startN}>
      {entries.map((e, i) => (
        <EntryRow key={e.id} entry={e} n={startN + i} />
      ))}
    </ol>
  );

  return (
    <div className="listing">
      <div className="breadcrumb">
        <Link to="/archive/math">math</Link> &gt; {cat}
      </div>
      <h1 className="page-title">{data.name}</h1>
      <h2 className="page-subtitle">
        {period === 'recent'
          ? 'Authors and titles for recent submissions'
          : `Authors and titles for ${formatMonth(period)}`}
      </h2>

      <Pagination total={data.total} skip={skip} show={show} onPage={(s) => setPage(s, show)} />
      <div className="per-page">
        Showing up to {show} entries per page:{' '}
        {PER_PAGE.map((p, i) => (
          <span key={p}>
            {i > 0 && ' | '}
            <button className="linklike" onClick={() => setPage(0, p)}>
              {p}
            </button>
          </span>
        ))}
        {' | '}
        <button className="linklike" onClick={() => setPage(0, 2000)}>
          all
        </button>
      </div>

      {data.entries.length === 0 && <p className="status">No entries in this period.</p>}

      {primaries.length > 0 && renderEntries(primaries, skip + 1)}

      {crosses.length > 0 && (
        <section className="cross-lists">
          <h3 className="day-head">
            Cross-lists ({crosses.length} {crosses.length === 1 ? 'entry' : 'entries'})
          </h3>
          {renderEntries(crosses, skip + 1 + primaries.length)}
        </section>
      )}
    </div>
  );
}
