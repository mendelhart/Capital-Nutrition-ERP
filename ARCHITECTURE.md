# CAPITAL NUTRITION ERP — ARCHITECTURE

**Status:** Working architecture. Authoritative.
**Last updated:** 2026-08-19 (ERP Architect chat, task `FND-002`)
**Applies to:** Tryton 8.0.9 · PostgreSQL 16.13 · Magento 1.9.4.2 · migration from Odoo

---

## 0. How to use this document

This is the one working architecture document. `docs/spec-package/01_ARCHITECTURE.md`
is the pristine build package and is read-only history; where the two differ, this
document governs (ADR-0013, *One working architecture document*).

It defines boundaries, not features. If you are implementing a domain, read this
first, then your domain specification in `docs/specs/`, then
`docs/integration/12_INTEGRATION_CONTRACTS.md`.

**Rule for readers:** anything stated here is binding on every domain. Anything a
domain wants that contradicts it is an architecture change and needs an ADR — not
a local exception, not a comment, not a `TODO`.

**ADR citation.** The repository's `docs/adr/` and the Claude project's ADR set
collide on numbers 0002–0008 (`docs/STATUS.md` Q10). **Cite every ADR by number
*and* title.** This document cites repository ADRs. Numbers 0004–0008 remain
unassigned in the repository until the two sets are reconciled.

---

## 1. What this system is

Capital Nutrition Inc. is replacing Odoo with a company-owned ERP built on Tryton,
operated by roughly three users and maintained by its owner rather than a vendor.

```
        Accountant / Operators (~3)
                   │  Tryton client (Sao web / desktop)
                   ▼
   ┌──────────────────────────────────┐        async, event-driven
   │        TRYTON ERP  8.0.x         │◄──────────────────────────► Magento 1.9.4.2
   │  system of record for operations │        (active selling site)
   │  and for the general ledger      │
   └──────────────────────────────────┘
                   │
                   ▼                              one-way, read-only,
          PostgreSQL 16 (single DB)  ◄───────────  ends at cutover
                                                  Odoo (legacy, migration source)
```

Three facts follow from that picture and constrain everything below.

1. **The ERP is the system of record.** Not the storefront, not the legacy system,
   not a spreadsheet, not a report.
2. **Magento is a peer that the ERP talks to asynchronously.** It is the active
   selling site and it stays live. It is never in the transaction path of an ERP
   write.
3. **Odoo is a source, not a system.** Data flows out of it once, is reconciled,
   and the connection is severed at cutover.

---

## 2. System boundaries

| System | Version | Role | Direction | Transport | Lifetime |
|---|---|---|---|---|---|
| Tryton ERP | 8.0.9 | System of record: operations and ledger | — | — | permanent |
| PostgreSQL | 16.13 | The ERP's only datastore | — | libpq, private network | permanent |
| Magento | 1.9.4.2 | **Active selling site.** Storefront identity and web presentation | bidirectional, asynchronous | HTTP API, exact endpoints per `docs/specs/09_MAGENTO.md` Phase 0 | permanent, until a separate project replaces it |
| Odoo | legacy | **Migration source only** | outbound to ERP, one-way, read-only | offline snapshot → `migration/` toolkit | ends at cutover |

### 2.1 The Magento boundary

Magento 1.9.4.2 is the active selling site and remains so. The coupling is fixed by
ADR-0012, *Magento is an asynchronous peer; Odoo is a one-way source*. The
boundary rules are binding on every domain:

- **Asynchronous only.** No business transaction in the ERP makes a synchronous
  call to Magento. A stock move, an invoice posting or a shipment confirmation
  completes on ERP state alone; the push to Magento is enqueued and happens after
  commit. A Magento outage must never be able to block a sale, a posting or a
  count.
- **Never a financial source of truth.** Magento may state what the storefront
  charged; the ERP states what was earned, owed and paid.
- **Never a silent corrector.** An inbound payload never mutates an ERP-owned
  field on a posted document. Divergence is recorded and reported. See
  `docs/specs/09_MAGENTO.md` § Ownership boundary.
