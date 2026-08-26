# CAPITAL NUTRITION ERP — SALES SPECIFICATION

## Objective

Build one consistent sales workflow for Magento-origin and ERP-origin orders.

## Order origins

Every order must identify its origin, such as:
- Magento
- ERP/phone/manual
- other approved future channel

Use explicit origin/channel fields rather than inferring origin from side effects.

## Sales lifecycle

Support:
- quote where required
- order
- reservation/availability
- fulfillment
- shipment
- invoice
- payment
- cancellation
- return/credit

## Pricing

Support:
- standard pricing
- customer-specific pricing
- quantity breaks
- discounts
- promotions where defined
- effective dates

Pricing must be deterministic and auditable.

## Fulfillment

Support:
- full fulfillment
- partial fulfillment
- backorder
- cancellation
- shipment tracking

Inventory is authoritative for availability.

## Accounting

Sales must integrate with:
- AR
- revenue
- tax
- inventory/COGS
- payments
- refunds

## Magento

Magento-origin orders must retain:
- external order ID
- external line IDs
- channel
- currency
- totals
- discounts
- taxes
- payment information
- product mapping

## ERP-origin orders

ERP users must be able to create orders that follow the same operational and accounting rules and can be sent to Magento where applicable.

## Acceptance scenarios

- normal order
- discounted order
- tax-bearing order
- partial fulfillment
- cancellation
- return
- refund
- ERP-origin order
- Magento-origin order
- duplicate external order event
- payment mismatch
