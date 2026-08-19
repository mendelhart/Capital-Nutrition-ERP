"""Odoo -> Tryton migration toolkit for Capital Nutrition ERP.

Implements the pipeline described in docs/specs/13_MIGRATION.md:

    extract -> stage -> map -> transform -> load -> reconcile

Design rules that follow directly from the spec:

* Never migrate blindly       -> every stage writes a manifest and a row count.
* Controlled source snapshot  -> extraction is pinned to one snapshot id.
* Preserve source identifiers -> every staged and loaded record carries its
                                 source system, model and id.
* Explicit mappings           -> reviewable CSV mapping tables, no fallbacks,
                                 no "best guess" matching.
* Idempotent loads            -> loads are keyed by migration_ref, so a rerun
                                 updates instead of duplicating.
* Rehearse repeatedly         -> the whole pipeline is one command.
* Reconcile automatically     -> reconciliation is a gate, not a report.
"""

__version__ = "0.1.0"
