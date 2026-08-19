Capital Nutrition Sale
======================

Sales-domain customisations for the Capital Nutrition ERP (Tryton 8.0.x).

Scope
-----

This module does not reimplement anything standard ``sale`` provides. It adds
only what ``docs/specs/08_SALES.md`` names as a gap:

* ``sale.sale.channel`` — explicit order origin, required, defaulting to
  ``erp``, read-only after draft. Origin is never inferred from side effects.
* ``sale.line.external_line_id`` — the originating system's line identifier,
  so a replayed or amended external order event reconciles line by line.
  Retained identity, not a de-duplication key; no unique constraint.
* ``capital_nutrition.external.event._get_origin()`` extended with
  ``sale.sale``, so the ADR-0002 ledger can link an inbound event to the sale
  it produced.

Deliberately absent
-------------------

There is **no order-level external identifier column** on ``sale.sale``.
ADR-0002 rejects per-integration de-duplication columns by name; order-level
external identity lives in ``capital_nutrition.external.event`` and is reached
through its ``origin`` reference. ``tests/test_module.py`` asserts the column's
absence so the decision cannot be reversed silently.

Status
------

Written ahead of the approval step in ``CLAUDE.md`` § One task, one chat, and
against a specification this same change expanded. Review before adopting.

Verified on PostgreSQL 16.13 with ``trytond`` 8.0.9, ``trytond_sale`` 8.0.3 and
``capital_nutrition_base``: 31 tests, 6823 subtests.
