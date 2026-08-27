import datetime as dt
from decimal import Decimal

import pytest

from capnut_migration.util import (
    aging_bucket,
    content_hash,
    migration_ref,
    money,
    month_key,
    parse_date,
)


def test_money_is_exact():
    assert money("1234.567") == Decimal("1234.57")
    assert money("1,000.00") == Decimal("1000.00")
    assert money(None) == Decimal("0.00")
    # the classic float trap the whole toolkit exists to avoid
    assert money("0.1") + money("0.2") == money("0.3")


def test_money_rejects_junk():
    with pytest.raises(ValueError):
        money("not a number")


def test_migration_ref_requires_a_source_id():
    assert migration_ref("odoo", "account.move", 7) == "odoo:account.move:7"
    with pytest.raises(ValueError):
        migration_ref("odoo", "account.move", None)


@pytest.mark.parametrize(
    "due,expected",
    [
        ("2026-01-15", "current"),
        ("2025-12-31", "current"),
        ("2025-12-15", "1-30"),
        ("2025-11-15", "31-60"),
        ("2025-10-15", "61-90"),
        ("2025-06-15", "90+"),
    ],
)
def test_aging_buckets(due, expected):
    assert aging_bucket(due, dt.date(2025, 12, 31)) == expected


def test_month_key_and_dates():
    assert month_key("2025-03-14 10:00:00") == "2025-03"
    assert parse_date("2025-03-14") == dt.date(2025, 3, 14)
    assert parse_date(None) is None


def test_content_hash_ignores_volatile_fields():
    a = {"_ref": "x", "amount": "1.00", "extracted_at": "2026-01-01"}
    b = {"_ref": "x", "amount": "1.00", "extracted_at": "2026-06-01"}
    c = {"_ref": "x", "amount": "2.00", "extracted_at": "2026-01-01"}
    assert content_hash(a) == content_hash(b)
    assert content_hash(a) != content_hash(c)
