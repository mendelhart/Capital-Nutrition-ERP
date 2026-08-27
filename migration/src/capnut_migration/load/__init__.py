"""Transform and load.

Transforms are pure functions: (extracted rows, mappings, config) -> load
documents. No I/O, no database, so every accounting decision in here is unit
testable without a Tryton instance.

Targets are where documents actually land. The jsonl target is complete and is
what rehearsals 1..n run against until the Tryton modules exist; the tryton
target is a declared stub.
"""

from .documents import (
    LoadDocument,
    TransformIssue,
    TransformResult,
    build_all,
    build_open_ap,
    build_open_ar,
    build_open_pos,
    build_opening_balances,
)
from .targets import JsonlTarget, LoadOutcome, Target, TrytonTarget, get_target

__all__ = [
    "LoadDocument",
    "TransformIssue",
    "TransformResult",
    "build_all",
    "build_opening_balances",
    "build_open_ar",
    "build_open_ap",
    "build_open_pos",
    "Target",
    "JsonlTarget",
    "TrytonTarget",
    "LoadOutcome",
    "get_target",
]