- **Facts before code.** Magento's edition, OpenMage status, available APIs, rate
  limits and customisations are established by the Phase 0 reconnaissance map
  (`docs/specs/09_MAGENTO_RECON.md`) before any connector is written. The version
  above is a project fact; everything else about that installation is unverified
  until Phase 0 lands.
- **One integration module.** All Magento-specific code lives in
  `capital_nutrition_magento` (§4). No domain module contains a Magento API call,
  a Magento field, or the word "magento" in a model name outside that module and
  the mapping models it owns.

### 2.2 The Odoo boundary

Odoo is the migration source and nothing else (ADR-0012, *Magento is an
asynchronous peer; Odoo is a one-way source*).

- Extraction is **read-only**, from a controlled snapshot, by the standalone
  `migration/` toolkit. The ERP never connects to Odoo at runtime.
- No Tryton module imports from `capnut_migration`, and no Tryton module carries
  an Odoo-shaped field. Legacy identifiers are retained only where a specification
  requires them for reconciliation (for example the Odoo party ID,
  `docs/specs/07_CUSTOMERS.md` § External identifiers) and they are inert
  reference data thereafter.
- After cutover, Odoo is a frozen archive. Any later need for Odoo data is a
  read against that archive, not a re-opened integration.
- The migration toolkit is **disposable by design**: when the third rehearsal and
  the cutover are done, it stops being a dependency of anything.

### 2.3 What is not in this system

The ERP has one database, one application, and the two external systems named
above. There is no other integration, no second datastore, and no additional
external service in this build. Adding one is an ADR.

---

## 3. Source of truth

The default is `00_MASTER_BUILD.md` § Source of truth: **the ERP owns operational
and financial records; Magento owns web-store identity and presentation.** The
register below is the specific form of that rule. Every major entity has exactly
one owner.

| Entity | Owner | Written by | Magento's part | Conflict rule |
|---|---|---|---|---|
| Chart of accounts, journals, fiscal periods | ERP | Accounting configuration | none | n/a |
| Journal entries / moves | ERP | Accounting posting rules only | none | posted moves are immutable |
| Customer invoices, credit notes, AR | ERP | Accounting, from sales documents | none | inbound payload never edits a posted document |
| Vendor bills, AP | ERP | Accounting, from purchasing documents | none | as above |
| Payments, refunds | ERP ledger | Accounting | Magento holds the storefront checkout artefact | ERP figure is the ledger figure; a mismatch is flagged, never auto-corrected |
| Tax amounts posted | ERP | Accounting | Magento computes what it charged | figure of record on disagreement is **OPEN** (`09_MAGENTO.md`) |
| Canonical party | ERP | Customers domain | Magento customer ID(s), storefront login and address book | one party may hold many Magento identities; the reverse is invalid |
| Billing address, payment terms, credit, receivable account | ERP | Customers domain | none | inbound never overwrites |
| Product master, SKU, UoM, case pack, categories | ERP | Products domain | web presentation fields (title, copy, images, storefront category) | mapping is explicit; SKU equality is never assumed |
| Price actually charged on an ERP document | ERP | Sales/Purchasing pricing resolution | storefront quotes its own price | divergence flagged for review |
| Stock quantities, locations, lots, moves | ERP | Inventory domain | receives availability updates only | ERP availability is authoritative; a failed push never rolls back a stock move |
| Inventory valuation / COGS | ERP | Inventory + Accounting | none | method fixed by ADR (**OPEN**, see §12) |
| Sale order and its lines, once accepted | ERP | Sales domain | order ID and increment number | one Magento order ↔ one ERP sale |
| Order provenance (channel) | ERP | set at creation, read-only after draft | none | never inferred from side effects |
| Shipments and tracking | ERP | Inventory/Sales | receives shipment + tracking | ERP is authoritative |
| Purchase orders, receipts | ERP | Purchasing domain | none | n/a |
| Inbound external events | ERP | `capital_nutrition.external.event` only | Magento is a `source` value | see §5 |
| ERP↔external record mapping | ERP | `capital_nutrition_magento` mapping models | Magento supplies the external IDs | cardinality stated per flow |
| Reports and extracts | derived | reporting layer, read-only | none | a report is never a source of truth |

