"""Command-line entry point. Prints the example paper fragment for a seed."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .examples import demo_paper


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eigencircuits",
        description="Generate an example arXiv-style paper fragment.",
    )
    parser.add_argument("--seed", default="demo", help="base36 seed (default: demo)")
    args = parser.parse_args(argv)
    print(demo_paper(args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
