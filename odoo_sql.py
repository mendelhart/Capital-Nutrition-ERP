"""Read-only SQL extraction from a restored Odoo snapshot.

This is the recommended adapter: a pg_dump restored to a local or staging
PostgreSQL gives a frozen, repeatable source that cannot be affected by
activity in production during a rehearsal.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

from .. import db
from .base import DATASETS, SourceAdapter, dataset

SQL_DIR = Path(__file__).resolve().parents[3] / "sql" / "extract"

TR_TOKEN = re.compile(r"\{\{TR\(([^)]+)\)\}\}")


def render_sql(sql: str, *, translations_jsonb: bool) -> str:
    """Resolve version tokens.

    Odoo 16 turned translatable char columns into jsonb. The same query text
    therefore has to read either ``pt.name`` or ``pt.name ->> 'en_US'``.
    """
    if translations_jsonb:
        return TR_TOKEN.sub(lambda m: f"({m.group(1)} ->> 'en_US')", sql)
    return TR_TOKEN.sub(lambda m: m.group(1), sql)


def load_query(dataset_name: str, *, sql_dir: Path | None = None) -> str:
    dataset(dataset_name)  # validates the name
    path = (sql_dir or SQL_DIR) / f"{dataset_name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"no extraction query for {dataset_name!r}: {path}")
    return path.read_text(encoding="utf-8")


class OdooSqlSource(SourceAdapter):
    name = "odoo_sql"

    def __init__(self, config) -> None:
        super().__init__(config)
        self._conn = None
        self._probe: dict[str, Any] | None = None

    # -- connection -----------------------------------------------------
    @property
    def conn(self):
        if self._conn is None:
            self._conn = db.connect(self.config.source.dsn, readonly=True)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- probing --------------------------------------------------------
    def probe(self) -> dict[str, Any]:
        """Inspect the snapshot so we know which SQL variant applies, and warn
        early about anything the queries reference that is missing."""
        if self._probe is not None:
            return self._probe

        with self.conn.cursor() as cur:
            cur.execute("SELECT latest_version FROM ir_module_module WHERE name = 'base'")
            row = cur.fetchone()
            odoo_version = row[0] if row else "unknown"

            cur.execute(
                """
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'product_template' AND column_name = 'name'
                """
            )
            row = cur.fetchone()
            name_type = row[0] if row else "unknown"

            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'account_account' AND column_name IN ('account_type','user_type_id')
                """
            )
            account_type_cols = sorted(r[0] for r in cur.fetchall())

            cur.execute(
                """
                SELECT id, name, currency_id FROM res_company
                ORDER BY id
                """
            )
            companies = [{"id": r[0], "name": r[1], "currency_id": r[2]} for r in cur.fetchall()]

            cur.execute("SELECT current_database(), now()")
            dbname, now = cur.fetchone()

        self._probe = {
            "database": dbname,
            "probed_at": now.isoformat() if hasattr(now, "isoformat") else str(now),
            "odoo_version": odoo_version,
            "translations_jsonb": name_type == "jsonb",
            "account_type_columns": account_type_cols,
            "companies": companies,
            "warnings": self._warnings(odoo_version, name_type, account_type_cols),
        }
        return self._probe

    @staticmethod
    def _warnings(version: str, name_type: str, account_type_cols: list[str]) -> list[str]:
        warnings: list[str] = []
        if "user_type_id" in account_type_cols and "account_type" not in account_type_cols:
            warnings.append(
                "This snapshot predates Odoo 15: account_account has user_type_id, not "
                "account_type. ar_open.sql / ap_open.sql must be edited to join "
                "account_account_type on internal_type."
            )
        if name_type not in ("jsonb", "character varying", "text"):
            warnings.append(f"Unexpected product_template.name type: {name_type!r}")
        if version.startswith(("11.", "12.", "13.")):
            warnings.append(
                f"Odoo {version}: account_payment has no move_id; payments.sql needs rework."
            )
        return warnings

    # -- SourceAdapter --------------------------------------------------
    def snapshot_info(self) -> dict[str, Any]:
        info = dict(self.probe())
        info["adapter"] = self.name
        info["company_id"] = self.config.source.company_id
        return info

    def fetch(self, dataset_name: str) -> Iterator[dict[str, Any]]:
        probe = self.probe()
        sql = render_sql(
            load_query(dataset_name), translations_jsonb=probe["translations_jsonb"]
        )
        params = {
            "company_id": self.config.source.company_id,
            "as_of": self.config.run.as_of,
        }
        yield from db.query(self.conn, sql, params)

    def available(self) -> tuple[str, ...]:
        return tuple(d.name for d in DATASETS if (SQL_DIR / f"{d.name}.sql").exists())
