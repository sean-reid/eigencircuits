import { useSearchParams } from 'react-router-dom';
import { fetchSearch } from '../api/client';
import { useAsync } from '../api/useAsync';
import { EntryRow } from './ListPage';

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get('q') ?? '';
  const cat = params.get('cat') ?? '';
  const skip = Math.max(0, Number(params.get('skip') ?? '0') || 0);
  const show = Math.min(500, Math.max(1, Number(params.get('show') ?? '50') || 50));

  const { data, error, loading } = useAsync(
    () => fetchSearch(query, cat, skip, show),
    [query, cat, skip, show],
  );

  if (!query.trim()) {
    return <p className="status">Enter a query to search titles, authors, and abstracts.</p>;
  }
  if (loading) return <p className="status">Searching…</p>;
  if (error || !data) return <p className="status error">Search failed: {error}</p>;

  const setPage = (nextSkip: number) => {
    const next = new URLSearchParams(params);
    next.set('skip', String(nextSkip));
    setParams(next);
  };

  const ranges: { from: number; to: number }[] = [];
  for (let start = 0; start < data.total; start += show) {
    ranges.push({ from: start, to: Math.min(start + show, data.total) });
  }

  return (
    <div className="listing">
      <h1 className="page-title">Search</h1>
      <h2 className="page-subtitle">
        {data.total} result{data.total === 1 ? '' : 's'} for &ldquo;{query}&rdquo;
      </h2>

      {data.total > show && (
        <div className="pagination">
          <span>Total of {data.total} entries</span>
          {' : '}
          {ranges.map((r) =>
            r.from === skip ? (
              <span key={r.from} className="range current">
                {r.from + 1}-{r.to}
              </span>
            ) : (
              <button key={r.from} className="range linklike" onClick={() => setPage(r.from)}>
                [{r.from + 1}-{r.to}]
              </button>
            ),
          )}
        </div>
      )}

      {data.entries.length === 0 ? (
        <p className="status">No papers matched.</p>
      ) : (
        <ol className="entries" start={skip + 1}>
          {data.entries.map((e, i) => (
            <EntryRow key={e.id} entry={e} n={skip + i + 1} />
          ))}
        </ol>
      )}
    </div>
  );
}
