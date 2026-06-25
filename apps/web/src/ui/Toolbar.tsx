import { useState } from 'react';

interface ToolbarProps {
  seed: string;
  subfield: string | null;
  revealed: boolean;
  dark: boolean;
  busy: boolean;
  onGenerate: () => void;
  onLoadSeed: (seed: string) => void;
  onToggleReveal: () => void;
  onToggleDark: () => void;
  onDownloadTex: () => void;
  onCopyLink: () => void;
}

export function Toolbar(props: ToolbarProps) {
  const [draft, setDraft] = useState(props.seed);

  const submitSeed = (e: React.FormEvent) => {
    e.preventDefault();
    if (draft.trim()) props.onLoadSeed(draft.trim());
  };

  return (
    <header className="toolbar">
      <div className="toolbar-left">
        <span className="brand">eigencircuits</span>
        <button className="primary" onClick={props.onGenerate} disabled={props.busy}>
          Generate
        </button>
        <form className="seed-form" onSubmit={submitSeed}>
          <label className="visually-hidden" htmlFor="seed">
            Seed
          </label>
          <input
            id="seed"
            className="seed-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="seed"
            spellCheck={false}
            autoComplete="off"
          />
        </form>
      </div>

      <div className="toolbar-right">
        <button onClick={props.onToggleReveal} aria-pressed={props.revealed}>
          {props.revealed ? (props.subfield ?? 'subfield') : 'Reveal subfield'}
        </button>
        <button onClick={props.onDownloadTex} disabled={props.busy}>
          Download .tex
        </button>
        <button onClick={props.onCopyLink}>Copy link</button>
        <button
          className="icon"
          onClick={props.onToggleDark}
          aria-label="Toggle dark mode"
          title="Toggle dark mode"
        >
          {props.dark ? '☀' : '☾'}
        </button>
      </div>
    </header>
  );
}
