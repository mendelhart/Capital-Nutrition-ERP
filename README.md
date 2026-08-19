# Architectural decision records

One decision per file, numbered, never rewritten once accepted. If a decision
changes, add a new ADR that supersedes the old one and mark the old one
`Superseded by ADR-####`.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-tryton-8-postgresql-16-foundation.md) | Tryton 8.0.x and PostgreSQL 16 as the foundation | Accepted |
| [0002](0002-external-event-idempotency-ledger.md) | A single external-event ledger for integration idempotency | Accepted |
| [0003](0003-module-layout-and-symlink-development.md) | Modules in-repo, symlinked into trytond for development | Accepted |
| [0010](0010-one-working-specification-directory.md) | One working specification directory | Accepted |
| [0011](0011-module-and-package-naming.md) | Module and package naming | Accepted |
| [0012](0012-external-system-boundaries.md) | Magento is an asynchronous peer; Odoo is a one-way source | Accepted |
| [0013](0013-one-working-architecture-document.md) | One working architecture document | Accepted |
| [0014](0014-tryton-queue-for-asynchronous-work.md) | Tryton's own queue for asynchronous integration work | Accepted |

> **Numbering warning.** This index covers the ADRs in this repository only.
> The Claude project holds a *different* ADR set numbered 0001–0008, and the two
> disagree from 0002 onward — repository ADR-0002 is the external-event ledger,
> project ADR-0002 is the costing method. The same number means different
> decisions in the two places. Until the sets are reconciled, cite ADRs by title
> as well as number, and do not assign 0004–0008 here. See `docs/STATUS.md`.

Use [TEMPLATE.md](TEMPLATE.md).
