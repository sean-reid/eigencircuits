import { Link } from 'react-router-dom';
import { fetchArchive } from '../api/client';
import { useAsync } from '../api/useAsync';

export function ArchivePage() {
  const { data, error, loading } = useAsync(fetchArchive, []);

  if (loading) return <p className="status">Loading…</p>;
  if (error || !data) return <p className="status error">Could not load archive: {error}</p>;

  return (
    <div className="archive">
      <h1 className="page-title">
        Mathematics <span className="since">(since February 1992)</span>
      </h1>
      <p className="intro">
        For a specific paper, enter the identifier into the top right search box.
      </p>
      <p className="archive-total">
        Total of {data.total.toLocaleString()} entries in the last 90 days.
      </p>
      <ul className="subject-list">
        {data.subjects.map((s) => (
          <li key={s.code}>
            <span className="subject-code">{s.code}</span>
            <span className="subject-name"> — {s.name}</span>{' '}
            <span className="cat-links">
              [<Link to={`/list/${s.code}/recent`}>recent</Link>]
            </span>
            <span className="subject-count">{s.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
