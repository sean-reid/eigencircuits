#!/usr/bin/env bash
# Generate a paper and open it as a PDF. Usage: bin/preview.sh [seed]
# With no seed, a random one is used and printed.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
seed="${1:-}"
tmp="$(mktemp -d)"

if [ -n "$seed" ]; then
  uv --project "$root/packages/engine" run eigencircuits --seed "$seed" --tex > "$tmp/paper.tex"
else
  uv --project "$root/packages/engine" run eigencircuits --tex > "$tmp/paper.tex"
fi

( cd "$tmp" && pdflatex -interaction=nonstopmode -halt-on-error paper.tex >/dev/null 2>&1 )
echo "$tmp/paper.pdf"
open "$tmp/paper.pdf" 2>/dev/null || xdg-open "$tmp/paper.pdf" 2>/dev/null || true