**Corollaries.**

- An ERP-origin order is a first-class order. Nothing in the ERP may treat
  "no external identifier" as an incomplete record.
- Nothing outside the accounting domain writes a journal entry. Sales, purchasing,
  inventory and the Magento connector produce *documents*; posting is accounting's.
- No domain stores a second copy of another domain's identity. If you need a
  product, hold a reference to the product, not a SKU string.

---

## 4. Module architecture

### 4.1 Layers

1. **Tryton standard modules** — used wherever they express the requirement.
   Configuration is preferred over code, and standard behaviour is preferred over
   configuration that mimics something else.
2. **Capital Nutrition domain modules** — extend standard models. A module is
   justified only by a genuine Capital Nutrition requirement that standard Tryton
   cannot express by configuration. Record the requirement in the module's
   `README.rst` and in the task file.
3. **Integration modules** — adapters to external systems. Translation, mapping,
   transport, queueing, retry and reconciliation state. No business rules.
4. **Reporting layer** — read-only, see §9.
5. **Standalone tooling** — the `migration/` package. Outside the Tryton runtime.

### 4.2 Naming

Tryton modules are named `capital_nutrition_<domain>`; the XML/model prefix is
`capital_nutrition.` (ADR-0011, *Module and package naming*). Standalone Python
distributions outside the Tryton runtime keep the short form (`capnut-migration`,
console script `capnut-migrate`). `capnut_core`, `capnut_purchase`,
`capnut_magento` and `capnut_report` as **Tryton module** names are superseded.

### 4.3 Module map

Only `capital_nutrition_base` and `capital_nutrition_sale` exist today. The rest
are the sanctioned names for work not yet started — creating one still requires a
justified requirement.

| Module | Status | Depends on | Owns | Must not |
|---|---|---|---|---|
| `capital_nutrition_base` | exists | `ir`, `res` | the external-event idempotency ledger; cross-cutting primitives with no domain of their own | contain domain logic, or depend on any domain module |
| `capital_nutrition_account` | not started | `account`, `account_invoice`, `_base` | Capital Nutrition accounting configuration and any justified posting extension | be bypassed by another domain writing moves directly |
| `capital_nutrition_product` | not started | `product`, `_base` | product-master extensions (case pack, identifiers) | hold storefront presentation fields |
| `capital_nutrition_stock` | not started | `stock`, `_base` | inventory extensions, landed-cost gaps | post to the ledger itself |
| `capital_nutrition_purchase` | not started | `purchase`, `_base` | vendor pricing/reorder extensions (`docs/tasks/PURCHASING_TASKS.md`) | duplicate product identity |
| `capital_nutrition_party` | not started | `party`, `_base` | party extensions, match/merge support | fork `party.party` |
| `capital_nutrition_sale` | exists — **proposal, unapproved** | `sale`, `_base` | sale channel/origin, external line identifiers | add an order-level external ID column (`docs/specs/08_SALES.md`) |
| `capital_nutrition_magento` | not started | domain modules it maps, `_base` | Magento mapping models, connector, queue plumbing, reconciliation reports | contain business rules, or be depended on by a domain module |
| `capital_nutrition_report` | not started | read access only | report definitions | write to any transactional model |

### 4.4 Dependency rules

- Dependencies point **inward and downward**: integration → domain → base →
  standard Tryton. Never the reverse, never sideways between domain modules
  without a documented contract in `docs/integration/12_INTEGRATION_CONTRACTS.md`.
- No cycles. `tryton.cfg` `depends` is the declaration of record.
- A module reaches another domain only through public Tryton models, documented
  extension points, or an integration contract. Convenience is not a reason.
- Registration is declared in `tryton.cfg` `[register]`, not `Pool.register()`
  (ADR-0003, *Modules in-repo, symlinked into trytond for development*).
- Every module ships its own tests and is listed in the `Makefile` `MODULES`
  variable and in CI. **A module that is not in both is not tested.**

