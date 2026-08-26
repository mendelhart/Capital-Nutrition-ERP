# CAPITAL NUTRITION ERP — MAGENTO 1 INTEGRATION SPECIFICATION

## Objective

Build a robust, observable, idempotent integration between the ERP and Magento 1.

The integration is an asynchronous, event-driven boundary. It is never a direct
call from a business transaction into a remote store, and it never resolves a
financial disagreement on its own.

## Ownership boundary

ERP owns:
- the sale, its lines, and its financial totals once accepted
- inventory availability
- the accounting ledger, including payments, refunds, and credit notes
- shipment and tracking data
- the canonical party (see `07_CUSTOMERS.md`)

Magento owns:
- web-store order identity (order ID and increment number)
- web-store customer identity
- storefront presentation, catalogue display, and storefront-specific data
- the storefront checkout record, including whatever payment artefact the
  storefront holds

Where payment authorisation and capture actually occur — in Magento, at the
gateway, or elsewhere — is a Phase 0 question, not an assumption. The ERP owns
the accounting ledger regardless of where capture happens.

Neither system silently overwrites the other's fields. Divergence is recorded and
reported by reconciliation; it is not applied.

An inbound Magento payload never mutates an ERP-owned financial field on an
already-posted document. It creates a new event to be reviewed.

## Phase 0 — reconnaissance

No connector code begins before the reconnaissance map is written and approved.

The map must document:
- exact Magento version and edition
- Magento vs OpenMage status, and the upgrade/maintenance position
- API availability (SOAP v1, SOAP v2, REST) and which are enabled
- API limitations discovered by inspection, not assumed
- customizations, overridden core classes, and third-party extensions in play
- authentication mechanism and credential handling
- required endpoints per flow, with the exact call and payload shape
- data fields available per endpoint, and fields that are missing
- webhook/event capabilities, or their absence
- rate limits, timeouts, and observed latency
- gaps that require a custom Magento module

Every entry is a stated fact with its source: an admin screen, a code path, an
observed API response, or a vendor document. Nothing in the map is inferred.

The map lands at `docs/specs/09_MAGENTO_RECON.md` and is referenced by every
downstream MAG task. Where a fact cannot be established, the map records it as
UNKNOWN rather than guessing.

**Gate:** MAG-002 onward are blocked until the map is approved.

## Integration architecture

Required components:

- **Event record** — the durable unit of work, inbound and outbound.
- **External-reference mapping** — the persistent link between an ERP record and its Magento counterpart.
- **Queue** — ordered, durable, worker-consumed.
- **Retry policy** — classified, bounded, backed off.
- **Dead-letter queue** — terminal parking for events that must not retry.
- **Replay** — authorised re-processing of a stored event.
- **Reconciliation** — periodic comparison that reports, never repairs.

No business logic lives in the transport layer. The connector translates and
enqueues; domain code applies effects.

### Event model

An event record carries at minimum:
- external identifier
- event type
- direction (inbound / outbound)
- raw payload as received or as sent
- payload hash
- state
- attempt count
- next attempt time
- first-seen and last-attempt timestamps
- error classification and last error detail
- resulting ERP record reference, once applied

States: `pending`, `processing`, `retrying`, `failed`, `dead_lettered`, `processed`.

The state machine is explicit. An event moves forward only through defined
transitions, and every transition is recorded.

### Idempotency

The event model must enforce:

`UNIQUE(external_id, event_type)`

Duplicate events must be acknowledged without repeating business effects.

Acknowledged means: the duplicate is recognised, recorded as a duplicate,
returned as success to the caller, and produces no second invoice, no second
payment, no second stock move.

Idempotency is enforced at the database constraint, not only in application code.
A race between two workers must be resolved by the constraint.

Where a payload for an already-seen `(external_id, event_type)` differs from the
stored payload, the difference is recorded and surfaced. It is not applied and
it is not discarded.

### External-reference mapping

Each mapping records:
- ERP model and record ID
- external system identifier
- external ID
- external secondary identifier where relevant (for example an order increment number)
- date the link was established

Constraints are stated per flow. They are not uniform, and no flow inherits a
default cardinality.

- Sales: one Magento order maps to exactly one ERP sale, and the reverse.
- Customers: one ERP party may hold many Magento customer mappings. One Magento
  customer mapping to more than one ERP party is invalid and must be rejected by
  constraint. See `07_CUSTOMERS.md`, "Legitimate multiplicity".
- Any further flow states its cardinality explicitly before implementation.

The customer mapping is specified in `07_CUSTOMERS.md`; this document does not
restate it. Where the two disagree, `07_CUSTOMERS.md` governs the party and this
document governs the transport.

## Inbound

### Orders

Magento order → ERP sale.

Requirements:
- deterministic mapping from Magento order identity to ERP sale identity
- external line identifiers preserved per line
- an order is never created against a party that was invented to satisfy it
- customer-before-order ordering is handled explicitly; a customer that has not
  yet matched parks the order rather than losing it

