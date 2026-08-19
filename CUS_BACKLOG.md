# CAPITAL NUTRITION ERP — CUSTOMERS TASK BACKLOG

Domain: Customers / Parties
Specification: `docs/specs/07_CUSTOMERS.md`
Task ID prefix: `CUS-###`

All tasks below are specification-stage unless marked otherwise. Nothing here is
approved for implementation until the open questions in the specification are closed.

## Backlog

- `CUS-001` Define the canonical party model and extension points on `party.party`.
- `CUS-002` Define address model, purposes, and posted-document immutability.
- `CUS-003` Define contact mechanism model and scoping.
- `CUS-004` Define tax information fields and exemption handling.
- `CUS-005` Define payment term assignment and override precedence.
- `CUS-006` Define credit limit, exposure calculation, and hold behavior.
- `CUS-007` Define pricing group assignment and price list resolution order.
- `CUS-008` Define external identifier model, including Odoo legacy ID.
- `CUS-009` Define the ERP↔Magento mapping model and its constraints.
- `CUS-010` Define normalization rules for matching inputs.
- `CUS-011` Define the ordered match strategy and its three outcomes.
- `CUS-012` Build the ambiguous-match review queue.
- `CUS-013` Define and test merge, including mapping re-point and history preservation.
- `CUS-014` Define lifecycle states and deletion refusal constraints.
- `CUS-015` Build the required-scenario test set.
- `CUS-016` Define migration mapping and reconciliation from Odoo.

## Sequencing

`CUS-001` through `CUS-008` define the party itself and can proceed in parallel.

`CUS-009` through `CUS-013` depend on the party model being settled, and on the
inbound payload schema in `12_INTEGRATION_CONTRACTS.md`.

`CUS-015` and `CUS-016` are last: the scenario set and the migration mapping both
need the models above to exist.

## Blocked

`CUS-011` is blocked on the match-strategy decision.
`CUS-006` is blocked on credit limit policy.
`CUS-007` is blocked on the default pricing group decision.

See "Open questions" in the specification.
