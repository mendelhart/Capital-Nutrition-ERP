import pytest

from capnut_migration.load import JsonlTarget, TrytonTarget, get_target
from capnut_migration.util import content_hash


def doc(ref, amount="100.00"):
    d = {"_ref": ref, "_type": "opening_balance", "account": "A1000", "balance": amount}
    d["_hash"] = content_hash(d)
    return d


def test_first_load_inserts(config):
    outcome = JsonlTarget(config).load("opening_balance", [doc("a"), doc("b")])
    assert (outcome.inserted, outcome.updated, outcome.unchanged) == (2, 0, 0)


def test_rerunning_the_same_load_changes_nothing(config):
    target = JsonlTarget(config)
    target.load("opening_balance", [doc("a"), doc("b")])
    outcome = target.load("opening_balance", [doc("a"), doc("b")])
    assert (outcome.inserted, outcome.updated, outcome.unchanged) == (0, 0, 2)
    assert len(target.read("opening_balance")) == 2, "a rerun must not duplicate"


def test_changed_content_updates_in_place(config):
    target = JsonlTarget(config)
    target.load("opening_balance", [doc("a")])
    outcome = target.load("opening_balance", [doc("a", "250.00")])
    assert (outcome.inserted, outcome.updated, outcome.unchanged) == (0, 1, 0)
    stored = target.read("opening_balance")
    assert len(stored) == 1 and stored[0]["balance"] == "250.00"


def test_document_without_a_ref_is_an_error_not_a_silent_skip(config):
    outcome = JsonlTarget(config).load("opening_balance", [{"_type": "opening_balance"}])
    assert outcome.errors


def test_reading_an_unloaded_type_is_empty(config):
    assert JsonlTarget(config).read("open_ar") == []


def test_tryton_target_is_declared_but_refuses_to_run(config):
    with pytest.raises(NotImplementedError) as exc:
        TrytonTarget(config).load("opening_balance", [doc("a")])
    assert "not implemented" in str(exc.value)


def test_target_factory_rejects_unknown_adapters(config):
    object.__setattr__(config.target, "adapter", "nope")
    with pytest.raises(ValueError):
        get_target(config)
