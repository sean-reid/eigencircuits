import { Link, useParams } from 'react-router-dom';
import { fetchAbs } from '../api/client';
import { useAsync } from '../api/useAsync';
import { Paper } from '../render/Paper';
import { downloadTex } from '../util/format';

export function HtmlPage() {
  const { id = '' } = useParams();
  const { data, error, loading } = useAsync(() => fetchAbs(id), [id]);

  if (loading) return <p className="status">Loading…</p>;
  if (error || !data) {
    return (
      <p className="status error">
        Article not found. <Link to="/">Return to the archive.</Link>
      </p>
    );
  }

  return (
    <div className="htmlview">
      <div className="htmlbar">
        <Link to={`/abs/${data.id}`}>← Back to abstract (arXiv:{data.id})</Link>
        <button className="linklike" onClick={() => downloadTex(data.id, data.tex)}>
          Download .tex
        </button>
      </div>
      <Paper model={data.model} />
    </div>
  );
}
