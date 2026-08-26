# CAPITAL NUTRITION ERP — STATUS

Running memory between Claude chats, per `specs/README.md` §Repository memory.

**Last updated:** 2026-08-19
**Updated by:** ERP Architect chat, task `FND-002` (previous update: Consolidation
chat, same day)
**Target platform:** Tryton 8.0.x / PostgreSQL 16
**Scope note:** Ship APL is excluded from this build (`specs/README.md`).

---

## Where the build actually is

Specification phase, **plus the first implemented domain**.

**The repository is now under version control.** It had never been committed:
167 files sat untracked on `master` with no recovery point, next to a
`_to_delete/` directory containing a merge zip. Commit `5fd05b6` records the
tree exactly as found, before any change; the consolidation work described below
is on branch `docs/consolidate-specs`.

Accounting was recorded by a previous update as implemented and verified end to
end against Tryton 8.0.0 / trytond_account 8.0.3 / PostgreSQL 16.13. **That work
is not in this repository** — see the box below before relying on it. Every other
domain is specification-only, apart from the foundation module and an unapproved
Sales scaffold.

Architecture is now worked rather than inherited: `docs/ARCHITECTURE.md` was a
byte-identical copy of the pristine package text and has been rewritten as the
working architecture (`FND-002`; see § Architecture below).

---

### ⚠ The Accounting implementation described below is not in this repository

Checked on 2026-08-19 by the ERP Architect chat, on every branch and across the
whole git history:

| Cited by this file | Present? |
|---|---|
| `modules/capital_nutrition_account` | **no** — `modules/` holds `capital_nutrition_base` and `capital_nutrition_sale` |
| `tasks/ACCOUNTING/ACC_BACKLOG.md` | **no** |
| `docs/tasks/PRODUCTS/PROD-001.md` | **no** |
| `scripts/representative_month.py` | **no** — `scripts/` holds `dev_postgres.sh`, `link_modules.py` |
| `scenario_ar_cycle.rst`, `scenario_ap_cycle.rst`, `scenario_inventory_accounting.rst`, `scenario_period_close.rst` | **no** — `tests/scenarios/` holds only its README |
| `14_TESTING_AND_ACCEPTANCE.md` | **no** — not in `docs/specs/` or `docs/spec-package/` |
| "all 30 tests pass" | unreproducible here |

Either that work lives in a working copy that was never pushed, or this text was
merged in from the project describing a different tree. Nothing has been deleted
or rewritten on either hypothesis. **Resolve this before opening any accounting
task**: find the tree and push it, or correct the record. Gate 1 cannot be
approached on evidence that cannot be reproduced. Tracked as R1 in
`docs/tasks/FND-002-architecture-baseline.md`.

---

## Architecture

`docs/ARCHITECTURE.md` is the one working architecture document (ADR-0013,
*One working architecture document*);
`docs/spec-package/01_ARCHITECTURE.md` stays pristine and no `01` is to be created
in `docs/specs/`. The rewrite adds what independent chats were previously left to
invent:

- system boundaries — Magento 1.9.4.2 as the active selling site and an
  **asynchronous** peer, Odoo as a one-way read-only source that ends at cutover
  (ADR-0012, *Magento is an asynchronous peer; Odoo is a one-way source*)
- a source-of-truth register naming an owner, a writer and a conflict rule for
  every major entity
- the module map, naming (ADR-0011, *Module and package naming*) and dependency
  direction rules
- integration architecture: one idempotency ledger, `ir.queue` + `trytond-worker`
  as transport only (ADR-0014, *Tryton's own queue for asynchronous integration
  work*), with retry/dead-letter/replay owned by the integration's own event
  records
- data, security, extensibility, testing, migration, reporting and deployment
  boundaries, and the list of decisions still open

Verified for it against the published `trytond` 8.0.9 package: `ir.queue` and
`Model.__queue__` exist; `trytond-worker` and `trytond-cron` are installed
console scripts; the worker retries **only** `DatabaseOperationalError`, reports
`UserError`/`UserWarning` to `ir.error` without retrying, and drops other
failures. Also verified: **no Canadian chart-of-accounts module is published for
Tryton 8.0** (`trytond_account_ca` does not exist on PyPI, while
`trytond_account_be` and `trytond_account_fr` do). This closes the
`docs/specs`-side of the § Verification debt question about a Canadian chart —
it is a build, not an install.

---

## Specifications

