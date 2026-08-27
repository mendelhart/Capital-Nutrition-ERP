# CAPITAL NUTRITION ERP — SALES TASK BACKLOG

Domain: Sales
Specification: `docs/specs/08_SALES.md`
Task ID prefix: `SAL-###`

Per `docs/specs/README.md` § Suggested sequence, this domain is specification-stage. Tasks below are not approved for implementation until the open questions in the specification are closed, except where explicitly marked.

## Gate

Two gates apply to this domain, and they are independent:

- **Accounting.** No sale that posts to the ledger is implemented until the chart of accounts, account mapping and tax provider in `03_ACCOUNTING.md` are approved. This gates most of the backlog.
- **ADR-0002.** Order-level external identity belongs to the external-event ledger, not to a column on the sale. `SAL-002` is therefore closed as *not to be built*; see `08_SALES.md` § External identity. Reopening it means revising ADR-0002, not adding a column.

## Backlog

### Foundation

- `SAL-001` Explicit `channel` field on `sale.sale`: required, default `erp`, read-only after draft. *Scaffolded — see Implementation notes.*
- `SAL-002` Extend `capital_nutrition.external.event._get_origin()` so an inbound event can point at `sale.sale` (ADR-0002). *Scaffolded.* Supersedes the earlier idea of an external order ID column, which ADR-0002 rejects.
- `SAL-003` Decide whether one-Magento-order-to-one-ERP-sale needs enforcement on `sale_sale` in addition to the ledger. **Open — ADR revision.** See `08_SALES.md` § External identity.
- `SAL-004` External line identifiers on `sale.line`, with a lookup index. *Scaffolded.*
- `SAL-005` Module test suite, including Tryton view validation. *Scaffolded and passing.*
- `SAL-006` Extend the channel selection when a new channel is approved. Requires business approval per channel.

### Configuration of standard `sale`

Configuration against stock `trytond_sale`. No custom code expected; if custom code appears necessary, stop and record why.

- `SAL-010` Sale and quotation number sequences. Blocked on the numbering decision.
- `SAL-011` Default invoice method and shipment method, company-wide and per customer.
- `SAL-012` Quotation validity and the expired-quotation cron. Blocked on the validity period.
- `SAL-013` Warehouse and shipment configuration for sales. Blocked on `05_INVENTORY.md`.
- `SAL-014` Sale-side account configuration: revenue, AR, tax accounts. Blocked on `03_ACCOUNTING.md`.
- `SAL-015` Backorder behaviour on partial shipment. Blocked on the backorder policy.

### Pricing

Nothing here starts until the pricing rules are documented from the current Odoo system and approved. Adopting a price list module first would bake in a structure the business has not confirmed.

- `SAL-020` Document current Odoo pricing rules: standard, customer-specific, quantity breaks, promotions, effective dates. **Available now** — needs source system access only.
- `SAL-021` Decide which Tryton pricing modules to adopt. Depends on `SAL-020`.
- `SAL-022` Implement the approved price list structure. Depends on `SAL-021`.
- `SAL-023` Price resolution audit trail: reproduce a historical price and show the resolution path. Depends on `SAL-021`.
- `SAL-024` Migrate customer-specific pricing from Odoo. Depends on `SAL-022` and `13_MIGRATION.md`.

### Sales side of the Magento boundary

The transport is owned by `09_MAGENTO.md`. These tasks define only what the sales domain must expose or accept.

- `SAL-030` Define the sales side of the order ingestion contract: required fields, references, and error semantics. **Available now** — feeds `12_INTEGRATION_CONTRACTS.md` and `MAG-009`.
- `SAL-031` Define parking behaviour for an order whose customer has not matched. Pairs with `MAG-010` and `07_CUSTOMERS.md`.
- `SAL-032` Define the sales-side review queue for payment and total mismatches. Pairs with `MAG-020`.
- `SAL-033` Product mapping consumption and unmapped-SKU behaviour. Blocked on `04_PRODUCTS.md` and the mapping decision.
- `SAL-034` Define what an ERP-origin order must carry to be pushable to Magento. Pairs with `MAG-017`; blocked on the channel contract.

