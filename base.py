"""The source contract, and the catalogue of datasets the migration needs."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Iterator


class SourceUnavailable(RuntimeError):
    """Raised by adapters that are declared but not implemented yet."""


@dataclass(frozen=True)
class Dataset:
    """One extractable table of source records.

    ``key_field``  - the source primary key; preserved end to end.
    ``model``      - the source model name, used to build migration_ref.
    ``required``   - datasets the acceptance criteria depend on.
    """

    name: str
    model: str
    description: str
    key_field: str = "source_id"
    required: bool = True
    columns: tuple[str, ...] = field(default_factory=tuple)


# The catalogue is deliberately explicit. Adding a dataset means adding an
# extraction query, a staging table and (usually) a reconciliation check.
DATASETS: tuple[Dataset, ...] = (
    Dataset("accounts", "account.account", "Chart of accounts",
            columns=("source_id", "code", "name", "account_type", "reconcile", "deprecated", "currency")),
    Dataset("journals", "account.journal", "Journals",
            columns=("source_id", "code", "name", "journal_type", "currency")),
    Dataset("taxes", "account.tax", "Taxes",
            columns=("source_id", "name", "amount", "amount_type", "type_tax_use", "active")),
    Dataset("parties", "res.partner", "Customers and vendors",
            columns=("source_id", "ref", "name", "is_company", "parent_id", "customer_rank",
                     "supplier_rank", "vat", "email", "phone", "street", "street2", "city",
                     "state_code", "zip", "country_code", "active")),
    Dataset("products", "product.product", "Products (variants)",
            columns=("source_id", "template_id", "default_code", "barcode", "name", "product_type",
                     "uom", "list_price", "standard_price", "categ_name", "active")),
    Dataset("gl_lines", "account.move.line", "Posted GL lines up to the as-of date",
            columns=("source_id", "move_id", "move_name", "date", "journal_code", "account_code",
                     "account_id", "partner_id", "debit", "credit", "balance", "currency",
                     "amount_currency", "label")),
    Dataset("ar_open", "account.move", "Open customer invoices and credit notes",
            columns=("source_id", "number", "move_type", "partner_id", "partner_ref", "date",
                     "due_date", "currency", "amount_total", "amount_residual", "account_code", "state")),
    Dataset("ap_open", "account.move", "Open vendor bills and refunds",
            columns=("source_id", "number", "move_type", "partner_id", "partner_ref", "date",
                     "due_date", "currency", "amount_total", "amount_residual", "account_code", "state")),
    Dataset("open_pos", "purchase.order", "Approved purchase orders not fully received/billed",
            columns=("source_id", "name", "partner_id", "date_order", "state", "currency",
                     "amount_untaxed", "amount_total")),
    Dataset("open_po_lines", "purchase.order.line", "Lines of the approved open POs",
            columns=("source_id", "order_id", "order_name", "product_id", "product_code",
                     "description", "qty_ordered", "qty_received", "qty_invoiced", "qty_open",
                     "price_unit", "line_total", "uom", "date_planned")),
    Dataset("inventory", "stock.quant", "On-hand quantity and value by product and location",
            columns=("source_id", "product_id", "product_code", "location_id", "location_name",
                     "internal", "quantity", "unit_cost", "value")),
    Dataset("sales_orders", "sale.order", "Sales orders (history and reference)", required=False,
            columns=("source_id", "name", "partner_id", "date_order", "state", "currency",
                     "amount_untaxed", "amount_tax", "amount_total")),
    Dataset("payments", "account.payment", "Customer and vendor payments", required=False,
            columns=("source_id", "name", "payment_type", "partner_id", "date", "currency",
                     "amount", "journal_code", "state")),
)

DATASETS_BY_NAME = {d.name: d for d in DATASETS}


def dataset(name: str) -> Dataset:
    try:
        return DATASETS_BY_NAME[name]
    except KeyError:
        raise ValueError(
            f"unknown dataset {name!r}; expected one of {sorted(DATASETS_BY_NAME)}"
        ) from None


class SourceAdapter(abc.ABC):
    """Read-only access to the source system.

    Implementations must never write to the source. ``snapshot_info`` pins the
    extraction to one identifiable snapshot so a rehearsal can be repeated
    against exactly the same data.
    """

    name: str = "abstract"

    def __init__(self, config) -> None:
        self.config = config

    @abc.abstractmethod
    def snapshot_info(self) -> dict[str, Any]:
        """Identify the snapshot: database, size/version markers, timestamp."""

    @abc.abstractmethod
    def fetch(self, dataset_name: str) -> Iterator[dict[str, Any]]:
        """Yield raw source rows for one dataset."""

    def available(self) -> tuple[str, ...]:
        return tuple(d.name for d in DATASETS)

    def close(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()
