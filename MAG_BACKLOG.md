# CAPITAL NUTRITION ERP — MAGENTO TASK BACKLOG

Domain: Magento 1 Integration
Specification: `docs/specs/09_MAGENTO.md`
Task ID prefix: `MAG-###`

All tasks below are specification-stage unless marked otherwise. Nothing here is
approved for implementation until the Phase 0 reconnaissance map exists and is
approved, and until the open questions in the specification are closed.

## Gate

`MAG-001` is a hard gate. No connector code is written, and no other MAG task
starts, until the reconnaissance map is approved.

## Backlog

### Phase 0
- `MAG-001` Produce the Magento reconnaissance map. **Gate — blocks everything below.**

### Foundation
- `MAG-002` Define the event model, states, and the `UNIQUE(external_id, event_type)` constraint.
- `MAG-003` Define the external-reference mapping model and its constraints.
- `MAG-004` Define the queue and worker model, including concurrency and ordering guarantees.
- `MAG-005` Define the error classification table: transient, permanent, unknown.
- `MAG-006` Define the retry policy: backoff, jitter, limits, and the dead-letter transition.
- `MAG-007` Define the connector/transport layer and credential handling.

### Inbound
- `MAG-008` Inbound customer event → party mapping, using the match strategy from `07_CUSTOMERS.md`.
- `MAG-009` Inbound order event → ERP sale, including line-level external identifiers.
- `MAG-010` Define parking behavior for out-of-order events (order before customer, refund before sale).
- `MAG-011` Inbound payment events.
- `MAG-012` Inbound refund and credit memo events, including partial refunds.
- `MAG-013` Inbound cancellation events.
- `MAG-014` Define payload-divergence handling for a repeated `(external_id, event_type)`.

### Outbound
- `MAG-015` Outbound inventory availability push, with throttle, debounce, and batching.
- `MAG-016` Outbound shipment and tracking push, including partial shipments.
- `MAG-017` ERP-origin order push, per the approved channel contract.

### Operations
- `MAG-018` Build the operator dashboard: queue states, throughput, synchronization lag.
- `MAG-019` Build authorized replay, with permissioning and an audit record.
- `MAG-020` Build nightly reconciliation and its discrepancy report.
- `MAG-021` Define discrepancy acknowledgement so reviewed items stop reporting as new.
- `MAG-022` Define observability: tracing by external identifier, alerting on dead-letter and lag.
- `MAG-023` Define payload retention and redaction.

### Verification
- `MAG-024` Build the required-scenario test set from `09_MAGENTO.md`.
- `MAG-025` Cross-domain integration run: Magento ↔ Sales, ↔ Inventory, ↔ Customers.
  Accounting effects are exercised through Sales; there is no Magento ↔ Accounting contract.
- `MAG-026` Define migration handling for Magento orders that predate cutover.

## Sequencing

`MAG-001` precedes everything.

`MAG-002` through `MAG-007` are the transport foundation and must settle before
any flow is implemented. `MAG-002` and `MAG-003` can proceed in parallel;
`MAG-004` depends on both.

`MAG-008` precedes `MAG-009`: an order is never created against a party that was
invented to satisfy it. `MAG-010` must exist before either is considered done,
or the ordering failure has nowhere to go.

`MAG-011` through `MAG-013` depend on `MAG-009` and on the accounting postings in
`03_ACCOUNTING.md` being settled. Money flows are not implemented against an
unsettled ledger.

`MAG-015` depends on the Inventory domain owning availability. `MAG-016` depends
on Sales and Inventory producing shipments.

`MAG-018` through `MAG-023` depend on the event model but not on any particular
flow, and can proceed alongside inbound work.

`MAG-024` through `MAG-026` are last.

## Blocked

`MAG-002` through `MAG-026` are blocked on `MAG-001`.

Beyond the gate:

- `MAG-004` is blocked on observed rate limits and safe concurrency.
- `MAG-005` and `MAG-006` are blocked on observed Magento fault behavior and rate limits.
- `MAG-008` is blocked on the match-strategy decision in `07_CUSTOMERS.md` (`CUS-011`).
- `MAG-009` is blocked on the tax figure of record when Magento and ERP disagree.
- `MAG-011` is blocked on the payment method mapping decision, and on where
  authorisation and capture actually occur.
- `MAG-012` is blocked on how Magento represents refunds and credit memos, and
  whether partials are supported.
- `MAG-015` is blocked on the debounce window and batch size, which need observed load.
- `MAG-017` is blocked on the approved channel contract for ERP-origin orders.
- `MAG-018` and `MAG-019` are blocked on who operates the dashboard and holds
  replay permission.
- `MAG-020` is blocked on the reconciliation rounding tolerance decision, and on
  the tax figure of record.
- `MAG-023` is blocked on the payload retention decision.

See "Open questions" in the specification.
