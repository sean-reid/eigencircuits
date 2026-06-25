import { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { fetchAbs } from '../api/client';
import { useAsync } from '../api/useAsync';
import { prewarmPdfEngine } from '../pdf/compile';
import { InlineText } from '../render/tex';
import { downloadTex, formatDateTime } from '../util/format';

export function AbsPage() {
  const { id = '' } = useParams();
  const { data, error, loading } = useAsync(() => fetchAbs(id), [id]);

  // The PDF compiler lives one click away; warm it while the reader is here.
  useEffect(() => {
    prewarmPdfEngine();
  }, []);

  if (loading) return <p className="status">Loading…</p>;
  if (error || !data) {
    return (
      <p className="status error">
        Article not found. <Link to="/">Return to the archive.</Link>
      </p>
    );
  }

  const month = data.date.slice(0, 7);
  const msc = [data.msc_primary, ...data.msc_secondary].join(', ');

  return (
    <div className="abs">
      <div className="abs-main">
        <div className="breadcrumb">
          <Link to="/archive/math">math</Link> &gt;{' '}
          <Link to={`/list/${data.primary}/recent`}>{data.primary}</Link> &gt; eiGen:{data.id}
        </div>
        <h1 className="abs-title">
          <InlineText text={data.model.title} />
        </h1>
        <div className="abs-authors">{data.model.authors.map((a) => a.name).join(', ')}</div>

        <div className="abs-block">
          <span className="label">Abstract:</span> <InlineText text={data.model.abstract} />
        </div>

        <table className="metatable">
          <tbody>
            {data.comments && (
              <tr>
                <td className="label">Comments:</td>
                <td>{data.comments}</td>
              </tr>
            )}
            <tr>
              <td className="label">Subjects:</td>
              <td>
                <span className="subject-primary">
                  {data.primary_name} ({data.primary})
                </span>
                {data.crosslist.map((c) => (
                  <span key={c.code}>
                    ; {c.name} ({c.code})
                  </span>
                ))}
              </td>
            </tr>
            {msc && (
              <tr>
                <td className="label">MSC classes:</td>
                <td>{msc}</td>
              </tr>
            )}
            <tr>
              <td className="label">Cite as:</td>
              <td>
                eiGen:{data.id} [{data.primary}]
              </td>
            </tr>
          </tbody>
        </table>

        <div className="submission-history">
          <h2>Submission history</h2>
          <div>From: {data.submitter}</div>
          {data.submission.map((v) => (
            <div key={v.version}>
              [v{v.version}] {formatDateTime(v.datetime)} ({v.size_kb} KB)
            </div>
          ))}
        </div>
      </div>

      <aside className="abs-side">
        <div className="side-box">
          <h2 className="side-head">Access Paper:</h2>
          <ul className="side-links">
            <li>
              <Link to={`/pdf/${data.id}`}>View PDF</Link>
            </li>
            <li>
              <Link to={`/html/${data.id}`}>Full text (HTML)</Link>
            </li>
            <li>
              <button className="linklike" onClick={() => downloadTex(data.id, data.tex)}>
                TeX Source
              </button>
            </li>
          </ul>
          <div className="license">License: CC BY 4.0</div>
        </div>

        <div className="side-box">
          <h2 className="side-head">Current browse context:</h2>
          <div className="browse-context">{data.primary}</div>
          <div className="browse-nav">
            <Link to={`/list/${data.primary}/recent`}>recent</Link> |{' '}
            <Link to={`/list/${data.primary}/${month}`}>{month}</Link>
          </div>
          <div className="browse-change">
            Change to browse by: <Link to="/archive/math">math</Link>
          </div>
        </div>
      </aside>
    </div>
  );
}
