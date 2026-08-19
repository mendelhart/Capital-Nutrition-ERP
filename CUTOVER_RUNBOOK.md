# RUNBOOK — PRODUCTION CUTOVER

Covers: `OPS-040` … `OPS-042`
Status: **DRAFT** — durations are estimates until the rehearsal (OPS-041) measures them.

## How to use this document

- Times are relative (`T-` / `T+`) where `T0` is the moment the ERP becomes
  the system of record. Absolute times are filled in once the window is set (Q9).
- Every step has an owner, a duration, and a completion checkbox.
- **Do not skip a checkbox because a step "obviously worked."** The checkbox
  is what lets a tired operator at T+6 know what has actually been done.
- Three decision gates (G1, G2, G3) are hard stops. At each, the answer is
  GO or ROLLBACK. "Continue and watch it" is not an option.
- Durations are replaced with rehearsal-measured values before the real run.

## Roles

| Role | Name | Responsibility |
|---|---|---|
| Cutover lead | TBD | Calls the gates. Only this person declares GO or ROLLBACK. |
| Technical operator | TBD | Executes migration, database, and infrastructure steps |
| Accountant | TBD | Owns all financial reconciliation sign-offs |
| Inventory lead | TBD | Owns the physical count |
| Owner | TBD | Final authority; approves the G3 gate |
| Comms | TBD | Notifies staff and, if needed, customers |

One person may hold more than one role, but the cutover lead must be
explicitly named before the window opens, and must not be simultaneously
executing the migration. The person calling the gates cannot also be the
person whose work is being judged at those gates.

## Before the window opens — preconditions

None of these are done on cutover day. If any is unchecked, the window does not open.

- [ ] Rehearsal completed end-to-end against a production data copy (OPS-041)
- [ ] Restore drill passed within the last 30 days (OPS-022)
- [ ] Required consecutive clean parallel-run days achieved (OPS-051)
- [ ] Monitoring live and observed for the full parallel-run period
- [ ] Rollback procedure tested during the rehearsal
- [ ] Zero open blocker-severity defects
- [ ] Freeze communicated to all staff (OPS-042)
- [ ] Magento freeze/behaviour during the window agreed and communicated
- [ ] All roles above filled with names
- [ ] Contact list distributed, including out-of-hours numbers
- [ ] Accountant available for the full window, not on call

---

## Timeline

### T-7 days — Communication and freeze notice

| # | Step | Owner | Est. |
|---|---|---|---|
| 1 | Send the freeze notice: window, what stops, what staff do with orders/receipts/payments during it | Comms | — |
| 2 | Confirm supplier and courier expectations for the window | Owner | — |
| 3 | Confirm Magento behaviour during the freeze (storefront open? orders queued?) | Technical operator | — |
| 4 | Distribute this runbook to everyone with a role | Cutover lead | — |

- [ ] T-7 complete

### T-2 days — Final readiness

| # | Step | Owner | Est. |
|---|---|---|---|
| 5 | Re-verify every precondition above | Cutover lead | 1 h |
| 6 | Take and verify a full Odoo backup; confirm it restores | Technical operator | TBD |
| 7 | Confirm production ERP environment is provisioned and empty | Technical operator | 30 m |
| 8 | Confirm rollback path is available and tested | Technical operator | 30 m |
| 9 | Dry-run the extraction scripts against a copy | Technical operator | TBD |

- [ ] T-2 complete

### T-1 day — Reduce the surface

| # | Step | Owner | Est. |
|---|---|---|---|
| 10 | Clear open transactional work in Odoo as far as practical: post pending invoices, confirm/close pending receipts and shipments | All | — |
| 11 | Resolve or explicitly defer any open reconciliation item | Accountant | — |
| 12 | Confirm no scheduled Odoo job will run during the window | Technical operator | 15 m |
| 13 | Reconfirm all role-holders are available tomorrow | Cutover lead | 15 m |

- [ ] T-1 complete

