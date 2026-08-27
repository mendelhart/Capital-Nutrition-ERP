"""Load targets.

Idempotency lives here, and it is the same rule for every target: a document is
identified by its ``_ref``. Loading a document whose _ref already exists updates
it; loading one whose _ref and _hash both already exist does nothing. Reruns are
therefore free, which is what makes "rehearse repeatedly" affordable.
"""

from __future__ import annotations

import abc
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from ..util import dumps


@dataclass
class LoadOutcome:
    doc_type: str
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.inserted + self.updated + self.unchanged

    def as_dict(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "inserted": self.inserted,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "total": self.total,
            "errors": self.errors,
        }


class Target(abc.ABC):
    name = "abstract"

    def __init__(self, config) -> None:
        self.config = config

    @abc.abstractmethod
    def load(self, doc_type: str, documents: Iterable[dict]) -> LoadOutcome:
        ...

    @abc.abstractmethod
    def read(self, doc_type: str) -> Iterable[dict]:
        """Read back what is loaded. Reconciliation compares against this."""

    def close(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class JsonlTarget(Target):
    """Loads into var/<label>/load/<doc_type>.jsonl.

    Complete and idempotent. This is the target every rehearsal uses until the
    Tryton modules exist, and it stays useful afterwards as a dry run: the same
    documents, the same refs, no database side effects.
    """

    name = "jsonl"

    def _path(self, doc_type: str) -> Path:
        return self.config.load_dir / f"{doc_type}.jsonl"

    def _existing(self, doc_type: str) -> dict[str, dict]:
        path = self._path(doc_type)
        if not path.exists():
            return {}
        out: dict[str, dict] = {}
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    doc = json.loads(line)
                    out[doc["_ref"]] = doc
        return out

    def load(self, doc_type: str, documents: Iterable[dict]) -> LoadOutcome:
        outcome = LoadOutcome(doc_type)
        self.config.load_dir.mkdir(parents=True, exist_ok=True)
        existing = self._existing(doc_type)
        for doc in documents:
            ref = doc.get("_ref")
            if not ref:
                outcome.errors.append(f"document without _ref: {doc}")
                continue
            previous = existing.get(ref)
            if previous is None:
                outcome.inserted += 1
            elif previous.get("_hash") == doc.get("_hash"):
                outcome.unchanged += 1
                continue
            else:
                outcome.updated += 1
            existing[ref] = doc

        path = self._path(doc_type)
        tmp = path.with_suffix(".part")
        with tmp.open("w", encoding="utf-8") as fh:
            for ref in sorted(existing):
                fh.write(dumps(existing[ref]) + "\n")
        tmp.replace(path)
        return outcome

    def read(self, doc_type: str) -> Iterable[dict]:
        return list(self._existing(doc_type).values())


class TrytonTarget(Target):
    """Load into Tryton 8.0.x — NOT IMPLEMENTED.

    Blocked on the Tryton modules existing (see 00_MASTER_BUILD.md /
    03_ACCOUNTING.md). The contract it must honour when it is written:

    * Idempotency by ``_ref``. Store the ref on the created record — Tryton's
      ``ir.model.data`` (module='capnut_migration', fu_name=<ref>) is the
      natural place, so a rerun finds and updates instead of duplicating.
    * One transaction per document type, rolled back entirely on any error.
      A half-loaded opening entry is worse than no opening entry.
    * Post nothing that the accountant has not approved: the opening journal
      entry is created in draft and posted as an explicit, separate step.
    * Never create master data implicitly. If a mapping resolves to a target
      key that does not exist in Tryton, that is an error, not a create.
    """

    name = "tryton"

    _MESSAGE = (
        "The tryton load target is not implemented yet — the Tryton modules do not "
        "exist. Run with [target] adapter = \"jsonl\" until they do; the documents, "
        "refs and reconciliation are identical."
    )

    def load(self, doc_type: str, documents: Iterable[dict]) -> LoadOutcome:
        raise NotImplementedError(self._MESSAGE)

    def read(self, doc_type: str) -> Iterable[dict]:
        raise NotImplementedError(self._MESSAGE)


_TARGETS = {"jsonl": JsonlTarget, "tryton": TrytonTarget}


def get_target(config) -> Target:
    name = config.target.adapter
    if name not in _TARGETS:
        raise ValueError(f"unknown target adapter {name!r}; expected one of {sorted(_TARGETS)}")
    return _TARGETS[name](config)
