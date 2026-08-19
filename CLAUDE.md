# Working in this repository

This repository is the ERP's persistent memory between chats. Read this before
changing anything.

## Read first, in this order

Per `docs/spec-package/15_CLAUDE_CHAT_PROTOCOL.md`:

1. `docs/spec-package/00_MASTER_BUILD.md` — scope, principles, non-negotiables.
2. `docs/ARCHITECTURE.md`
3. `docs/STATUS.md` — where the build actually stands.
4. The relevant `docs/specs/*.md` specification.
5. `docs/integration/12_INTEGRATION_CONTRACTS.md`
6. Relevant ADRs in `docs/adr/`.
7. The task specification in `docs/tasks/`.

`docs/spec-package/` is the pristine build package — treat it as read-only.

Working specifications live in `docs/specs/`, and nowhere else. There is exactly
one working copy of each specification. `docs/domains/` was a duplicate that had
drifted out of step and has been retired (see ADR-0010); do not recreate it.
If a specification needs to change, change it in `docs/specs/`.

## Out of scope

**Ship APL.** Do not design it, implement it, or create dependencies on it.

## One task, one chat

1. Summarise your understanding of the specification and current status.
2. Identify ambiguities and conflicts with existing architecture — **before** coding.
3. Propose the implementation plan and the tests you will add. Wait for approval.
4. Write the tests.
5. Implement the smallest maintainable solution.
6. `make test` — against PostgreSQL, never sqlite.
7. Update the affected documentation.
8. Record new architectural decisions as ADRs in `docs/adr/`.
9. Commit.
10. Update `docs/STATUS.md`.

Task files use `docs/spec-package/16_DOMAIN_TASK_TEMPLATE.md`. If a chat grows
too large, write a handoff into `docs/handoffs/` and start a new one — do not
rush to finish.

## If the specification is wrong

Do not silently implement it. Stop, explain what is wrong and why, state the
impact, and propose a correction. Update the specification and ADR after
approval.

## Hard rules

- Prefer Tryton standard functionality over custom code. A custom module needs
  a genuine Capital Nutrition requirement behind it.
- Never hide accounting logic in UI code.
- Never let an integration silently correct a financial discrepancy. Report it.
- Every external integration must be idempotent — register inbound events
  through `capital_nutrition.external.event` (ADR-0002) rather than inventing a
  new de-duplication scheme.
- Enforce invariants with database constraints wherever the database can.
- Tests must cover failure paths, not only happy paths.
- No domain is production-ready on isolated tests alone; cross-domain scenarios
  in `tests/scenarios/` must pass too.
- No production credentials in the repository, ever. Migration credentials live
  in `migration/config/migration.toml`, which is gitignored.
- Never migrate data without an explicit approved mapping, and never let a
  migration load run while reconciliation is failing.
- Boring readable code over clever abstractions.

## What already exists

- `modules/capital_nutrition_base` — the external-event idempotency ledger.
  See `docs/tasks/FND-001-foundation-and-idempotency-ledger.md` and ADR-0002.
- `migration/` — the Odoo → Tryton migration toolkit (MIG-001): read-only
  extraction, reviewable mapping tables, idempotent loads and the
  reconciliation gate. `make migration-test` runs it; it needs no database.
  See `migration/README.md` and `docs/tasks/MIGRATION/`.
- Toolchain, PostgreSQL 16 test harness, and CI. See `README.md`.

## Task IDs

`ACC-###` accounting · `PROD-###` products · `INV-###` inventory ·
`PUR-###` purchasing · `CUS-###` customers · `SAL-###` sales ·
`MAG-###` Magento · `REP-###` reporting · `UI-###` UI/UX ·
`MIG-###` migration · `FND-###` foundation work predating the domains.