The cleaner Odoo is at freeze, the smaller the reconciliation at T+2. Time
spent here is cheaper than time spent at the G2 gate.

---

### T-6h — FINAL ODOO FREEZE

| # | Step | Owner | Est. |
|---|---|---|---|
| 14 | Announce freeze start | Comms | 5 m |
| 15 | Stop all Odoo write access — revoke or set users read-only. Announcing a freeze is not enforcing one. | Technical operator | 15 m |
| 16 | Disable all Odoo scheduled jobs and background workers | Technical operator | 15 m |
| 17 | Freeze the Magento→Odoo integration; record the exact stop point | Technical operator | 15 m |
| 18 | **Record the freeze watermark**: last order ID, last invoice number, last stock move ID, last Magento order processed, timestamp | Technical operator | 15 m |
| 19 | Take the definitive final Odoo backup; verify it; keep it untouched. This is the rollback anchor. | Technical operator | TBD |
| 20 | Announce freeze confirmed | Comms | 5 m |

- [ ] T-6h complete — **freeze watermark recorded and stored in the incident log**

The watermark is the single most important artifact of the cutover. Every
later reconciliation and any rollback depends on knowing exactly where Odoo
stopped. Record it in writing, in two places.

---

### T-5h — FINAL EXTRACTION

| # | Step | Owner | Est. |
|---|---|---|---|
| 21 | Run the extraction against the frozen Odoo database | Technical operator | TBD |
| 22 | Verify extract row counts against Odoo source counts | Technical operator | 30 m |
| 23 | Verify extract control totals: AR, AP, trial balance, inventory quantity and valuation | Accountant | 30 m |
| 24 | Archive the extract with a checksum | Technical operator | 15 m |

- [ ] T-5h complete — extract counts and control totals match Odoo

**If the extract does not tie to Odoo, stop. Do not migrate a bad extract and
plan to fix it later.** Fixing reconciliation differences after load, inside
a live window, is how cutovers overrun.

---

### T-4h — MIGRATION / LOAD

| # | Step | Owner | Est. |
|---|---|---|---|
| 25 | Confirm the ERP production database is empty | Technical operator | 10 m |
| 26 | Run transformation and load | Technical operator | TBD |
| 27 | Capture all load errors and warnings — zero unexplained errors permitted | Technical operator | — |
| 28 | Run post-load integrity checks: referential integrity, orphan records, sequence positions | Technical operator | 30 m |
| 29 | Verify loaded row counts against the extract | Technical operator | 20 m |
| 30 | **Take a database snapshot of the freshly loaded ERP** — this is the restart point if a later step fails | Technical operator | TBD |

- [ ] T-4h complete — load clean, snapshot taken

Step 30 is not optional. Without it, any failure after this point means
re-running extraction and load from the beginning, which is usually what
turns an overrunning cutover into an aborted one.

---

### T-2h — PHYSICAL INVENTORY COUNT

| # | Step | Owner | Est. |
|---|---|---|---|
| 31 | Freeze all physical movement. Nothing ships, nothing is received, nothing moves between locations. | Inventory lead | 10 m |
| 32 | Execute the full physical count | Inventory lead | TBD |
| 33 | Second count on all discrepancies and on high-value items | Inventory lead | TBD |
| 34 | Enter counted quantities | Inventory lead | TBD |
| 35 | Produce the variance report: system vs. counted, by item and by value | Inventory lead | 30 m |
| 36 | Investigate variances above the agreed threshold | Inventory lead + accountant | TBD |
| 37 | Accountant approves the inventory adjustment and its accounting treatment | Accountant | 30 m |

- [ ] T-2h complete — count entered, variances explained, adjustment approved

The count is the one step that cannot be repeated later. Warehouse movement
stays frozen until step 37 is signed off, not until counting stops.

---

### T-1h — GATE G1: DATA INTEGRITY

**Cutover lead calls this gate. GO or ROLLBACK.**

