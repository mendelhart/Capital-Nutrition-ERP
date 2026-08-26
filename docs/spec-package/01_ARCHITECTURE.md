# CAPITAL NUTRITION ERP — ARCHITECTURE

## Purpose

Define the technical boundaries that every domain must respect.

## Stack

- Tryton 8.0.x
- PostgreSQL 16
- Python compatible with the selected Tryton release
- Containerized development and production environments where appropriate
- Magento 1 integration through a dedicated custom integration layer

## Architectural layers

### 1. Tryton standard modules
Use standard Tryton modules whenever they correctly express the requirement.

### 2. Capital Nutrition custom modules
Custom modules should extend Tryton models and workflows rather than duplicate standard ERP functionality.

Expected areas include:
- `capnut_core`
- `capnut_purchasing`
- `capnut_magento`
- `capnut_report`
- additional domain modules only when justified

### 3. Integration layer
External systems communicate through explicit adapters, event records, mappings, queues, retries, and reconciliation.

### 4. Reporting layer
Operational reporting must not introduce fragile dependencies into accounting or transactional workflows.

## Module boundary rules

A module must not reach into another domain's private implementation merely because doing so is convenient.

Use:
- public Tryton models
- explicit services
- integration contracts
- documented events
- database constraints where appropriate

## Data ownership

### Accounting
ERP owns:
- ledger
- journal entries
- receivables
- payables
- payments
- reconciliation
- tax accounting

### Inventory
ERP owns:
- stock quantities
- locations
- lots
- receipts
- shipments
- stock movements
- valuation

### Products
ERP owns:
- internal product master
- SKUs
- units
- product categories
- inventory/accounting attributes

Magento may own web presentation fields where appropriate.

### Customers
ERP owns the canonical party record.
Magento owns web-store identity and Magento-specific identifiers.

### Sales
ERP owns the operational sales transaction after ingestion.

### Magento
Magento remains the storefront. It does not become the ERP's financial source of truth.

## Integration principles

Every external integration should support:

- deterministic mapping
- idempotency
- retry
- dead-letter handling
- replay
- observability
- reconciliation
- rate limiting
- clear ownership

## Database principles

Prefer database constraints for:
- uniqueness
- required relationships
- valid state transitions where practical
- idempotency keys
- referential integrity

Do not rely solely on application-level checks when PostgreSQL can enforce the invariant.

## Security

- Least privilege
- Secrets outside source control
- Separate staging and production credentials
- Audit sensitive administrative actions
- No direct production database manipulation as a normal workflow
- Backup encryption
- Controlled administrative access

## Testing architecture

Tests should exist at several levels:

1. Unit tests for isolated business logic.
2. Model tests for Tryton behavior.
3. Integration tests against PostgreSQL.
4. Cross-domain scenario tests.
5. Magento staging tests.
6. Migration reconciliation tests.
7. Production restore tests.

## Performance

Do not optimize speculatively.

Measure:
- query counts
- slow queries
- queue latency
- synchronization lag
- report refresh times
- inventory query performance

Use indexes based on actual access patterns and documented requirements.

## Failure philosophy

A failure must be:
- visible
- classified
- recoverable where possible
- non-destructive
- auditable

Never hide an integration or financial failure merely to make a workflow appear successful.
