import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { fetchAbs } from '../api/client';
import { compilePdf } from '../pdf/compile';
import type { AbsResponse } from '../types/api';
import { downloadTex } from '../util/format';

type Phase =
  | { kind: 'loading' }
  | { kind: 'compiling' }
  | { kind: 'failed'; reason: string; log?: string };

export function PdfPage() {
  const { id = '' } = useParams();
  const [abs, setAbs] = useState<AbsResponse | null>(null);
  const [phase, setPhase] = useState<Phase>({ kind: 'loading' });

  useEffect(() => {
    let alive = true;
    setPhase({ kind: 'loading' });
    setAbs(null);

    (async () => {
      let data: AbsResponse;
      try {
        data = await fetchAbs(id);
      } catch {
        if (alive) setPhase({ kind: 'failed', reason: 'Article not found.' });
        return;
      }
      if (!alive) return;
      setAbs(data);
      setPhase({ kind: 'compiling' });

      try {
        const result = await compilePdf(data.tex);
        if (!alive) return;
        if (result.status === 0 && result.pdf) {
          const url = URL.createObjectURL(
            new Blob([result.pdf as BlobPart], { type: 'application/pdf' }),
          );
          // Hand the compiled PDF to the browser's native viewer, like arXiv.
          // Same-tab navigation avoids popup blocking and renders full-screen
          // (fitting correctly on mobile); replace() keeps Back -> abstract.
          // The object URL is intentionally not revoked so the viewer keeps it.
          window.location.replace(url);
        } else {
          setPhase({
            kind: 'failed',
            reason: 'The compiler did not produce a PDF.',
            log: lastLines(result.log),
          });
        }
      } catch {
        if (alive) {
          setPhase({
            kind: 'failed',
            reason: 'The TeX engine could not be reached. Its package mirror may be unavailable.',
          });
        }
      }
    })();

    return () => {
      alive = false;
    };
  }, [id]);

  if (phase.kind === 'failed' && !abs) {
    return (
      <p className="status error">
        {phase.reason} <Link to="/">Return to the archive.</Link>
      </p>
    );
  }

  return (
    <div className="pdfview">
      <div className="pdfbar">
        <Link to={`/abs/${id}`}>← Back to abstract (eiGen:{id})</Link>
        {abs && (
          <button className="linklike" onClick={() => downloadTex(id, abs.tex)}>
            Download .tex
          </button>
        )}
      </div>

      {phase.kind === 'loading' && <p className="status">Loading…</p>}

      {phase.kind === 'compiling' && (
        <div className="pdf-progress">
          <div className="spinner" aria-hidden="true" />
          <p className="status">Compiling with pdfTeX…</p>
          <p className="muted">
            The PDF will open in your browser&rsquo;s viewer when it is ready. The first paper you
            open downloads the TeX engine and its packages, so it can take a few seconds; later
            papers compile much faster.
          </p>
        </div>
      )}

      {phase.kind === 'failed' && abs && (
        <div className="pdf-failed">
          <p className="status error">{phase.reason}</p>
          <p className="muted">
            You can still{' '}
            <button className="linklike" onClick={() => downloadTex(id, abs.tex)}>
              download the LaTeX source
            </button>{' '}
            or read the <Link to={`/html/${id}`}>full text in HTML</Link>.
          </p>
          {phase.log && <pre className="pdf-log">{phase.log}</pre>}
        </div>
      )}
    </div>
  );
}

function lastLines(log: string, n = 24): string {
  return log.split('\n').slice(-n).join('\n').trim();
}
