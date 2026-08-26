# CAPITAL NUTRITION ERP — MASTER BUILD

## Purpose

Build a company-owned ERP for Capital Nutrition on Tryton 8.0.x and PostgreSQL 16.

This document is the top-level contract for every Claude development chat. It defines scope, architecture, development discipline, and the relationship between domain specifications.

## Scope

### In scope
- Accounting
- Inventory and warehouse operations
- Purchasing
- Sales and order management
- Customers and parties
- Products and product data
- Magento 1 integration
- Reporting
- UI/UX
- Migration from Odoo
- Production, backup, monitoring, reconciliation, and cutover

### Explicitly out of scope
**Ship APL is removed from this build.**

Do not design, implement, or create dependencies for Ship APL. It will be evaluated as a separate future project after the ERP is stable in production.

## Foundation

- ERP framework: Tryton 8.0.x
- Database: PostgreSQL 16
- Existing selling site: Magento 1
- ERP users: approximately 3
- Repository is the project's persistent memory.
- Git is mandatory.
- Tests are mandatory.

## Core architecture principles

1. Tryton standard functionality is preferred over custom code.
2. Custom modules should contain only genuine Capital Nutrition requirements.
3. Business rules must be explicit and testable.
4. The ERP must remain maintainable by its owner.
5. Never hide accounting logic inside UI code.
6. Never allow an integration to silently correct financial discrepancies.
7. Every external integration must be idempotent.
8. Database constraints should enforce invariants whenever possible.
9. All important decisions are recorded as ADRs.
10. Domain modules may be developed independently, but integration contracts are mandatory.
11. No domain is considered production-ready merely because its isolated tests pass; cross-domain scenarios must also pass.
12. Prefer boring, readable code over clever abstractions.

## Source of truth

Unless a domain specification explicitly says otherwise:

- ERP owns operational and financial records.
- Magento owns web-store identity and web-store-specific presentation.
- Inventory quantities are owned by ERP.
- Accounting ledger is owned by ERP.
- ERP-origin orders are valid and must be represented consistently with Magento-origin orders.
- Migration data must be reconciled rather than assumed correct.

## Repository memory

Maintain:

- `docs/STATUS.md` — current state
- `docs/ARCHITECTURE.md` — system architecture
- `docs/BUSINESS_RULES.md` — Capital Nutrition business rules
- `docs/adr/` — architectural decisions
- `docs/domains/` — domain specifications
- `docs/integration/` — cross-domain contracts
- `docs/tasks/` — implementation task specifications and handoffs

## Development model

Use one Claude chat per implementation task.

A domain may have many tasks. The domain specification is the authoritative functional specification; the task file is the implementation slice.

Every task must:

1. Begin by reviewing relevant specification and current status.
2. Identify disagreements or ambiguities before coding.
3. Produce a written implementation plan.
4. Write tests.
5. Implement the smallest maintainable solution.
6. Run tests against PostgreSQL.
7. Update documentation.
8. Record new architectural decisions as ADRs.
9. Commit changes.
10. Update STATUS.md.

## Domain build order

The specifications should be developed and reviewed in this broad order:

1. Foundation / architecture
2. Accounting
3. Products
4. Inventory
5. Purchasing
6. Customers
7. Sales
8. Magento
9. Reporting
10. UI/UX
11. Integration testing
12. Migration
13. Production and cutover

This is a planning order, not permission to create hidden dependencies. Integration contracts define the actual interfaces.

## Required cross-domain contracts

Before implementation of dependent functionality, define:

- Sales ↔ Inventory
- Sales ↔ Accounting
- Purchasing ↔ Inventory
- Purchasing ↔ Accounting
- Products ↔ Inventory
- Products ↔ Sales
- Products ↔ Purchasing
- Magento ↔ Sales
- Magento ↔ Inventory
- Magento ↔ Customers
- Reporting ↔ transactional domains

## Quality gates

### Gate 1 — Financial correctness
Accountant signs off:
- chart of accounts
- fiscal periods
- journals
- posting behavior
- AR/AP
- taxes
- inventory accounting
- month-end scenarios

### Gate 2 — Operational and integration correctness
Prove:
- sales
- inventory
- purchasing
- Magento synchronization
- reconciliation
- failure/retry behavior

### Gate 3 — Production readiness
Prove:
- migration reconciliation
- backups
- restore
- monitoring
- security
- parallel run
- rollback plan

## Non-negotiables

- Inventory is counted at cutover, not blindly copied.
- Financial reconciliation reports discrepancies; it does not silently auto-correct them.
- Posted accounting moves cannot be casually modified.
- External events must be idempotent.
- Tests must cover failure paths, not only happy paths.
- No production credentials belong in the repository.
