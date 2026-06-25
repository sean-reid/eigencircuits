#!/usr/bin/env bash
# Generate a paper for every subject class and compile each with pdflatex.
# Guards that the grammar never emits LaTeX that fails to build. Used in CI and
# runnable locally (falls back to the MacTeX path).
set -uo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
seeds=("${SEEDS:-1 7 42}")
read -r -a seeds <<<"${seeds[0]}"

latex="$(command -v pdflatex || true)"
if [ -z "$latex" ] && [ -x /Library/TeX/texbin/pdflatex ]; then
  latex=/Library/TeX/texbin/pdflatex
fi
if [ -z "$latex" ]; then
  echo "error: pdflatex not found" >&2
  exit 1
fi

codes="$(uv --project "$root/packages/engine" run python -c \
  'from eigencircuits_engine.lexicon.fields.registry import FIELDS; print(" ".join(f.code for f in FIELDS))')"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fail=0
count=0

for code in $codes; do
  for seed in "${seeds[@]}"; do
    name="${code//./_}-$seed"
    tex="$tmp/$name.tex"
    uv --project "$root/packages/engine" run eigencircuits --subfield "$code" --seed "$seed" --tex >"$tex"
    if ( cd "$tmp" && "$latex" -interaction=nonstopmode -halt-on-error "$name.tex" >"$tmp/$name.log" 2>&1 ); then
      count=$((count + 1))
    else
      echo "FAIL: $code (seed $seed)" >&2
      grep -A2 -m1 '^!' "$tmp/$name.log" >&2 || true
      fail=1
    fi
  done
done

if [ "$fail" = 0 ]; then
  echo "compiled $count papers across all subject classes"
else
  echo "one or more papers failed to compile" >&2
  exit 1
fi