---

## 5. Integration architecture

### 5.1 One idempotency mechanism

Every inbound external event is registered exactly once in
`capital_nutrition.external.event` before any domain code acts on it, keyed
`(source, event_type, external_id)` under a **database** unique constraint
(ADR-0002, *A single external-event ledger for integration idempotency*).

- Per-integration de-duplication columns are forbidden. `magento_order_id` on the
  sale is the named anti-pattern.
- A known key arriving with a different payload digest raises and is surfaced. It
  is never applied and never overwritten.
- Domain modules extend `_get_origin()` to declare which of their models an event
  may point at. They do not extend the keying scheme.
- "Which ERP record came from external event X?" is answered from the ledger.

### 5.2 Asynchronous work: what the platform gives us, and what it does not

Verified against the installed `trytond` 8.0.9 package:

- `ir.queue` exists (`trytond/ir/queue_.py`), with `Model.__queue__` as the
  caller, `push`/`pull`, `scheduled_at` and `expected_at`, and PostgreSQL
  `LISTEN`/`NOTIFY` wake-up.
- `trytond-worker` and `trytond-cron` are installed console scripts.
- Failure handling is thin: the worker reschedules only on
  `DatabaseOperationalError`; a `UserError`/`UserWarning` is reported to `ir.error`
  and **not** retried; any other exception is logged and the task ends.

