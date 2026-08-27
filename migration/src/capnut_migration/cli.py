"""Command line interface.

    capnut-migrate probe                 what is in the snapshot
    capnut-migrate schema --write        regenerate sql/staging_schema.sql
    capnut-migrate extract [-d NAME]     source -> var/<label>/extract/*.jsonl
    capnut-migrate stage                 JSONL -> PostgreSQL stg schema (optional)
    capnut-migrate profile               row counts, sums, nulls, flags
    capnut-migrate map stub|check        mapping tables
    capnut-migrate build                 transform only, report issues
    capnut-migrate load                  transform + load (idempotent)
    capnut-migrate reconcile             run the checks, write the report
    capnut-migrate rehearse              all of the above, with a written record
    capnut-migrate history               previous rehearsals

Exit codes: 0 success, 1 stage failed, 2 reconciliation blocks cutover.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import pipeline
from .config import load_config
from .profile import profile as run_profile
from .staging import generate_ddl
from .util import json_default

EXIT_OK, EXIT_FAILED, EXIT_BLOCKED = 0, 1, 2


def _emit(stage: pipeline.StageResult) -> int:
    mark = "ok" if stage.ok else "FAILED"
    print(f"[{stage.stage}] {mark}")
    for message in stage.messages:
        print(f"    {message}")
    if stage.detail:
        print(textwrap_json(stage.detail))
    return EXIT_OK if stage.ok else EXIT_FAILED


def textwrap_json(data: dict) -> str:
    text = json.dumps(data, indent=2, default=json_default)
    return "\n".join("    " + line for line in text.splitlines())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capnut-migrate", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", help="path to migration.toml")
    parser.add_argument("--root", help="migration/ directory (default: cwd)")
    parser.add_argument("--label", help="override [run] label")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("probe", help="inspect the source snapshot")
    schema = sub.add_parser("schema", help="print or write the staging DDL")
    schema.add_argument("--write", action="store_true")

    extract = sub.add_parser("extract", help="extract the source into JSONL")
    extract.add_argument("-d", "--dataset", action="append", dest="datasets")

    sub.add_parser("stage", help="load the JSONL snapshot into PostgreSQL")
    prof = sub.add_parser("profile", help="profile the extracted data")
    prof.add_argument("-d", "--dataset", action="append", dest="datasets")

    mapping = sub.add_parser("map", help="mapping tables")
    mapping.add_argument("action", choices=("stub", "check"))

    sub.add_parser("build", help="transform only")
    sub.add_parser("load", help="transform and load")
    sub.add_parser("reconcile", help="run reconciliation checks")
    rehearse = sub.add_parser("rehearse", help="run the whole pipeline")
    rehearse.add_argument("--skip-extract", action="store_true",
                          help="reuse the existing snapshot for this label")
    sub.add_parser("history", help="show previous rehearsals")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config, args.root)
    if args.label:
        object.__setattr__(config.run, "label", args.label)

    if args.command == "probe":
        from .sources import get_source
        with get_source(config) as source:
            info = source.snapshot_info()
        print(json.dumps(info, indent=2, default=json_default))
        return EXIT_OK if not info.get("warnings") else EXIT_FAILED

    if args.command == "schema":
        ddl = generate_ddl()
        if args.write:
            path = Path(config.root) / "sql" / "staging_schema.sql"
            path.write_text(ddl, encoding="utf-8")
            print(f"wrote {path}")
        else:
            print(ddl)
        return EXIT_OK

    if args.command == "extract":
        return _emit(pipeline.stage_extract(config, args.datasets))

    if args.command == "stage":
        from .stage_db import stage
        print(json.dumps(stage(config), indent=2, default=json_default))
        return EXIT_OK

    if args.command == "profile":
        print(json.dumps(run_profile(config, args.datasets), indent=2, default=json_default))
        return EXIT_OK

    if args.command == "map":
        if args.action == "stub":
            return _emit(pipeline.stage_map_stub(config))
        return _emit(pipeline.stage_map_check(config))

    if args.command == "build":
        stage_result, _ = pipeline.stage_build(config)
        return _emit(stage_result)

    if args.command == "load":
        return _emit(pipeline.stage_load(config))

    if args.command == "reconcile":
        stage_result, results = pipeline.stage_reconcile(config)
        print(pipeline.summarise(results))
        print(f"\nreport: {stage_result.detail.get('report')}")
        return EXIT_OK if stage_result.ok else EXIT_BLOCKED

    if args.command == "rehearse":
        record = pipeline.rehearse(config, skip_extract=args.skip_extract)
        for stage in record["stages"]:
            print(f"[{stage['stage']}] {'ok' if stage['ok'] else 'FAILED'}")
            for message in stage["messages"][:20]:
                print(f"    {message}")
        print(f"\nreport: {record['report']}\nlog:    {record['log']}")
        if not record["ok"]:
            return EXIT_FAILED
        return EXIT_OK if record["cutover_ready"] else EXIT_BLOCKED

    if args.command == "history":
        rows = pipeline.rehearsal_history(config)
        if not rows:
            print("no rehearsals recorded yet")
            return EXIT_OK
        for i, row in enumerate(rows, 1):
            ready = "cutover-ready" if row["cutover_ready"] else "NOT cutover-ready"
            print(f"{i:>3}. {row['finished_at']}  {row['label']:<16} "
                  f"{'ok' if row['ok'] else 'FAILED':<7} {ready}")
        print(f"\n{len(rows)} rehearsal(s) recorded; the spec requires at least 3 complete runs, "
              "the third routine.")
        return EXIT_OK

    return EXIT_FAILED


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
