#!/usr/bin/env bash
# Generate a paper and open it as a PDF. Usage: bin/preview.sh [seed]
# With no seed, a random one is used.
set -uo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
seed="${1:-}"
tmp="$(mktemp -d)"
tex="$tmp/paper.tex"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' is not on your PATH. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

# Find a LaTeX engine; fall back to the standard macOS MacTeX location.
latex="$(command -v pdflatex || true)"
if [ -z "$latex" ] && [ -x /Library/TeX/texbin/pdflatex ]; then
  latex=/Library/TeX/texbin/pdflatex
fi
if [ -z "$latex" ]; then
  echo "error: pdflatex not found. Install MacTeX (https://tug.org/mactex/) or add it to PATH." >&2
  echo "The LaTeX source was still written to: $tex" >&2
  uv --project "$root/packages/engine" run eigencircuits ${seed:+--seed "$seed"} --tex > "$tex"
  exit 1
fi

uv --project "$root/packages/engine" run eigencircuits ${seed:+--seed "$seed"} --tex > "$tex"

if ! ( cd "$tmp" && "$latex" -interaction=nonstopmode -halt-on-error paper.tex >build.log 2>&1 ); then
  echo "error: pdflatex failed. Last lines of the log:" >&2
  tail -20 "$tmp/build.log" >&2
  echo "(source: $tex)" >&2
  exit 1
fi

echo "$tmp/paper.pdf"
open "$tmp/paper.pdf" 2>/dev/null || xdg-open "$tmp/paper.pdf" 2>/dev/null || \
  echo "Open it manually: $tmp/paper.pdf"
