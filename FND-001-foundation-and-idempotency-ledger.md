# CAPITAL NUTRITION ERP — TASK FND-001

## Task ID

`FND-001`

## Domain

`FOUNDATION` — predates the domain build order.

## Objective

Stand up the repository, toolchain and test harness on Tryton 8.0.x /
PostgreSQL 16, and implement the one piece of infrastructure the master build
mandates before any integration exists: an idempotency boundary for inbound
external events.

**Status: done.** 44 tests passing against PostgreSQL 16.

## Context

- `docs/spec-package/00_MASTER_BUILD.md` — foundation, core principles, non-negotiables
- `docs/ARCHITECTURE.md`
- ADR-0001, ADR-0002, ADR-0003 (written by this task)

## Scope

### In scope
- Git repository, `.gitignore`, Makefile, pinned dependencies
- PostgreSQL 16 development database (docker-compose, plus a no-Docker script)
- Module discovery mechanism for in-repo modules
- Test harness executing against real PostgreSQL
- CI running lint and tests
- `capital_nutrition_base` with `capital_nutrition.external.event`
- ADRs for every decision above

### Out of scope
- Any domain model, workflow, or business rule. Every domain specification was
  a stub when this task ran, and implementing against a stub is how a build
  acquires rules nobody agreed to.
- Ship APL, permanently.

## Existing code

None. This task created the repository's code tree.

## Functional requirements

1. An inbound external event is recorded exactly once, keyed by
   `(source, event_type, external_id)`.
2. Replaying a known key returns the existing record and reports it as not new,
   so the caller skips the work rather than repeating it.
3. A known key arriving with different content is **reported**, not applied and
   not overwritten.
4. A processing failure is recorded and counted; the event stays retryable.
5. A successful retry clears the stale error and links the ERP record produced.

## Business rules

- BR: external events are idempotent (master build, principle 7 and
  non-negotiable 4).
- BR: an integration never silently corrects a discrepancy (principle 6).
- BR: database constraints enforce invariants wherever possible (principle 8).

## Integration requirements

- **Upstream:** any external system. Magento 1 first; migration tooling next.
- **Downstream:** every domain module that consumes external events.
- **Data exchanged:** source, event type, external identifier, payload digest.
- **Failure behaviour:** failures counted and retryable; payload mismatch
  raises `ExternalEventPayloadMismatch` and applies nothing.
- **Idempotency:** this task *is* the idempotency mechanism. Domain modules
  extend `_get_origin()` to declare which of their models an event may point
  at; they do not extend the keying scheme.

## Technical requirements

| Item | Delivered |
|---|---|
| Model | `capital_nutrition.external.event` |
| Fields | source, event_type, external_id, payload_digest, state, received_at, processed_at, attempts, error_message, origin |
| Constraint | `key_unique` — database UNIQUE on (source, event_type, external_id) |
| Indexes | (state, source); plus Tryton's rec_name index |
| Services | `register()`, `process()`, `fail()`, `ignore()`, `pending()`, `digest()` |
| Permissions | read for `res.group_admin`; no write/create/delete through the UI |
| Queues | none — deliberately. Retry is the caller's transaction, not a queue. |

## Tests

### Unit
- New key recorded and reported as new
- Replay returns the same row with `is_new=False`
- Keys whitespace-normalised
- Digest independent of dict ordering
- Same external id from two sources is two events
- `rec_name` identifies the event across systems and is searchable

### Integration
- Module installs into a real database via `trytond-admin`, with the unique
  constraint confirmed present in PostgreSQL
- `ModuleTestCase` framework checks: views, model access, selections, field
  dependencies, menu actions (~1900 subtests)

### Failure paths
- Replay with a changed payload raises and does not overwrite
- Duplicate insert rejected by the **database** constraint, not just by Python
- A failure is counted and the event stays retryable
- A successful retry clears the stale error
- An incomplete key raises rather than creating a partial record
- Copying an event resets its processing state
- The suite refuses to run on a non-PostgreSQL backend (verified to fail on sqlite)

### Cross-domain
- None. No contract exists yet.

## Acceptance criteria

- [x] `make test` green against PostgreSQL 16 — 44 passed
- [x] `make lint` clean
- [x] Module installs into a real database; constraint verified in PostgreSQL
- [x] Test harness proven to reject sqlite
- [x] ADR-0001, ADR-0002, ADR-0003 recorded
- [x] Committed
- [x] `docs/STATUS.md` updated

## Documentation

- `docs/adr/0001-tryton-8-postgresql-16-foundation.md`
- `docs/adr/0002-external-event-idempotency-ledger.md`
- `docs/adr/0003-module-layout-and-symlink-development.md`
- `README.md`, `CLAUDE.md`, `docs/STATUS.md`

## Traps found in Tryton 8.0

- Model classes are declared in the `[register]` section of `tryton.cfg`, not
  through `Pool.register()` in `__init__.py`.
- The PostgreSQL backend needs `psycopg` **3** *and* `psycopg_pool`.
  `psycopg2-binary` is not sufficient — install the `trytond[postgresql]` extra.
- `ModuleTestCase` defines its own `test_rec_name`; a module test with that
  name silently replaces the framework check. Name yours `test_get_rec_name`.

## Handoff

The floor is in place. No domain work has started.

The next session should **not** start writing domain code. It should settle the
open questions in `docs/STATUS.md` — in particular the baseline set of standard
Tryton modules, and the costing method, which constrains Inventory and
Accounting jointly and belongs in an ADR before either is built.

When integrations arrive they go through `ExternalEvent.register()`. They do
not invent their own de-duplication.
