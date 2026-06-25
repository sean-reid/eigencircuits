// Mirrors the Python PaperModel serialized by eigencircuits_engine.generate.to_dict.

export interface Author {
  name: string;
  affiliation: number;
  email: string | null;
}

export interface Para {
  kind: 'para';
  text: string;
}

export interface EnvBlock {
  kind: 'env';
  env: string; // Theorem | Proposition | Lemma | Corollary | Conjecture | Definition | Example | Remark
  number: string;
  text: string;
  name: string | null;
}

export interface ProofBlock {
  kind: 'proof';
  text: string;
}

export interface EquationBlock {
  kind: 'equation';
  tex: string;
  number: string | null;
}

export type Block = Para | EnvBlock | ProofBlock | EquationBlock;

export interface SectionModel {
  number: string;
  heading: string;
  blocks: Block[];
}

export interface Reference {
  label: string;
  text: string;
}

export interface PaperStyle {
  numbering: 'section' | 'doc';
  citations: 'alpha' | 'numeric';
  caps: 'title' | 'sentence';
  length_class: 'note' | 'standard' | 'long';
}

export interface PaperModel {
  seed: string;
  grammar_version: number;
  subfield: string;
  title: string;
  authors: Author[];
  affiliations: string[];
  abstract: string;
  msc_primary: string;
  msc_secondary: string[];
  keywords: string[];
  sections: SectionModel[];
  references: Reference[];
  style: PaperStyle;
  acknowledgments: string | null;
  funding: string | null;
}

export interface GenerateResponse {
  model: PaperModel;
  tex: string;
}
