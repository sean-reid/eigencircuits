"""Symbol allocation.

Hands out non-colliding math symbols, one per role, so that prose and equations
agree on notation (the variety bound to ``mainObject`` is the same ``X``
everywhere) and two distinct objects never share a symbol.
"""

from __future__ import annotations

from collections.abc import Sequence

from .rng import Rng


class SymbolAllocator:
    __slots__ = ("_assigned", "_pool", "_used")

    def __init__(self, pool: Sequence[str]) -> None:
        self._pool: list[str] = list(pool) or ["X", "Y", "Z"]
        self._assigned: dict[str, str] = {}
        self._used: set[str] = set()

    def get(self, role: str, rng: Rng) -> str:
        """Return the symbol for ``role``, allocating one on first use."""
        existing = self._assigned.get(role)
        if existing is not None:
            return existing
        available = [s for s in self._pool if s not in self._used]
        if available:
            symbol = available[rng.int_in_range(0, len(available) - 1)]
        else:
            symbol = self._next_subscripted(rng)
        self._assigned[role] = symbol
        self._used.add(symbol)
        return symbol

    def assigned(self) -> dict[str, str]:
        """A copy of the current role-to-symbol assignments."""
        return dict(self._assigned)

    def _next_subscripted(self, rng: Rng) -> str:
        base = self._pool[rng.int_in_range(0, len(self._pool) - 1)]
        i = 1
        while f"{base}_{{{i}}}" in self._used:
            i += 1
        return f"{base}_{{{i}}}"
