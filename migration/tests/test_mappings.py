import pytest

from capnut_migration.mappings import (
    MAPPING_SPECS,
    MappingRow,
    MappingSet,
    MappingTable,
    Unmapped,
)
from conftest import write_mappings


def table(name="accounts", rows=()):
    spec = next(s for s in MAPPING_SPECS if s.name == name)
    t = MappingTable(spec=spec)
    for row in rows:
        t.rows[row.source_key] = row
    return t


def test_resolve_returns_target_for_approved_rows():
    t = table(rows=[MappingRow("1000", target_key="A1000", status="approved", reviewer="M. Hart")])
    assert t.resolve("1000") == "A1000"


def test_unknown_value_raises_rather_than_guessing():
    with pytest.raises(Unmapped):
        table().resolve("9999")


def test_pending_row_blocks_the_load():
    t = table(rows=[MappingRow("1000", target_key="A1000", status="pending")])
    with pytest.raises(Unmapped):
        t.resolve("1000")
    assert any("unreviewed" in i.problem for i in t.validate())


def test_excluded_row_resolves_to_none_and_needs_a_note():
    t = table(rows=[MappingRow("9999", status="excluded")])
    assert t.resolve("9999") is None
    assert any("without a note" in i.problem for i in t.validate())
    t.rows["9999"].notes = "Odoo suspense account, deliberately not migrated"
    assert t.validate() == []


def test_accounting_mappings_require_a_reviewer():
    t = table(rows=[MappingRow("1000", target_key="A1000", status="approved")])
    assert any("without a reviewer" in i.problem for i in t.validate())


def test_product_mapping_does_not_require_a_reviewer():
    t = table("products", [MappingRow("SKU1", target_key="P-SKU1", status="approved")])
    assert t.validate() == []


def test_approved_without_target_is_an_error():
    t = table(rows=[MappingRow("1000", status="approved", reviewer="M. Hart")])
    assert any("empty target_key" in i.problem for i in t.validate())


def test_two_accounts_collapsing_into_one_target_is_flagged():
    t = table(rows=[
        MappingRow("1000", target_key="A1000", status="approved", reviewer="M. Hart"),
        MappingRow("1001", target_key="A1000", status="approved", reviewer="M. Hart"),
    ])
    assert any("already used by" in i.problem for i in t.validate())


def test_stub_never_overwrites_a_reviewed_row():
    t = table(rows=[MappingRow("1000", target_key="A1000", status="approved", reviewer="M. Hart")])
    assert t.add_pending("1000", "Cash") is False
    assert t.rows["1000"].status == "approved"
    assert t.add_pending("1100", "Petty cash") is True
    assert t.rows["1100"].status == "pending"


def test_round_trip_through_csv(tmp_path):
    t = table(rows=[MappingRow("1000", "Cash", "", "A1000", "Cash", "approved", "M. Hart")])
    t.save(tmp_path / "accounts.csv")
    reloaded = MappingTable.load(t.spec, tmp_path)
    assert reloaded.resolve("1000") == "A1000"
    assert reloaded.rows["1000"].reviewer == "M. Hart"


def test_coverage_lists_values_with_no_row(tmp_path):
    write_mappings(tmp_path)
    mappings = MappingSet.load(tmp_path)
    assert mappings["accounts"].coverage(["1000", "5000", "6000"]) == ["5000", "6000"]


def test_a_complete_mapping_set_validates(tmp_path):
    write_mappings(tmp_path)
    assert MappingSet.load(tmp_path).validate() == []


def test_an_empty_mapping_set_does_not_validate(tmp_path):
    assert MappingSet.load(tmp_path).validate()
