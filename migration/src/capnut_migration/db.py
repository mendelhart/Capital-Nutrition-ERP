"""Minimal PostgreSQL access. psycopg is imported lazily so the pure-python
parts of the toolkit (mappings, transforms, reconciliation) run and test
without a database or a driver installed.
"""

from __future__ import annotations

from typing import Any, Iterator


class DriverMissing(RuntimeError):
    pass


def _psycopg():
    try:
        import psycopg  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise DriverMissing(
            "psycopg is not installed. Install it with:\n"
            "    pip install 'psycopg[binary]'\n"
            "or run:  pip install -e 'migration[postgres]'"
        ) from exc
    return psycopg


def connect(dsn: str, *, readonly: bool = False):
    """Open a connection. readonly=True is used for every source connection so a
    misdirected DSN cannot write to the Odoo snapshot."""
    if not dsn:
        raise ValueError("empty DSN")
    psycopg = _psycopg()
    conn = psycopg.connect(dsn, autocommit=True)
    if readonly:
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
    return conn


def query(conn, sql: str, params: dict | None = None) -> Iterator[dict[str, Any]]:
    """Stream rows as dicts. Server-side cursor keeps large extracts off-heap."""
    psycopg = _psycopg()
    row_factory = psycopg.rows.dict_row  # type: ignore[attr-defined]
    with conn.cursor(name="capnut_extract", row_factory=row_factory) as cur:
        cur.itersize = 5000
        cur.execute(sql, params or {})
        yield from cur


def execute(conn, sql: str, params: dict | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params or {})
