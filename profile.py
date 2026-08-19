"""Data profiling — "never migrate blindly".

Answers the questions you want answered *before* writing a transform: how many
rows, how much money, what is null, which values are about to need a mapping,
and is anything in a currency we are not expecting.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from typing import Iterable

from .extract import dataset_rows, load_manifest
from .sources.base import DATASETS, dataset
from .util import money

MONEY_HINTS = ("debit", "credit", "balance", "amount", "value", "total", "residual")
# Columns whose name contains a money hint but whose content is a label, not a
# number: amount_type='percent', move_type='out_invoice', payment_type='inbound'.
MONEY_EXCLUDE = ("_type", "currency", "name", "code", "label", "state")


def _is_money(column: str) -> bool:
    if any(part in column for part in MONEY_EXCLUDE):
        return False
    return any(hint in column for hint in MONEY_HINTS)


def profile_dataset(rows: Iterable[dict], name: str, *, top: int = 10) -> dict:
    ds = dataset(name)
    count = 0
    nulls: Counter = Counter()
    sums: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    distinct: dict[str, Counter] = defaultdict(Counter)
    currencies: Counter = Counter()

    track_distinct = [c for c in ds.columns if c in (
        "account_type", "journal_type", "move_type", "state", "product_type",
        "type_tax_use", "location_name", "uom", "payment_type", "currency",
    )]

    for row in rows:
        count += 1
        for column in ds.columns:
            value = row.get(column)
            if value in (None, ""):
                nulls[column] += 1
                continue
            if _is_money(column):
                sums[column] += money(value)
            if column in track_distinct:
                distinct[column][str(value)] += 1
            if column == "currency":
                currencies[str(value)] += 1

    return {
        "dataset": name,
        "rows": count,
        "nulls": {k: v for k, v in sorted(nulls.items()) if v},
        "sums": {k: str(v) for k, v in sorted(sums.items())},
        "distinct": {k: dict(v.most_common(top)) for k, v in sorted(distinct.items())},
        "currencies": dict(currencies),
    }


def profile(config, dataset_names: Iterable[str] | None = None) -> dict:
    manifest = load_manifest(config)
    extracted = {d["dataset"] for d in manifest["datasets"] if not d["error"]}
    names = list(dataset_names) if dataset_names else [d.name for d in DATASETS]
    out = {"label": config.run.label, "datasets": []}
    for name in names:
        if name not in extracted:
            continue
        out["datasets"].append(profile_dataset(dataset_rows(config, name), name))
    out["flags"] = _flags(out["datasets"], config)
    return out


def _flags(profiles: list[dict], config) -> list[str]:
    """Things a human should look at before trusting the rest of the run."""
    flags: list[str] = []
    for prof in profiles:
        name = prof["dataset"]
        if prof["rows"] == 0 and dataset(name).required:
            flags.append(f"{name}: required dataset is empty")
        foreign = {c: n for c, n in prof["currencies"].items() if c and c != config.run.currency}
        if foreign:
            flags.append(
                f"{name}: {sum(foreign.values())} rows in non-{config.run.currency} currencies "
                f"({', '.join(sorted(foreign))}) — these are never auto-converted"
            )
        if name == "gl_lines":
            debit = prof["sums"].get("debit", "0")
            credit = prof["sums"].get("credit", "0")
            if money(debit) != money(credit):
                flags.append(
                    f"gl_lines: source is out of balance — debits {debit} vs credits {credit}"
                )
        if name == "parties" and prof["nulls"].get("ref"):
            flags.append(
                f"parties: {prof['nulls']['ref']} parties have no reference code — "
                "party mapping will have to key on source id"
            )
    return flags