Nine of the twenty documents `README.md` refers to existed at the UI/UX
update. Several of the mandatory five were written later the same day by other
chats. As of this update the project holds `00_MASTER_BUILD.md`,
`01_ARCHITECTURE.md`, `02_BUSINESS_RULES.md`, `12_INTEGRATION_CONTRACTS.md`
and `15_CLAUDE_CHAT_PROTOCOL.md`, so the mandatory-reading gap the UI/UX chat
flagged as the largest risk on the build is **closed**.

**`16_TESTING.md` has been retired.** It was a thin duplicate of
`14_TESTING_AND_ACCEPTANCE.md`, written by a chat that could not see the
newer document, and it also squatted on the number the original package uses
for `16_DOMAIN_TASK_TEMPLATE.md`. Nothing in it was not already covered in
more detail by `14_TESTING_AND_ACCEPTANCE.md`. **`14_TESTING_AND_ACCEPTANCE.md`
is authoritative for testing.** This closes the previous update's next-action 4.

### Two open numbering defects

Both need a decision; neither should be guessed.

1. **Two documents occupy number 14** — `14_TESTING_AND_ACCEPTANCE.md` and
   `14_PRODUCTION_CUTOVER.md`. `README.md` §Specification index lists only the
   first, so a chat following §Start with will never discover production and
   cutover. One of them must be renumbered. `16` is now free.
2. **`PROD-###` is assigned twice** — to the Products domain in `README.md`
   §File conventions, and implicitly to production/infrastructure work.
   `14_PRODUCTION_CUTOVER.md` proposes `OPS-###` for the latter and asks for
   confirmation. Unconfirmed.

`README.md` §Specification index also omits `16_DOMAIN_TASK_TEMPLATE.md` and
`17_STATUS_TEMPLATE.md`, both of which exist in `docs/spec-package/`.

### Repo / project spec drift

The project holds 20 documents under `specs/`. The repository splits the same
material three ways — `docs/spec-package/` (the original package),
`docs/domains/` and `docs/integration/` (working copies), and `docs/specs/`
(the deeper rewrites) — and `docs/specs/` currently holds 11 of them. A chat
told to read `docs/specs/` will not find `00`, `01`, `02`, `04`, `05`, `10`,
`12`, `14_TESTING_AND_ACCEPTANCE` or `15` there.

**Resolved for the repository (ADR-0010).** `docs/specs/` is the single working
specification directory and now holds the complete set 03–14. `docs/domains/`
was a drifted duplicate — it still held the 1.5 KB stub of `08_SALES.md` against
12 KB in `docs/specs/`, and the 2 KB stub of `09_MAGENTO.md` against 11.5 KB —
while `CLAUDE.md` instructed every chat to read it. Any Sales or Magento chat
following the documented procedure would have designed against the stub.

Every overlapping file was compared byte for byte before retiring it; the three
that existed only there (`04_PRODUCTS`, `05_INVENTORY`, `10_REPORTING`, all
byte-identical to the pristine package) were carried across unchanged and remain
unworked stubs. The retired copies are in `_to_delete/docs-domains-retired/`.
`docs/spec-package/` stays as read-only history. `CLAUDE.md` now points at
`docs/specs/`.

Still open: `docs/specs/` does not hold `00`, `01`, `02`, `12`, `15` or
`14_TESTING_AND_ACCEPTANCE` — those live in `docs/spec-package/` and
`docs/integration/` in the repository, and under `specs/` in the project. The
repo-versus-project question below is a separate problem from the
three-directories-in-one-repo question that ADR-0010 closes.

---

## Tasks

| Domain | Backlog | State |
|---|---|---|
| Accounting | `tasks/ACCOUNTING/ACC_BACKLOG.md` | ACC-001…009 DONE, 010…014 ready, 101…109 BLOCKED |
| UI/UX | `docs/tasks/UI/UI_BACKLOG.md` | UI-001 … UI-038, all OPEN or BLOCKED |
| Migration | `tasks/MIGRATION/MIG_BACKLOG.md` | MIG-001 |
| Magento | `tasks/MAGENTO/MAG_BACKLOG.md` | MAG-001 |
| Customers | `tasks/CUSTOMERS/CUS_BACKLOG.md` | CUS-001 |
| Sales | `tasks/SALES/SAL_BACKLOG.md` | written |
| Products | `docs/tasks/PRODUCTS/PROD-001.md` | PROD-001 |
| Purchasing | `tasks/PURCHASING_TASKS.md` | written |

