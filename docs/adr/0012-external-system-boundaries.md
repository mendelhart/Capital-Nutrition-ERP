# ADR-0012: Magento is an asynchronous peer; Odoo is a one-way source

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** ERP Architect chat (`FND-002`), Morris Hart

## Context

The ERP has exactly two external systems: Magento 1.9.4.2, which is the active
selling site and stays live, and Odoo, which is the legacy system being replaced.

`00_MASTER_BUILD.md` states the ownership principle but not the coupling. Without
a stated coupling rule, two reasonable implementations are available to any
domain chat and they differ in kind:

- call Magento from the transaction that changed the stock, so the storefront is
  never stale; or
- record the change, commit, and push afterwards.

The first is the one people reach for. It also makes a Magento timeout able to
roll back an ERP stock move, and makes the ERP's availability a function of a
system we do not own. The same question exists for Odoo: a "temporary" runtime
read from the legacy database during the parallel run is easy to write and hard
to remove.

## Decision

**Magento is an asynchronous peer.**

- No ERP business transaction makes a synchronous call to Magento. Work is
  enqueued and runs after commit.
- A Magento outage or a failed push never blocks or reverses an ERP write.
- Magento is never a financial source of truth, and an inbound payload never
  mutates an ERP-owned field on a posted document.
- All Magento-specific code lives in `capital_nutrition_magento`.

**Odoo is a one-way, read-only migration source with an end date.**

- Extraction happens offline, from a controlled snapshot, through the standalone
  `migration/` toolkit. The ERP itself never connects to Odoo.
- No Tryton module imports the migration package or carries an Odoo-shaped field.
  Legacy identifiers are retained only where a specification requires them for
  reconciliation, and are inert reference data thereafter.
- At cutover the connection is severed and Odoo becomes a frozen archive. The
  migration toolkit stops being a dependency of anything.

## Consequences

### Accepted costs

- The storefront is eventually consistent. There is a window in which Magento
  shows an availability figure the ERP has already changed, and the debounce
  policy widens it deliberately. Overselling within that window is a business
  risk to be managed by buffer policy, not a bug to be fixed by making the push
  synchronous.
- Every outbound flow needs its own durable state — enqueued, attempted, failed,
  dead-lettered — because "the call returned" is no longer the answer.
- Anything Odoo knows that was not extracted and reconciled before cutover is
  reachable only from the archive, by hand. That raises the cost of an incomplete
  extraction, which is the point: it forces the reconciliation gate to be taken
  seriously while the source is still live.

### Rejected alternatives

- **Synchronous Magento calls in the transaction.** Rejected: it makes ERP
  correctness and availability depend on a remote system, and it puts a network
  call inside a transaction that writes financial data.
- **A background thread rather than a durable queue.** Rejected: an in-process
  thread loses its work on restart, which is silent data loss on the money path.
- **Keep a live Odoo read for the parallel run.** Rejected: the parallel run
  compares two independently operated systems (`docs/runbooks/PARALLEL_RUN.md`).
  A runtime dependency on the system being replaced is exactly what cutover is
  supposed to remove, and temporary integrations are not temporary.

## Verification

Wrong if the business finds the availability lag commercially unacceptable at
observed volume — the reconciliation report's inventory divergence and any
oversell incidents are the observation to watch — or if a required Magento flow
turns out to have no asynchronous form once the Phase 0 map lands.

Check: no ERP model method calls the Magento client directly; every outbound flow
has a durable event record; `grep -ri odoo modules/` returns nothing.
