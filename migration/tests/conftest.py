"""A small, deliberately *consistent* fixture company.

Balances (as of 2025-12-31):
    1000 Cash          debit  1,000.00
    1200 AR            debit    500.00   (one open invoice)
    1300 Inventory     debit    300.00
    2100 AP           credit    600.00   (one open bill)
    4000 Revenue      credit  1,200.00
                      ---------------
                      debits 1,800.00 = credits 1,800.00

Tests that expect a failure break this fixture on purpose.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from capnut_migration.config import load_config
from capnut_migration.mappings import FIELDNAMES

LABEL = "test"

ACCOUNTS = [
    {"source_id": 1, "code": "1000", "name": "Cash", "account_type": "asset_cash",
     "reconcile": False, "deprecated": False, "currency": "USD"},
    {"source_id": 2, "code": "1200", "name": "Accounts Receivable",
     "account_type": "asset_receivable", "reconcile": True, "deprecated": False, "currency": "USD"},
    {"source_id": 3, "code": "1300", "name": "Inventory", "account_type": "asset_current",
     "reconcile": False, "deprecated": False, "currency": "USD"},
    {"source_id": 4, "code": "2100", "name": "Accounts Payable",
     "account_type": "liability_payable", "reconcile": True, "deprecated": False, "currency": "USD"},
    {"source_id": 5, "code": "4000", "name": "Revenue", "account_type": "income",
     "reconcile": False, "deprecated": False, "currency": "USD"},
]

GL_LINES = [
    ("1000", "1000.00", "0.00"),
    ("1200", "500.00", "0.00"),
    ("1300", "300.00", "0.00"),
    ("2100", "0.00", "600.00"),
    ("4000", "0.00", "1200.00"),
]

AR_OPEN = [{
    "source_id": 101, "number": "INV/2025/0001", "move_type": "out_invoice",
    "partner_id": 11, "partner_ref": "C-11", "date": "2025-11-15", "due_date": "2025-12-15",
    "currency": "USD", "amount_total": "500.00", "amount_residual": "500.00",
    "account_code": "1200", "state": "posted",
}]

AP_OPEN = [{
    "source_id": 201, "number": "BILL/2025/0007", "move_type": "in_invoice",
    "partner_id": 21, "partner_ref": "V-21", "date": "2025-12-01", "due_date": "2026-01-05",
    "currency": "USD", "amount_total": "600.00", "amount_residual": "600.00",
    "account_code": "2100", "state": "posted",
}]

OPEN_POS = [{
    "source_id": 301, "name": "PO00042", "partner_id": 21, "date_order": "2025-12-20",
    "state": "purchase", "currency": "USD", "amount_untaxed": "250.00", "amount_total": "250.00",
}]

OPEN_PO_LINES = [{
    "source_id": 401, "order_id": 301, "order_name": "PO00042", "product_id": 31,
    "product_code": "WPI-1KG", "description": "Whey protein isolate 1kg",
    "qty_ordered": "10", "qty_received": "0", "qty_invoiced": "0", "qty_open": "10",
    "price_unit": "25.00", "line_total": "250.00", "uom": "Units", "date_planned": "2026-01-10",
}]

PARTIES = [
    {"source_id": 11, "ref": "C-11", "name": "Acme Health Foods", "is_company": True,
     "parent_id": None, "customer_rank": 3, "supplier_rank": 0, "vat": None, "email": None,
     "phone": None, "street": None, "street2": None, "city": "Ottawa", "state_code": "ON",
     "zip": None, "country_code": "CA", "active": True},
    {"source_id": 21, "ref": "V-21", "name": "Bulk Ingredients Ltd", "is_company": True,
     "parent_id": None, "customer_rank": 0, "supplier_rank": 5, "vat": None, "email": None,
     "phone": None, "street": None, "street2": None, "city": "Toronto", "state_code": "ON",
     "zip": None, "country_code": "CA", "active": True},
]

PRODUCTS = [{
    "source_id": 31, "template_id": 31, "default_code": "WPI-1KG", "barcode": None,
    "name": "Whey Protein Isolate 1kg", "product_type": "product", "uom": "Units",
    "list_price": "49.99", "standard_price": "25.00", "categ_name": "All / Protein",
    "active": True,
}]

JOURNALS = [{"source_id": 1, "code": "MISC", "name": "Miscellaneous", "journal_type": "general",
             "currency": "USD"}]
TAXES = [{"source_id": 1, "name": "HST 13%", "amount": "13.0", "amount_type": "percent",
          "type_tax_use": "sale", "active": True}]
INVENTORY = [{"source_id": 501, "product_id": 31, "product_code": "WPI-1KG", "location_id": 8,
              "location_name": "WH/Stock", "internal": True, "quantity": "12",
              "unit_cost": "25.00", "value": "300.00"}]
SALES_ORDERS = [{"source_id": 601, "name": "SO0001", "partner_id": 11, "date_order": "2025-11-15",
                 "state": "sale", "currency": "USD", "amount_untaxed": "500.00",
                 "amount_tax": "0.00", "amount_total": "500.00"}]
PAYMENTS: list[dict] = []

MAPPING_ROWS = {
    "accounts": [("1000", "Cash", "A1000"), ("1200", "AR", "A1200"), ("1300", "Inventory", "A1300"),
                 ("2100", "AP", "A2100"), ("4000", "Revenue", "A4000")],
    "journals": [("MISC", "Miscellaneous", "J-MISC")],
    "taxes": [("1", "HST 13%", "T-HST13")],
    "products": [("WPI-1KG", "Whey Protein Isolate 1kg", "P-WPI-1KG")],
    "parties": [("11", "Acme Health Foods", "PARTY-11")],
    "vendors": [("21", "Bulk Ingredients Ltd", "PARTY-21")],
    "uom": [("Units", "Units", "UOM-UNIT")],
}


def _write_jsonl(path: Path, rows: list[dict], model: str, system: str = "odoo") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            row = dict(row)
            row["_ref"] = f"{system}:{model}:{row['source_id']}"
            fh.write(json.dumps(row) + "\n")


def gl_rows() -> list[dict]:
    rows = []
    for i, (code, debit, credit) in enumerate(GL_LINES, start=1):
        rows.append({
            "source_id": 900 + i, "move_id": 90, "move_name": "OPEN/2025",
            "date": "2025-12-31", "journal_code": "MISC", "account_code": code,
            "account_id": next(a["source_id"] for a in ACCOUNTS if a["code"] == code),
            "partner_id": None, "debit": debit, "credit": credit,
            "balance": str(float(debit) - float(credit)), "currency": "USD",
            "amount_currency": "0.00", "label": "opening",
        })
    return rows


def write_mappings(directory: Path, *, approved: bool = True) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in MAPPING_ROWS.items():
        with (directory / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(FIELDNAMES))
            writer.writeheader()
            for source_key, label, target in rows:
                writer.writerow({
                    "source_key": source_key, "source_label": label, "source_context": "",
                    "target_key": target, "target_label": target,
                    "status": "approved" if approved else "pending",
                    "reviewer": "M. Hart" if approved else "",
                    "reviewed_on": "2026-01-05" if approved else "", "notes": "",
                })


def write_extract(extract_dir: Path) -> None:
    _write_jsonl(extract_dir / "accounts.jsonl", ACCOUNTS, "account.account")
    _write_jsonl(extract_dir / "journals.jsonl", JOURNALS, "account.journal")
    _write_jsonl(extract_dir / "taxes.jsonl", TAXES, "account.tax")
    _write_jsonl(extract_dir / "parties.jsonl", PARTIES, "res.partner")
    _write_jsonl(extract_dir / "products.jsonl", PRODUCTS, "product.product")
    _write_jsonl(extract_dir / "gl_lines.jsonl", gl_rows(), "account.move.line")
    _write_jsonl(extract_dir / "ar_open.jsonl", AR_OPEN, "account.move")
    _write_jsonl(extract_dir / "ap_open.jsonl", AP_OPEN, "account.move")
    _write_jsonl(extract_dir / "open_pos.jsonl", OPEN_POS, "purchase.order")
    _write_jsonl(extract_dir / "open_po_lines.jsonl", OPEN_PO_LINES, "purchase.order.line")
    _write_jsonl(extract_dir / "inventory.jsonl", INVENTORY, "stock.quant")
    _write_jsonl(extract_dir / "sales_orders.jsonl", SALES_ORDERS, "sale.order")
    _write_jsonl(extract_dir / "payments.jsonl", PAYMENTS, "account.payment")
    (extract_dir / "manifest.json").write_text(json.dumps({
        "label": LABEL, "created_at": "2026-01-05T00:00:00+00:00",
        "config": {}, "snapshot": {"adapter": "fixture"},
        "datasets": [
            {"dataset": p.stem, "rows": sum(1 for _ in p.open()), "digest": "fixture",
             "path": str(p), "started_at": "", "finished_at": "", "error": ""}
            for p in sorted(extract_dir.glob("*.jsonl"))
        ],
        "required_failed": [],
    }, indent=2), encoding="utf-8")


@pytest.fixture
def migration_root(tmp_path: Path) -> Path:
    """A complete, valid migration/ working directory."""
    root = tmp_path / "migration"
    (root / "config").mkdir(parents=True)
    (root / "config" / "migration.toml").write_text(
        f"""
[run]
label = "{LABEL}"
work_dir = "var"
cutover_date = "2026-01-01"
currency = "USD"

[source]
adapter = "odoo_sql"
system = "odoo"

[target]
adapter = "jsonl"

[reconcile]
tolerance = "0.00"
""".strip(),
        encoding="utf-8",
    )
    write_mappings(root / "config" / "mappings")
    write_extract(root / "var" / LABEL / "extract")
    return root


@pytest.fixture
def config(migration_root: Path):
    cfg = load_config(migration_root / "config" / "migration.toml", root=migration_root)
    cfg.ensure_dirs()
    return cfg
