"""Registry of available subfields with selection weights.

Filled out one field at a time. The weighted draw in ``theme`` uses the
``weight`` on each lexicon.
"""

from __future__ import annotations

from ..schema import SubfieldLexicon
from .nt import NT

FIELDS: tuple[SubfieldLexicon, ...] = (NT,)

BY_CODE: dict[str, SubfieldLexicon] = {f.code: f for f in FIELDS}


def weighted_fields() -> list[tuple[float, SubfieldLexicon]]:
    return [(f.weight, f) for f in FIELDS]
