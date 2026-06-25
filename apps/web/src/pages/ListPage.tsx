import { Link, useParams, useSearchParams } from 'react-router-dom';
import { fetchAbs, fetchList } from '../api/client';
import { useAsync } from '../api/useAsync';
import { InlineText } from '../render/tex';
import type { ListEntry } from '../types/api';
import { downloadTex, formatDate, formatMonth } from '../util/format';

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

export function EntryRow({ entry, n }: { entry: ListEntry; n: number }) {
  const onTex = () => {
    void fetchAbs(entry.id).then((r) => downloadTex(entry.id, r.tex));
  };
  return (
    <li className="entry" value={n}>
      <div className="entry-id">
        <span className="entry-num">[{n}]</span>{' '}
        <Link to={`/abs/${entry.id}`} className="arxiv-id">
          arXiv:{entry.id}
        </Link>{' '}
        <span className="formats">
          [<Link to={`/html/${entry.id}`}>pdf</Link>,{' '}
          <button className="linklike" onClick={onTex}>
            tex
          </button>
          , <Link to={`/abs/${entry.id}`}>other</Link>]
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
}

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

  // Continuous [n] numbering over the page; group by day for the recent view.
  const groups: { date: string; entries: ListEntry[] }[] = [];
  for (const e of data.entries) {
    const last = groups[groups.length - 1];
    if (period === 'recent' && last && last.date === e.date) last.entries.push(e);
    else if (period === 'recent') groups.push({ date: e.date, entries: [e] });
    else if (last) last.entries.push(e);
    else groups.push({ date: e.date, entries: [e] });
  }

  const ranges: { from: number; to: number }[] = [];
  for (let start = 0; start < data.total; start += show) {
    ranges.push({ from: start, to: Math.min(start + show, data.total) });
  }

  let counter = skip;

  return (
    <div className="listing">
      <h1 className="page-title">{data.name}</h1>
      <h2 className="page-subtitle">
        {period === 'recent'
          ? 'Authors and titles for recent submissions'
          : `Authors and titles for ${formatMonth(period)}`}
      </h2>

      <div className="pagination">
        <span>Total of {data.total} entries</span>
        {ranges.length > 0 && ' : '}
        {ranges.map((r) =>
          r.from === skip ? (
            <span key={r.from} className="range current">
              {r.from + 1}-{r.to}
            </span>
          ) : (
            <button key={r.from} className="range linklike" onClick={() => setPage(r.from, show)}>
              [{r.from + 1}-{r.to}]
            </button>
          ),
        )}
      </div>
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

      {groups.map((g) => {
        const start = counter;
        counter += g.entries.length;
        return (
          <section key={g.date} className="day-group">
            {period === 'recent' && (
              <h3 className="day-head">
                {formatDate(g.date)} (showing {g.entries.length} of {g.entries.length} entries)
              </h3>
            )}
            <ol className="entries" start={start + 1}>
              {g.entries.map((e, i) => (
                <EntryRow key={e.id} entry={e} n={start + i + 1} />
              ))}
            </ol>
          </section>
        );
      })}
    </div>
  );
}
