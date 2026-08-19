"""Extraction: source -> JSONL snapshot on disk.

The JSONL files *are* the snapshot. Everything downstream reads them, never the
source, so a rehearsal can be repeated byte-for-byte and a reconciliation
failure can always be traced to a specific extracted row.

Each dataset produces:
    var/<label>/extract/<dataset>.jsonl
and every run rewrites:
    var/<label>/extract/manifest.json   (snapshot info, row counts, digests)
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

from .sources import get_source
from .sources.base import DATASETS, Dataset, dataset
from .util import dumps, json_default, migration_ref


@dataclass
class ExtractResult:
    dataset: str
    rows: int
    digest: str
    path: str
    started_at: str
    finished_at: str
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def normalise(row: dict, ds: Dataset, system: str) -> dict:
    """Preserve source identity, and keep only declared columns.

    An undeclared column reaching staging means the SQL and the catalogue have
    drifted apart, which is exactly the kind of silent change this migration
    cannot afford — so it is an error, not a warning.
    """
    if "source_id" not in row or row["source_id"] in (None, ""):
        raise ValueError(f"{ds.name}: row without source_id: {row!r}")
    if ds.columns:
        unexpected = set(row) - set(ds.columns)
        if unexpected:
            raise ValueError(
                f"{ds.name}: query returned undeclared columns {sorted(unexpected)}; "
                f"update DATASETS in sources/base.py or the SQL"
            )
    out = {k: row.get(k) for k in (ds.columns or tuple(row))}
    out["_ref"] = migration_ref(system, ds.model, row["source_id"])
    return out


def write_jsonl(rows: Iterable[dict], path: Path) -> tuple[int, str]:
    """Stream to disk, hashing as we go. Returns (row_count, digest)."""
    digest = hashlib.sha256()
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            line = dumps(row)
            fh.write(line + "\n")
            digest.update(line.encode("utf-8"))
            count += 1
    tmp.replace(path)
    return count, digest.hexdigest()[:16]


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing — run `capnut-migrate extract` for this label first"
        )
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract(config, dataset_names: Iterable[str] | None = None) -> dict:
    """Run extraction and write the manifest. Returns the manifest."""
    config.ensure_dirs()
    names = list(dataset_names) if dataset_names else [d.name for d in DATASETS]
    results: list[ExtractResult] = []

    with get_source(config) as source:
        snapshot = source.snapshot_info()
        available = set(source.available())
        for name in names:
            ds = dataset(name)
            started = _now()
            path = config.extract_dir / f"{name}.jsonl"
            if name not in available:
                results.append(ExtractResult(
                    name, 0, "", str(path), started, _now(),
                    error="no extraction query available for this adapter",
                ))
                continue
            try:
                rows = (normalise(r, ds, config.source.system) for r in source.fetch(name))
                count, digest = write_jsonl(rows, path)
                results.append(ExtractResult(name, count, digest, str(path), started, _now()))
            except Exception as exc:  # keep going; the manifest records the failure
                results.append(ExtractResult(
                    name, 0, "", str(path), started, _now(), error=f"{type(exc).__name__}: {exc}"
                ))

    manifest = {
        "label": config.run.label,
        "created_at": _now(),
        "config": config.redacted(),
        "snapshot": snapshot,
        "datasets": [asdict(r) for r in results],
        "required_failed": sorted(
            r.dataset for r in results
            if r.error and dataset(r.dataset).required
        ),
    }
    manifest_path = config.extract_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=json_default), encoding="utf-8"
    )
    return manifest


def load_manifest(config) -> dict:
    path = config.extract_dir / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"no extraction manifest at {path}; run `extract` first")
    return json.loads(path.read_text(encoding="utf-8"))


def dataset_rows(config, name: str) -> Iterator[dict]:
    yield from read_jsonl(config.extract_dir / f"{name}.jsonl")
