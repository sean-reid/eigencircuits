"""Render a :class:`PaperModel` to a compilable ``amsart`` LaTeX document."""

from __future__ import annotations

from .types import EnvBlock, EquationBlock, PaperModel, Para, ProofBlock


def _preamble(section_numbered: bool) -> str:
    # Match equation numbering to the theorem numbering scheme.
    base = r"""\documentclass[11pt]{amsart}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
"""
    if section_numbered:
        thm = r"\newtheorem{theorem}{Theorem}[section]"
        numbering = "\n\\numberwithin{equation}{section}"
    else:
        thm = r"\newtheorem{theorem}{Theorem}"
        numbering = ""
    shared = (
        "\n\\theoremstyle{plain}\n"
        f"{thm}\n"
        r"\newtheorem{proposition}[theorem]{Proposition}"
        "\n"
        r"\newtheorem{lemma}[theorem]{Lemma}"
        "\n"
        r"\newtheorem{corollary}[theorem]{Corollary}"
        "\n\\theoremstyle{definition}\n"
        r"\newtheorem{definition}[theorem]{Definition}"
        "\n"
        r"\newtheorem{example}[theorem]{Example}"
        "\n\\theoremstyle{remark}\n"
        r"\newtheorem{remark}[theorem]{Remark}"
    )
    return base + shared + numbering + "\n"


_ENV_NAMES = {
    "Theorem": "theorem",
    "Proposition": "proposition",
    "Lemma": "lemma",
    "Corollary": "corollary",
    "Definition": "definition",
    "Example": "example",
    "Remark": "remark",
}


def to_latex(model: PaperModel) -> str:
    out: list[str] = [_preamble(model.style.numbering == "section")]
    out.append(f"\\title{{{model.title}}}")
    for author in model.authors:
        out.append(f"\\author{{{author.name}}}")
    if len(model.affiliations) == 1:
        # All authors share one institution: print it once, emails stacked.
        out.append(f"\\address{{{model.affiliations[0]}}}")
        for author in model.authors:
            if author.email:
                out.append(f"\\email{{{author.email}}}")
    else:
        # Distinct institutions: attribute each with a single author name.
        for author in model.authors:
            out.append(f"\\address{{({author.name}) {model.affiliations[author.affiliation]}}}")
            if author.email:
                out.append(f"\\email{{({author.name}) {author.email}}}")
    secondary = ", ".join(model.msc_secondary)
    subj = model.msc_primary + (f"; {secondary}" if secondary else "")
    out.append(f"\\subjclass[2020]{{{subj}}}")
    out.append(f"\\keywords{{{', '.join(model.keywords)}}}")
    out.append("")
    out.append(r"\begin{document}")
    # In amsart the abstract must precede \maketitle.
    out.append(r"\begin{abstract}")
    out.append(model.abstract)
    out.append(r"\end{abstract}")
    out.append(r"\maketitle")
    out.append("")

    for section in model.sections:
        out.append(f"\\section{{{section.heading}}}")
        for block in section.blocks:
            out.append(_render_block(block))
        out.append("")

    if model.acknowledgments:
        ack = model.acknowledgments
        if model.funding:
            ack += f" {model.funding}"
        out.append(f"\\subsection*{{Acknowledgments}} {ack}")
        out.append("")

    out.append(r"\begin{thebibliography}{99}")
    for entry in model.references:
        out.append(f"\\bibitem[{entry.label}]{{{entry.label}}} {entry.text}")
    out.append(r"\end{thebibliography}")
    out.append("")
    out.append(r"\end{document}")
    return "\n".join(out)


def _render_block(block: object) -> str:
    if isinstance(block, Para):
        return block.text + "\n"
    if isinstance(block, EnvBlock):
        env = _ENV_NAMES.get(block.env, "theorem")
        opener = f"\\begin{{{env}}}"
        if block.name:
            opener += f"[{block.name}]"
        return f"{opener}\n{block.text}\n\\end{{{env}}}\n"
    if isinstance(block, ProofBlock):
        return f"\\begin{{proof}}\n{block.text}\n\\end{{proof}}\n"
    if isinstance(block, EquationBlock):
        return f"\\begin{{equation}}\n{block.tex}\n\\end{{equation}}\n"
    raise TypeError(f"unknown block {block!r}")
