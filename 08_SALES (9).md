# CAPITAL NUTRITION ERP — SALES SPECIFICATION

## Objective

Build one consistent sales workflow for Magento-origin and ERP-origin orders, on Tryton 8.0.x / PostgreSQL 16.

An order must behave identically — operationally and in the general ledger — regardless of which channel it arrived through. Channel affects *provenance and reconciliation*, never *accounting treatment*.

## Relationship to other specifications

This document owns the sale: its lifecycle, pricing, fulfillment and the field that records where it came from.

It does not restate, and does not override:

- `docs/specs/09_MAGENTO.md` — the event model, queue, retry, replay and reconciliation that carry a Magento order to this domain. Where the two disagree on transport, the Magento specification governs.
- `docs/specs/07_CUSTOMERS.md` — party matching, deduplication and merge. An order is never created against a party invented to satisfy it.
- `docs/specs/03_ACCOUNTING.md` — chart of accounts, posting rules, tax treatment and period close. This domain produces financial documents; it does not write journal entries.
- `docs/integration/12_INTEGRATION_CONTRACTS.md` — the shared boundary definitions.
- **ADR-0002** — the external-event idempotency ledger. Binding on everything in *External identity* below.

## Platform baseline

Verified against the packages actually published for this release line:

- `trytond` 8.0.9
- `trytond_sale` 8.0.3

Standard `trytond_sale` already provides quotation, sale order, stock reservation via `stock`, shipment, invoice generation, cancellation, a return wizard, shipment and invoice exception handling, and sale reporting. It depends on `account`, `account_invoice`, `account_invoice_stock`, `account_product`, `company`, `country`, `currency`, `ir`, `party`, `product`, `res`, `stock`.

**Build rule** (per `CLAUDE.md`): prefer Tryton standard functionality. Custom code needs a genuine Capital Nutrition requirement behind it. Everything this specification asks for beyond standard `sale` is named explicitly below; anything not named is configuration.

## Functional scope

### Order origins

Every order carries an explicit origin. Origin is set at creation and is never inferred from side effects — not from the presence of an external identifier, not from which user created it, not from which sequence was used, not from whether a payment record exists.

Channels in scope for this build:

- `erp` — ERP / phone / manual
- `magento` — Magento 1 web store

The channel field is an extensible selection. Adding an approved future channel is a configuration and specification change, not a schema migration.

Rules:

1. Channel is required on every sale.
2. Channel is read-only once the sale leaves draft.
3. Default channel is `erp`. An order created through the ERP UI is an ERP order unless an integration explicitly states otherwise.
4. An order on an internal channel carries no external line identifiers.

### External identity

Magento-origin orders retain, at minimum: external order identity, external line identifiers, channel, currency, totals, discounts, taxes, payment information and product mapping.

**Order-level identity is not a column on the sale.** ADR-0002 records every inbound external event once in `capital_nutrition.external.event`, keyed `(source, event_type, external_id)` with a database unique constraint, and links the ERP record it produced through that event's `origin` reference. The ADR explicitly rejects per-integration de-duplication columns — a `magento_order_id` on the sale is the named anti-pattern — because such schemes are invisible to each other and usually unenforced at the database level.

This domain therefore:

- extends `_get_origin()` so an event may point at `sale.sale`, which is the sanctioned extension point for a domain module; and
- does **not** add an order-level external identifier column, and does not add a second uniqueness key.

"Which sale corresponds to Magento order X?" is answered from the ledger, not from a column on the sale.

**Consequence to watch.** `09_MAGENTO.md` states the cardinality rule — one Magento order maps to exactly one ERP sale, and the reverse. With order identity held in the ledger, that rule is enforced by the ledger's key plus the discipline that one event produces one origin, rather than by a constraint on `sale_sale`. If the build later wants that cardinality enforced directly against the sales table, it is an ADR revision, not a quiet column addition. `MAG-003`'s external-reference mapping model is where a secondary identifier such as the Magento increment number belongs.

**Line-level identity is a column**, on `sale.line`. The event ledger keys whole events, not lines, so it cannot express "this line is Magento line 4". `09_MAGENTO.md` § Inbound / Orders requires external line identifiers preserved per line so a replayed or amended order event reconciles line by line rather than by position or description matching. This is retained identity, not a de-duplication scheme, and carries no unique constraint.

### Sales lifecycle

Support, in this order:

1. quote (where required)
2. order
3. reservation / availability
4. fulfillment
5. shipment
6. invoice
7. payment
8. cancellation
9. return / credit

Inventory is authoritative for availability. The sales domain never asserts stock on hand independently of the inventory domain.

An inbound order whose customer has not yet matched parks rather than proceeding — that rule is owned by `09_MAGENTO.md` § Inbound and `07_CUSTOMERS.md`.

### Pricing

Support standard pricing, customer-specific pricing, quantity breaks, discounts, promotions where defined, and effective dates.

Pricing must be deterministic and auditable: given the same customer, product, quantity, date and channel, the resolved unit price must be reproducible, and the resolution path must be inspectable after the fact.

**Not yet decided** — see *Open questions*. Candidate Tryton modules (`product_price_list`, `sale_price_list`, `sale_promotion`, `sale_discount`) are not adopted until the pricing rules are documented from the current Odoo system and approved.

