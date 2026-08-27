"""Small shared helpers. Money is Decimal, never float."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any

CENTS = Decimal("0.01")


def money(value: Any) -> Decimal:
    """Coerce to a 2dp Decimal. Never uses float as an intermediate."""
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    elif isinstance(value, float):
        # Float input means an upstream bug; be loud about the precision loss.
        d = Decimal(repr(value))
    else:
        try:
            d = Decimal(str(value).strip().replace(",", ""))
        except InvalidOperation as exc:  # pragma: no cover - defensive
            raise ValueError(f"not a money value: {value!r}") from exc
    return d.quantize(CENTS)


def migration_ref(system: str, model: str, source_id: Any) -> str:
    """Stable identity of a source record. This is what makes loads idempotent."""
    if source_id is None or str(source_id).strip() == "":
        raise ValueError(f"missing source id for {system}:{model}")
    return f"{system}:{model}:{source_id}"


def parse_date(value: Any) -> _dt.date | None:
    if value in (None, ""):
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"):
        try:
            return _dt.datetime.strptime(text[: len(fmt) + 2].strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unparseable date: {value!r}")


def month_key(value: Any) -> str:
    d = parse_date(value)
    if d is None:
        raise ValueError("cannot derive month from empty date")
    return f"{d.year:04d}-{d.month:02d}"


def aging_bucket(due_date: Any, as_of: _dt.date) -> str:
    """Standard 4-bucket aging. Anything not yet due is 'current'."""
    due = parse_date(due_date)
    if due is None or due >= as_of:
        return "current"
    days = (as_of - due).days
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"not JSON serialisable: {type(obj).__name__}")


def dumps(obj: Any) -> str:
    return json.dumps(obj, default=json_default, sort_keys=True, ensure_ascii=False)


def content_hash(record: dict) -> str:
    """Hash of a load document's payload, used to skip unchanged rows on rerun."""
    payload = {k: v for k, v in record.items() if k not in ("_hash", "extracted_at")}
    return hashlib.sha256(dumps(payload).encode("utf-8")).hexdigest()[:16]
