# CAPITAL NUTRITION ERP — ACCOUNTING SPECIFICATION

## Objective

Build a financially reliable ERP accounting foundation that an accountant can review, reconcile, operate, and trust.

## Functional scope

### Chart of accounts
Define:
- account numbering
- account names
- account types
- debit/credit behavior
- receivable/payable accounts
- revenue accounts
- expense accounts
- inventory accounts
- tax accounts
- cash/bank accounts
- required analytic dimensions if applicable

The chart must be loadable as code/fixtures and reproducible on a fresh database.

### Fiscal calendar
Support:
- fiscal years
- periods
- period state
- journal sequences
- reproducible setup

### Journals
Define:
- sales
- purchases
- cash/bank
- general journal
- other required journals

### AR
Support:
- customer invoices
- credit notes
- payments
- reconciliation
- aging
- partial payments

### AP
Support:
- vendor bills
- credit notes
- payments
- reconciliation
- aging
- partial payments

### Taxes
Canadian indirect tax: GST, HST and PST/QST, which vary by province and by
product category. Nutrition products in particular may be zero-rated or exempt
depending on classification — this is a tax determination, not a build decision,
and must come from the accountant.

Use a provider/adaptor approach where required.

Do not build a custom tax determination engine unless explicitly approved.

Tax calculations must be testable against the chosen provider.

### Inventory accounting
Document and test:
- receipt valuation
- shipment/consumption
- inventory revaluation
- landed cost
- cost of goods sold
- returns

### Period close
Define:
- pre-close checks
- reconciliation
- closing
- lock behavior
- post-close corrections

## Required scenarios

1. Sales invoice → GL.
2. Vendor bill → GL.
3. Payment → reconciliation.
4. Credit note → reversal.
5. Partial payment.
6. Partial refund.
7. Inventory receipt → valuation.
8. Shipment → inventory/accounting.
9. Landed cost.
10. Period close.
11. Attempted modification of posted move → refused.

## Acceptance

Accountant must be able to post a representative month and confirm:
- Trial balance ties.
- P&L ties.
- Balance sheet ties.
- AR ties.
- AP ties.
- Inventory accounting ties.

## Open questions

Do not invent:
- final Canadian chart of accounts
- exact tax provider
- exact tax configuration (GST/HST/PST-QST by province and product category)
- costing policy
- account mapping

Mark them as open until source documentation/accountant approval exists.
