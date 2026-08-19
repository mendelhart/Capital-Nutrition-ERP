# CAPITAL NUTRITION ERP — BUSINESS RULES

## Purpose

This is the canonical location for Capital Nutrition operating rules that do not belong exclusively to a single technical module.

Claude must not invent a business rule when the requirement is unknown. Mark it `OPEN QUESTION` and ask for clarification.

## Product and quantity rules

- Products may be sold by unit and case where applicable.
- Case-pack multiples must be respected in purchasing where configured.
- Quantity conversions must be deterministic.
- Quantity calculations must not accumulate floating-point drift.
- Product packaging and sellable units must be explicit.

## Purchasing rules

- Vendors may have quantity-break pricing.
- Vendors may have order multiples/case packs.
- Vendor lead time must be represented where useful.
- Purchase recommendations should respect configured ordering constraints.
- Three-way matching must be supported where applicable.

## Inventory rules

- ERP is the source of truth for inventory.
- Receipts increase available inventory according to the configured workflow.
- Shipments reduce inventory according to the configured workflow.
- Reservations, availability, backorders, and partial fulfillment must have explicit states.
- Lots and shelf-life must be supported where required.
- Inventory at cutover is counted rather than blindly copied.

## Sales rules

Sales may originate from:
- Magento
- ERP users entering orders directly

Both origins must produce consistent ERP operational records.

Sales must support:
- partial fulfillment
- cancellations
- returns/credit processes
- discounts
- taxes
- customer-specific pricing where required
- product availability
- backorders where permitted

## Accounting rules

- Financial postings are controlled by the accounting configuration.
- Posted accounting moves must not be casually altered.
- Corrections should use proper accounting mechanisms such as reversals/credit notes where appropriate.
- Month-end and period-close procedures must be reproducible.
- Financial discrepancies must be reported rather than silently corrected.

## Magento rules

- Magento owns storefront identity.
- ERP owns financial and operational truth.
- Integration must be idempotent.
- Duplicate events must not duplicate orders, payments, inventory effects, or customers.
- Failures must be observable and replayable.

## Reporting rules

Reports should answer actual business questions.

Do not build a large report catalogue merely because a report is technically possible.

The initial reporting pack should prioritize:
- sales
- gross margin
- inventory
- purchasing
- AR
- AP
- cash/payment status
- operational exceptions
- reconciliation

## Open questions

Maintain unresolved business questions here until explicitly decided.

Each resolved question should become:
1. a documented rule
2. an ADR if architectural
3. relevant acceptance tests
