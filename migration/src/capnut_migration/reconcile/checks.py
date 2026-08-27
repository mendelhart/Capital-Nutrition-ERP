"""The reconciliation checks.

Every check answers the same question in the same shape: for some grouping key,
does the source total equal the loaded total? Differences are reported per key,
because "the trial balance is out by $412.00" is useless and "account 1200 is
out by $412.00" is a lead.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable, Sequence

from ..mappings import MappingSet, Unmapped
from ..util import aging_bucket, month_key, money

ZERO = Decimal("0.00")


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class Variance:
    key: str
    source: Decimal
    target: Decimal

    @property
    def difference(self) -> Decimal:
        return self.target - self.source

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "source": str(self.source),
            "target": str(self.target),
            "difference": str(self.difference),
        }


@dataclass
class CheckResult:
    name: str
    title: str
    status: Status
    unit: str = "money"
    source_total: Decimal = ZERO
    target_total: Decimal = ZERO
    variances: list[Variance] = field(default_factory=list)
    note: str = ""
    blocking: bool = True

    @property
    def difference(self) -> Decimal:
        return self.target_total - self.source_total

    @property
    def blocks_cutover(self) -> bool:
        return self.blocking and self.status in (Status.FAIL, Status.ERROR)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "status": self.status.value,
            "unit": self.unit,
            "source_total": str(self.source_total),
            "target_total": str(self.target_total),
            "difference": str(self.difference),
            "variance_count": len(self.variances),
            "variances": [v.as_dict() for v in self.variances],
            "note": self.note,
            "blocking": self.blocking,
        }


# ------------------------------------------------------------------ helpers
def sum_by(rows: Iterable[dict], key: Callable[[dict], str | None],
           value: Callable[[dict], Decimal]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for row in rows:
        k = key(row)
        if k is None:
            continue
        out[k] += value(row)
    return dict(out)


def compare(source: dict[str, Decimal], target: dict[str, Decimal],
            tolerance: Decimal = ZERO) -> list[Variance]:
    """Per-key differences outside tolerance, largest first."""
    variances = []
    for key in sorted(set(source) | set(target)):
        s = source.get(key, ZERO)
        t = target.get(key, ZERO)
        if abs(t - s) > tolerance:
            variances.append(Variance(key, s, t))
    variances.sort(key=lambda v: abs(v.difference), reverse=True)
    return variances


def _result(name, title, source, target, tolerance, *, unit="money", blocking=True,
            note="") -> CheckResult:
    variances = compare(source, target, tolerance)
    return CheckResult(
        name=name,
        title=title,
        status=Status.PASS if not variances else Status.FAIL,
        unit=unit,
        source_total=sum(source.values(), ZERO),
        target_total=sum(target.values(), ZERO),
        variances=variances,
        blocking=blocking,
        note=note,
    )


def _skipped(name, title, source_total=ZERO, note="", blocking=False) -> CheckResult:
    return CheckResult(name=name, title=title, status=Status.SKIPPED,
                       source_total=source_total, note=note, blocking=blocking)


def _map_account(mappings: MappingSet, code) -> str | None:
    try:
        return mappings["accounts"].resolve(code)
    except Unmapped:
        return f"UNMAPPED:{code}"


# ------------------------------------------------------------------- checks
def check_trial_balance(rows_for, docs_for, mappings, config) -> CheckResult:
    """The acceptance criterion. Source GL balance per target account must equal
    what the load produced — opening entry plus AR and AP open items."""
    source = sum_by(
        rows_for("gl_lines"),
        lambda r: _map_account(mappings, r.get("account_code")),
        lambda r: money(r.get("debit")) - money(r.get("credit")),
    )
    target: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for doc in docs_for("opening_balance"):
        target[doc["account"]] += money(doc["balance"])
    for doc in docs_for("open_ar"):
        target[_map_account(mappings, doc.get("source_account"))] += money(doc["amount_open"])
    for doc in docs_for("open_ap"):
        target[_map_account(mappings, doc.get("source_account"))] -= money(doc["amount_open"])
    return _result(
        "trial_balance", "Opening trial balance by account",
        source, dict(target), config.reconcile.tolerance,
        note="Source is every posted GL line up to the as-of date, grouped by mapped target "
             "account. Target is the opening entry plus AR/AP open items.",
    )


def _aging(rows, docs, config, doc_key="amount_open"):
    source = sum_by(
        rows,
        lambda r: aging_bucket(r.get("due_date") or r.get("date"), config.run.as_of),
        lambda r: money(r.get("amount_residual")),
    )
    target = sum_by(docs, lambda d: d["aging_bucket"], lambda d: money(d[doc_key]))
    return source, target


def check_ar_aging(rows_for, docs_for, mappings, config) -> CheckResult:
    source, target = _aging(rows_for("ar_open"), docs_for("open_ar"), config)
    return _result("ar_aging", "AR aging by bucket", source, target, config.reconcile.tolerance)


def check_ap_aging(rows_for, docs_for, mappings, config) -> CheckResult:
    source, target = _aging(rows_for("ap_open"), docs_for("open_ap"), config)
    return _result("ap_aging", "AP aging by bucket", source, target, config.reconcile.tolerance)


def check_open_pos(rows_for, docs_for, mappings, config) -> CheckResult:
    source = sum_by(
        rows_for("open_po_lines"),
        lambda r: str(r.get("order_name") or r.get("order_id")),
        lambda r: (money(r.get("qty_open")) * money(r.get("price_unit"))).quantize(Decimal("0.01")),
    )
    target = sum_by(docs_for("open_po"), lambda d: str(d["number"]), lambda d: money(d["open_value"]))
    return _result("open_pos", "Open PO value by order", source, target, config.reconcile.tolerance)


def check_open_po_count(rows_for, docs_for, mappings, config) -> CheckResult:
    source_orders = {str(r.get("source_id")) for r in rows_for("open_pos")}
    target_orders = {d["_ref"].rsplit(":", 1)[-1] for d in docs_for("open_po")}
    source = {"open purchase orders": Decimal(len(source_orders))}
    target = {"open purchase orders": Decimal(len(target_orders))}
    return _result("open_po_count", "Open PO count", source, target,
                   Decimal(config.reconcile.count_tolerance), unit="count")


def check_inventory_value(rows_for, docs_for, mappings, config) -> CheckResult:
    """Inventory is special: opening operational inventory comes from the
    approved physical count, never from Odoo (spec: Inventory). So this check
    reports the source valuation and, when a count file has been loaded,
    compares against it. It never passes silently on Odoo data alone."""
    source = sum_by(
        rows_for("inventory"),
        lambda r: str(r.get("product_code") or f"product:{r.get('product_id')}"),
        lambda r: money(r.get("value")),
    )
    counted = list(docs_for("inventory_count"))
    if not counted:
        return _skipped(
            "inventory_value", "Inventory value",
            source_total=sum(source.values(), ZERO),
            note="No approved physical count has been loaded. Opening inventory must come from "
                 "the count, so this check stays SKIPPED until count documents exist. The source "
                 "valuation above is reference only.",
            blocking=False,
        )
    target = sum_by(counted, lambda d: str(d["product"]), lambda d: money(d["value"]))
    return _result("inventory_value", "Inventory value vs approved physical count",
                   source, target, config.reconcile.tolerance,
                   note="Differences here are count-vs-system differences and need a written "
                        "explanation before cutover.")


def _reference_check(name, title, rows, docs, key, value, config, unit="money") -> CheckResult:
    source = sum_by(rows, key, value)
    if not docs:
        return _skipped(
            name, title, source_total=sum(source.values(), ZERO),
            note="Nothing of this type is in the load scope, so there is nothing to compare "
                 "against. Source totals are recorded so the figure is on the record for the "
                 "parallel run.",
        )
    target = sum_by(docs, key, value)
    return _result(name, title, source, target,
                   Decimal(config.reconcile.count_tolerance) if unit == "count"
                   else config.reconcile.tolerance, unit=unit)


def check_order_counts(rows_for, docs_for, mappings, config) -> CheckResult:
    rows = list(rows_for("sales_orders"))
    return _reference_check(
        "order_counts", "Sales order count by month", rows, list(docs_for("sales_order")),
        lambda r: month_key(r.get("date_order")), lambda r: Decimal(1), config, unit="count")


def check_sales_totals(rows_for, docs_for, mappings, config) -> CheckResult:
    rows = list(rows_for("sales_orders"))
    return _reference_check(
        "sales_totals", "Sales total by month", rows, list(docs_for("sales_order")),
        lambda r: month_key(r.get("date_order")), lambda r: money(r.get("amount_total")), config)


def check_payments(rows_for, docs_for, mappings, config) -> CheckResult:
    rows = list(rows_for("payments"))
    return _reference_check(
        "payments", "Payments and refunds by month", rows, list(docs_for("payment")),
        lambda r: f"{month_key(r.get('date'))} {r.get('payment_type')}",
        lambda r: money(r.get("amount")), config)


CHECKS: tuple[Callable, ...] = (
    check_trial_balance,
    check_ar_aging,
    check_ap_aging,
    check_open_pos,
    check_open_po_count,
    check_inventory_value,
    check_order_counts,
    check_sales_totals,
    check_payments,
)


def run_all(rows_for, docs_for, mappings: MappingSet, config,
            checks: Sequence[Callable] = CHECKS) -> list[CheckResult]:
    results = []
    for check in checks:
        name = check.__name__.removeprefix("check_")
        try:
            results.append(check(rows_for, docs_for, mappings, config))
        except Exception as exc:
            results.append(CheckResult(
                name=name, title=name.replace("_", " ").title(), status=Status.ERROR,
                note=f"{type(exc).__name__}: {exc}"))
    return results


def blocks_cutover(results: Iterable[CheckResult]) -> list[CheckResult]:
    return [r for r in results if r.blocks_cutover]
