from decimal import Decimal

from capnut_migration.load import (
    build_open_ap,
    build_open_ar,
    build_open_pos,
    build_opening_balances,
)
from capnut_migration.load.documents import classify_accounts
from capnut_migration.mappings import MappingSet
from capnut_migration.pipeline import rows_reader
from conftest import ACCOUNTS, AR_OPEN, OPEN_PO_LINES, OPEN_POS, gl_rows


def mappings_for(config):
    return MappingSet.load(config.mapping_dir)


def test_account_classification():
    kinds = classify_accounts(ACCOUNTS)
    assert kinds["1200"] == "receivable"
    assert kinds["2100"] == "payable"
    assert kinds["1000"] == "other"


def test_opening_entry_excludes_ar_and_ap_control_accounts(config):
    result = build_opening_balances(gl_rows(), ACCOUNTS, mappings_for(config), config)
    assert result.ok, [str(i) for i in result.issues]
    accounts = {d["account"]: Decimal(d["balance"])
                for d in result.documents if d["_type"] == "opening_balance"}
    assert accounts == {
        "A1000": Decimal("1000.00"),
        "A1300": Decimal("300.00"),
        "A4000": Decimal("-1200.00"),
    }
    assert "A1200" not in accounts, "AR must come from open items, not the opening entry"
    assert "A2100" not in accounts, "AP must come from open items, not the opening entry"


def test_opening_control_totals_are_recorded(config):
    result = build_opening_balances(gl_rows(), ACCOUNTS, mappings_for(config), config)
    control = next(d for d in result.documents if d["_type"] == "opening_control")
    assert Decimal(control["ar_control_total"]) == Decimal("500.00")
    assert Decimal(control["ap_control_total"]) == Decimal("-600.00")
    assert Decimal(control["non_control_total"]) == Decimal("100.00")


def test_out_of_balance_source_is_reported(config):
    rows = gl_rows()
    rows[0]["debit"] = "1100.00"  # break the fixture on purpose
    result = build_opening_balances(rows, ACCOUNTS, mappings_for(config), config)
    assert not result.ok
    assert any("does not balance" in str(i) for i in result.issues)


def test_unmapped_account_is_an_issue_not_a_guess(config):
    rows = gl_rows() + [dict(gl_rows()[0], source_id=999, account_code="7777", debit="0.00",
                             credit="0.00")]
    accounts = ACCOUNTS + [{"source_id": 9, "code": "7777", "name": "Mystery",
                            "account_type": "expense", "reconcile": False,
                            "deprecated": False, "currency": "USD"}]
    result = build_opening_balances(rows, accounts, mappings_for(config), config)
    # zero balance -> nothing to load, and nothing invented
    assert all(d.get("account") != "7777" for d in result.documents)


def test_account_missing_from_the_accounts_extract_is_reported(config):
    rows = gl_rows() + [dict(gl_rows()[0], source_id=999, account_code="7777",
                             debit="50.00", credit="0.00")]
    result = build_opening_balances(rows, ACCOUNTS, mappings_for(config), config)
    assert any("missing from the accounts extract" in str(i) for i in result.issues)


def test_open_ar_carries_party_residual_and_bucket(config):
    result = build_open_ar(AR_OPEN, mappings_for(config), config)
    assert result.ok
    doc = result.documents[0]
    assert doc["party"] == "PARTY-11"
    assert doc["amount_open"] == "500.00"
    assert doc["aging_bucket"] == "1-30"
    assert doc["_ref"] == "odoo:open_ar.item:101"


def test_open_ar_with_no_party_is_refused(config):
    rows = [dict(AR_OPEN[0], partner_id=None)]
    result = build_open_ar(rows, mappings_for(config), config)
    assert not result.ok
    assert not result.documents


def test_open_ap_uses_the_vendor_mapping(config):
    from conftest import AP_OPEN

    result = build_open_ap(AP_OPEN, mappings_for(config), config)
    assert result.ok
    assert result.documents[0]["party"] == "PARTY-21"
    assert result.documents[0]["amount_open"] == "600.00"


def test_open_po_values_only_the_open_quantity(config):
    result = build_open_pos(OPEN_POS, OPEN_PO_LINES, mappings_for(config), config)
    assert result.ok, [str(i) for i in result.issues]
    doc = result.documents[0]
    assert doc["open_value"] == "250.00"
    assert doc["lines"][0]["product"] == "P-WPI-1KG"
    assert doc["lines"][0]["quantity_open"] == "10.00"


def test_open_po_with_an_unmapped_product_is_refused(config):
    lines = [dict(OPEN_PO_LINES[0], product_code="UNKNOWN-SKU")]
    result = build_open_pos(OPEN_POS, lines, mappings_for(config), config)
    assert not result.ok
    assert not result.documents


def test_build_all_produces_every_document_type(config):
    from capnut_migration.load import build_all

    result = build_all(config, mappings_for(config), rows_reader(config))
    assert result.ok, [str(i) for i in result.issues]
    counts = result.by_type()
    assert counts["opening_balance"] == 3
    assert counts["open_ar"] == 1
    assert counts["open_ap"] == 1
    assert counts["open_po"] == 1