---

## Accounting — what is verified

| Area | State | Evidence |
|---|---|---|
| Module layout per `01_ARCHITECTURE.md` | done | `capital_nutrition_base` + `capital_nutrition_account` |
| Fiscal calendar, periods, move sequences | done | all scenarios |
| Journals | done (upstream defaults) | OQ-ACC-008 |
| AR: invoice, partial payment, settlement, credit note, partial refund | done | `scenario_ar_cycle.rst` (required scenarios 1, 3, 4, 5, 6) |
| AP: bill, partial payment, settlement, supplier credit note | done | `scenario_ap_cycle.rst` (2) |
| Inventory: receipt, landed cost, shipment, COGS | done | `scenario_inventory_accounting.rst` (7, 8, 9) |
| Period close / reopen / lock, posted-move immutability | done | `scenario_period_close.rst` (10, 11) |
| Representative month + 7 tie-outs | done | `scripts/representative_month.py` |
| Chart of accounts | **placeholder** | OQ-ACC-001 — now unblocked by ADR-0006 |
| Tax | **placeholder flat rate** | ADR-0003 |
| Costing policy | **provisional: average** | ADR-0002 |
| Stock accounting method | **provisional: anglo-saxon** | ADR-0008 |
| Account mapping | **auto-selected placeholder** | OQ-ACC-004 |

All 30 tests pass on SQLite (~24s) and PostgreSQL 16 (~110s) from a database
built from scratch, which satisfies the `14_TESTING_AND_ACCEPTANCE.md` rule
that CI must not depend on a persistent shared database.

**Read this before quoting any number.** The representative month ties, but
ties are a property of double-entry bookkeeping, not evidence that the
accounts are correct. On the placeholder chart, 2 of the 9 account types
posted to carry no statement classification at all. Balance-sheet and P&L
subtotals are indicative only until OQ-ACC-001 closes.

---

## Decisions of record

`docs/adr/` now holds ADR-0001 … ADR-0003, ADR-0010 and ADR-0011 … ADR-0014.
The table below still lists the **project** set for 0002 … 0008; the collision it
records is Q10. The UI/UX chat's seven binding
decisions (§ below, from `11_UI_UX_STANDARDS.md`) are still not ADRs and
should be promoted if they survive review.

| ADR | Subject | Status |
|---|---|---|
| 0001 | Tryton 8.0 / PostgreSQL 16 | Accepted |
| 0002 | Inventory costing method | **Proposed — BLOCKING** |
| 0003 | Tax calculation provider | **Proposed — BLOCKING** |
| 0004 | Magento direction of truth | Proposed |
| 0005 | Migration history depth | Proposed |
| 0006 | Operating jurisdiction | **Accepted — Canada** |
| 0007 | Accounting foundation on standard Tryton modules | **Accepted** |
| 0008 | Stock accounting method (continental vs anglo-saxon) | **Proposed — BLOCKING** |
| 0010 | One working specification directory | **Accepted** (repository only — see Q10) |
| 0011 | Module and package naming | **Accepted** — closes next-action 8 |
| 0012 | Magento is an asynchronous peer; Odoo is a one-way source | **Accepted** |
| 0013 | One working architecture document | **Accepted** |
| 0014 | Tryton's own queue for asynchronous integration work | **Accepted** |

ADR-0008 is new and is **not** a duplicate of ADR-0002: ADR-0002 chooses how a
unit is costed, ADR-0008 chooses when and to which accounts that cost reaches
the ledger. Both are open and answering one does not answer the other.

UI/UX decisions binding but not yet ADRs:

1. The Tryton client is the UI; anything requiring a bespoke front end is an
   architecture decision, not a UI task.
2. A canonical lexicon overrides Tryton's stock labels.
3. On Hand / Reserved / Available are three distinct labelled quantities.
4. `visual` carries exactly four meanings ERP-wide; colour is never the only
   carrier of meaning.
5. Every list opens filtered to the work, with a visible route to the
   unfiltered set.
6. Editable lists are forbidden on anything opened from a menu.
7. Consistency is enforced by an automated view-convention test (UI-008).

---

## Open questions

