"""Command-line entry point. Generates a paper and prints it for a seed."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .generate import generate, to_dict
from .latex import to_latex
from .types import EnvBlock, EquationBlock, PaperModel, Para, ProofBlock


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eigencircuits",
        description="Generate an arXiv-style mathematics paper.",
    )
    parser.add_argument("--seed", default=None, help="base36 seed (default: random)")
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--tex", action="store_true", help="emit LaTeX")
    fmt.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    model = generate(args.seed)
    if args.tex:
        print(to_latex(model))
    elif args.json:
        print(json.dumps(to_dict(model), ensure_ascii=False, indent=2))
    else:
        print(_to_text(model))
    return 0


_SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _sup(n: int) -> str:
    return "".join(_SUPERSCRIPTS[int(d)] for d in str(n))


def _to_text(model: PaperModel) -> str:
    lines = [model.title, ""]
    multi = len(model.affiliations) > 1
    names = [a.name + (_sup(a.affiliation + 1) if multi else "") for a in model.authors]
    lines.append(", ".join(names))
    for i, aff in enumerate(model.affiliations, 1):
        lines.append(f"{_sup(i)} {aff}" if multi else aff)
    lines.append("")
    lines.append("Abstract. " + model.abstract)
    lines.append("")
    for section in model.sections:
        lines.append(f"{section.number}. {section.heading}")
        for block in section.blocks:
            lines.append(_block_text(block))
        lines.append("")
    if model.acknowledgments:
        ack = model.acknowledgments + (f" {model.funding}" if model.funding else "")
        lines.append("Acknowledgments. " + ack)
        lines.append("")
    lines.append("References")
    for entry in model.references:
        text = entry.text.replace("\\emph{", "").replace("\\textbf{", "").replace("}", "")
        lines.append(f"[{entry.label}] {text}")
    lines.append("")
    lines.append(f"-- generated: {model.subfield}, seed {model.seed} --")
    return "\n".join(lines)


def _block_text(block: object) -> str:
    if isinstance(block, Para):
        return block.text
    if isinstance(block, EnvBlock):
        head = f"{block.env} {block.number}"
        if block.name:
            head += f" ({block.name})"
        return f"{head}. {block.text}"
    if isinstance(block, ProofBlock):
        return f"Proof. {block.text}"
    if isinstance(block, EquationBlock):
        return f"    {block.tex}"
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
