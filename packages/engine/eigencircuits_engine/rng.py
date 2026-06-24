"""Seeded pseudo-random number generator.

A direct port of mulberry32, chosen because it is tiny, fast, and fully
deterministic from a 32-bit seed. The engine consumes randomness only through
an instance of :class:`Rng`, so a seed reproduces a paper exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

_T = TypeVar("_T")

_U32 = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    """32-bit integer multiply, matching JavaScript's ``Math.imul`` modulo sign."""
    return (a * b) & _U32


class Rng:
    """Deterministic PRNG seeded by a 32-bit integer."""

    __slots__ = ("_a",)

    def __init__(self, seed: int) -> None:
        self._a = seed & _U32

    def next_u32(self) -> int:
        self._a = (self._a + 0x6D2B79F5) & _U32
        t = self._a
        t = _imul(t ^ (t >> 15), 1 | t)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & _U32) ^ t
        return (t ^ (t >> 14)) & _U32

    def random(self) -> float:
        """A float in ``[0, 1)``."""
        return self.next_u32() / 4294967296.0

    def int_in_range(self, lo: int, hi: int) -> int:
        """An integer in the inclusive range ``[lo, hi]``."""
        if hi < lo:
            raise ValueError(f"empty range [{lo}, {hi}]")
        return lo + int(self.random() * (hi - lo + 1))

    def choice(self, seq: Sequence[_T]) -> _T:
        if not seq:
            raise ValueError("cannot choose from an empty sequence")
        return seq[self.int_in_range(0, len(seq) - 1)]

    def chance(self, p: float) -> bool:
        return self.random() < p

    def pick_weighted(self, options: Sequence[tuple[float, _T]]) -> _T:
        """Choose one value by weight. Weights need not be normalized."""
        if not options:
            raise ValueError("cannot pick from no options")
        total = sum(w for w, _ in options)
        if total <= 0:
            raise ValueError("weights must sum to a positive value")
        r = self.random() * total
        upto = 0.0
        for weight, value in options:
            upto += weight
            if r < upto:
                return value
        return options[-1][1]


def parse_seed(seed: str | int) -> int:
    """Accept a base36 string or an integer and return a 32-bit seed."""
    if isinstance(seed, int):
        return seed & _U32
    text = seed.strip().lower()
    if not text:
        raise ValueError("empty seed")
    return int(text, 36) & _U32


def format_seed(seed: int) -> str:
    """Render a 32-bit seed as a short base36 string."""
    seed &= _U32
    if seed == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out: list[str] = []
    while seed:
        seed, rem = divmod(seed, 36)
        out.append(digits[rem])
    return "".join(reversed(out))