| Check | Criterion | Verified by |
|---|---|---|
| Extract ties to Odoo | Exact | Accountant |
| Load ties to extract | Exact | Technical operator |
| Trial balance | Debits = credits, ties to Odoo at freeze | Accountant |
| AR total and aging | Ties to Odoo at freeze | Accountant |
| AP total and aging | Ties to Odoo at freeze | Accountant |
| Inventory quantity | Matches approved physical count | Inventory lead |
| Inventory valuation | Ties, adjustment approved | Accountant |
| Open sales orders | Count and value tie | Operations |
| Open purchase orders | Count and value tie | Operations |
| Load errors | Zero unexplained | Technical operator |
| Referential integrity | Clean | Technical operator |

- [ ] **G1 = GO** — signed: cutover lead ______  accountant ______
- [ ] G1 = ROLLBACK → go to `ROLLBACK.md`

Rollback at G1 is cheap: Odoo is intact and frozen, nothing has been
activated, no external system has been touched. This is by far the best place
to stop. A difference nobody can explain is a reason to stop here, not a
reason to hurry.

---

### T-0h — MAGENTO SYNCHRONIZATION STATE

| # | Step | Owner | Est. |
|---|---|---|---|
| 38 | Reconcile Magento orders against the freeze watermark; identify anything that arrived during the window | Technical operator | TBD |
| 39 | Load or queue window orders into the ERP; confirm none are duplicated or lost | Technical operator | TBD |
| 40 | Set the ERP's Magento cursor/watermark to the correct starting position | Technical operator | 20 m |
| 41 | Verify stock levels the ERP will publish match the approved physical count | Technical operator | 20 m |
| 42 | Point the integration at the ERP; keep it **disabled** | Technical operator | 20 m |
| 43 | Confirm Odoo can no longer write to Magento | Technical operator | 15 m |

- [ ] T-0h complete — Magento state reconciled, integration configured but off

Two systems believing they own Magento stock is the highest-consequence
mistake available today. Step 43 is what prevents it.

---

### T0 — ERP ACTIVATION

| # | Step | Owner | Est. |
|---|---|---|---|
| 44 | Enable ERP background workers | Technical operator | 10 m |
| 45 | Enable ERP scheduled jobs | Technical operator | 10 m |
| 46 | Enable the Magento integration | Technical operator | 10 m |
| 47 | Confirm monitoring is receiving data from every signal in `MONITORING.md` | Technical operator | 20 m |
| 48 | Enable user access; confirm logins and permissions | Technical operator | 20 m |
| 49 | Announce: the ERP is now the system of record | Comms | 5 m |

- [ ] **T0 complete — ERP LIVE**

---

### T+1h — VERIFICATION

Real transactions, executed by the people who will do this work daily. Not a
demo, and not driven by whoever built the system.

| # | Scenario | Owner | Pass criterion |
|---|---|---|---|
| 50 | Create and confirm a sales order | Operations | Order created, stock reserved |
| 51 | Ship it | Operations | Stock moves, accounting entries correct |
| 52 | Invoice it | Accountant | Invoice posts, AR and GL correct |
| 53 | Receive a payment and reconcile | Accountant | AR clears, bank/cash correct |
| 54 | Create and confirm a purchase order | Purchasing | PO created |
| 55 | Receive against it | Warehouse | Stock and valuation correct |
| 56 | Post the vendor bill | Accountant | AP and GL correct |
| 57 | Credit note / return | Accountant | Reversal correct |
| 58 | Magento order flows in end-to-end | Technical operator | Appears correctly, no duplicate |
| 59 | Stock change publishes to Magento | Technical operator | Magento reflects ERP within lag target |
| 60 | Run trial balance, P&L, balance sheet, AR aging, AP aging, inventory valuation | Accountant | All tie and are internally consistent |
| 61 | Confirm queue depth and dead-letter queue | Technical operator | Queue draining, DLQ = 0 |
| 62 | Confirm no unexpected errors in logs since T0 | Technical operator | Clean |

