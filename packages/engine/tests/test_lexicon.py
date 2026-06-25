from __future__ import annotations

import pkgutil

import pytest

from eigencircuits_engine.lexicon import fields as fields_pkg
from eigencircuits_engine.lexicon.fields.registry import BY_CODE, FIELDS
from eigencircuits_engine.lexicon.schema import FIELD_BANKS, SubfieldLexicon


def test_codes_are_unique() -> None:
    codes = [f.code for f in FIELDS]
    assert len(codes) == len(set(codes))


def test_registry_covers_every_field_module() -> None:
    # Every fields/*.py module (except registry/schema helpers) must be wired
    # into FIELDS, so adding a module without registering it is caught.
    modules = {
        name for _, name, _ in pkgutil.iter_modules(fields_pkg.__path__) if name not in {"registry"}
    }
    registered = {f.code.split(".", 1)[1].lower() for f in FIELDS}
    assert modules == registered


@pytest.mark.parametrize("field", FIELDS, ids=[f.code for f in FIELDS])
def test_field_is_well_formed(field: SubfieldLexicon) -> None:
    assert field.code.startswith("math.")
    assert field.name
    assert field.weight > 0
    for bank in FIELD_BANKS:
        terms = field.banks.get(bank)
        assert terms, f"{field.code} missing bank {bank!r}"
    assert len(field.symbols) >= 2
    assert field.msc, f"{field.code} has no MSC codes"
    assert field.inline_eqns and field.display_eqns


def test_by_code_matches_fields() -> None:
    assert set(BY_CODE) == {f.code for f in FIELDS}
