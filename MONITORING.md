# RUNBOOK — MONITORING AND ALERTING

Covers: `OPS-030` … `OPS-032`
Status: **DRAFT** — thresholds require the OPS-004 capacity baseline.

## Principle

Every alert answers three questions before it is allowed to exist:

1. What is broken, in business terms?
2. Who is woken up, or who reads it in the morning?
3. What do they do about it?

An alert that cannot answer all three is deleted. In a business this size,
the scarce resource is attention, and an alert nobody acts on consumes it
just as fast as one that matters.

---

## 1. Signal catalogue

Thresholds marked TBD are set from the capacity baseline (OPS-004), not guessed.

### 1.1 Application

| Signal | Threshold | Severity | Response |
|---|---|---|---|
| Health endpoint failing | 2 consecutive failures | **Page** | §3.1 Application down |
| Error rate | TBD above baseline | Warn | Check logs, correlate with deploy |
| Response time p95 | TBD | Warn | Check DB (§1.2) and queue depth first |
| Login failures spike | TBD | Warn | Possible credential attack or auth misconfiguration |

### 1.2 PostgreSQL

| Signal | Threshold | Severity | Response |
|---|---|---|---|
| Instance unreachable | Any | **Page** | §3.2 Database down |
| Connection count | > 80% of max | **Page** | Connection leak or traffic spike; identify and kill idle-in-transaction |
| Longest transaction | > 5 min | Warn | Long transactions block vacuum and hold locks |
| Idle-in-transaction | > 5 min | Warn | Usually an application bug; find and fix, do not just kill repeatedly |
| Lock waits | > 30 s | Warn | Identify blocking query |
| Cache hit ratio | < 95% sustained | Warn | Undersized memory or a missing index |
| Table/index bloat | TBD | Info | Schedule maintenance |
| Autovacuum not running on a large table | > 24 h | Warn | Transaction-ID wraparound risk if ignored long enough |

### 1.3 Integration and background work

| Signal | Threshold | Severity | Response |
|---|---|---|---|
| Queue depth | > TBD, or rising for 30 min | Warn | Workers stopped, or one poison message blocking the queue |
| Queue depth | > TBD critical | **Page** | Orders are not being processed |
| Worker process count | Below expected | **Page** | Workers died; restart and find out why |
| Magento sync lag | > TBD minutes | Warn | Stock and orders drifting between systems |
| Magento sync lag | > TBD critical | **Page** | Overselling risk |
| Magento API errors | Any sustained | Warn | Auth expiry, IP block, or upstream outage |
| **Dead-letter queue depth** | **> 0** | **Page** | §3.3. Never alert-only-above-N. One permanently failed message is one lost business event. |
| Failed scheduled job | Any | Warn | Nightly work failed silently — this is what silent failure looks like |
| Scheduled job did not run | Missed window | Warn | Worse than a failure, because nothing appears wrong |

### 1.4 Infrastructure

| Signal | Threshold | Severity | Response |
|---|---|---|---|
| Disk free — data volume | < 20% | Warn | |
| Disk free — data volume | < 10% | **Page** | §3.4 |
| Disk free — WAL volume | < 20% | **Page** | A full WAL volume stops the database. Never let archiving fail silently. |
| Disk free — backup staging | < 20% | Warn | Backups will start failing |
| WAL archiving failing | Any | **Page** | PITR window is closing right now |
| Memory pressure / swap | TBD | Warn | |
| CPU sustained | > TBD for 15 min | Warn | |
| TLS certificate expiry | < 21 days | Warn | |
| TLS certificate expiry | < 7 days | **Page** | Avoidable total outage |
| Replication lag (if used) | > TBD | Warn | |

### 1.5 Backup

| Signal | Threshold | Severity | Response |
|---|---|---|---|
| Last successful full backup | Older than schedule + grace | **Page** | §3.5 |
| Backup job failed | Any | **Page** | |
| Backup size deviation | ±TBD% vs. trailing average | Warn | A backup that suddenly shrank is often an empty backup |
| Backup duration deviation | ±TBD% | Info | Early warning of growth or degradation |
| Offsite copy age | Older than schedule + grace | **Page** | Local backups are not disaster recovery |
| Restore drill overdue | > 30 days (pre-cutover) | Warn | Blocks cutover approval (OPS-022) |

Backup-size monitoring earns its place: silent truncation to a near-empty
dump is one of the few failure modes that passes every other check.

---

## 2. Routing (OPS-032)

Capital Nutrition does not have a 24/7 operations team. Route accordingly.

| Tier | Meaning | Channel | Hours |
|---|---|---|---|
| **Page** | Business is stopped or data is at risk | Phone / SMS to named responder | Any hour |
| **Warn** | Will become a Page if ignored | Email / chat | Business hours |
| **Info** | Trend and capacity data | Dashboard only | Reviewed weekly |

Named responder: **TBD (Q10).**
During cutover week, a single named responder is on call and this is written
into the cutover runbook before the window opens.

---

## 3. Response procedures

Each entry is deliberately short. Long procedures do not get read at 03:00.

### 3.1 Application down
1. Confirm from a second location — rule out your own network.
2. Check container/process state; check for OOM kill.
3. Check the database (§3.2) — the application is usually the symptom.
4. Check disk (§3.4).
5. Restart the application. If it fails again immediately, stop restarting and read the logs.
6. Record start time, actions, and end time for the incident log.

### 3.2 Database down
1. Check disk on the data and WAL volumes first. This is the most common cause.
2. Check the PostgreSQL log for the last clean shutdown or crash.
3. If the volume is full, free space before attempting a start.
4. Do **not** restore from backup as a first response to an unreachable database. Diagnose first — restoring loses everything since the last backup.
5. Escalate if the cause is not identified within 30 minutes.

### 3.3 Dead-letter queue non-empty
1. Read the failed message and the failure reason. Do not blind-retry.
2. Classify: transient (retry), poison/malformed (fix and replay), or logic defect (fix code, then replay).
3. Assess business impact — an order, a stock movement, and a log line are not equivalent losses.
4. Replay after the cause is fixed. Confirm the replayed message succeeded.
5. Record it. Recurring dead letters are a defect, not an operations task.

### 3.4 Disk pressure
1. Identify the consumer: WAL, logs, backup staging, database growth, or temp files.
2. Never delete WAL by hand. Deleting unarchived WAL destroys your PITR window and can prevent the database from starting.
3. Safe first moves: rotate and compress logs, clear expired backup staging, drop old temp files.
4. If growth is genuine, extend the volume. Free space is not a fix.

### 3.5 Backup failed or stale
1. Read the backup job log.
2. Check disk on the backup staging area and credentials for the offsite target.
3. Run the backup manually and watch it complete.
4. If it cannot be fixed within the RPO window, this is escalated — the business is running without a recovery point.
5. After recovery, run a restore drill against the first good backup. A backup that has failed and been fixed is unproven until restored.

---

## 4. Dashboard

One dashboard, readable in 30 seconds, showing:
- application up/down
- database up/down, connections, longest transaction
- queue depth, dead-letter count
- Magento sync lag
- disk free on all volumes
- last successful backup, last successful offsite copy, last passed restore drill
- certificate expiry

The last-restore-drill tile matters more than it appears. It is the only
place where "we can recover" is a fact on a screen rather than an assumption.

---

## 5. Pre-cutover requirement

Monitoring is live and observed for at least the full parallel-run period
**before** cutover. Cutover day is not the day to discover the alerting
threshold is wrong.
