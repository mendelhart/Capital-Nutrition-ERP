# RUNBOOKS

Operational procedures for the Capital Nutrition ERP production and cutover domain.

Spec: `docs/specs/14_PRODUCTION_CUTOVER.md` (task prefix `OPS-###`)

| Runbook | Covers | Read it when |
|---|---|---|
| `BACKUP_RESTORE.md` | OPS-010 … OPS-022 | Setting up backups; restoring; running a restore drill |
| `MONITORING.md` | OPS-030 … OPS-032 | Configuring alerts; responding to one |
| `PARALLEL_RUN.md` | OPS-050 … OPS-052 | Running the daily Odoo-vs-ERP comparison |
| `CUTOVER_RUNBOOK.md` | OPS-040 … OPS-042 | Rehearsing and executing the cutover |
| `ROLLBACK.md` | OPS-060, OPS-061, OPS-070, OPS-071 | Before cutover (agree triggers); during cutover (execute) |

## Logs

| Log | Purpose |
|---|---|
| `docs/ops/restore-drill-log.md` | Evidence that backups restore |
| `docs/ops/parallel-run-log.md` | Evidence that the ERP agrees with Odoo |
| `docs/ops/key-custody.md` | Who can decrypt the backups |

## Reading order before cutover

1. `docs/specs/14_PRODUCTION_CUTOVER.md` — scope and open questions
2. `BACKUP_RESTORE.md` — recovery must work before anything else matters
3. `MONITORING.md` — must be live for the whole parallel run
4. `PARALLEL_RUN.md` — produces the evidence for approval
5. `ROLLBACK.md` — triggers agreed **before** the window opens
6. `CUTOVER_RUNBOOK.md` — rehearsed, then executed

## Status

All documents are DRAFT. They resolve to FINAL when the open questions in
`14_PRODUCTION_CUTOVER.md` are answered and the rehearsal has corrected the
measured durations.
