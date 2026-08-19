"""Guardrails on the SQL side.

These do not need a database. They keep the extraction queries and the dataset
catalogue from drifting apart, which is the failure mode that produces a
reconciliation difference nobody can explain three rehearsals later.
"""

import re
from pathlib import Path

import pytest

from capnut_migration.sources import get_source
from capnut_migration.sources.base import DATASETS, dataset
from capnut_migration.sources.odoo_sql import SQL_DIR, load_query, render_sql

ALIAS = re.compile(r"\bAS\s+([a-z_][a-z0-9_]*)\s*(?:,|\n|$)", re.IGNORECASE)


@pytest.mark.parametrize("ds", DATASETS, ids=lambda d: d.name)
def test_every_dataset_has_an_extraction_query(ds):
    assert (SQL_DIR / f"{ds.name}.sql").exists()


@pytest.mark.parametrize("ds", DATASETS, ids=lambda d: d.name)
def test_query_aliases_match_the_declared_columns(ds):
    sql = load_query(ds.name)
    select = sql.split("FROM")[0]
    aliases = [m.group(1) for m in ALIAS.finditer(select)]
    assert aliases == list(ds.columns), (
        f"{ds.name}.sql selects {aliases} but DATASETS declares {list(ds.columns)}"
    )


@pytest.mark.parametrize("ds", DATASETS, ids=lambda d: d.name)
def test_query_is_scoped_to_a_company(ds):
    assert "%(company_id)s" in load_query(ds.name)


@pytest.mark.parametrize("ds", DATASETS, ids=lambda d: d.name)
def test_query_is_read_only(ds):
    sql = load_query(ds.name).upper()
    for verb in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE "):
        assert verb not in sql, f"{ds.name}.sql contains {verb.strip()}"


def test_transactional_queries_respect_the_as_of_date():
    for name in ("gl_lines", "ar_open", "ap_open", "open_pos", "sales_orders", "payments"):
        assert "%(as_of)s" in load_query(name), f"{name}.sql ignores the as-of date"


def test_only_posted_gl_lines_are_extracted():
    assert "am.state = 'posted'" in load_query("gl_lines")


def test_translation_token_renders_for_both_odoo_generations():
    sql = "SELECT {{TR(pt.name)}} AS name"
    assert render_sql(sql, translations_jsonb=True) == "SELECT (pt.name ->> 'en_US') AS name"
    assert render_sql(sql, translations_jsonb=False) == "SELECT pt.name AS name"


def test_unknown_dataset_is_rejected():
    with pytest.raises(ValueError):
        dataset("nope")
    with pytest.raises(ValueError):
        load_query("nope")


def test_stub_adapters_refuse_loudly(config):
    from capnut_migration.sources.base import SourceUnavailable

    for adapter in ("odoo_rpc", "csv"):
        object.__setattr__(config.source, "adapter", adapter)
        source = get_source(config)
        with pytest.raises(SourceUnavailable):
            source.snapshot_info()


def test_unknown_adapter_is_rejected(config):
    object.__setattr__(config.source, "adapter", "carrier-pigeon")
    with pytest.raises(ValueError):
        get_source(config)


def test_normalise_preserves_source_identity_and_rejects_drift():
    from capnut_migration.extract import normalise

    ds = dataset("accounts")
    row = {c: None for c in ds.columns} | {"source_id": 7, "code": "1000"}
    out = normalise(row, ds, "odoo")
    assert out["_ref"] == "odoo:account.account:7"

    with pytest.raises(ValueError):
        normalise(row | {"surprise_column": 1}, ds, "odoo")
    with pytest.raises(ValueError):
        normalise(row | {"source_id": None}, ds, "odoo")


def test_staging_ddl_covers_every_dataset():
    from capnut_migration.staging import generate_ddl

    ddl = generate_ddl()
    for ds in DATASETS:
        assert f"CREATE OR REPLACE VIEW stg.{ds.name} AS" in ddl
    assert ddl == (Path(SQL_DIR).parent / "staging_schema.sql").read_text(encoding="utf-8"), (
        "sql/staging_schema.sql is stale — run `capnut-migrate schema --write`"
    )
