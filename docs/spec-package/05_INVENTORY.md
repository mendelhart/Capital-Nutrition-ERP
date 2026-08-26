# CAPITAL NUTRITION ERP — INVENTORY SPECIFICATION

## Objective

Provide authoritative inventory quantities, locations, lots, valuation, and warehouse workflows.

## Scope

- warehouses
- location tree
- stock moves
- receipts
- shipments
- internal transfers
- reservations
- availability
- lots
- shelf life
- quantity precision
- costing
- landed costs
- period close

## Warehouse model

Define:
- warehouses
- stock locations
- receiving locations
- shipping locations
- inventory adjustment locations
- transit locations if needed

## Lots and shelf life

Use lot tracking where required.

Support:
- lot identifier
- expiration/shelf-life date
- receipt association
- movement history

## Quantity precision

Test repeated partial movements and conversions.

The system must not accumulate material drift from repeated operations.

## Costing

The costing method must be explicitly selected and documented in an ADR.

The initial plan calls for testing the ability to reconstruct:
- quantity at an arbitrary historical date
- valuation at an arbitrary historical date

## Landed cost

Determine whether the selected Tryton landed-cost functionality correctly handles costs that arrive after inventory has already been consumed.

If standard behavior is insufficient, document and implement the smallest safe extension.

## Inventory accounting

Inventory transactions must connect correctly to accounting according to the Accounting specification.

## Period close

Inventory and accounting period close must have coordinated behavior.

## Acceptance scenarios

- receive stock
- transfer stock
- reserve stock
- ship stock
- partial shipment
- return stock
- lot-tracked movement
- historical quantity query
- historical valuation query
- landed cost
- month-end close
- 10,000 randomized partial quantity movements without material drift
