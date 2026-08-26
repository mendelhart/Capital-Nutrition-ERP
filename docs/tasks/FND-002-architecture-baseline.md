# CAPITAL NUTRITION ERP — TASK FND-002

## Task ID

`FND-002`

## Domain

`FOUNDATION` — architecture, predates the domain build order.

## Objective

Make `docs/ARCHITECTURE.md` explicit enough that independent chats can implement
their domains without inventing conflicting designs, and review the existing
build plan for architectural risk before more coding begins.

**Status: done.** No application features were built; this task owns boundaries,
not implementation.

## Context

- `docs/spec-package/00_MASTER_BUILD.md` — scope, principles, non-negotiables
- `docs/STATUS.md` as of 2026-08-19 (commit `afd850d`)
- `docs/specs/03`…`14`, `docs/integration/12_INTEGRATION_CONTRACTS.md`
- Existing ADRs: ADR-0001 *Tryton 8.0.x and PostgreSQL 16 as the foundation*,
  ADR-0002 *A single external-event ledger for integration idempotency*,
  ADR-0003 *Modules in-repo, symlinked into trytond for development*,
  ADR-0010 *One working specification directory*
- `modules/capital_nutrition_base`, `modules/capital_nutrition_sale`, `migration/`

## What was produced

| File | Change |
|---|---|
| `docs/ARCHITECTURE.md` | Rewritten. Was a 3.6 KB byte-identical copy of the pristine `docs/spec-package/01_ARCHITECTURE.md`; now the working architecture: system boundaries, source-of-truth register, module map and dependency rules, integration architecture, data/security/extensibility/testing/migration/reporting/deployment boundaries, failure philosophy, open decisions, change control. |
| `docs/adr/0011-module-and-package-naming.md` | New. `capital_nutrition_*` for Tryton modules, `capnut-*` for standalone distributions. Closes `STATUS.md` next-action 8. |
| `docs/adr/0012-external-system-boundaries.md` | New. Magento is an asynchronous peer; Odoo is a one-way, read-only source that ends at cutover. |
| `docs/adr/0013-one-working-architecture-document.md` | New. `docs/ARCHITECTURE.md` is the working copy; `docs/spec-package/01_ARCHITECTURE.md` is pristine history; no `01` is to be created in `docs/specs/`. |
| `docs/adr/0014-tryton-queue-for-asynchronous-work.md` | New. `ir.queue` + `trytond-worker`, no external broker; the queue is transport, not the integration's state machine. |
| `docs/adr/README.md` | Index extended; numbering warning left intact. |
| `docs/STATUS.md` | Updated. |

## Platform facts verified for this task

Checked against the published `trytond` 8.0.9 package rather than assumed, in the
spirit of the `11_UI_UX_STANDARDS.md` verification register:

| Fact | Evidence |
|---|---|
| `ir.queue` exists, with `Model.__queue__`, `push`/`pull`, `scheduled_at`, `expected_at`, and `LISTEN`/`NOTIFY` wake-up | `trytond/ir/queue_.py` |
| `trytond-worker` and `trytond-cron` are installed console scripts | `console_scripts` entry points; `trytond/cli/worker.py` |
| The worker reschedules only on `DatabaseOperationalError`; `UserError`/`UserWarning` is reported to `ir.error` and not retried; other exceptions end the task | `trytond/worker.py` `run_task` |
| Queue rows are cleaned on a `clean_days` setting, default 30 | `Queue.clean` |
| **No Canadian chart-of-accounts module is published for Tryton 8.0.** `trytond_account_ca` does not exist on PyPI; `trytond_account_be` and `trytond_account_fr` do, at 8.0.0 | PyPI index |

The last one matters beyond this task: `STATUS.md` § Verification debt asks
whether a Canadian chart module exists. It does not. A Canadian chart is a build,
not an install, and `OQ-ACC-001` should be scoped accordingly.

## Architectural risk register

Reviewed the build plan before further coding, as the assignment requires.
Ordered by what it would cost to discover late.

### R1 — `STATUS.md` describes work that is not in this repository — **HIGH**

`docs/STATUS.md` states that Accounting "has moved to implementation and is
verified end to end", and cites `capital_nutrition_account`,
`tasks/ACCOUNTING/ACC_BACKLOG.md`, `docs/tasks/PRODUCTS/PROD-001.md`,
`scripts/representative_month.py`, `scenario_ar_cycle.rst`,
`scenario_ap_cycle.rst`, `scenario_inventory_accounting.rst`,
`scenario_period_close.rst`, `14_TESTING_AND_ACCEPTANCE.md` and "all 30 tests
pass".

**None of those files exist in this repository, in any branch, or anywhere in its
git history.** `modules/` holds `capital_nutrition_base` and
`capital_nutrition_sale`; `scripts/` holds `dev_postgres.sh` and
`link_modules.py`; `tests/scenarios/` holds only its README.

Either that work lives in another working copy that was never pushed here, or the
status text was merged in from the Claude project describing a different tree.
Both are dangerous, and in opposite directions: the first means real accounting
work is unbacked and could be lost; the second means the build's own memory
overstates its progress, and Gate 1 could be approached on evidence nobody can
reproduce.

**This was not "fixed" here.** An architecture chat must not quietly delete a
claim that accounting is done, nor quietly delete the work if it exists. The
status file now carries the discrepancy explicitly. Resolving it — find the tree,
or correct the record — is the next chat's first job, before any accounting task
is opened.

### R2 — Repository and project ADR sets collide — **HIGH**

