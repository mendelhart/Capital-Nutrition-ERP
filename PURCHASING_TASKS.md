# PURCHASING — BUILD TASK BREAKDOWN (`PUR-###`)

Derived from `docs/specs/06_PURCHASING.md`.
Target platform: Tryton 8.0.x / PostgreSQL 16.

## How to read this document

Each task states what to build, which Tryton module it belongs to, and how it is
accepted. Tasks marked **CUSTOM** have no native Tryton 8.0 equivalent and land in
a new module, `capnut_purchase`. Tasks marked **BLOCKED** cannot be closed until a
decision listed in "Open decisions" is made.

Platform facts below were verified by reading the Tryton 8.0 module source
(`trytond_purchase 8.0.1`, `trytond_stock_supply 8.0.0`,
`trytond_account_stock_landed_cost 8.0.0`, `trytond_account_stock_anglo_saxon 8.0.0`,
`trytond_purchase_price_list 8.0.0`). They are not assumptions.

---

## Phase 0 — Platform baseline

### PUR-001 — Fix the purchasing module set
Install and pin the following, and record the decision as an ADR:

Required:
- `purchase` — PO, product suppliers, supplier price breaks
- `stock_supply` — order points, purchase requests
- `account_invoice` — vendor bills
- `account_stock_anglo_saxon` **or** `account_stock_continental` — stock/GRNI accounting

Evaluate and decide (do not install by default):
- `purchase_price_list` — price-list-driven purchase pricing
- `purchase_requisition` — internal request-to-buy approval
- `purchase_request_quotation` — RFQ to multiple vendors
- `purchase_amendment` — controlled change of a processing PO
- `purchase_blanket_agreement` — committed volume/price agreements
- `purchase_shipment_cost` — freight on the inbound shipment
- `account_stock_landed_cost` / `account_stock_landed_cost_weight`
- `stock_supply_day` — vendor order-day calendars

**Acceptance:** a fresh database provisions from a pinned module list with no manual
UI steps, and the list is reproducible in CI.

### PUR-002 — Reproducible purchasing fixtures
Vendors, product suppliers, price breaks, order points, and purchase configuration
load from code/fixtures on a fresh database.

**Acceptance:** `create db → load fixtures → run scenario tests` passes from clean.

---

## Phase 1 — Vendor pricing

Verified platform behaviour:
- `purchase.product_supplier` carries `party`, `template`/`product`, `name`,
  `code` (vendor SKU), `lead_time` (TimeDelta), `currency`, and `prices`.
  It is `sequence_ordered` + `MatchMixin` + deactivatable.
- `purchase.product_supplier.price` carries `quantity` (minimum quantity) and
  `unit_price`, is `sequence_ordered` + `MatchMixin`, and **the last matching
  line wins**.

### PUR-010 — Vendor / product-supplier master
Model vendor-specific product, vendor SKU (`code`), currency, and lead time.

**Acceptance:** a product with three vendors resolves the correct vendor SKU and
lead time per vendor; PO lines default from the selected vendor.

### PUR-011 — Quantity price breaks
Configure `product_supplier.price` tiers and confirm break selection at the tier
boundary, above it, and below the lowest tier.

**Acceptance:** ordering exactly at a break quantity selects the break price, not
the tier below. Boundary cases are covered by tests.

### PUR-012 — Order multiples / case pack — **CUSTOM**
Tryton 8.0 has **no** case-pack or order-multiple field on `product_supplier` or
on the price line. Add to `capnut_purchase`:
- `order_multiple` (case pack) and optional `minimum_order_quantity` on
  `purchase.product_supplier`
- rounding on PO line quantity change and on purchase-request-to-PO conversion
- rounding direction policy (up / nearest / block)

**Acceptance:** entering 10 units where the case pack is 12 yields 12 (or is
refused) per the configured policy, and the resulting price break is recomputed
**after** rounding, not before.

### PUR-013 — Effective-dated vendor pricing — **CUSTOM, BLOCKED**
Neither `product_supplier` nor `product_supplier.price` has start/end date fields
in 8.0; the only native levers are `active` and sequence order. If effective
dating is genuinely required, add `start_date`/`end_date` and extend the match
pattern.

**Blocked on:** decision D-3 (is effective dating required, or is deactivate-and-
supersede acceptable?).

### PUR-014 — Purchase price lists (optional)
If `purchase_price_list` is adopted in PUR-001, define precedence between the
price list and `product_supplier.price` and test it explicitly.

**Acceptance:** a documented, tested precedence rule. No ambiguity about which
price wins.

---

## Phase 2 — Purchase-to-pay workflow

Verified platform behaviour:
- `purchase.purchase.invoice_method` ∈ `manual` | `order` | `fulfillment`.
  (`shipment` was renamed to `fulfillment`; an 8.0 upgrade rewrites it.)
- `invoice_state` ∈ `none` | `pending` | `awaiting payment` | `partially paid` |
  `paid` | `exception`.
- `shipment_state` ∈ `none` | `waiting` | `partially shipped` | `received` |
  `exception`.

### PUR-020 — PO lifecycle
Draft → quotation → confirmed → processing → done, with cancel paths.

**Acceptance:** state transitions are tested including cancel-after-partial-receipt.

### PUR-021 — Partial receipt
Receive less than ordered; the PO reaches `partially shipped` and the remainder
stays open.

**Acceptance:** back-order quantity is correct and visible; a second receipt closes
the line.

### PUR-022 — Partial billing
Bill less than received under `invoice_method = fulfillment`.

**Acceptance:** `invoice_state` reflects partial billing; the uninvoiced balance is
reportable per PO and in aggregate.