| # | Question | Gates | Owner |
|---|---|---|---|
| Q1 | Date/number format, symbol placement, first day of week | UI-003, all screens | Business — **partly answered**: locale is Canadian and currency is CAD (ADR-0006). The formatting conventions are still unset. |
| Q2 | Dashboard implementation mechanism | UI-010 | ADR |
| Q3 | Lot expiry warning window | UI-024 | Business |
| Q4 | Final chart of accounts | Accounting build | Accountant — OQ-ACC-001, **unblocked by ADR-0006** |
| Q5 | Tax provider and configuration | Accounting build | Accountant — ADR-0003, now scoped to Canadian indirect tax |
| Q6 | Costing policy | Accounting + Inventory | Accountant — ADR-0002 |
| Q7 | Account mapping | Accounting build | Accountant — OQ-ACC-004 |
| Q8 | Which document keeps number 14, and confirm `OPS-###` for production work | Spec package navigation | Build owner |
| Q9 | Which repository directory is authoritative for specs | Every chat's mandatory reading | **Answered — `docs/specs/` (ADR-0010)** |
| Q10 | The repository and the project hold two different ADR sets under the same numbers | Every citation of an ADR | Build owner — see below |

Q4–Q7 are carried verbatim from `03_ACCOUNTING.md` §Open questions, which
instructs that they must not be invented. The Accounting build has honoured
that: nothing in `modules/` decides any of them.

### Q10 — divergent ADR numbering

The repository's `docs/adr/` and the project's `docs/adr/` are different sets
that collide:

| # | In the repository | In the project |
|---|---|---|
| 0001 | Tryton 8.0.x and PostgreSQL 16 | Tryton 8.0 / PostgreSQL 16 (same decision) |
| 0002 | External-event idempotency ledger | Inventory costing method |
| 0003 | Modules in-repo, symlinked into trytond | Tax calculation provider |
| 0004–0008 | *(absent)* | Magento direction of truth, migration history depth, operating jurisdiction, accounting foundation, stock accounting method |

"ADR-0002" therefore names two unrelated decisions depending on which copy the
reader has. This is more dangerous than the spec duplication ADR-0010 closes,
because ADRs are cited by number throughout the specs and task files. Until it
is reconciled, **cite ADRs by title as well as number**, and do not assign
0004–0008 in the repository. The new spec-directory ADR took 0010 to stay clear
of both sets.

Accounting-domain detail lives in `docs/domains/ACCOUNTING-open-questions.md`
in the **project** (it has no repository copy),
including one new question — **OQ-ACC-009**, presentation and transaction
currency, which shares its underlying fact with Q1.

**ADR-0006 is answered: the operating jurisdiction is Canada, and Canada only**
(Morris Hart, 2026-08-19). This releases the chart of accounts question to the
accountant, scopes the ADR-0003 tax evaluation to Canadian indirect tax
(GST/HST/PST-QST — not US nexus), confirms PIPEDA for `07_CUSTOMERS.md` and
Canadian retention for `13_MIGRATION.md`, and sets presentation currency to CAD.
`03_ACCOUNTING.md` in `docs/specs/` has been corrected from "US chart of
accounts" to Canadian, and its tax section now names GST/HST/PST-QST.

It does **not** answer OQ-ACC-001 (which chart), ADR-0002 (costing) or ADR-0008
(stock accounting method). Those remain the blocking set.

**ADR-0002 and ADR-0008 are now the highest-value answers to obtain.**

---

## Known trap: git on the Cowork workspace mount

The workspace mount forbids `unlink`, so git cannot remove its own lock files. A
failed or interrupted git command leaves `.git/index.lock` or `.git/HEAD.lock`
behind, and every later git command then reports "another git process seems to
be running". Move the lock aside (`mv .git/index.lock _to_delete/`) rather than
assuming a real concurrent process — check the lock's age first. `git commit`
succeeds despite the warnings it prints. Working directly on the Windows
filesystem avoids this entirely.

---

## Verification debt

`11_UI_UX_STANDARDS.md` §Verification register holds nine platform assumptions
(V-01 … V-09) made because the Tryton documentation site timed out. **UI-009
closes this and should run before any screen is built.**

Partially discharged by the Accounting chat, which verified the following
against a live Tryton 8.0.0 install and the 8.0 source. Anyone writing a
module should read these first — most Tryton material online is 7.x:

- 8.0 registers Pool classes from `[register]` sections in `tryton.cfg`, not
  from `register()` in `__init__.py` (which is deprecated and warns).
- 8.0 uses `pyproject.toml` with hatchling + hatch-tryton; there is no
  `setup.py`. Version pins derive from `tryton.cfg` `depends`.
