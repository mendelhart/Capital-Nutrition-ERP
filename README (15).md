# Capital Nutrition ERP — Claude Build Package

This directory contains the specifications for rebuilding Capital Nutrition's ERP on Tryton 8.0.x / PostgreSQL 16.

## Important scope decision

**Ship APL is intentionally excluded from this build.**

It will be evaluated as a separate project after the ERP is stable.

## Start with

1. `00_MASTER_BUILD.md`
2. `01_ARCHITECTURE.md`
3. `02_BUSINESS_RULES.md`
4. Relevant domain specification
5. `12_INTEGRATION_CONTRACTS.md`
6. `15_CLAUDE_CHAT_PROTOCOL.md`

## Domains

- Accounting
- Products
- Inventory
- Purchasing
- Customers
- Sales
- Magento
- Reporting
- UI/UX

## Build philosophy

Each domain can have dedicated Claude chats so the model can focus deeply on that domain.

However, domains are not isolated silos. The master architecture and integration contracts are mandatory shared boundaries.

## Suggested sequence

### Specification first
Develop/review all domain specifications and integration contracts before large-scale implementation.

### Implementation second
Build domain tasks in focused Claude chats.

### Integration third
Run cross-domain scenarios.

### Migration fourth
Rehearse Odoo extraction, transformation, loading, and reconciliation.

### Production last
Backup, restore, monitoring, parallel run, and cutover.

## File conventions

Task IDs:

- `ACC-###`
- `PROD-###`
- `INV-###`
- `PUR-###`
- `CUS-###`
- `SAL-###`
- `MAG-###`
- `REP-###`
- `UI-###`

## Repository memory

The repository remains the persistent memory between Claude chats.

Keep `STATUS.md`, specifications, ADRs, and task handoffs current.
