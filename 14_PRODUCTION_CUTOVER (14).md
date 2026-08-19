# CAPITAL NUTRITION ERP — PRODUCTION / CUTOVER SPECIFICATION

Status: **DRAFT — awaiting hosting decision**
Domain prefix: `OPS-###` (see "Task ID collision" below)
Depends on: `01_ARCHITECTURE.md`, `12_INTEGRATION_CONTRACTS.md`, `13_MIGRATION.md`

Satisfies **Gate 3 — Production readiness** in `00_MASTER_BUILD.md` (migration
reconciliation, backups, restore, monitoring, security, parallel run, rollback
plan). Gate 1 (financial correctness) and Gate 2 (operational and integration
correctness) must be signed off before the parallel run begins.

## Objective

Deploy and transition to the ERP safely.

"Safely" is defined here as: the business can operate on the new ERP, the
accountant can close a period on it, and there exists a tested, time-boxed
path back to Odoo if it does not work.

## Task ID collision

`README.md` assigns `PROD-###` to the **Products** domain. This document
therefore uses `OPS-###` for production/infrastructure/cutover tasks.

**Decision required:** confirm `OPS-###`, or reassign the Products domain.
Do not use `PROD-###` for both.

---

## 1. Production stack

### OPS-001 — Document the target stack

Produce `docs/adr/ADR-###-production-stack.md` recording the decision and
the rejected alternatives for each layer:

| Layer | Requirement | Status |
|---|---|---|
| Application containers | Tryton 8.0.x application server; pinned image digest, not a floating tag | Open |
| Database | PostgreSQL 16; version pinned to a specific minor release | Fixed by `README.md` |
| Reverse proxy | TLS termination, HTTP→HTTPS redirect, request size limits, timeouts appropriate to long-running reports | Open |
| TLS | Certificate source, renewal automation, expiry alerting | Open |
| Network isolation | Database reachable only from the application network. No public port on PostgreSQL. Admin access via bastion or VPN only. | Required |
| Magento connectivity | Direction, authentication, IP allow-listing, retry/backoff — must match `12_INTEGRATION_CONTRACTS.md` | Open |
| Background workers | Queue runner processes, concurrency, isolation from the web workers | Open |
| Scheduled jobs | Cron/timer definitions, single-execution guarantee, timezone | Open |

### OPS-002 — Reproducible provisioning

The production environment must be rebuildable from committed configuration.

Requirements:
- No manual, undocumented server changes. Anything done by hand gets written down and then automated.
- Secrets are **not** in the repository. Reference a secret store or an
  operator-supplied environment file; commit only a `.env.example`.
- A staging environment is built from the same configuration as production,
  differing only in secrets, hostnames, and resource size.

### OPS-003 — Timezone and locale

Fix and document:
- server timezone
- PostgreSQL timezone
- application timezone
- the timezone in which "a business day" is defined for reporting and for the parallel run

Mismatched timezones are a recurring source of one-day reconciliation
differences. Settle this before the parallel run, not during it.

### OPS-004 — Capacity baseline

Record expected concurrent users, order volume, and database size, and the
resources allocated. Without a baseline, monitoring thresholds are guesses.

---

## 2. Backup

### OPS-010 — Full backups

- Regular full logical or physical backup of the PostgreSQL cluster.
- Frequency must satisfy the agreed RPO (see open questions).
- Backup must include: database, application configuration, uploaded
  documents/attachments, and any file storage used by the ERP.
- A database-only backup is **not** a complete backup.

### OPS-011 — WAL / continuous archiving

Continuous WAL archiving is required where the agreed RPO is shorter than
the full-backup interval. Point-in-time recovery must be demonstrably
possible to an arbitrary timestamp within the retention window.

### OPS-012 — Encrypted offsite copy

- Backups are encrypted at rest, and encrypted in transit to the offsite location.
- The offsite copy is in a different failure domain from production.
- The decryption key is stored separately from the backups, and at least one
  copy exists outside any system an attacker who reached production could reach.
- **Test that the key can be retrieved by someone other than the person who created it.**

### OPS-013 — Retention

Document, and enforce automatically:
- daily retention period
- weekly retention period
- monthly/annual retention period
- retention required for tax/accounting purposes (accountant confirms)
- deletion procedure for expired backups