- Scenario tests are unittest `load_tests` doctests. **pytest collects zero of
  them and reports success.** Use `python -m unittest`.
- There is no `account_us` module and never has been; `account_es` and
  `account_de_skr03` were removed in 8.0. A US chart is a build, not an
  install. **With ADR-0006 settled, the relevant question is whether a Canadian
  chart module exists — check before assuming one does.**
- `account.account.kind` was merged into the type model in 5.2. Move numbering
  comes from the fiscal year / period (`move_sequence`, `ir.sequence.strict`),
  not from the journal.

---

## Repo / project sync

The repository on disk and the Claude project are both used, and there is no
automatic sync. Anything written to one must be written to the other in the
same session.

Note for any chat that starts by listing the repository or calling
`project_info`: **both views can lag.** A chat on 2026-08-19 listed
`docs/specs/` (3 files) and `project_info` (2 docs), concluded fifteen
specifications were missing, and wrote them — while other chats were writing
the real versions. Three project documents were overwritten as a result; two
were restored from disk, one (`10_REPORTING.md`) was rewritten later the same
day by its own chat. **Re-check both views immediately before writing, and
prefer filling gaps over replacing anything you did not just read.**

This trap recurred on the same day. A second chat's `device_list_dir` returned
four empty directories and three spec files for a repository that in fact held
167; it drafted a full foundation package on that basis before a shell listing
showed the real tree. Nothing was written. **A directory listing that looks
implausibly empty is more likely to be a stale view than an empty repository —
confirm with a second method before concluding anything is missing.**

The Accounting chat wrote to both. Note that the repository also contains code
(`modules/`, `scripts/`, `infra/`, `Makefile`) that has no project-doc
equivalent — the project holds the documents, the repository holds the build.

---

## Next actions, in order

0. **Resolve R1 — find the Accounting implementation or correct the record.**
   See the box in § Where the build actually is and
   `docs/tasks/FND-002-architecture-baseline.md`. Nothing in Accounting should
   start until this is settled, and no ACC task should be marked done on the
   strength of the table below.
1. ~~Answer ADR-0006 (operating jurisdiction).~~ **Done — Canada.**
2. **Answer ADR-0002 (costing) and ADR-0008 (stock accounting method).** Both
   are cheap now and require a restatement later. These are now the highest
   leverage open items.
3. **Obtain the Odoo chart of accounts export** so ACC-101 can start. ADR-0006
   no longer blocks it. Check the export for US tax codes or US-form accounts —
   if any appear, ADR-0006 is wrong and must be superseded before Gate 1.
4. **Resolve the two numbering defects (Q8).** Renumber one of the two `14`
   documents — `16` is free — and confirm `OPS-###`. Then update
   `README.md` §Specification index, which currently omits `14_PRODUCTION_CUTOVER.md`,
   `16_DOMAIN_TASK_TEMPLATE.md` and `17_STATUS_TEMPLATE.md`.
5. ~~Decide the authoritative spec directory (Q9).~~ **Done — `docs/specs/`,
   ADR-0010.** The follow-on is Q10: reconcile the repository and project ADR
   sets, which currently collide on numbers 0002 and 0003.
6. **Run UI-009** to close the remaining verification register entries.
7. **Wire CI** (ACC-011 / TEST-015). The Accounting suite is the first real
   test signal this build has; it should be running on every push.
8. ~~**Reconcile module naming.**~~ **Done — ADR-0011.** Tryton modules are
   `capital_nutrition_*`; standalone distributions keep `capnut-*`. Follow-on,
   for the Purchasing chat when `PUR-001` starts:
   `docs/tasks/PURCHASING_TASKS.md` still says `capnut_purchase` in four places.
9. **Add `capital_nutrition_sale` to `Makefile` `MODULES` and CI, or remove it** —
   it is currently in neither, so its 31 tests never run
   (`docs/specs/08_SALES.md` records it as an unapproved proposal). R3 in
   `FND-002`.
10. **Deepen `12_INTEGRATION_CONTRACTS.md` before the first cross-domain task.**
    It names inputs and outputs but no payload shapes, cardinalities or failure
    semantics, so two domains can each satisfy it and still not interoperate.
    R5 in `FND-002`.

---

## How to update this file

Every chat that changes anything updates this file in the same session, in
both the repo and the project. State what changed, what is now blocked or
unblocked, and what the next chat should pick up. A status file that lags is
worse than none, because it is trusted.
