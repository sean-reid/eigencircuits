import { useCallback, useEffect, useState } from 'react';
import { generatePaper } from './api/client';
import { Paper } from './render/Paper';
import { SUBFIELD_NAMES } from './subfields';
import type { PaperModel } from './types/paperModel';
import { Toolbar } from './ui/Toolbar';

export function App() {
  const [model, setModel] = useState<PaperModel | null>(null);
  const [tex, setTex] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [dark, setDark] = useState(false);

  const load = useCallback(async (seed?: string) => {
    setBusy(true);
    setError(null);
    setRevealed(false);
    try {
      const { model, tex } = await generatePaper(seed);
      setModel(model);
      setTex(tex);
      const url = new URL(window.location.href);
      url.searchParams.set('seed', model.seed);
      window.history.replaceState(null, '', url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    const seed = new URL(window.location.href).searchParams.get('seed') ?? undefined;
    void load(seed);
  }, [load]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  const downloadTex = () => {
    if (!model) return;
    const blob = new Blob([tex], { type: 'text/x-tex' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `eigencircuits-${model.seed}.tex`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const copyLink = () => {
    void navigator.clipboard?.writeText(window.location.href);
  };

  const subfieldLabel = model
    ? `${model.subfield} — ${SUBFIELD_NAMES[model.subfield] ?? ''}`.trim()
    : null;

  return (
    <div className="app">
      <Toolbar
        seed={model?.seed ?? ''}
        subfield={subfieldLabel}
        revealed={revealed}
        dark={dark}
        busy={busy}
        onGenerate={() => void load(undefined)}
        onLoadSeed={(s) => void load(s)}
        onToggleReveal={() => setRevealed((r) => !r)}
        onToggleDark={() => setDark((d) => !d)}
        onDownloadTex={downloadTex}
        onCopyLink={copyLink}
      />

      <main className="stage">
        {error && <div className="error">Could not reach the generator: {error}</div>}
        {model ? (
          <Paper model={model} />
        ) : (
          !error && <div className="loading">Generating…</div>
        )}
      </main>
    </div>
  );
}
