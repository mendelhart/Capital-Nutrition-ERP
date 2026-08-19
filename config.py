"""Configuration loading.

Credentials live in migration/config/migration.toml (gitignored) or in the
environment. Nothing secret is ever written back to disk by this toolkit.
"""

from __future__ import annotations

import datetime as _dt
import os
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .util import parse_date

ENV_OVERRIDES = {
    ("source", "dsn"): "CAPNUT_SOURCE_DSN",
    ("source", "url"): "CAPNUT_ODOO_URL",
    ("source", "db"): "CAPNUT_ODOO_DB",
    ("source", "user"): "CAPNUT_ODOO_USER",
    ("source", "password"): "CAPNUT_ODOO_PASSWORD",
    ("target", "dsn"): "CAPNUT_TARGET_DSN",
}

DEFAULT_CONFIG_PATH = Path("config/migration.toml")


@dataclass(frozen=True)
class RunConfig:
    label: str = "rehearsal"
    work_dir: Path = Path("var")
    cutover_date: _dt.date = _dt.date.today()
    currency: str = "USD"

    @property
    def as_of(self) -> _dt.date:
        """Balances are struck at end of the day before cutover."""
        return self.cutover_date - _dt.timedelta(days=1)


@dataclass(frozen=True)
class SourceConfig:
    adapter: str = "odoo_sql"
    system: str = "odoo"
    dsn: str = ""
    company_id: int | None = None
    url: str = ""
    db: str = ""
    user: str = ""
    password: str = ""
    csv_dir: Path = Path("var/source_csv")


@dataclass(frozen=True)
class TargetConfig:
    adapter: str = "jsonl"
    dsn: str = ""


@dataclass(frozen=True)
class ReconcileConfig:
    tolerance: Decimal = Decimal("0.00")
    count_tolerance: int = 0
    detail_rows: int = 25


@dataclass(frozen=True)
class Config:
    run: RunConfig = field(default_factory=RunConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    target: TargetConfig = field(default_factory=TargetConfig)
    reconcile: ReconcileConfig = field(default_factory=ReconcileConfig)
    root: Path = Path(".")

    # --- derived paths (all under run.work_dir, all gitignored) ---
    @property
    def work(self) -> Path:
        return self.root / self.run.work_dir / self.run.label

    @property
    def extract_dir(self) -> Path:
        return self.work / "extract"

    @property
    def load_dir(self) -> Path:
        return self.work / "load"

    @property
    def report_dir(self) -> Path:
        return self.work / "reports"

    @property
    def mapping_dir(self) -> Path:
        return self.root / "config" / "mappings"

    def ensure_dirs(self) -> None:
        for path in (self.extract_dir, self.load_dir, self.report_dir):
            path.mkdir(parents=True, exist_ok=True)

    def redacted(self) -> dict:
        """Safe to print or write into a manifest."""
        def scrub(dsn: str) -> str:
            if "@" not in dsn:
                return dsn
            head, _, tail = dsn.rpartition("@")
            scheme, _, _creds = head.partition("://")
            return f"{scheme}://***@{tail}"

        return {
            "label": self.run.label,
            "cutover_date": self.run.cutover_date.isoformat(),
            "as_of": self.run.as_of.isoformat(),
            "currency": self.run.currency,
            "source_adapter": self.source.adapter,
            "source_system": self.source.system,
            "source_dsn": scrub(self.source.dsn),
            "source_company_id": self.source.company_id,
            "target_adapter": self.target.adapter,
            "target_dsn": scrub(self.target.dsn),
            "tolerance": str(self.reconcile.tolerance),
        }


def _apply_env(data: dict) -> dict:
    for (section, key), env_name in ENV_OVERRIDES.items():
        value = os.environ.get(env_name)
        if value:
            data.setdefault(section, {})[key] = value
    return data


def load_config(path: str | Path | None = None, root: str | Path | None = None) -> Config:
    root_path = Path(root) if root else Path.cwd()
    cfg_path = Path(path) if path else root_path / DEFAULT_CONFIG_PATH
    data: dict = {}
    if cfg_path.exists():
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    elif path is not None:
        raise FileNotFoundError(f"config not found: {cfg_path}")
    data = _apply_env(data)

    run_raw = data.get("run", {})
    src_raw = data.get("source", {})
    tgt_raw = data.get("target", {})
    rec_raw = data.get("reconcile", {})

    cutover = parse_date(run_raw.get("cutover_date")) or _dt.date.today()
    run = RunConfig(
        label=str(run_raw.get("label", "rehearsal")),
        work_dir=Path(run_raw.get("work_dir", "var")),
        cutover_date=cutover,
        currency=str(run_raw.get("currency", "USD")),
    )
    source = SourceConfig(
        adapter=str(src_raw.get("adapter", "odoo_sql")),
        system=str(src_raw.get("system", "odoo")),
        dsn=str(src_raw.get("dsn", "")),
        company_id=src_raw.get("company_id"),
        url=str(src_raw.get("url", "")),
        db=str(src_raw.get("db", "")),
        user=str(src_raw.get("user", "")),
        password=str(src_raw.get("password", "")),
        csv_dir=Path(src_raw.get("csv_dir", "var/source_csv")),
    )
    target = TargetConfig(
        adapter=str(tgt_raw.get("adapter", "jsonl")),
        dsn=str(tgt_raw.get("dsn", "")),
    )
    reconcile = ReconcileConfig(
        tolerance=Decimal(str(rec_raw.get("tolerance", "0.00"))),
        count_tolerance=int(rec_raw.get("count_tolerance", 0)),
        detail_rows=int(rec_raw.get("detail_rows", 25)),
    )
    return Config(run=run, source=source, target=target, reconcile=reconcile, root=root_path)