**Decision (ADR-0014, *Tryton's own queue for asynchronous integration work*):**
use `ir.queue` and `trytond-worker`. Do not introduce Celery, Redis, RabbitMQ or
any external broker.

**Consequence, and this is the part that matters:** `ir.queue` is transport. It is
not the integration's state machine. Attempt counts, error classification, backoff,
dead-lettering, parking and replay live in the integration's own event records —
the ledger in §5.1 and the Magento event model in `docs/specs/09_MAGENTO.md`
§ Integration architecture — which are durable, queryable and operator-visible.
A design that relies on the queue to remember a failure is wrong.

### 5.3 Boundary rules for every integration

- Enqueue after commit; never call a remote system inside a transaction that
  writes financial or inventory data.
- Outbound pushes are throttled, debounced and batched; a burst on one SKU
  produces one push carrying the settled figure.
- A failed outbound push never rolls back the ERP change that triggered it.
- Errors are classified transient / permanent / unknown from an explicit,
  versioned, testable table. Nothing retries indefinitely.
- Replay is permissioned, recorded (actor, time, reason) and re-enters the same
  idempotent path, so replaying a processed event changes nothing.
- Reconciliation **reports**; it never repairs. Financial discrepancies are
  surfaced to a human.
- Every event is traceable end to end by its external identifier.

---

## 6. Data and database

- PostgreSQL is the only supported backend, in development, CI and production
  (ADR-0001, *Tryton 8.0.x and PostgreSQL 16 as the foundation*). The suite
  refuses to run on sqlite (`tests/test_backend.py`).
- **Invariants belong in the database** where the database can hold them:
  uniqueness, idempotency keys, referential integrity, check constraints, and
  exclusion of invalid states. An application-level check is a convenience on top,
  never the only guard. Concurrency is resolved by the constraint, not by a
  Python helper.
- Money and quantities use `Numeric`/`Decimal` with declared precision. Never
  binary floating point in a financial or inventory path.
- One identity per concept. A second column that means the same thing as an
  existing key is a defect.
- Timestamps are stored in UTC; the business-day timezone is a single documented
  setting (`OPS-003`).
- Indexes follow measured access patterns, not speculation.
- Schema change reaches the database only through Tryton module update on a fresh
  or migrated database. Ad-hoc DDL against production is not a workflow.

---

## 7. Security

- **No credential, key or production connection string in the repository, ever.**
  `.env.example` and `etc/trytond.conf.template` are the committed shapes;
  `migration/config/migration.toml` is gitignored and stays on the operator's
  machine.
- Staging and production credentials are distinct. Tests never use production
  credentials or production data.
- PostgreSQL is reachable only from the application network — no public port,
  admin access by bastion or VPN (`docs/specs/14_PRODUCTION_CUTOVER.md` § 1).
- API credentials are scoped to the minimum the flow needs.
- Least privilege inside the ERP too: Tryton groups gate who may post, close a
  period, edit a party, and replay an event. Replay and reconciliation-override
  are privileged actions, not general user actions.
- Personal data is in scope for PIPEDA (Canada, ADR-0006 in the project set,
  *Operating jurisdiction*). Stored payloads are reviewed for personal and payment
  data before retention periods are set; credentials and payment instrument data
  never appear in logs or stored payloads.
- Sensitive administrative actions are auditable: who posted, who closed, who
  replayed, who merged two parties.
- Backups are encrypted and the key custody register is maintained
  (`docs/ops/key-custody.md`).

---

## 8. Extensibility

- **Extend, do not fork.** Inherit standard models; never copy a Tryton model to
  change three lines.
- Use the sanctioned extension points: `__setup__` and field/`states` extension,
  view inheritance, `_get_origin()` on the event ledger, `__queue__` for
  asynchronous calls, `ir.action` and menu XML for navigation.
- **Configuration before code.** A new sales channel, a new journal, a new
  category is data. Adding one must not require a schema migration.
- A custom module needs a written, genuine Capital Nutrition requirement. "Odoo
  did it this way" is not one.
- The user interface is the Tryton client, driven by `ir.ui.view` XML. Anything
  requiring a bespoke front end or custom client code is an **architecture**
  decision and needs an ADR (`docs/specs/11_UI_UX_STANDARDS.md` § 0).
- Platform claims are verified against 8.0.x before they are relied on. Most
  Tryton material online is 7.x. Unverified assumptions go in a verification
  register with an owner, not into a design.

---

## 9. Reporting boundaries

- Reporting is **read-only**. A report never writes to an accounting, inventory or
  sales model, and never holds state another domain depends on.
- A report is derived data. It is never a source of truth and never the input to a
  posting.
- Expensive reporting must not be able to compromise the ledger: long-running
  queries run against read-only access, outside the transaction path of
  operational work. A dedicated reporting schema or materialised views are
  permitted **where justified and measured** — not by default, and their refresh
  frequency and source fields are documented.
- Month-end figures come from accounting, not from a parallel calculation in a
  report. Where a report restates a ledger figure it must tie to it exactly.
- The report catalogue starts from what users actually open
  (`docs/specs/10_REPORTING.md`).

---

## 10. Testing architecture

Levels, in the order a change should meet them:

1. **Unit** — isolated logic, no database.
2. **Model** — Tryton model behaviour and constraints.
3. **Integration** — against PostgreSQL 16, from a database built from scratch.
   CI must not depend on a persistent shared database.
4. **Cross-domain scenarios** — `tests/scenarios/`, named after the contract in
   `docs/integration/12_INTEGRATION_CONTRACTS.md` they prove. **No domain is
   production-ready on isolated tests alone.**
5. **Integration-boundary tests** — replayed real payloads against a Magento
   staging store, not synthetic fixtures alone.
6. **Migration reconciliation** — `make migration-test`, plus the rehearsal gate.
7. **Restore drill** — production recovery is tested, not assumed.

Rules:

- Failure paths are mandatory. A suite that only proves the happy path proves
  nothing about an ERP.
- Every defect gets a regression test.
- Scenario tests are unittest `load_tests` doctests. **pytest collects zero of
  them and reports success** — run them with `python -m unittest`.
- Ownership: a domain owns its module tests; the domain named first in a contract
  owns the scenario that proves it; nobody owns a test that nobody runs — see the
  `MODULES`/CI rule in §4.4.

---

## 11. Migration architecture

- The migration toolkit (`migration/`, distribution `capnut-migration`) is a
  standalone Python package with no `trytond` dependency. It runs beside the ERP,
  not inside it.
- Pipeline: **extract → stage → map → build → load → reconcile**, every stage
  writing an artifact.
- Extraction is read-only from a controlled snapshot; credentials stay with the
  operator.
- Mappings are explicit, reviewable tables. Accounting mappings are reviewed by
  the accountant. Nothing loads against an unapproved mapping.
- Loads are idempotent by `_ref`, so rehearsals are free to repeat.
- **Reconciliation is a gate, not a report** — a non-zero exit blocks cutover.
  Discrepancies are explained or corrected through an approved process; they are
  never absorbed.
- **Inventory is counted at cutover, not copied.** Historical inventory may be
  migrated for reference; opening operational stock comes from an approved
  physical count.
- At least three complete rehearsals; the third must be routine.
- Migration writes no permanent structure into the ERP beyond the legacy
  identifiers a specification requires for reconciliation.

---

## 12. Deployment boundaries

Fixed by architecture:

- Runtime processes are distinct: the **application/web** process (`trytond`),
  the **queue worker** (`trytond-worker`), and **scheduled jobs**
  (`trytond-cron`). Workers are isolated from web workers, and scheduled jobs have
  a single-execution guarantee.
- One PostgreSQL 16 database is the system of record. No second datastore.
- Development runs from a virtualenv with modules symlinked into
  `trytond/modules` (`make link`, ADR-0003); production packaging is an OPS
  decision and may differ, which is the documented fallback in that ADR.
- The environment is rebuildable from committed configuration. Anything done by
  hand on a server gets written down and then automated.
- Staging is built from the same configuration as production, differing only in
  secrets, hostnames and size.
- Secrets come from a secret store or an operator-supplied environment file.

Owned by the production/cutover domain, **not** by this document:
hosting target, container images and digests, reverse proxy and TLS, network
topology specifics, backup/RPO/RTO, monitoring thresholds, capacity, cutover
window. See `docs/specs/14_PRODUCTION_CUTOVER.md` (`OPS-001` … `OPS-071`) and
`docs/runbooks/`.

---

## 13. Failure philosophy

A failure must be **visible, classified, recoverable where possible,
non-destructive and auditable**.

- Never hide an integration or financial failure to make a workflow look
  successful.
- Never let an integration silently correct a financial discrepancy.
- Every failure path terminates in a known state: processed, dead-lettered, or
  parked for review. "Nothing happened and nobody knows" is not a state.
- Prefer a loud missing path to a quiet wrong one.

---

## 14. Architectural decisions still open

These block or shape work and must not be invented by an implementer.

| Decision | Effect on architecture | Where it lives |
|---|---|---|
| Inventory costing method | valuation, COGS, and every inventory-accounting test | project ADR *Inventory costing method* — **BLOCKING** |
| Stock accounting method (continental vs anglo-saxon) | when and to which accounts cost reaches the ledger | project ADR *Stock accounting method* — **BLOCKING** |
| Tax provider and Canadian indirect-tax configuration | whether an adaptor layer exists at all | project ADR *Tax calculation provider*, `docs/specs/03_ACCOUNTING.md` |
| Final Canadian chart of accounts | account mapping for every domain | `OQ-ACC-001`. Verified 2026-08-19: **no Canadian chart module is published for Tryton 8.0** (`trytond_account_ca` does not exist on PyPI; `account_be`, `account_fr` and others do). A Canadian chart is a build, not an install. |
| Magento Phase 0 reconnaissance | every connector design choice | `docs/specs/09_MAGENTO.md`, gates `MAG-002` onward |
| Repository/project ADR reconciliation | every ADR citation in the build | `docs/STATUS.md` Q10 |
| Hosting target and production stack | §12 specifics | `OPS-001`, `OPS-002` |

---

## 15. Changing this document

1. Propose the change in an ADR under `docs/adr/`, using `TEMPLATE.md`.
2. Name the domains affected and the contracts that must change with it.
3. Update this document and `docs/integration/12_INTEGRATION_CONTRACTS.md`
   together — a boundary change that touches only one of them is incomplete.
4. Update the tests on both sides of the boundary.
5. Update `docs/STATUS.md` in the same session, in the repository *and* the
   project.

Never change architecture silently, and never resolve a conflict with an existing
ADR by overriding it in prose. Write the superseding ADR.
