"""CSV extraction — NOT IMPLEMENTED.

Stub for the "you export from the Odoo UI" path. The reading half is trivial;
what makes this adapter unsafe by default is that nothing guarantees two
exports were taken at the same instant, which breaks reconciliation in ways
that look like migration bugs.

If this is ever enabled, it must require a manifest file recording, per CSV:
export timestamp, Odoo model, filter/domain used, and row count — and refuse to
run when those timestamps disagree by more than a threshold.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator

from .base import SourceAdapter, SourceUnavailable, dataset

_MESSAGE = (
    "The csv source adapter is not implemented yet.\n"
    "It also needs an export manifest before it can be trusted — see the module "
    "docstring in capnut_migration/sources/csv_files.py."
)


class CsvSource(SourceAdapter):
    name = "csv"

    def snapshot_info(self) -> dict[str, Any]:
        raise SourceUnavailable(_MESSAGE)

    def fetch(self, dataset_name: str) -> Iterator[dict[str, Any]]:
        raise SourceUnavailable(_MESSAGE)

    # Kept so the eventual implementation has an obvious starting point.
    def _read(self, dataset_name: str) -> Iterator[dict[str, Any]]:  # pragma: no cover
        dataset(dataset_name)
        path = Path(self.config.source.csv_dir) / f"{dataset_name}.csv"
        with path.open(newline="", encoding="utf-8-sig") as fh:
            yield from csv.DictReader(fh)
