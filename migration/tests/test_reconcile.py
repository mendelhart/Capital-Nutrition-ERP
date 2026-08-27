from decimal import Decimal

from capnut_migration.mappings import MappingSet
from capnut_migration.pipeline import docs_reader, rows_reader, stage_load
from capnut_migration.reconcile import compare, render_markdown, run_all, sum_by
from capnut_migration.reconcile.checks import Status
from capnut_migration.load import get_target


def results_for(config):
    stage_load(config)
    with get_target(config) as target:
        return run_all(rows_reader(config), docs_reader(target),
                       MappingSet.load(config.mapping_dir), config)


def by_name(results):
    return {r.name: r for r in results}


def test_compare_reports_only_differences_outside_tolerance():
    source = {"a": Decimal("100.00"), "b": Decimal("50.00")}
    target = {"a": Decimal("100.00"), "b": Decimal("49.99")}
    assert compare(source, target) and compare(source, target)[0].key == "b"
    assert compare(source, target, Decimal("0.01")) == []


def test_compare_catches_keys_present_on_only_one_side():
    variances = compare({"a": Decimal("10.00")}, {"b": Decimal("10.00")})
    assert {v.key for v in variances} == {"a", "b"}


def test_sum_by_skips_rows_with_no_key():
    rows = [{"k": "x", "v": "1.00"}, {"k": None, "v": "9.00"}]
    totals = sum_by(rows, lambda r: r["k"], lambda r: Decimal(r["v"]))
    assert totals == {"x": Decimal("1.00")}


def test_trial_balance_ties_on_a_consistent_migration(config):
    check = by_name(results_for(config))["trial_balance"]
    assert check.status is Status.PASS, [v.as_dict() for v in check.variances]
    assert check.difference == Decimal("0.00")


def test_trial_balance_fails_when_an_open_item_is_dropped(config):
    stage_load(config)
    with get_target(config) as target:
        docs = docs_reader(target)

        def missing_ar(doc_type):
            return [] if doc_type == "open_ar" else docs(doc_type)

        results = run_all(rows_reader(config), missing_ar,
                          MappingSet.load(config.mapping_dir), config)
    check = by_name(results)["trial_balance"]
    assert check.status is Status.FAIL
    assert check.blocks_cutover
    assert check.variances[0].key == "A1200"
    assert check.variances[0].difference == Decimal("-500.00")


def test_ar_and_ap_aging_tie(config):
    results = by_name(results_for(config))
    assert results["ar_aging"].status is Status.PASS
    assert results["ap_aging"].status is Status.PASS
    assert results["ar_aging"].source_total == Decimal("500.00")


def test_open_po_value_and_count_tie(config):
    results = by_name(results_for(config))
    assert results["open_pos"].status is Status.PASS
    assert results["open_pos"].source_total == Decimal("250.00")
    assert results["open_po_count"].status is Status.PASS
    assert results["open_po_count"].source_total == Decimal("1")


def test_inventory_is_skipped_until_a_physical_count_exists(config):
    check = by_name(results_for(config))["inventory_value"]
    assert check.status is Status.SKIPPED
    assert not check.blocks_cutover
    assert check.source_total == Decimal("300.00")
    assert "physical count" in check.note


def test_reference_checks_record_source_totals_without_blocking(config):
    results = by_name(results_for(config))
    assert results["sales_totals"].status is Status.SKIPPED
    assert results["sales_totals"].source_total == Decimal("500.00")
    assert not results["sales_totals"].blocks_cutover
    assert results["order_counts"].source_total == Decimal("1")


def test_a_broken_check_is_reported_as_error_not_swallowed(config):
    def explode(rows_for, docs_for, mappings, cfg):
        raise RuntimeError("boom")

    explode.__name__ = "check_explode"
    results = run_all(rows_reader(config), lambda t: [], MappingSet.load(config.mapping_dir),
                      config, checks=[explode])
    assert results[0].status is Status.ERROR
    assert results[0].blocks_cutover


def test_report_states_the_verdict(config):
    results = results_for(config)
    markdown = render_markdown(results, config)
    assert "No blocking differences" in markdown
    assert "Sign-off" in markdown
    assert "| Accountant |" in markdown


def test_report_blocks_cutover_when_a_check_fails(config):
    results = results_for(config)
    results[0].status = Status.FAIL
    assert "CUTOVER BLOCKED" in render_markdown(results, config)
