import json

from capnut_migration import pipeline
from capnut_migration.cli import main
from conftest import write_mappings


def test_rehearsal_runs_end_to_end_and_is_cutover_ready(config):
    record = pipeline.rehearse(config, skip_extract=True)
    assert record["ok"], record["stages"]
    assert record["cutover_ready"]
    assert {s["stage"] for s in record["stages"]} == {"extract", "map check", "load", "reconcile"}
    assert (config.report_dir / "reconciliation.md").exists()
    assert (config.report_dir / "reconciliation.json").exists()


def test_rehearsal_is_repeatable_and_does_not_duplicate(config):
    pipeline.rehearse(config, skip_extract=True)
    second = pipeline.rehearse(config, skip_extract=True)
    assert second["cutover_ready"]
    load_stage = next(s for s in second["stages"] if s["stage"] == "load")
    outcomes = {o["doc_type"]: o for o in load_stage["detail"]["outcomes"]}
    assert all(o["inserted"] == 0 and o["updated"] == 0 for o in outcomes.values())
    assert outcomes["opening_balance"]["unchanged"] == 3


def test_rehearsal_history_accumulates(config):
    pipeline.rehearse(config, skip_extract=True)
    pipeline.rehearse(config, skip_extract=True)
    history = pipeline.rehearsal_history(config)
    assert len(history) == 2
    assert all(row["cutover_ready"] for row in history)


def test_unreviewed_mappings_stop_the_rehearsal_before_loading(config):
    write_mappings(config.mapping_dir, approved=False)
    record = pipeline.rehearse(config, skip_extract=True)
    assert not record["ok"]
    stages = {s["stage"]: s for s in record["stages"]}
    assert stages["map check"]["ok"] is False
    assert "load" not in stages, "nothing may load while mappings are unreviewed"


def test_map_stub_creates_pending_rows_for_every_source_value(config):
    for csv_file in config.mapping_dir.glob("*.csv"):
        csv_file.unlink()
    stage = pipeline.stage_map_stub(config)
    assert stage.ok
    assert stage.detail["added"]["accounts"] == 5
    assert stage.detail["added"]["products"] == 1
    # ...and they block until reviewed
    assert not pipeline.stage_map_check(config).ok


def test_map_stub_is_idempotent(config):
    first = pipeline.stage_map_stub(config)
    second = pipeline.stage_map_stub(config)
    # The fixture already maps every account, so the first run adds none.
    assert first.detail["added"]["accounts"] == 0
    # Whatever the first run added, a second run must add nothing.
    assert all(count == 0 for count in second.detail["added"].values()), second.detail


def test_profile_flags_are_clean_on_the_fixture(config):
    from capnut_migration.profile import profile

    report = profile(config)
    assert report["flags"] == []
    gl = next(d for d in report["datasets"] if d["dataset"] == "gl_lines")
    assert gl["sums"]["debit"] == gl["sums"]["credit"] == "1800.00"


def test_profile_flags_an_unbalanced_source(config):
    from capnut_migration.profile import profile

    path = config.extract_dir / "gl_lines.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["debit"] = "1100.00"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert any("out of balance" in f for f in profile(config)["flags"])


def test_cli_rehearse_exits_zero_when_ready(config, monkeypatch):
    monkeypatch.chdir(config.root)
    assert main(["--root", str(config.root), "rehearse", "--skip-extract"]) == 0


def test_cli_reconcile_exits_two_when_cutover_is_blocked(config, monkeypatch):
    monkeypatch.chdir(config.root)
    main(["--root", str(config.root), "load"])
    # drop a loaded open AR item -> the trial balance no longer ties
    (config.load_dir / "open_ar.jsonl").write_text("")
    assert main(["--root", str(config.root), "reconcile"]) == 2


def test_cli_map_check_exits_one_when_unreviewed(config, monkeypatch):
    monkeypatch.chdir(config.root)
    write_mappings(config.mapping_dir, approved=False)
    assert main(["--root", str(config.root), "map", "check"]) == 1
