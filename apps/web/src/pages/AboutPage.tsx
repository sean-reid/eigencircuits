import { Link } from 'react-router-dom';

export function AboutPage() {
  return (
    <div className="about">
      <h1 className="page-title">About eigencircuits</h1>
      <p>
        eigencircuits generates mathematics papers that read like real arXiv preprints and are
        entirely meaningless. It is a descendant of SCIgen, retargeted to mathematics with a much
        larger grammar covering all 32 arXiv mathematics subject classes.
      </p>
      <p>
        Each paper is built by a seeded, context-sensitive grammar: the central object is chosen
        once and reused throughout, so a paper stays internally consistent in its subject, notation,
        theorems, and references. A given identifier always maps to the same seed, so every visitor
        sees the same papers, and a fresh batch is minted each day.
      </p>
      <p>
        Nothing here is true. Theorems, proofs, equations, authors, and citations are fabricated.
        The point is the imitation of form. Browse the{' '}
        <Link to="/archive/math">mathematics archive</Link>, open any abstract, and download the
        LaTeX source.
      </p>
      <p className="muted">
        eigencircuits is an independent parody and is not affiliated with arXiv, Cornell University,
        or the Simons Foundation.
      </p>
    </div>
  );
}