### Accounting integration

- `SAL-040` Sales invoice → GL, tied to scenario 1 of `03_ACCOUNTING.md`. Blocked on `SAL-014`.
- `SAL-041` Shipment → inventory / COGS. Blocked on `SAL-013` and `05_INVENTORY.md`.
- `SAL-042` Credit note and refund path, including partial refunds. Blocked on `SAL-014` and the return policy.
- `SAL-043` Tax computation wired to the approved provider. Blocked on the tax provider decision.

### Verification

One task per numbered scenario in `08_SALES.md` § Required scenarios. Scenarios 12 and 13 are already covered by `SAL-005`.

- `SAL-050` Scenario 1 — normal order. Blocked on `SAL-011`, `SAL-014`.
- `SAL-051` Scenario 2 — discounted order. Blocked on `SAL-022`.
- `SAL-052` Scenario 3 — tax-bearing order. Blocked on `SAL-043`.
- `SAL-053` Scenario 4 — partial fulfillment and backorder. Blocked on `SAL-015`.
- `SAL-054` Scenario 5 — cancellation, pre- and post-shipment. Blocked on `SAL-013`.
- `SAL-055` Scenario 6 — return. Blocked on `SAL-042`.
- `SAL-056` Scenario 7 — refund, including partial. Blocked on `SAL-042`.
- `SAL-057` Scenario 8 — ERP-origin order end to end. Blocked on `SAL-050`.
- `SAL-058` Scenario 9 — Magento-origin order end to end. Blocked on `MAG-009`.
- `SAL-059` Scenario 10 — duplicate external order event, against a replayed payload. Blocked on `MAG-009`.
- `SAL-060` Scenario 11 — payment mismatch. Blocked on `SAL-032`.
- `SAL-061` Scenario 14 — order before customer match. Blocked on `SAL-031`.

## Sequencing

`SAL-001` precedes everything else in Foundation.

`SAL-003` is a decision, not a build task, and needs the Magento domain in the room.

`SAL-014` is the highest-leverage blocker in this backlog: it gates `SAL-040` through `SAL-043`, which in turn gate most of Verification. It cannot be unblocked from inside this domain.

`SAL-020`, `SAL-030` and `SAL-031` are the only substantive tasks that can start today. `SAL-020` needs Odoo access; `SAL-030` and `SAL-031` are specification work feeding `12_INTEGRATION_CONTRACTS.md`.

## Cross-domain dependencies

| Depends on | For |
|---|---|
| `03_ACCOUNTING.md` | chart of accounts, account mapping, tax provider — gates `SAL-014`, `SAL-040`–`SAL-043` |
| `04_PRODUCTS.md` | product mapping key — gates `SAL-033` |
| `05_INVENTORY.md` | warehouse, availability, COGS — gates `SAL-013`, `SAL-041` |
| `07_CUSTOMERS.md` | party matching and parking — gates `SAL-031` |
| `09_MAGENTO.md` | event model, mapping model, ingestion — gates `SAL-003`, `SAL-034`, `SAL-058`, `SAL-059` |
| `13_MIGRATION.md` | historical pricing and orders — gates `SAL-024` |

## Implementation notes

`modules/capital_nutrition_sale` scaffolds `SAL-001`, `SAL-002`, `SAL-004` and `SAL-005`.

Verified: activates against `trytond` 8.0.9 with `trytond_sale` 8.0.3 and `capital_nutrition_base`, on **PostgreSQL 16.13** — 31 tests, 6823 subtests, including Tryton's view validation. Layout follows ADR-0003 (in-repo module, `[register]` in `tryton.cfg`, no per-module `pyproject.toml`).

Not verified: no end-to-end sale has been run through it, because that needs the accounting and inventory configuration that is still gated. `make test`'s `MODULES` list does not yet include this module.

The scaffold was written ahead of the approval step in `CLAUDE.md` § One task, one chat, and against a specification this same change expanded. Review before adopting.