Repository ADR-0002 is *A single external-event ledger for integration
idempotency*; project ADR-0002 is the costing method. The same number names different decisions, and ADRs are cited by number
throughout the specs and task files. Until reconciled, every citation is
ambiguous. Mitigated in `docs/ARCHITECTURE.md` § 0 by requiring citation by
number *and* title, and by leaving 0004–0008 unassigned here. Not solved —
`STATUS.md` Q10 owns it.

### R3 — `capital_nutrition_sale` is neither approved nor tested by CI — **MEDIUM**

The module exists, `docs/specs/08_SALES.md` records it as written ahead of the
approval step and "a proposal to review". Meanwhile `Makefile` `MODULES` is
`capital_nutrition_base` only, and `.github/workflows/ci.yml` runs
`tests modules/capital_nutrition_base/tests`. Its 31 tests therefore never run
in CI, and a change that breaks it is invisible.

Not changed here: adding the module to the build is a sales/foundation
implementation act, and it should follow the review the specification asks for,
not precede it. `docs/ARCHITECTURE.md` § 4.4 now states the rule — a module not
listed in both `MODULES` and CI is not tested — so the omission is a stated
defect rather than an accident.

### R4 — Two blocking accounting decisions gate valuation architecture — **HIGH, known**

Costing method and stock accounting method (project ADRs) both remain Proposed.
They determine what inventory valuation means, when cost reaches the ledger, and
which accounts it touches. Every inventory-accounting test and the Products,
Inventory, Purchasing and Sales domains inherit them. Answering them late means
restating figures, not editing code. `STATUS.md` already ranks these highest; the
architecture cannot remove the dependency, only name it (§ 14).

### R5 — No cross-domain scenario harness exists — **MEDIUM**

`00_MASTER_BUILD.md` principle 11 says no domain is production-ready on isolated
tests alone, and `tests/scenarios/` is empty by design pending the first agreed
contract. `docs/integration/12_INTEGRATION_CONTRACTS.md` is currently a 2 KB
outline: it names inputs and outputs per boundary but no payload shapes, no
cardinalities, no failure semantics. Two domains can each satisfy it and still
not interoperate. The first cross-domain implementation task should deepen the
contract it depends on before writing code, and land the scenario with it.

### R6 — Magento facts are unverified until Phase 0 — **MEDIUM, planned**

Version 1.9.4.2 is a project fact; edition, OpenMage status, which APIs are
enabled, rate limits and customisations are not. `docs/specs/09_MAGENTO.md` gates
`MAG-002` onward on the reconnaissance map, and `MAG-001` exists to produce it.
The risk is only that someone starts connector work before the map lands.

### R7 — Specification numbering defects remain open — **LOW, build-owner decision**

Two documents occupy number 14, and `PROD-###` is assigned both to Products and,
implicitly, to production work (`14_PRODUCTION_CUTOVER.md` proposes `OPS-###`
and asks for confirmation). `docs/ARCHITECTURE.md` § 12 uses `OPS-###` when
referring to production tasks, which is the proposed convention, but confirming
it is `STATUS.md` Q8/Q11 and belongs to the build owner.

### R8 — Queue semantics are easy to over-trust — **MEDIUM, mitigated**

Verified above: `ir.queue` retries only database operational errors. A connector
built expecting the queue to retry a failed Magento call, or to hold a failure an
operator can see, would lose money events silently. ADR-0014 states the boundary
and § 5.2 of the architecture repeats it at the point of use.

## Decisions made

1. `capital_nutrition_*` for Tryton modules; `capnut-*` for standalone Python
   distributions (ADR-0011, *Module and package naming*). The `capnut_core`/`capnut_purchasing`/`capnut_magento`/
   `capnut_report` names inherited from the pristine architecture text are
   superseded — resolved by ADR rather than by silent overwrite, per `CLAUDE.md`.
2. Magento is an asynchronous peer; Odoo is a one-way source that ends at cutover
   (ADR-0012, *Magento is an asynchronous peer; Odoo is a one-way source*).
3. `docs/ARCHITECTURE.md` is the one working architecture document (ADR-0013,
   *One working architecture document*).
4. `ir.queue` + `trytond-worker`, no external broker; the queue is transport only
   (ADR-0014, *Tryton's own queue for asynchronous integration work*).
5. The module map in § 4.3 fixes sanctioned names for modules not yet built. It
   does not authorise building them.

## Assumptions

- Magento 1.9.4.2 and PostgreSQL 16.13 are taken as project facts from the
  assignment and `docs/specs/08_SALES.md`; everything else about the Magento
  installation is treated as unverified pending `MAG-001`.
- The ownership register in § 3 is a consolidation of `00_MASTER_BUILD.md`
  § Source of truth and the domain specifications, not new policy. Where a domain
  specification is more specific, it governs its own domain and the register
  points at it.
- The reporting layer's "dedicated reporting schema where justified" is read as
  permission, not instruction; the architecture requires measurement first.

## Out of scope for this task

Application features, module implementation, the Makefile/CI omission in R3,
resolving R1, and the numbering decisions in R7 — all belong to their owners.

## Verification performed

- `docs/ARCHITECTURE.md` contains no Ship APL reference and no `capnut_` Tryton
  module name.
- Every repository path cited in the new documents exists (checked by script).
- Every ADR cited by number is cited with its title.
- Platform claims verified against the published `trytond` 8.0.9 package (table
  above), not from memory or from 7.x material.
- `make lint` / `make test` were not run: no application code changed, and this
  repository has no virtualenv or PostgreSQL instance on the machine the work was
  done from. Nothing in this task can affect the suite — the change set is
  Markdown only.

## Handoff

Read, in order: `docs/ARCHITECTURE.md`, `docs/STATUS.md`, ADR-0011 … ADR-0014,
this file.

Then, before any new domain task starts: resolve **R1**. Everything else in the
register is either owned elsewhere or already stated where an implementer will
meet it.
