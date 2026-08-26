# CAPITAL NUTRITION ERP — PURCHASING SPECIFICATION

## Objective

Provide reliable purchase-to-pay operations and Capital Nutrition-specific vendor purchasing logic.

## Standard workflow

Support:

PO → receipt → vendor bill → payment

with:
- partial receipt
- partial billing
- over-receipt handling
- three-way match
- GRNI/accrual behavior where applicable

## Vendor pricing

Support:
- vendor-specific product
- vendor SKU
- price
- quantity breaks
- case-pack/order multiples
- lead time
- effective dates where required

## Reordering

A reorder mechanism/report should consider:
- current availability
- reservations
- expected receipts
- demand
- minimum levels if configured
- vendor lead time
- case-pack multiples
- price breaks

Do not automatically place orders without an explicit approved workflow.

## Accounting integration

Purchasing must correctly feed:
- inventory
- AP
- accrual/GRNI
- landed cost

## Acceptance

A purchaser can:
1. identify a reorder need
2. create a PO
3. have the system select the correct vendor price break
4. respect case-pack multiples
5. receive partially
6. match the bill
7. resolve discrepancies
8. complete payment
9. see correct accounting and inventory.
