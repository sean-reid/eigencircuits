from __future__ import annotations

from eigencircuits_engine.postprocess import (
    cap_first,
    finalize,
    is_math_balanced,
    pluralize,
    titlecase,
    with_article,
)


def test_pluralize_regular() -> None:
    assert pluralize("group") == "groups"
    assert pluralize("space") == "spaces"


def test_pluralize_irregular() -> None:
    assert pluralize("matrix") == "matrices"
    assert pluralize("locus") == "loci"
    assert pluralize("complex") == "complexes"


def test_pluralize_head_of_phrase() -> None:
    assert pluralize("smooth projective variety") == "smooth projective varietys".replace(
        "varietys", "varieties"
    )
    assert pluralize("moduli space") == "moduli spaces"


def test_pluralize_y_rule() -> None:
    assert pluralize("variety") == "varieties"
    assert pluralize("category") == "categories"


def test_article_consonant_and_vowel() -> None:
    assert with_article("group") == "a group"
    assert with_article("ideal") == "an ideal"


def test_article_before_math_symbol() -> None:
    # The spoken names of X, F, L, M begin with a vowel sound.
    assert with_article("$X$-bundle").startswith("an ")
    assert with_article("$\\mathbb{F}_q$-scheme").startswith("an ")
    assert with_article("$G$-action").startswith("a ")


def test_cap_first_skips_leading_math() -> None:
    assert cap_first("$X$ is smooth") == "$X$ is smooth"
    assert cap_first("the group") == "The group"


def test_titlecase_keeps_small_words_and_math() -> None:
    out = titlecase("on the cohomology of $X$")
    assert out == "On the Cohomology of $X$"


def test_finalize_collapses_spaces_and_fixes_punctuation() -> None:
    assert finalize("we  prove that  $X$ is smooth .") == "We prove that $X$ is smooth."


def test_finalize_capitalizes_sentence_starts() -> None:
    assert finalize("first. second statement holds.") == "First. Second statement holds."


def test_math_balance() -> None:
    assert is_math_balanced("a $x$ b $$y$$ c")
    assert not is_math_balanced("a $x b")
