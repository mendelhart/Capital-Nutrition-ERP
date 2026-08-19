"""Transforms: extracted source rows -> load documents.

A load document is a dict with:
    _ref    migration ref, the idempotency key
    _type   document type (opening_balance, open_ar, open_ap, open_po)
    _hash   content hash, so a rerun can tell "unchanged" from "updated"
plus the payload.

What is loaded (spec: Financial opening):
    opening balances, open AR, open AP, approved open POs, reference data.

Deliberate accounting decision, encoded here and asserted by the balance check:
the opening journal entry carries every account EXCEPT the AR and AP control
accounts. AR and AP arrive as open items — invoice by invoice — which post to
those control accounts themselves. Putting both in would double the receivable
and payable balances.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Sequence

from ..mappings import MappingSet, Unmapped
from ..util import aging_bucket, content_hash, migration_ref, money, parse_date

RECEIVABLE_TYPES = {"asset_receivable", "receivable"}
PAYABLE_TYPES = {"liability_payable", "payable"}

LoadDocument = dict


@dataclass
class TransformIssue:
    doc_type: str
    ref: str
    problem: str

    def __str__(self) -> str:
        return f"[{self.doc_type}] {self.ref}: {self.problem}"


@dataclass
class TransformResult:
    documents: list[LoadDocument] = field(default_factory=list)
    issues: list[TransformIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def extend(self, other: "TransformResult") -> "TransformResult":
        self.documents.extend(other.documents)
        self.issues.extend(other.issues)
        return self

    def by_type(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for doc in self.documents:
            counts[doc["_type"]] += 1
        return dict(counts)


def _finish(doc: LoadDocument) -> LoadDocument:
    doc["_hash"] = content_hash(doc)
    return doc


def classify_accounts(accounts: Iterable[dict]) -> dict[str, str]:
    """account_code -> 'receivable' | 'payable' | 'other'."""
    out: dict[str, str] = {}
    for row in accounts:
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        atype = str(row.get("account_type") or "").strip()
        if atype in RECEIVABLE_TYPES:
            out[code] = "receivable"
        elif atype in PAYABLE_TYPES:
            out[code] = "payable"
        else:
            out[code] = "other"
    return out


# ---------------------------------------------------------------- opening TB
def build_opening_balances(
    gl_lines: Iterable[dict],
    accounts: Sequence[dict],
    mappings: MappingSet,
    config,
) -> TransformResult:
    result = TransformResult()
    kinds = classify_accounts(accounts)
    table = mappings["accounts"]

    balances: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    control: dict[str, Decimal] = {"receivable": Decimal("0.00"), "payable": Decimal("0.00")}
    unknown: set[str] = set()

    for line in gl_lines:
        code = str(line.get("account_code") or "").strip()
        if not code:
            result.issues.append(TransformIssue(
                "opening_balance", str(line.get("_ref", "")), "GL line with no account code"))
            continue
        amount = money(line.get("debit")) - money(line.get("credit"))
        kind = kinds.get(code)
        if kind is None:
            unknown.add(code)
            continue
        if kind in control:
            control[kind] += amount
            continue
        balances[code] += amount

    for code in sorted(unknown):
        result.issues.append(TransformIssue(
            "opening_balance", code, "GL line references an account missing from the accounts extract"))

    total = Decimal("0.00")
    for code in sorted(balances):
        amount = balances[code]
        if amount == 0:
            continue  # a zero opening balance is not an accounting fact worth loading
        try:
            target = table.resolve(code)
        except Unmapped as exc:
            result.issues.append(TransformIssue("opening_balance", code, str(exc)))
            continue
        if target is None:
            result.issues.append(TransformIssue(
                "opening_balance", code,
                f"account is excluded from the mapping but carries a balance of {amount}"))
            continue
        total += amount
        result.documents.append(_finish({
            "_ref": migration_ref(config.source.system, "opening.balance", code),
            "_type": "opening_balance",
            "date": config.run.as_of.isoformat(),
            "source_account": code,
            "account": target,
            "currency": config.run.currency,
            "debit": str(amount if amount > 0 else Decimal("0.00")),
            "credit": str(-amount if amount < 0 else Decimal("0.00")),
            "balance": str(amount),
            "description": f"Opening balance {config.run.as_of.isoformat()}",
        }))

    # The opening entry only balances once AR and AP open items are added back.
    residual = total + control["receivable"] + control["payable"]
    if residual != 0:
        result.issues.append(TransformIssue(
            "opening_balance", "TOTAL",
            f"opening entry does not balance: non-control {total} + AR control "
            f"{control['receivable']} + AP control {control['payable']} = {residual}"))
    result.documents.append(_finish({
        "_ref": migration_ref(config.source.system, "opening.control", "totals"),
        "_type": "opening_control",
        "date": config.run.as_of.isoformat(),
        "non_control_total": str(total),
        "ar_control_total": str(control["receivable"]),
        "ap_control_total": str(control["payable"]),
        "note": "AR and AP control balances are created by the open-item loads, not by the opening entry.",
    }))
    return result


# ------------------------------------------------------------------- open AR
def _open_item(row, mappings, config, *, doc_type, party_table, sign_note):
    party_id = row.get("partner_id")
    if party_id in (None, ""):
        raise Unmapped(f"{doc_type}: {row.get('number')} has no partner")
    party = mappings[party_table].resolve(party_id)
    if party is None:
        raise Unmapped(f"{doc_type}: party {party_id} is excluded but has an open balance")
    residual = money(row.get("amount_residual"))
    due = row.get("due_date") or row.get("date")
    doc = {
        "_ref": migration_ref(config.source.system, f"{doc_type}.item", row["source_id"]),
        "_type": doc_type,
        "number": row.get("number"),
        "party": party,
        "source_party_id": str(party_id),
        "date": (parse_date(row.get("date")) or config.run.as_of).isoformat(),
        "due_date": (parse_date(due) or config.run.as_of).isoformat(),
        "currency": row.get("currency") or config.run.currency,
        "amount_total": str(money(row.get("amount_total"))),
        "amount_open": str(residual),
        "aging_bucket": aging_bucket(due, config.run.as_of),
        "source_account": row.get("account_code"),
        "move_type": row.get("move_type"),
        "note": sign_note,
    }
    return doc, residual


def build_open_ar(rows: Iterable[dict], mappings: MappingSet, config) -> TransformResult:
    result = TransformResult()
    for row in rows:
        try:
            doc, residual = _open_item(
                row, mappings, config, doc_type="open_ar", party_table="parties",
                sign_note="positive = customer owes us")
        except Unmapped as exc:
            result.issues.append(TransformIssue("open_ar", str(row.get("source_id")), str(exc)))
            continue
        if residual == 0:
            continue
        result.documents.append(_finish(doc))
    return result


def build_open_ap(rows: Iterable[dict], mappings: MappingSet, config) -> TransformResult:
    result = TransformResult()
    for row in rows:
        try:
            doc, residual = _open_item(
                row, mappings, config, doc_type="open_ap", party_table="vendors",
                sign_note="positive = we owe the vendor")
        except Unmapped as exc:
            result.issues.append(TransformIssue("open_ap", str(row.get("source_id")), str(exc)))
            continue
        if residual == 0:
            continue
        result.documents.append(_finish(doc))
    return result


# ------------------------------------------------------------------ open POs
def build_open_pos(
    orders: Iterable[dict],
    lines: Iterable[dict],
    mappings: MappingSet,
    config,
) -> TransformResult:
    result = TransformResult()
    lines_by_order: dict[str, list[dict]] = defaultdict(list)
    for line in lines:
        lines_by_order[str(line.get("order_id"))].append(line)

    for order in orders:
        order_id = str(order.get("source_id"))
        order_lines = lines_by_order.get(order_id, [])
        if not order_lines:
            result.issues.append(TransformIssue(
                "open_po", order_id, "approved open PO has no open lines in the extract"))
            continue
        try:
            party = mappings["vendors"].resolve(order.get("partner_id"))
        except Unmapped as exc:
            result.issues.append(TransformIssue("open_po", order_id, str(exc)))
            continue
        if party is None:
            result.issues.append(TransformIssue(
                "open_po", order_id, "vendor is excluded but has an approved open PO"))
            continue

        doc_lines = []
        failed = False
        open_value = Decimal("0.00")
        for line in order_lines:
            code = line.get("product_code")
            try:
                product = mappings["products"].resolve(code) if code else None
                uom = mappings["uom"].resolve(line.get("uom")) if line.get("uom") else None
            except Unmapped as exc:
                result.issues.append(TransformIssue("open_po", f"{order_id}/{line.get('source_id')}", str(exc)))
                failed = True
                continue
            qty_open = money(line.get("qty_open"))
            price = money(line.get("price_unit"))
            line_value = (qty_open * price).quantize(Decimal("0.01"))
            open_value += line_value
            doc_lines.append({
                "source_line_id": str(line.get("source_id")),
                "product": product,
                "source_product_code": code,
                "description": line.get("description"),
                "quantity_open": str(qty_open),
                "quantity_ordered": str(money(line.get("qty_ordered"))),
                "quantity_received": str(money(line.get("qty_received"))),
                "unit_price": str(price),
                "line_open_value": str(line_value),
                "uom": uom,
                "source_uom": line.get("uom"),
                "date_planned": (parse_date(line.get("date_planned")) or config.run.as_of).isoformat(),
            })
        if failed:
            continue
        result.documents.append(_finish({
            "_ref": migration_ref(config.source.system, "purchase.order", order_id),
            "_type": "open_po",
            "number": order.get("name"),
            "party": party,
            "source_party_id": str(order.get("partner_id")),
            "date": (parse_date(order.get("date_order")) or config.run.as_of).isoformat(),
            "currency": order.get("currency") or config.run.currency,
            "source_state": order.get("state"),
            "open_value": str(open_value),
            "lines": doc_lines,
        }))
    return result


def build_all(config, mappings: MappingSet, rows_for) -> TransformResult:
    """rows_for(dataset_name) -> iterable of extracted rows."""
    accounts = list(rows_for("accounts"))
    result = TransformResult()
    result.extend(build_opening_balances(rows_for("gl_lines"), accounts, mappings, config))
    result.extend(build_open_ar(rows_for("ar_open"), mappings, config))
    result.extend(build_open_ap(rows_for("ap_open"), mappings, config))
    result.extend(build_open_pos(rows_for("open_pos"), rows_for("open_po_lines"), mappings, config))
    return result
