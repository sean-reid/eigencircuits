import type { Block, PaperModel } from '../types/paperModel';
import { DisplayMath, InlineText } from './tex';

const PLAIN_ENVS = new Set(['Theorem', 'Proposition', 'Lemma', 'Corollary', 'Conjecture']);

function Authors({ model }: { model: PaperModel }) {
  const multi = model.affiliations.length > 1;
  return (
    <div className="authors">
      <div className="author-line">
        {model.authors.map((a, i) => (
          <span key={i}>
            {a.name}
            {multi && <sup>{a.affiliation + 1}</sup>}
            {i < model.authors.length - 1 ? ', ' : ''}
          </span>
        ))}
      </div>
      <ol className="affiliations">
        {model.affiliations.map((aff, i) => (
          <li key={i} value={i + 1}>
            {aff}
          </li>
        ))}
      </ol>
    </div>
  );
}

function BlockView({ block }: { block: Block }) {
  switch (block.kind) {
    case 'para':
      return (
        <p className="para">
          <InlineText text={block.text} />
        </p>
      );
    case 'env': {
      const italic = PLAIN_ENVS.has(block.env);
      return (
        <p className="env">
          <strong>
            {block.env} {block.number}
            {block.name ? ` (${block.name})` : ''}.
          </strong>{' '}
          <span className={italic ? 'statement italic' : 'statement'}>
            <InlineText text={block.text} />
          </span>
        </p>
      );
    }
    case 'proof':
      return (
        <p className="proof">
          <em>Proof.</em> <InlineText text={block.text} />
          <span className="qed"> □</span>
        </p>
      );
    case 'equation':
      return (
        <div className="equation">
          <DisplayMath tex={block.tex} />
          {block.number && <span className="eqno">({block.number})</span>}
        </div>
      );
  }
}

export function Paper({ model }: { model: PaperModel }) {
  const secondary = model.msc_secondary.join(', ');
  return (
    <article className="paper" aria-label="generated paper">
      <h1 className="title">{model.title}</h1>
      <Authors model={model} />

      <section className="abstract">
        <span className="abstract-head">Abstract.</span> <InlineText text={model.abstract} />
      </section>

      <p className="msc">
        <span className="label">2020 Mathematics Subject Classification.</span> {model.msc_primary}
        {secondary ? `; ${secondary}` : ''}.
      </p>
      <p className="keywords">
        <span className="label">Key words and phrases.</span> {model.keywords.join(', ')}.
      </p>

      {model.sections.map((s) => (
        <section className="section" key={s.number}>
          <h2 className="section-head">
            {s.number}. {s.heading}
          </h2>
          {s.blocks.map((b, i) => (
            <BlockView block={b} key={i} />
          ))}
        </section>
      ))}

      {model.acknowledgments && (
        <section className="acks">
          <h3 className="subsection-head">Acknowledgments</h3>
          <p className="para">
            {model.acknowledgments}
            {model.funding ? ` ${model.funding}` : ''}
          </p>
        </section>
      )}

      <section className="references">
        <h2 className="section-head">References</h2>
        <ol className="reflist">
          {model.references.map((r) => (
            <li key={r.label}>
              <span className="reflabel">[{r.label}]</span> <InlineText text={r.text} />
            </li>
          ))}
        </ol>
      </section>
    </article>
  );
}
