# CAPITAL NUTRITION ERP — MAGENTO 1 INTEGRATION

## Objective

Build a robust, observable, idempotent integration between the ERP and Magento 1.

## Phase 0 — reconnaissance

Before connector implementation document:
- exact Magento version
- Magento/OpenMage status
- API availability
- API limitations
- customizations
- authentication
- required endpoints
- data fields
- webhook/event capabilities
- rate limits
- gaps requiring a custom Magento module

No connector code should begin before this map is approved.

## Integration architecture

Use:
- event records
- external-reference mappings
- queue
- retry policy
- dead-letter queue
- replay
- reconciliation

## Idempotency

The event model must enforce:

`UNIQUE(external_id, event_type)`

Duplicate events must be acknowledged without repeating business effects.

## Inbound

### Orders
Magento order → ERP sale.

### Customers
Magento customer → ERP party mapping.

### Money
Support:
- payments
- refunds
- credit memos
- cancellations

## Outbound

### Inventory
ERP availability → Magento.

Pushes should be:
- throttled
- debounced
- batched where possible

### Fulfillment
ERP shipment → Magento shipment/tracking.

### ERP-origin orders
ERP-created orders may be pushed to Magento according to the approved channel contract.

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

## Reconciliation

Nightly reconciliation should compare:
- order counts
- totals
- payments
- refunds
- status
- inventory availability

It reports discrepancies. It never silently changes money.

## Acceptance

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
- reconciliation discrepancy.
