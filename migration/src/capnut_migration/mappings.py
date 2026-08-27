"""Explicit mapping tables.

Spec: "Use explicit mappings" and "Accountant reviews accounting mappings."

So: no fuzzy matching, no fallback to the source value, no "if it looks like a
GL code, use it". Every source value that the migration touches must appear in
a reviewable CSV with an explicit decision, and accounting mappings must carry
a reviewer's name before a load is allowed to run.

Workflow:

    capnut-migrate map stub     # extract distinct source values -> pending rows
    (accountant / operator edits the CSVs, sets target_key and status)
    capnut-migrate map check    # blocks on anything pending or invalid
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

FIELDNAMES = (
    "source_key",
    "source_label",
    "source_context",
    "target_key",
    "target_label",
    "status",
    "reviewer",
    "reviewed_on",
    "notes",
)

STATUS_APPROVED = "approved"
STATUS_PENDING = "pending"
STATUS_EXCLUDED = "excluded"
VALID_STATUSES = (STATUS_APPROVED, STATUS_PENDING, STATUS_EXCLUDED)


class Unmapped(KeyError):
    """A source value reached a transform without an approved mapping."""


@dataclass(frozen=True)
class MappingSpec:
    """Declares one mapping table."""

    name: str
    description: str
    source_dataset: str
    source_key_field: str
    source_label_field: str = "name"
    requires_accountant: bool = False


MAPPING_SPECS: tuple[MappingSpec, ...] = (
    MappingSpec("accounts", "Odoo GL account -> Tryton account", "accounts", "code",
                requires_accountant=True),
    MappingSpec("journals", "Odoo journal -> Tryton journal", "journals", "code",
                requires_accountant=True),
    MappingSpec("taxes", "Odoo tax -> Tryton tax / provider tax code", "taxes", "source_id",
                requires_accountant=True),
    MappingSpec("products", "Odoo product -> Tryton product", "products", "default_code"),
    MappingSpec("parties", "Odoo customer -> Tryton party", "parties", "source_id"),
    MappingSpec("vendors", "Odoo vendor -> Tryton party", "parties", "source_id"),
    MappingSpec("uom", "Odoo unit of measure -> Tryton UoM", "products", "uom", "uom"),
)

SPECS_BY_NAME = {s.name: s for s in MAPPING_SPECS}


@dataclass
class MappingRow:
    source_key: str
    source_label: str = ""
    source_context: str = ""
    target_key: str = ""
    target_label: str = ""
    status: str = STATUS_PENDING
    reviewer: str = ""
    reviewed_on: str = ""
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in FIELDNAMES}


@dataclass
class Issue:
    table: str
    source_key: str
    problem: str

    def __str__(self) -> str:
        return f"[{self.table}] {self.source_key or '(blank)'}: {self.problem}"


@dataclass
class MappingTable:
    spec: MappingSpec
    rows: dict[str, MappingRow] = field(default_factory=dict)
    path: Path | None = None

    # -- io -------------------------------------------------------------
    @classmethod
    def load(cls, spec: MappingSpec, directory: Path) -> "MappingTable":
        path = Path(directory) / f"{spec.name}.csv"
        table = cls(spec=spec, path=path)
        if not path.exists():
            return table
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for raw in csv.DictReader(fh):
                row = MappingRow(
                    **{k: (raw.get(k) or "").strip() for k in FIELDNAMES}
                )
                if not row.source_key:
                    continue
                table.rows[row.source_key] = row
        return table

    def save(self, path: Path | None = None) -> Path:
        target = Path(path or self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(FIELDNAMES))
            writer.writeheader()
            for key in sorted(self.rows, key=_sort_key):
                writer.writerow(self.rows[key].as_dict())
        return target

    # -- editing --------------------------------------------------------
    def add_pending(self, source_key: str, label: str = "", context: str = "") -> bool:
        """Add a row for an unseen source value. Existing rows are never
        overwritten — a stub run must not silently undo a review."""
        key = str(source_key).strip()
        if not key or key in self.rows:
            return False
        self.rows[key] = MappingRow(
            source_key=key, source_label=str(label or ""), source_context=str(context or "")
        )
        return True

    # -- use ------------------------------------------------------------
    def resolve(self, source_key) -> str | None:
        """Return the target key. None means 'deliberately excluded'.

        Raises Unmapped for anything unknown or unapproved: the load stops
        rather than inventing a destination.
        """
        key = str(source_key).strip()
        row = self.rows.get(key)
        if row is None:
            raise Unmapped(f"{self.spec.name}: no mapping row for {key!r}")
        if row.status == STATUS_EXCLUDED:
            return None
        if row.status != STATUS_APPROVED:
            raise Unmapped(f"{self.spec.name}: mapping for {key!r} is {row.status!r}, not approved")
        if not row.target_key:
            raise Unmapped(f"{self.spec.name}: mapping for {key!r} is approved but has no target_key")
        return row.target_key

    def is_excluded(self, source_key) -> bool:
        row = self.rows.get(str(source_key).strip())
        return bool(row and row.status == STATUS_EXCLUDED)

    # -- review ---------------------------------------------------------
    def validate(self) -> list[Issue]:
        issues: list[Issue] = []
        seen_targets: dict[str, str] = {}
        for key, row in self.rows.items():
            if row.status not in VALID_STATUSES:
                issues.append(Issue(self.spec.name, key,
                                    f"status {row.status!r} is not one of {VALID_STATUSES}"))
            if row.status == STATUS_PENDING:
                issues.append(Issue(self.spec.name, key, "unreviewed (status=pending)"))
            if row.status == STATUS_APPROVED:
                if not row.target_key:
                    issues.append(Issue(self.spec.name, key, "approved with empty target_key"))
                if self.spec.requires_accountant and not row.reviewer:
                    issues.append(Issue(self.spec.name, key,
                                        "accounting mapping approved without a reviewer name"))
                if row.target_key in seen_targets and self.spec.name in ("accounts", "journals"):
                    issues.append(Issue(
                        self.spec.name, key,
                        f"target {row.target_key!r} already used by {seen_targets[row.target_key]!r}"
                        " — collapsing accounts must be a deliberate, noted decision",
                    ))
                seen_targets.setdefault(row.target_key, key)
            if row.status == STATUS_EXCLUDED and not row.notes:
                issues.append(Issue(self.spec.name, key, "excluded without a note explaining why"))
        return issues

    def coverage(self, source_values: Iterable) -> list[str]:
        """Source values with no row at all. Used to fail fast before a load."""
        missing = []
        for value in source_values:
            key = str(value).strip()
            if key and key not in self.rows:
                missing.append(key)
        return sorted(set(missing))

    def counts(self) -> dict[str, int]:
        out = {status: 0 for status in VALID_STATUSES}
        for row in self.rows.values():
            out[row.status] = out.get(row.status, 0) + 1
        out["total"] = len(self.rows)
        return out


def _sort_key(value: str):
    return (0, int(value)) if value.isdigit() else (1, value)


@dataclass
class MappingSet:
    tables: dict[str, MappingTable]

    @classmethod
    def load(cls, directory: Path) -> "MappingSet":
        return cls({s.name: MappingTable.load(s, Path(directory)) for s in MAPPING_SPECS})

    def __getitem__(self, name: str) -> MappingTable:
        return self.tables[name]

    def __iter__(self) -> Iterator[MappingTable]:
        return iter(self.tables.values())

    def validate(self) -> list[Issue]:
        issues: list[Issue] = []
        for table in self.tables.values():
            if not table.rows:
                issues.append(Issue(table.spec.name, "", "mapping table is empty — run `map stub`"))
            issues.extend(table.validate())
        return issues

    def summary(self) -> dict[str, dict[str, int]]:
        return {name: table.counts() for name, table in self.tables.items()}
