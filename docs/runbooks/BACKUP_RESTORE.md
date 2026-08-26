# RUNBOOK — BACKUP AND RESTORE

Covers: `OPS-010` … `OPS-022`
Status: **DRAFT** — commands are placeholders until hosting is decided (Q1).

## Who this is written for

An operator who did not build this system, working at an inconvenient hour,
possibly without access to whoever did build it. Write every step so that
person can follow it.

---

## 1. What is backed up

| Item | Why | Method |
|---|---|---|
| PostgreSQL cluster | The ERP | Full dump or physical base backup |
| WAL archive | Point-in-time recovery between full backups | Continuous archiving |
| Application configuration | A restored database with no configuration is not a running ERP | Config repo + secrets store |
| Attachments / document store | Invoices, POs, scanned documents | File-level backup |
| Secrets and decryption keys | Everything above is useless without them | Separate store, separate custody |

A database-only backup is not a complete backup. If the attachment store and
configuration are not covered, say so explicitly rather than implying coverage.

---

## 2. Backup schedule

To be finalised against the RPO decision (Q2).

| Backup | Frequency | Retention | Destination |
|---|---|---|---|
| Full | TBD | TBD (Q5) | Local + offsite |
| WAL archive | Continuous | TBD | Offsite |
| Attachments | TBD | TBD | Offsite |
| Configuration | On change (git) | Indefinite | Repository |

Retention must be enforced automatically. Manual pruning drifts, and the
drift is always discovered when the disk fills.

---

## 3. Encryption and key custody

- Encrypt before the data leaves the host. Do not rely solely on the storage
  provider's at-rest encryption.
- Store the decryption key **outside** production. If an incident takes out
  production, the key must survive it.
- At least two people can retrieve the key. A single-custodian key is a
  single point of failure wearing a security costume.
- Record key custody in `docs/ops/key-custody.md` — who holds it, where, and
  how it is rotated.

**Verification:** at each restore drill, the key is retrieved by someone
other than its creator, using only the written procedure.

---

## 4. Restore procedure (OPS-014)

> Read this whole section before starting. Do not restore over a running
> production database. Restore into a clean target, verify, then decide.

### 4.1 Preconditions

- [ ] Target environment is clean and empty
- [ ] Target has enough disk for the database plus WAL replay headroom
- [ ] PostgreSQL major version on the target matches production (16)
- [ ] Backup location credentials available
- [ ] Decryption key retrieved
- [ ] Start time recorded

### 4.2 Steps

1. **Identify the backup.** Record the backup ID, its timestamp, and whether
   this is a full restore or a point-in-time restore to a target timestamp.
2. **Fetch** the backup and the WAL segments needed to reach the target time.
3. **Verify integrity** — checksum against what was recorded at backup time.
   A corrupt backup found here is a good outcome; found during an incident, it is not.
4. **Decrypt** into the staging area.
5. **Restore the database** into the clean target.
6. **Replay WAL** to the target timestamp, if doing point-in-time recovery.
7. **Restore attachments** and configuration.
8. **Start the application** against the restored database, with outbound
   integrations disabled — see the warning below.
9. **Run the verification set** (§5).
10. **Record** the end time and the result.

### 4.3 Integration safety — read this

A restored copy still holds production credentials. Started carelessly, it
will happily send real requests to Magento, real email to customers, and real
payments to a payment provider.

Before starting any restored instance:
- [ ] Outbound Magento sync disabled
- [ ] Outbound email disabled or redirected to a sink
- [ ] Scheduled jobs and queue workers disabled
- [ ] Payment/tax provider credentials replaced with sandbox values

Restoring a backup and emailing every customer an invoice they already paid
is a self-inflicted incident that has happened to better-resourced teams than this one.

---

## 5. Verification set (OPS-021)

Run against every restored copy. Compare to the snapshot recorded at backup time.

| # | Check | Expected |
|---|---|---|
| V1 | Row counts: partners, products, account moves, invoices, stock moves | Match snapshot exactly |
| V2 | Trial balance: sum(debit) − sum(credit) | 0 |
| V3 | AR total | Matches snapshot |
| V4 | AP total | Matches snapshot |
| V5 | Inventory quantity total | Matches snapshot |
| V6 | Inventory valuation total | Matches snapshot |
| V7 | Latest posted document date and ID | Matches snapshot, or the PITR target |
| V8 | Magento sync watermark | Matches snapshot |
| V9 | Application starts; authenticated login succeeds | Yes |
| V10 | No errors in application log during startup | Yes |

Store the queries in `scripts/verify_restore.sql` so the check is identical
every time and cannot drift from what was verified last quarter.

---

## 6. Restore drill (OPS-020)

### Procedure

1. Provision a clean environment.
2. Restore **from the offsite encrypted copy**. Not from a local copy — the
   local copy will not exist in the scenario you are drilling for.
3. Follow §4 exactly as written. If a step is wrong or missing, that is the
   most valuable finding of the drill. Fix the runbook the same day.
4. Run §5.
5. Record duration.
6. Log the outcome.

### Log format — `docs/ops/restore-drill-log.md`

| Date | Backup ID | Operator | Source | Duration | V1–V10 | Result | Runbook changes |
|---|---|---|---|---|---|---|---|
| | | | offsite | | | PASS / FAIL | |

Log failures with the same care as successes. A drill log containing only
passes is a log nobody trusts.

### Pass criteria (OPS-022)

- All of V1–V10 pass
- Duration is within the agreed RTO (Q3)
- The runbook was followed as written, with corrections recorded

### Cadence

At least monthly before cutover. Post-cutover cadence: TBD.

**A failed or overdue drill blocks cutover approval.** No exceptions — a
restore path that has not been exercised in the last 30 days is a hypothesis.

---

## 7. Escalation

If restore fails and this is a real incident, not a drill:

1. Stop. Do not delete or overwrite the failed target — it is evidence.
2. Try the previous backup generation, following §4 from the top.
3. If the failure is decryption or key access, go to the key custody document.
4. If the failure is corruption across multiple generations, Odoo is still
   the fallback of record until cutover is complete. After cutover it is not —
   which is precisely why drills are non-negotiable.

Named escalation contact: **TBD (Q10).**