### PUR-023 — Over-receipt policy — **CUSTOM, BLOCKED**
Define whether over-receipt is blocked, warned, or allowed within a tolerance
(percentage and/or absolute, possibly per vendor or per product category).

**Blocked on:** decision D-1 (over-receipt tolerance policy).

**Acceptance:** receiving 105 against an order of 100 behaves exactly as the
written policy states, and the policy is enforced in the model layer — not only in
the UI.

### PUR-024 — Three-way match — **CUSTOM**
Native Tryton bills from ordered or fulfilled quantity at PO price. A purchaser-
facing PO / receipt / bill match with an explicit discrepancy queue is custom.

Build:
- a match view keyed on PO line → move → invoice line
- quantity variance and price variance, each with its own tolerance
- a discrepancy worklist with hold / approve / dispute outcomes
- an audit trail of who cleared what

**Acceptance:** a bill priced 3% over the PO is held and appears in the worklist;
an in-tolerance bill posts without human intervention.

### PUR-025 — Discrepancy resolution
Short receipt, over-billing, price variance, and wrong-item receipts each have a
documented resolution path ending in a posted or cancelled bill.

**Acceptance:** each of the four scenarios runs end to end in tests.

### PUR-026 — Payment
Vendor bill → payment → reconciliation, including partial payment.

**Acceptance:** AP aging and the PO's `invoice_state` agree after each step.

---

## Phase 3 — Reordering

Verified platform behaviour:
- `stock.order_point` carries `type`, `min_quantity`, `target_quantity`,
  `max_quantity`, `provisioning_location`, `overflowing_location`.
- `purchase.request.generate_requests()` uses order points plus supply dates
  derived from `product_supplier.lead_time` and a configurable `supply_period`.
- Native request generation does **not** consider price breaks or case packs.

### PUR-030 — Order points
Configure min/target/max per product per warehouse; load from fixtures.

**Acceptance:** order points reproduce on a fresh database.

### PUR-031 — Purchase request generation
Generate requests from availability, reservations, expected receipts, demand,
minimum levels, and vendor lead time.

**Acceptance:** a seeded stock position produces the expected request set, and
re-running is idempotent — it does not duplicate open requests.

### PUR-032 — Reorder report with commercial rounding — **CUSTOM**
Extend request generation so suggested quantities respect case-pack multiples
(PUR-012) and surface the price break the rounded quantity would reach, including
"add N more units to reach the next break" guidance.

**Acceptance:** the purchaser sees suggested quantity, case-pack-rounded quantity,
resulting unit price, and distance to the next break — in one view.

### PUR-033 — No silent auto-ordering
Request → PO conversion requires an explicit human approval step. Nothing converts
on a timer.

**Acceptance:** no scheduled task can create a confirmed PO. Verified by test, not
by convention.

---

## Phase 4 — Accounting integration

**Every task in this phase is BLOCKED on the accounting spec's open questions**
(chart of accounts, costing policy, account mapping) — see
`docs/specs/03_ACCOUNTING.md`.

### PUR-040 — Stock accounting method — **BLOCKED**
Choose `account_stock_anglo_saxon` or `account_stock_continental` and record an ADR.
Anglo-saxon posts receipts to the product's stock-in account, which is what makes a
received-not-invoiced balance visible.

**Blocked on:** decision D-2.

### PUR-041 — GRNI / accrual — **BLOCKED**
Receipt debits inventory and credits the GRNI clearing account; the vendor bill
clears GRNI to AP.

**Acceptance:** GRNI balance equals (received − billed) valued at PO price, at any
point in time, and is reportable by vendor and by PO.

### PUR-042 — Landed cost — **BLOCKED**
`account.landed_cost` links supplier invoice lines to inbound shipments with an
allocation method (by value natively; by weight with the `_weight` module).

**Acceptance:** a freight bill allocated across a multi-line receipt changes unit
cost by the expected amount, and COGS on later shipments reflects it.

### PUR-043 — Purchase returns
Return to vendor with the matching credit note and inventory reversal.

**Acceptance:** inventory, GRNI, and AP all return to their pre-transaction state.

---

## Phase 5 — Acceptance

### PUR-050 — End-to-end purchaser scenario
The nine numbered steps in the spec's Acceptance section, run as one automated
scenario: reorder need → PO → correct price break → case-pack respected → partial
receipt → bill match → discrepancy resolved → payment → correct accounting and
inventory.

**Acceptance:** green in CI on a fresh database, with no manual setup.

---

## Open decisions

| ID | Decision | Blocks | Owner |
|----|----------|--------|-------|
| D-1 | Over-receipt policy: block, warn, or tolerance (and tolerance basis) | PUR-023 | Operations |
| D-2 | Anglo-saxon vs continental stock accounting | PUR-040, PUR-041 | Accountant |
| D-3 | Is effective-dated vendor pricing required? | PUR-013 | Purchasing |
| D-4 | Case-pack rounding direction: up, nearest, or refuse | PUR-012 | Purchasing |
| D-5 | Three-way match tolerances: quantity % and price % | PUR-024 | Operations + Accountant |
| D-6 | Which optional modules from PUR-001 are in scope | PUR-001 | Morris |
| D-7 | Landed cost allocation basis: value or weight | PUR-042 | Accountant |
| D-8 | Vendor selection rule when several vendors supply one product | PUR-010 | Purchasing |

Do not invent answers to these. Leave the dependent tasks open until the decision
is recorded as an ADR.

---

## Known platform gaps requiring `capnut_purchase`

1. Case-pack / order multiples on vendor supply records — no native field.
2. Effective-dated vendor pricing — no native start/end dates.
3. Over-receipt tolerance policy — needs explicit enforcement.
4. Three-way match workbench and discrepancy queue — no native equivalent.
5. Reorder suggestions that account for case packs and price breaks.
