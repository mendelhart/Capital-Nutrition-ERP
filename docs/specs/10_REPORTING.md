# CAPITAL NUTRITION ERP — REPORTING SPECIFICATION

## Objective

Build reports around the information management actually uses.

## Architecture

Reporting should be sufficiently separated from transactional logic that expensive reports cannot compromise the ledger.

Use:
- dedicated reporting schema where justified
- refresh jobs
- indexes
- defined refresh frequency
- documented source fields

## Initial report families

### Sales
- sales by period
- sales by customer
- sales by product
- sales by channel
- discounts
- returns
- gross margin

### Inventory
- inventory on hand
- inventory valuation
- inventory movement
- slow-moving inventory
- lot/shelf-life exceptions

### Purchasing
- purchases by vendor
- open POs
- vendor pricing
- expected receipts
- purchasing trends

### Finance
- trial balance
- P&L
- balance sheet
- AR aging
- AP aging
- cash/payment status

### Operations
- backorders
- failed integrations
- reconciliation exceptions
- order fulfillment status

## Rule

Start with the reports users actually open.

Do not reproduce an audit catalogue merely for completeness.

## Acceptance

The initial month-end reporting pack can be generated from the ERP and reconciles with approved accounting figures.