### Customers

Magento customer → ERP party mapping.

Matching, deduplication, ambiguity handling, and merge are specified in
`07_CUSTOMERS.md`. This domain owns only the event, the transport, and the
mapping record.

### Money

Support:
- payments
- refunds
- credit memos
- cancellations

Money events are the highest-risk path. Requirements:
- every money event is idempotent by construction
- a partial refund is a first-class case, not an edge case
- a refund whose parent sale is not yet present parks rather than fails
- no money event auto-corrects an existing posted move
- accounting effects follow `03_ACCOUNTING.md`; this document does not restate them

## Outbound

### Inventory

ERP availability → Magento.

Pushes should be:
- throttled
- debounced
- batched where possible

A burst of stock moves on one SKU results in one push carrying the settled
figure, not one push per move. The debounce window and batch size are
configuration, and their values are an open question until load is observed.

Push failure never blocks the ERP stock move that triggered it.

### Fulfillment

ERP shipment → Magento shipment/tracking.

Partial shipments and multiple tracking numbers per order must be supported.

### ERP-origin orders

ERP-created orders may be pushed to Magento according to the approved channel
contract.

Per `00_MASTER_BUILD.md`, ERP-origin orders are valid and must be represented
consistently with Magento-origin orders. This is not optional.

An ERP-origin order must not be re-imported back into the ERP as a new sale. The
mapping record established at push time is what prevents the round trip.

What remains open is the channel contract itself: which orders are pushed, in
what state, and how Magento is expected to display them. That contract must be
approved before `MAG-017`.

## Retry

Classify errors:
- transient
- permanent
- unknown

Transient errors:
- exponential backoff
- jitter
- retry limit

Permanent errors:
- dead-letter immediately

Unknown errors are retried under the transient policy with a lower limit, then
dead-lettered. An unclassified error is never retried indefinitely.

The classification table is explicit, versioned, and testable. A new Magento
fault code is added to the table deliberately; it does not fall through to a
default that happens to be convenient.

## Operator dashboard

Show:
- pending
- retrying
- failed
- dead-lettered
- processed
- recent throughput
- synchronization lag

Allow authorized replay.

Replay requirements:
- replay is permissioned, not open to every ERP user
- every replay is recorded with actor, time, and reason
- replay re-enters the same idempotent path, so replaying a processed event
  produces no second business effect

## Reconciliation

Nightly reconciliation should compare:
- order counts
- totals
- payments
- refunds
- status
- inventory availability

It reports discrepancies. It never silently changes money.

Output is a dated report, retained, with each discrepancy identified well enough
to be actioned: the record on both sides, the field, and both values.

A discrepancy that has been reviewed and accepted is marked as such so it stops
appearing as new.

## Observability

Beyond the dashboard:
- every event is traceable end to end by its external identifier
- credentials and payment instrument data never appear in logs or stored payloads
- synchronization lag is measurable and alertable
- dead-letter arrivals are alertable

## Security

- No production credentials in the repository.
- API credentials are scoped to the minimum required.
- Stored payloads are reviewed for personal and payment data before retention
  periods are set.

## Required scenarios

Test:
- duplicate order
- duplicate payment
- partial refund
- failed API call
- permanent API error
- replay
- large batch
- inventory debounce
- ERP-origin order
- reconciliation discrepancy

Additional scenarios required by this specification:
- refund arriving before its parent sale
- order arriving before its customer has matched
- same `(external_id, event_type)` arriving with a changed payload
- two workers processing the same event concurrently
- dead-lettered event replayed after the underlying fault is fixed
- outbound inventory push failing while the ERP stock move succeeds

## Acceptance

The integration is accepted when:

- No scenario in the list above produces a duplicated financial effect.
- Every failure path terminates in a known state: processed, dead-lettered, or parked for review.
- The nightly reconciliation for a representative period reports zero unexplained discrepancies.
- An operator can find any order by its Magento increment number and see its full event history.
- An authorised replay of any processed event changes nothing.
- The accountant's month-end tie-out (see `03_ACCOUNTING.md`) is unaffected by integration activity.

## Open questions

Do not invent:
- the exact Magento version, edition, and OpenMage status
- which APIs are enabled and what they actually return
- whether a custom Magento module is required, and for which flows
- rate limits and safe concurrency
- the retry limits, backoff base, and jitter range
- the inventory debounce window and batch size
- the channel contract for ERP-origin order push: which orders, in what state
- the payment method mapping between Magento and ERP
- the tax figure of record when Magento and ERP disagree
- the reconciliation tolerance, if any, for rounding
- payload retention period and redaction rules
- who operates the dashboard and holds replay permission
- how Magento represents refunds and credit memos, and whether partials are supported

Mark them as open until the Phase 0 reconnaissance map and business approval exist.
