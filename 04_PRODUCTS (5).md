# CAPITAL NUTRITION ERP — PRODUCTS SPECIFICATION

## Objective

Create a reliable product master shared by sales, purchasing, inventory, accounting, reporting, and Magento.

## Product master

Define:
- SKU
- product name
- description
- product type
- active/inactive
- unit of measure
- sales unit
- purchasing unit
- inventory unit
- case-pack quantity
- barcode/identifiers
- product category
- accounting category
- tax configuration
- weight/dimensions where required

## Packaging

Support product relationships where one sellable form represents multiple physical units.

Examples:
- individual unit
- case
- carton

Avoid ambiguous conversion logic.

## Pricing

Product data must support:
- standard price
- customer/vendor-specific prices where appropriate
- quantity breaks
- effective dates if required

Pricing rules belong in the appropriate sales/purchasing domain; product master should provide the underlying identifiers and relationships.

## Magento relationship

Maintain explicit ERP ↔ Magento product mapping.

Never assume SKU equality unless the integration contract explicitly establishes it.

## Data quality

Prevent:
- duplicate SKUs
- ambiguous units
- invalid conversions
- orphaned product mappings

## Migration

Product migration must include:
- source identifier
- target identifier
- mapping status
- exceptions
- validation

## Acceptance

A product can be created once and then correctly used in:
- purchase order
- receipt
- inventory
- sales order
- shipment
- invoice
- Magento synchronization
- reporting.
