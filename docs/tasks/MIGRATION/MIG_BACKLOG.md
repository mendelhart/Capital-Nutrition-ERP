# MIGRATION — task backlog

Spec: `docs/specs/13_MIGRATION.md`. Code: `migration/`.

| ID | Task | Status | Blocked by |
|---|---|---|---|
| MIG-001 | Migration toolkit skeleton: extract → stage → map → build → load → reconcile | **done** | — |
| MIG-002 | Point `odoo_sql` at a real restored Odoo snapshot; run `probe`; fix the SQL for the actual Odoo version | todo | a restored snapshot + read-only credentials |
| MIG-003 | Run `map stub` on real data; review and approve the account, journal and tax mappings | todo | MIG-002, accountant availability |
| MIG-004 | Review and approve product, party, vendor and UoM mappings | todo | MIG-002, PROD-### product decisions |
| MIG-005 | Implement the `tryton` load target (idempotent by `_ref` via `ir.model.data`) | todo | Tryton modules existing (ACC-###) |
| MIG-006 | Physical count import + make `inventory_value` a blocking check | todo | INV-###, the count process in the cutover runbook |
| MIG-007 | Decide how much sales/payment history migrates; make those checks blocking if it does | todo | a business decision |
| MIG-008 | Rehearsal 1 — expect breakage, record every difference | todo | MIG-002..004 |
| MIG-009 | Rehearsal 2 — differences explained or fixed | todo | MIG-008 |
| MIG-010 | Rehearsal 3 — routine and repeatable, accountant signs the report | todo | MIG-009 |
| MIG-011 | Wire the rehearsal exit codes into the cutover runbook's go/no-go gate | todo | MIG-010 |

## Open questions

1. Which Odoo version and which `res_company.id` is the real source?
2. Is the source a restored `pg_dump` snapshot, live RPC, or CSV exports? (Toolkit assumes a snapshot; the others are declared stubs.)
3. How much history migrates — GL detail, or opening balances plus reference data only?
4. Who signs the accounting mappings, and by when?
5. Multi-currency: are there non-USD open items? Nothing is auto-converted; the profiler flags them.
