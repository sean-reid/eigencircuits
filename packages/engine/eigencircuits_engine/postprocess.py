"""Text shaping: articles, pluralization, capitalization, and a final cleanup.

These helpers operate on already-realized text. Capitalization and article
selection happen here rather than in the lexicon, so banks can stay lowercase
and singular.
"""

from __future__ import annotations

import re

# Letters whose spoken name begins with a vowel sound, used to pick "a"/"an"
# before a math symbol such as "$X$" -> "an $X$".
_VOWEL_SOUND_LETTERS = frozenset("AEFHILMNORSX")

_IRREGULAR_PLURALS: dict[str, str] = {
    "matrix": "matrices",
    "vertex": "vertices",
    "vortex": "vortices",
    "simplex": "simplices",
    "complex": "complexes",
    "index": "indices",
    "locus": "loci",
    "radius": "radii",
    "focus": "foci",
    "modulus": "moduli",
    "annulus": "annuli",
    "genus": "genera",
    "series": "series",
    "data": "data",
    "datum": "data",
    "calculus": "calculi",
    "basis": "bases",
    "hypothesis": "hypotheses",
    "analysis": "analyses",
    "manifold": "manifolds",
    "polynomial": "polynomials",
    "class": "classes",
    "lattice": "lattices",
    "sheaf": "sheaves",
    "leaf": "leaves",
    "curve": "curves",
}


def pluralize(text: str) -> str:
    """Pluralize the head (final word) of a noun phrase."""
    text = text.rstrip()
    if not text:
        return text
    head, sep, _ = text.rpartition(" ")
    word = text if not sep else text[len(head) + len(sep) :]
    plural = _pluralize_word(word)
    return f"{head}{sep}{plural}" if sep else plural


def _pluralize_word(word: str) -> str:
    lower = word.lower()
    if lower in _IRREGULAR_PLURALS:
        result = _IRREGULAR_PLURALS[lower]
        return result.capitalize() if word[:1].isupper() else result
    if re.search(r"(s|x|z|ch|sh)$", lower):
        return word + "es"
    if re.search(r"[^aeiou]y$", lower):
        return word[:-1] + "ies"
    return word + "s"


_LEADING_ARTICLE = re.compile(r"^(the|an|a)\s+", re.IGNORECASE)

# Banks the grammar prefixes with its own article/"the"; their entries must not
# carry a leading article of their own.
ARTICLE_BANKS = frozenset({"objects", "props", "invariants", "spaces", "maps"})


def strip_leading_article(text: str) -> str:
    """Drop a leading 'the'/'a'/'an' so the grammar can supply its own."""
    return _LEADING_ARTICLE.sub("", text, count=1)


def with_article(text: str) -> str:
    """Prefix ``text`` with "a" or "an" by the sound of its first token."""
    stripped = text.lstrip()
    if not stripped:
        return text
    return f"{'an' if _starts_with_vowel_sound(stripped) else 'a'} {stripped}"


# Greek-letter macros whose spoken name begins with a vowel sound.
_VOWEL_SOUND_GREEK = frozenset(
    {"alpha", "epsilon", "eta", "iota", "omicron", "omega", "upsilon", "ell"}
)


def _starts_with_vowel_sound(text: str) -> bool:
    if text[0] == "$":
        return _math_starts_with_vowel_sound(text)
    first = text[0].lower()
    if first not in "aeiou":
        return False
    # A few common spelled exceptions; the corpus rarely hits these.
    return not re.match(r"(uni|use|euler|eu)", text.lower())


def _math_starts_with_vowel_sound(text: str) -> bool:
    """Decide a/an for an inline symbol, reading the real symbol, not the macro
    name (``\\mathcal{C}`` is "C", ``\\rho`` is read as 'rho')."""
    inner = re.search(r"\\[a-zA-Z]+\*?\{([^}]*)\}", text)  # \mathcal{C}, \mathbb{Z}, ...
    if inner and (m := re.search(r"[A-Za-z]", inner.group(1))):
        return m.group(0).upper() in _VOWEL_SOUND_LETTERS
    greek = re.match(r"\$\s*\\([a-zA-Z]+)", text)  # bare greek/named macro
    if greek:
        return greek.group(1).lower() in _VOWEL_SOUND_GREEK
    letter = re.search(r"[A-Za-z]", text)
    return letter is not None and letter.group(0).upper() in _VOWEL_SOUND_LETTERS


def cap_first(text: str) -> str:
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1 :]
        if ch == "$":
            return text  # leading math: leave as written
    return text


def lower_first(text: str) -> str:
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.lower() + text[i + 1 :]
        if ch == "$":
            return text
    return text


_SMALL_WORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "if",
        "in",
        "nor",
        "of",
        "on",
        "or",
        "per",
        "the",
        "to",
        "via",
        "vs",
        "with",
    ]
)


def titlecase(text: str) -> str:
    """Title Case, leaving small words and math (``$...$``) untouched."""
    words = text.split(" ")
    out: list[str] = []
    last = len(words) - 1
    for i, word in enumerate(words):
        if not word or word.startswith("$"):
            out.append(word)
        elif i not in (0, last) and word.lower() in _SMALL_WORDS:
            out.append(word.lower())
        else:
            out.append(cap_first(word))
    return " ".join(out)


_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?)])")
_MULTISPACE = re.compile(r"[ \t]{2,}")
_SENTENCE_BOUNDARY = re.compile(r"([.!?])\s+([a-z])")


def finalize(text: str) -> str:
    """Whitespace and sentence cleanup that never touches inside ``$...$``."""
    segments = _split_math(text)
    for i, (is_math, seg) in enumerate(segments):
        if is_math:
            continue
        seg = _SPACE_BEFORE_PUNCT.sub(r"\1", seg)
        seg = _MULTISPACE.sub(" ", seg)
        segments[i] = (False, seg)
    joined = "".join(seg for _, seg in segments)
    joined = _SENTENCE_BOUNDARY.sub(lambda m: f"{m.group(1)} {m.group(2).upper()}", joined)
    return cap_first(joined.strip())


def _split_math(text: str) -> list[tuple[bool, str]]:
    """Split into (is_math, chunk) runs, treating ``$...$`` and ``$$...$$`` as math."""
    out: list[tuple[bool, str]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "$":
            display = text.startswith("$$", i)
            delim = "$$" if display else "$"
            end = text.find(delim, i + len(delim))
            if end == -1:
                out.append((False, text[i:]))
                break
            out.append((True, text[i : end + len(delim)]))
            i = end + len(delim)
        else:
            j = text.find("$", i)
            if j == -1:
                out.append((False, text[i:]))
                break
            out.append((False, text[i:j]))
            i = j
    return out


def is_math_balanced(text: str) -> bool:
    """True when ``$`` and ``$$`` delimiters are balanced."""
    i = 0
    n = len(text)
    open_count = 0
    while i < n:
        if text.startswith("$$", i):
            open_count ^= 1
            i += 2
        elif text[i] == "$":
            open_count ^= 1
            i += 1
        else:
            i += 1
    return open_count == 0
