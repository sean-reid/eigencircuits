from __future__ import annotations

from eigencircuits_engine.rng import Rng, format_seed, parse_seed


def test_rng_is_deterministic() -> None:
    a = [Rng(12345).next_u32() for _ in range(50)]
    b = [Rng(12345).next_u32() for _ in range(50)]
    assert a == b


def test_rng_differs_by_seed() -> None:
    assert Rng(1).next_u32() != Rng(2).next_u32()


def test_random_in_unit_interval() -> None:
    rng = Rng(7)
    for _ in range(1000):
        x = rng.random()
        assert 0.0 <= x < 1.0


def test_int_in_range_bounds() -> None:
    rng = Rng(99)
    for _ in range(1000):
        v = rng.int_in_range(3, 8)
        assert 3 <= v <= 8


def test_int_in_range_singleton() -> None:
    assert Rng(0).int_in_range(5, 5) == 5


def test_pick_weighted_respects_zero_weight() -> None:
    rng = Rng(42)
    seen = {rng.pick_weighted([(1.0, "a"), (0.0, "b")]) for _ in range(200)}
    assert seen == {"a"}


def test_seed_roundtrip() -> None:
    for value in (0, 1, 1234567, 0xFFFFFFFF):
        assert parse_seed(format_seed(value)) == value
