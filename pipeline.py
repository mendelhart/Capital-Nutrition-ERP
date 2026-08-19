"""Orchestration: the stages, and the rehearsal that runs all of them.

Rehearsal is one command on purpose. The spec asks for at least three complete
rehearsals with the third being routine — that only happens if a rehearsal is
cheap to run and impossible to run differently by accident.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from . import extract as extract_mod
from .load import build_all, get_target
from .load.targets import LoadOutcome
from .mappings import MappingSet
from .reconcile import render_markdown, render_summary, run_all
from .reconcile.checks import CheckResult, Status
from .util import json_default

DOC_TYPES = ("opening_balance", "opening_control", "open_ar", "open_ap", "open_po")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def rows_reader(config):
    """rows_for(dataset) -> list of extracted rows; missing datasets read empty."""
    def rows_for(name: str) -> list[dict]:
        path = config.extract_dir / f"{name}.jsonl"
        if not path.exists():
            return []
        return list(extract_mod.read_jsonl(path))
    return rows_for


def docs_reader(target):
    def docs_for(doc_type: str) -> list[dict]:
        try:
            return list(target.read(doc_type))
        except FileNotFoundError:
            return []
    return docs_for


@dataclass
class StageResult:
    stage: str
    ok: bool
    detail: dict = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ stages
def stage_extract(config, datasets: Iterable[str] | None = None) -> StageResult:
    manifest = extract_mod.extract(config, datasets)
    failed = manifest["required_failed"]
    rows = {d["dataset"]: d["rows"] for d in manifest["datasets"] if not d["error"]}
    messages = [f"{d['dataset']}: {d['error']}" for d in manifest["datasets"] if d["error"]]
    return StageResult("extract", not failed, {"rows": rows, "snapshot": manifest["snapshot"]}, messages)


def stage_map_check(config) -> StageResult:
    mappings = MappingSet.load(config.mapping_dir)
    issues = mappings.validate()
    return StageResult(
        "map check", not issues,
        {"summary": mappings.summary()},
        [str(i) for i in issues],
    )


def stage_map_stub(config) -> StageResult:
    """Add pending rows for every source value that needs a decision."""
    from .mappings import MAPPING_SPECS, MappingTable

    rows_for = rows_reader(config)
    added: dict[str, int] = {}
    for spec in MAPPING_SPECS:
        table = MappingTable.load(spec, config.mapping_dir)
        count = 0
        for row in rows_for(spec.source_dataset):
            key = row.get(spec.source_key_field)
            if key in (None, ""):
                continue
            label = row.get(spec.source_label_field) or ""
            context = _context(spec.name, row)
            if table.add_pending(key, label, context):
                count += 1
        table.save()
        added[spec.name] = count
    return StageResult("map stub", True, {"added": added},
                       [f"{k}: +{v} pending rows" for k, v in added.items()])


def _context(mapping_name: str, row: dict) -> str:
    if mapping_name == "accounts":
        return f"type={row.get('account_type')} reconcile={row.get('reconcile')}"
    if mapping_name == "journals":
        return f"type={row.get('journal_type')}"
    if mapping_name == "taxes":
        return f"{row.get('amount')} {row.get('amount_type')} scope={row.get('type_tax_use')}"
    if mapping_name in ("parties", "vendors"):
        return f"customer_rank={row.get('customer_rank')} supplier_rank={row.get('supplier_rank')}"
    if mapping_name == "products":
        return f"type={row.get('product_type')} uom={row.get('uom')}"
    return ""


def stage_build(config) -> tuple[StageResult, object]:
    mappings = MappingSet.load(config.mapping_dir)
    result = build_all(config, mappings, rows_reader(config))
    return (
        StageResult("build", result.ok, {"documents": result.by_type()},
                    [str(i) for i in result.issues[:200]]),
        result,
    )


def stage_load(config) -> StageResult:
    build_result_stage, result = stage_build(config)
    if not result.ok:
        return StageResult(
            "load", False, build_result_stage.detail,
            ["refusing to load: transform issues must be resolved first"] + build_result_stage.messages,
        )
    by_type: dict[str, list[dict]] = {t: [] for t in DOC_TYPES}
    for doc in result.documents:
        by_type.setdefault(doc["_type"], []).append(doc)

    outcomes: list[LoadOutcome] = []
    with get_target(config) as target:
        for doc_type, docs in by_type.items():
            if not docs:
                continue
            outcomes.append(target.load(doc_type, docs))
    errors = [e for o in outcomes for e in o.errors]
    return StageResult(
        "load", not errors,
        {"outcomes": [o.as_dict() for o in outcomes]},
        errors,
    )


def stage_reconcile(config) -> tuple[StageResult, list[CheckResult]]:
    mappings = MappingSet.load(config.mapping_dir)
    with get_target(config) as target:
        results = run_all(rows_reader(config), docs_reader(target), mappings, config)
    blocking = [r for r in results if r.blocks_cutover]
    config.report_dir.mkdir(parents=True, exist_ok=True)
    md_path = config.report_dir / "reconciliation.md"
    md_path.write_text(render_markdown(results, config), encoding="utf-8")
    (config.report_dir / "reconciliation.json").write_text(
        json.dumps([r.as_dict() for r in results], indent=2, default=json_default),
        encoding="utf-8",
    )
    return (
        StageResult("reconcile", not blocking,
                    {"report": str(md_path),
                     "statuses": {r.name: r.status.value for r in results}},
                    [f"{r.title}: {r.status.value} diff {r.difference}" for r in blocking]),
        results,
    )


# --------------------------------------------------------------- rehearsal
def rehearse(config, *, skip_extract: bool = False) -> dict:
    """extract -> map check -> load -> reconcile, with a written record."""
    started = _now()
    stages: list[StageResult] = []

    if skip_extract:
        stages.append(StageResult("extract", True, {}, ["skipped (--skip-extract)"]))
    else:
        stages.append(stage_extract(config))

    if stages[-1].ok:
        stages.append(stage_map_check(config))
    if stages[-1].ok:
        stages.append(stage_load(config))
    check_results: list[CheckResult] = []
    if stages[-1].ok:
        rec_stage, check_results = stage_reconcile(config)
        stages.append(rec_stage)

    record = {
        "label": config.run.label,
        "started_at": started,
        "finished_at": _now(),
        "config": config.redacted(),
        "stages": [
            {"stage": s.stage, "ok": s.ok, "detail": s.detail, "messages": s.messages}
            for s in stages
        ],
        "checks": [r.as_dict() for r in check_results],
        "ok": all(s.ok for s in stages),
        "cutover_ready": bool(check_results) and all(
            r.status is not Status.FAIL and r.status is not Status.ERROR
            for r in check_results if r.blocking
        ),
    }
    config.report_dir.mkdir(parents=True, exist_ok=True)
    log_path = config.report_dir / "rehearsal.json"
    log_path.write_text(json.dumps(record, indent=2, default=json_default), encoding="utf-8")

    history = config.root / "var" / "rehearsal_history.jsonl"
    history.parent.mkdir(parents=True, exist_ok=True)
    with history.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "label": record["label"],
            "finished_at": record["finished_at"],
            "ok": record["ok"],
            "cutover_ready": record["cutover_ready"],
            "stages": {s.stage: s.ok for s in stages},
        }, default=json_default) + "\n")

    record["report"] = str(config.report_dir / "reconciliation.md")
    record["log"] = str(log_path)
    return record


def summarise(check_results: list[CheckResult]) -> str:
    return render_summary(check_results)


def rehearsal_history(config) -> list[dict]:
    path = Path(config.root) / "var" / "rehearsal_history.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
