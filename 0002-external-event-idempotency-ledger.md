# ADR-0002: A single external-event ledger for integration idempotency

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** Capital Nutrition

## Context

`docs/spec-package/00_MASTER_BUILD.md` requires that every external integration be idempotent,
and that integrations never silently correct financial discrepancies. Magento 1
is the first integration; migration tooling and future systems will follow.

Left to themselves, each integration would grow its own de-duplication scheme —
a "magento_order_id" column here, an "already imported" flag there. Those
schemes are invisible to each other, are usually enforced in Python rather than
in the database, and are exactly where duplicate financial records come from.

## Decision

Every inbound external event is recorded once in
`capital_nutrition.external.event`, in `capital_nutrition_base`, before any
domain code acts on it.

- The key is `(source, event_type, external_id)` with a **database** unique
  constraint. The constraint, not the Python helper, is the invariant.
- `ExternalEvent.register(...)` returns `(event, is_new)`. `is_new=False` is
  the caller's signal to skip the work, not to repeat it.
- The SHA-256 digest of the payload is stored. A known key arriving with a
  different digest raises `ExternalEventPayloadMismatch`. It is never applied
  and never overwritten — a source that changes the content behind an
  identifier it already delivered is a data-integrity problem an operator has
  to see.
- Failures are recorded with an attempt count and stay retryable. Success
  clears the error and links `origin` to the ERP record produced.
- Domain modules extend `_get_origin()` to declare which of their models an
  event may point at. They do not extend the keying scheme.

## Consequences

### Accepted costs

- One extra table write per inbound event.
- Integrations must be written against `register()` rather than doing whatever
  is locally convenient.
- Concurrency is handled by the database, not by the helper: two transactions
  registering the same key at once means the loser gets an integrity error and
  must retry the whole transaction. Callers must be retry-safe.
- The ledger grows monotonically and will need a retention policy before it
  becomes large. Not urgent at Capital Nutrition's volume; revisit at Gate 3.

### Rejected alternatives

- **Per-integration de-duplication columns.** Rejected: invisible to each
  other, usually unenforced at the database level, and they make "did this
  order import twice?" a per-integration investigation.
- **Rely on Magento's own idempotency.** Rejected: it makes correctness a
  property of a system we do not own and cannot test.
- **Upsert on replay (last write wins).** Rejected directly by the master
  build — it is silent correction of a discrepancy.
- **Ignore payload changes entirely.** Rejected: it would let a corrected
  order total pass through as a no-op, which looks like success and is not.

## Verification

This decision is wrong if a domain finds it needs a key the
`(source, event_type, external_id)` triple cannot express, or if payload
mismatches turn out to be routine and benign rather than exceptional. The
mismatch rate in the Magento parallel run is the observation to watch.

Proven by `modules/capital_nutrition_base/tests/test_module.py`, including the
failure paths: replay with a different payload, duplicate insert against the
database constraint, and retry after failure.