### Fulfillment

Support full fulfillment, partial fulfillment, backorder, cancellation and shipment tracking.

Partial fulfillment must not create an accounting event that a full fulfillment would not, other than for the quantities actually moved.

Partial shipments and multiple tracking numbers per order must be supported, including on the outbound push to Magento.

### Accounting integration

Sales integrate with, and never bypass, the accounting domain: AR, revenue, tax, inventory / COGS, payments, refunds.

Every sales document with a financial consequence produces its GL effect through the accounting domain's posting rules. Per `CLAUDE.md`, accounting logic never lives in UI code.

### Financial disagreement between systems

`09_MAGENTO.md` § Ownership boundary already settles the principle, and this domain does not reopen it:

- The ERP owns the sale and its financial totals once accepted.
- An inbound Magento payload never mutates an ERP-owned financial field on an already-posted document.
- Divergence is recorded and reported by reconciliation. It is not applied.
- No money event auto-corrects an existing posted move.

What remains open is not *who wins* but *what the figure of record is* for tax, and what rounding tolerance — if any — reconciliation accepts.

A payment or total mismatch therefore results in the order being flagged for review, not silently posted and not silently corrected.

### ERP-origin orders

ERP users create orders that follow the same operational and accounting rules as Magento-origin orders.

Per `00_MASTER_BUILD.md` and `09_MAGENTO.md`, ERP-origin orders are valid and must be represented consistently with Magento-origin orders. **This is not optional and is not out of scope.**

An ERP-origin order pushed to Magento must not be re-imported as a new sale; the mapping record established at push time prevents the round trip. The channel contract governing which orders are pushed, in what state, and how Magento displays them is open and gates `MAG-017`.

## Required scenarios

Each scenario must be a runnable test, not a manual checklist. Per `CLAUDE.md`, failure paths count, and cross-domain scenarios live in `tests/scenarios/`.

1. Normal order — quote → order → shipment → invoice → payment, ERP origin.
2. Discounted order — discount visible on the line, reflected in revenue and AR.
3. Tax-bearing order — tax computed, posted to the tax account, reconcilable to the provider's figure.
4. Partial fulfillment — ship part, invoice part, backorder remainder, then complete.
5. Cancellation — before shipment, and after partial shipment.
6. Return — goods back into inventory at the correct cost.
7. Refund — credit note, AR reversal, payment refund, including a partial refund.
8. ERP-origin order — full lifecycle.
9. Magento-origin order — full lifecycle from an ingested payload, with the sale linked as the event's origin.
10. Duplicate external order event — the replayed event is recognised by the ledger and produces exactly one sale.
11. Payment mismatch — external payment total disagrees with the ERP-computed total; the order is flagged for review rather than posted.
12. Internal-channel order carrying an external line identifier — refused by validation.
13. Channel modification after confirmation — refused.
14. Order arriving before its customer has matched — parks, and completes once the party matches.

## Acceptance

Operationally, a salesperson must be able to run scenarios 1–9 end to end without leaving the ERP.

Financially, the accountant's acceptance in `03_ACCOUNTING.md` must still hold with sales volume present: trial balance, P&L, balance sheet, AR and inventory accounting all tie.

Integration-wise, scenarios 10, 11 and 14 must be demonstrable against a replayed Magento payload, not a synthetic fixture alone.

## Open questions

Do not invent:

- **Pricing rules.** Customer-specific pricing, quantity break structure, promotion definitions and effective-date semantics must come from the current Odoo configuration and be approved before any price list module is adopted.
- **Cardinality enforcement.** Whether one-order-one-sale should additionally be constrained on `sale_sale`, or left to the ledger. See *External identity*. An ADR revision either way.
- **Tax figure of record** when Magento and the ERP disagree. Inherited from `09_MAGENTO.md`.
- **Reconciliation tolerance** for rounding, if any, and who approves an over/under. Inherited from `09_MAGENTO.md`.
- **Product mapping.** The key linking Magento SKUs to ERP products, and behaviour on an unmapped SKU. Owned jointly with `04_PRODUCTS.md`.
- **Return / RMA policy.** Authorisation requirement, restocking fees, condition grading, and the window.
- **Tax provider.** Inherited as open from `03_ACCOUNTING.md`.
- **Numbering.** Sale and quotation sequences, and whether Magento increment numbers are preserved as the ERP reference or held only in the mapping model.
- **Currencies.** Whether multi-currency sales are in scope.
- **Backorder policy.** Auto-backorder versus cancel-remainder, and whether it varies by channel.
- **Quotation validity period.**

Mark each as open until source documentation or business approval exists.

## Implementation status

`STATUS.md` records Sales as not started, and `README.md` § Suggested sequence puts specification before implementation.

`modules/capital_nutrition_sale` scaffolds the origin and line-identity requirements above (`SAL-001`, `SAL-004`, `SAL-005`). Verified: activates against `trytond` 8.0.9 with `trytond_sale` 8.0.3 and `capital_nutrition_base`, on **PostgreSQL 16.13**; 31 tests and 6823 subtests pass, including Tryton view validation.

It was written ahead of the approval step in `CLAUDE.md` § One task, one chat. Treat it as a proposal to review, not as sanctioned work.

See `docs/tasks/SALES/SAL_BACKLOG.md`.