- [ ] T+1h complete — all scenarios pass

Any failure here is triaged immediately as blocker / non-blocker. Blockers go
straight to gate G2.

---

### T+4h — GATE G2: OPERATIONAL VIABILITY

**Cutover lead calls this gate. GO or ROLLBACK.**

| Check | Criterion |
|---|---|
| Verification scenarios 50–62 | All pass |
| Blocker defects | Zero |
| Magento sync | Flowing both directions, lag within target |
| Dead-letter queue | Zero |
| Failed jobs | Zero |
| Monitoring | All signals reporting, no unexplained alerts |
| Staff | Able to do their actual work |
| Accountant | Financial reports tie and are trusted |

- [ ] **G2 = GO** — signed: cutover lead ______  accountant ______  owner ______
- [ ] G2 = ROLLBACK → go to `ROLLBACK.md`

Rollback at G2 is more expensive than G1 — real transactions exist in the ERP
and Magento has been touched — but it is still available. The rollback
deadline is defined in `ROLLBACK.md`; after it passes, the path is
forward-only. Know that time before this gate is called, not after.

---

### T+8h — END OF DAY 1

| # | Step | Owner | Est. |
|---|---|---|---|
| 63 | Take the first production backup of the live ERP and verify it | Technical operator | TBD |
| 64 | Confirm the backup landed offsite | Technical operator | 20 m |
| 65 | Run the day-1 comparison against the frozen Odoo baseline (`PARALLEL_RUN.md`) | Accountant | TBD |
| 66 | Log all issues, workarounds, and open items | Cutover lead | 30 m |
| 67 | Brief everyone on day-2 expectations and how to report problems | Cutover lead | 20 m |
| 68 | Confirm overnight scheduled jobs are configured and someone is watching for their results | Technical operator | 20 m |

- [ ] Day 1 complete

---

### T+1 day to T+5 days — STABILISATION

Daily, every day:

- [ ] Overnight jobs completed successfully
- [ ] Backup succeeded and reached offsite
- [ ] Dead-letter queue = 0
- [ ] Magento sync lag within target
- [ ] Queue depth normal
- [ ] Financial reports tie
- [ ] New issues logged and triaged
- [ ] Rollback still available? (Record yes/no explicitly each day. When the answer first becomes "no", say so out loud to everyone.)

---

### T+5 days — GATE G3: ACCEPTANCE

**Owner calls this gate.**

| Check | Criterion |
|---|---|
| Stabilisation period | Completed with no blocker defects |
| Financial reports | Tie for the full period |
| Backups | Succeeding, offsite, verified |
| Restore drill | Passed against a live production backup |
| Monitoring | Stable, alerts tuned, no chronic noise |
| Staff | Operating without daily workarounds |
| Accountant | Confirms the ERP is the reliable book of record |

- [ ] **G3 = ACCEPTED** — signed: owner ______  accountant ______  technical operator ______

On acceptance:
- Odoo goes permanently read-only. Do not decommission it — retain it for the
  documented retention period as the historical record.
- Rollback is formally closed. Record the date it closed.
- The cutover incident log is archived to `docs/ops/`.

---

## Standing rules for the window

1. **One voice.** Only the cutover lead declares GO, ROLLBACK, or a step complete.
2. **No unplanned changes.** Anything not in this runbook is proposed to the cutover lead, written down, and approved before it happens. "While we're in here" is how a controlled window stops being controlled.
3. **Record everything.** Every step: who, start, end, outcome. Memory is unreliable at hour nine.
4. **Fix the runbook as you go.** Corrections are made in the document during the window, not reconstructed afterwards.
5. **Stop when tired.** If the window overruns badly, rolling back and rerunning on a fresh day beats pushing through at 02:00 with a fatigued team. Overrun is itself a rollback trigger — see `ROLLBACK.md`.