### OPS-014 — Restore procedure

A written procedure that a competent operator who did not build the system
can follow. It must state, explicitly:
- where backups live and how to authenticate to that location
- how to obtain the decryption key
- the exact commands to restore
- how to verify the restore succeeded
- expected duration

---

## 3. Restore testing

> A backup is not considered valid until it has been restored into a clean
> environment successfully.

### OPS-020 — Restore drill

Recurring drill. Each drill must:
1. Provision a clean environment. No reuse of an environment that already has data.
2. Restore from the offsite encrypted copy — not from a local convenience copy.
3. Start the application against the restored database.
4. Run the verification query set (OPS-021).
5. Record wall-clock duration from "start" to "verified".
6. Log the result in `docs/ops/restore-drill-log.md`, including failures.

A drill that is not logged did not happen.

### OPS-021 — Restore verification set

A fixed, versioned set of checks run against every restored copy:
- row counts for the core tables (partners, products, moves, invoices, stock moves)
- trial balance total (debits = credits)
- AR total and AP total
- inventory quantity total and inventory valuation total
- most recent posted document date and ID
- Magento sync watermark / last-processed cursor
- application starts and an authenticated user can log in

### OPS-022 — Drill cadence and pass criteria

- Cadence: at least monthly before cutover; frequency after cutover to be confirmed.
- Pass criteria: all OPS-021 checks match the source-of-truth snapshot, and the
  restore completed within the agreed RTO.
- A failed drill is a **blocker** for cutover approval.

---

## 4. Monitoring

### OPS-030 — Signals

| Signal | What it catches |
|---|---|
| Application health endpoint | Process up, database reachable |
| PostgreSQL: connections, longest transaction, locks, cache hit ratio, bloat | Database degradation before it becomes an outage |
| Queue depth | Work arriving faster than it is processed |
| Synchronization lag (Magento) | Orders/stock drifting between systems |
| Dead-letter queue | Messages that failed permanently — must be non-zero-alerting |
| Failed scheduled jobs | Silent failure of nightly work |
| Disk free (data, WAL, backup staging) | The most common self-inflicted database outage |
| Backup status: last success, size, duration | Backups that stopped working weeks ago |
| Certificate expiry | Avoidable full outage |
| Replication lag (if replication is used) | Failover readiness |

### OPS-031 — Alerts must be actionable

Every alert must define:
- **Condition and threshold** — derived from the OPS-004 baseline, not invented.
- **Who is notified**, and through which channel.
- **What the responder does** — a link to a runbook section, not just a metric name.
- **Business impact if ignored.**

An alert with no defined response is deleted, not tuned. Alert fatigue is a
cutover risk in its own right.

### OPS-032 — Alert routing

Document the on-call reality: this is a small business, not a 24/7 operations
team. Decide and record which alerts justify waking someone, which wait until
morning, and who the single named responder is during cutover week.

---

## 5. Cutover

### OPS-040 — Runbook

The hour-by-hour runbook lives in `docs/runbooks/CUTOVER_RUNBOOK.md`.

It must cover, in order:
1. final Odoo freeze
2. final extraction
3. migration
4. physical inventory count
5. reconciliation
6. Magento synchronization state
7. ERP activation
8. verification
9. rollback decision points

### OPS-041 — Rehearsal

The full runbook is rehearsed end-to-end against a copy of production data
at least once before the real cutover. The rehearsal produces a corrected
runbook and a measured duration for every step.

An unrehearsed runbook is an estimate, and estimates are what make cutovers
run past their window.

### OPS-042 — Freeze communication

Before the freeze: who is told, how far in advance, and what they are told to
do with orders, receipts, and payments that arrive during the window.
This includes Magento customers if the storefront behaviour changes.

---

## 6. Parallel run

### OPS-050 — Comparison

Before final approval, Odoo and the ERP are compared for an agreed number of
**consecutive clean days**. Procedure in `docs/runbooks/PARALLEL_RUN.md`.

Compared daily:
- inventory (quantity and valuation)
- AR (total and aging buckets)
- AP (total and aging buckets)
- P&L (period to date, by account)
- sales (count, gross, tax, net)
- operational orders (sales orders, purchase orders, shipments, receipts)

### OPS-051 — Clean day definition

