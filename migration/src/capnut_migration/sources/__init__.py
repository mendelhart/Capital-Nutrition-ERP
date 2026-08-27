"""Source adapters.

The rest of the toolkit only ever sees a ``SourceAdapter``. Which system the
data actually comes from is a configuration choice, so the extraction decision
(restored snapshot vs live RPC vs hand exports) can change without touching
staging, mapping, transform, load or reconciliation.
"""

from __future__ import annotations

from .base import DATASETS, Dataset, SourceAdapter, SourceUnavailable

_REGISTRY: dict[str, str] = {
    "odoo_sql": "capnut_migration.sources.odoo_sql:OdooSqlSource",
    "odoo_rpc": "capnut_migration.sources.odoo_rpc:OdooRpcSource",
    "csv": "capnut_migration.sources.csv_files:CsvSource",
}


def get_source(config) -> SourceAdapter:
    """Instantiate the adapter named by config.source.adapter."""
    import importlib

    name = config.source.adapter
    if name not in _REGISTRY:
        raise ValueError(
            f"unknown source adapter {name!r}; expected one of {sorted(_REGISTRY)}"
        )
    module_name, _, class_name = _REGISTRY[name].partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)(config)


__all__ = [
    "DATASETS",
    "Dataset",
    "SourceAdapter",
    "SourceUnavailable",
    "get_source",
    "register",
]


def register(name: str, dotted_path: str) -> None:
    _REGISTRY[name] = dotted_path