A day is clean when every comparison in OPS-050 is within its documented
tolerance and every difference outside tolerance has a written, accepted
explanation.

A difference that is "probably rounding" is not explained. A difference
traced to a specific known cause, with the cause recorded, is explained.

The counter resets to zero on any non-clean day. It does not resume.

### OPS-052 — Tolerances

Each comparison declares its tolerance. Most financial comparisons should be
zero-tolerance; where a non-zero tolerance is proposed, it requires the
accountant's written agreement and a recorded reason.

---

## 7. Rollback

### OPS-060 — Triggers defined in advance

Explicit rollback triggers are written down and agreed **before** cutover
begins. Procedure in `docs/runbooks/ROLLBACK.md`.

Deciding what constitutes failure while failing is how a bad cutover becomes
a bad week.

### OPS-061 — Rollback procedure

- Tested during the OPS-041 rehearsal.
- Time-boxed: the decision has a deadline, after which rollback is no longer
  available and the path is forward-only.
- Names who has authority to call it.
- States what happens to transactions entered into the ERP after cutover.

---

## 8. Approval

### OPS-070 — Sign-off

Final cutover requires recorded approval from:
- owner
- accountant
- responsible technical operator

Sign-off sheet in `docs/runbooks/ROLLBACK.md` (§ Go / No-Go).

### OPS-071 — Evidence, not impression

> No production cutover based solely on "it appears to work."

Approval requires attached evidence:
- a passed restore drill within the last 30 days (OPS-022)
- the required number of consecutive clean parallel-run days (OPS-051)
- a completed rehearsal (OPS-041)
- the accountant's confirmation that a representative month closes and ties
  (see `03_ACCOUNTING.md` § Acceptance)
- zero open blocker-severity defects

---

## Acceptance

The production/cutover domain is complete when:

1. The stack is documented in an ADR and is rebuildable from committed configuration.
2. A restore drill has passed into a clean environment, from the offsite copy, and is logged.
3. Monitoring is live, and every alert has a named responder and a runbook link.
4. The cutover runbook has been rehearsed end to end and corrected.
5. The agreed number of consecutive clean parallel-run days has been achieved.
6. Rollback triggers and procedure are written, tested, and agreed.
7. All three approvers have signed, with evidence attached.

---

## Open questions

Do not invent. These require a decision or source documentation before this
spec leaves DRAFT.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Hosting target: on-prem, VPS, or managed cloud? | Owner + technical operator | OPS-001, OPS-002, most of §1 |
| Q2 | RPO — how much data may be lost in a disaster? | Owner | OPS-010, OPS-011 |
| Q3 | RTO — how long may the ERP be down? | Owner | OPS-014, OPS-022 |
| Q4 | Offsite backup destination and who holds the decryption key | Owner | OPS-012 |
| Q5 | Backup retention required for tax/accounting | Accountant | OPS-013 |
| Q6 | Number of consecutive clean days required before approval | Owner + accountant | OPS-051 |
| Q7 | Non-zero tolerances, if any, for financial comparisons | Accountant | OPS-052 |
| Q8 | Magento connectivity direction and auth model | Technical operator | OPS-001, §5 step 6 |
| Q9 | Cutover window: date, duration, acceptable downtime | Owner | OPS-040 |
| Q10 | Named responder during cutover week and after | Owner | OPS-032, OPS-061 |
| Q11 | Confirm `OPS-###` prefix, or reassign Products | Owner | This document |
| Q12 | Is streaming replication in scope, or is backup-restore the only recovery path? | Technical operator | OPS-030 |

## Alignment with the master non-negotiables

`00_MASTER_BUILD.md` § Non-negotiables constrains this domain directly:

| Non-negotiable | Where it is enforced here |
|---|---|
| Inventory is counted at cutover, not blindly copied | Cutover steps 31–37; gate G1 requires the count to be approved |
| Reconciliation reports discrepancies, does not silently auto-correct | OPS-051 clean-day definition; `PARALLEL_RUN.md` § Handling a difference, step 3 |
| External events must be idempotent | Cutover steps 38–40 (Magento watermark); OPS-030 dead-letter alerting |
| No production credentials in the repository | OPS-002 |

**Ship APL remains out of scope** per `README.md` and `00_MASTER_BUILD.md`.
No cutover step depends on it.
