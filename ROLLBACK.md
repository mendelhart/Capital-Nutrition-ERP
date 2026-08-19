# RUNBOOK — ROLLBACK AND GO/NO-GO

Covers: `OPS-060`, `OPS-061`, `OPS-070`, `OPS-071`
Status: **DRAFT** — rollback deadline and approvers not yet set.

## Principle

Rollback triggers are agreed and signed **before** the cutover window opens.

During a failing cutover, the people deciding whether to roll back are tired,
invested in the work they have just done, and aware that rolling back means
doing it all again. That is the worst possible moment to be defining what
counts as failure. Define it now, while nothing is at stake, and then follow
the definition.

---

## 1. Rollback triggers

Any single trigger is sufficient. Triggers are **not** subject to negotiation
during the window — that is the point of writing them down.

### Automatic — roll back, no discussion

| # | Trigger |
|---|---|
| R1 | Migrated financial data does not tie to Odoo at the freeze watermark, and the difference is not explained within the G1 gate window |
| R2 | Trial balance does not balance in the ERP |
| R3 | Inventory in the ERP does not match the approved physical count |
| R4 | Data loss or corruption detected in the migrated data |
| R5 | Duplicate or lost Magento orders that cannot be fully reconciled |
| R6 | Both systems capable of writing to Magento simultaneously, and this cannot be resolved immediately |
| R7 | The ERP cannot produce a trial balance, P&L, balance sheet, AR aging, or AP aging |
| R8 | ERP production backup cannot be taken or verified on day 1 |

### Judgement — cutover lead decides, with the owner

| # | Trigger |
|---|---|
| R9 | A verification scenario (steps 50–62) fails and has no acceptable workaround |
| R10 | Staff cannot perform core daily work: take an order, ship, receive, invoice |
| R11 | The window overruns its planned duration by more than the agreed margin (TBD) |
| R12 | Magento sync cannot be stabilised within the agreed period |
| R13 | Blocker defects accumulate faster than they are resolved |
| R14 | The accountant does not trust the financial position |
| R15 | Key personnel become unavailable, or the team is too fatigued to work safely |

R14 deserves emphasis. If the accountant is not confident, the business cannot
close its books, and no amount of technical success compensates for that.

R11 and R15 are the ones teams talk themselves out of. Overrun and fatigue
cause the mistakes that turn a recoverable cutover into an unrecoverable one.

---

## 2. Authority

| Gate | Who may declare rollback |
|---|---|
| Before G1 | Cutover lead, unilaterally |
| G1 | Cutover lead |
| G1 → G2 | Cutover lead; owner may also require it |
| G2 | Cutover lead + owner |
| After G2, before deadline | Owner, on the accountant's or cutover lead's recommendation |
| After the rollback deadline | Not available — forward-only |

Nobody else may declare rollback, and nobody may overrule it once declared.
A declared rollback is executed.

---

## 3. Rollback deadline

Rollback is available only until: **TBD — set before the window opens.**

Suggested basis, to be confirmed: the end of the cutover day, or the first
point at which business transactions have been entered into the ERP that
cannot practically be re-entered into Odoo — whichever comes first.

After the deadline:
- The path is forward-only. Problems are fixed in the ERP.
- The deadline is announced to everyone when it passes. People must know
  which world they are in; a team that believes rollback is still available
  will make different, worse decisions than one that knows it is not.

Record the actual deadline here before the window: __________

---

## 4. Rollback procedure

Tested during the rehearsal (OPS-041). If it has not been tested, it is not a
procedure — it is a hope.

### 4.1 Declare and stop

| # | Step | Owner |
|---|---|---|
| 1 | Cutover lead declares ROLLBACK. State the trigger by number. | Cutover lead |
| 2 | Record the time and the reason | Cutover lead |
| 3 | Stop all cutover activity immediately. No "just finishing this step." | All |
| 4 | Announce to all staff: stop entering data into the ERP | Comms |

### 4.2 Sever the ERP

| # | Step | Owner |
|---|---|---|
| 5 | Disable the ERP→Magento integration first. Before anything else — this is the outward-facing risk. | Technical operator |
| 6 | Disable ERP scheduled jobs and background workers | Technical operator |
| 7 | Disable ERP user access | Technical operator |
| 8 | **Snapshot the ERP database as-is.** Do not delete it. It holds the evidence of what went wrong and any transactions entered after T0. | Technical operator |

### 4.3 Capture what happened in the ERP

| # | Step | Owner |
|---|---|---|
| 9 | Extract every transaction created in the ERP after T0: orders, shipments, receipts, invoices, payments, adjustments | Technical operator |
| 10 | Produce a re-entry worklist | Technical operator |
| 11 | Identify anything that reached Magento or a customer from the ERP | Technical operator |

Step 11 matters: an ERP-issued invoice or shipment notification that reached a
customer cannot be un-sent. It must be reconciled in Odoo, not ignored
because the system that produced it was rolled back.

### 4.4 Restore Odoo

| # | Step | Owner |
|---|---|---|
| 12 | Confirm the final Odoo backup (cutover step 19) is intact and verified | Technical operator |
| 13 | If Odoo was left frozen and untouched, unfreeze — no restore needed. Preferred. | Technical operator |
| 14 | If Odoo was modified, restore from the step-19 backup | Technical operator |
| 15 | Re-enable Odoo scheduled jobs and workers | Technical operator |
| 16 | Repoint Magento at Odoo; verify the ERP can no longer write to Magento | Technical operator |
| 17 | Reconcile Magento orders received during the window against the freeze watermark | Technical operator |
| 18 | Verify Odoo control totals against the freeze watermark: AR, AP, trial balance, inventory | Accountant |

Keeping Odoo frozen and untouched, rather than shut down or repurposed, is
what makes step 13 possible. That is the cheap rollback. Protect it.

### 4.5 Re-enter and reconcile

| # | Step | Owner |
|---|---|---|
| 19 | Re-enter the §4.3 worklist into Odoo | Operations |
| 20 | Apply the approved physical count adjustment to Odoo | Inventory lead + accountant |
| 21 | Reconcile: Odoo now reflects reality | Accountant |
| 22 | Confirm Magento is in sync with Odoo | Technical operator |
| 23 | Accountant confirms Odoo is a correct book of record | Accountant |

- [ ] Rollback complete — signed: cutover lead ______ accountant ______

### 4.6 Resume operations

| # | Step | Owner |
|---|---|---|
| 24 | Announce: Odoo is the system of record; normal operations resume | Comms |
| 25 | Confirm staff can work normally | Cutover lead |
| 26 | Verify Odoo backups are running again | Technical operator |

### 4.7 Post-rollback review

Within 5 business days:

- What triggered the rollback, and was the trigger correct?
- What was missed at the rehearsal that appeared on the day?
- Which runbook steps were wrong, missing, or took longer than estimated?
- What must be true before another attempt?
- Was the rollback itself smooth? Fix what was not.

Output: a corrected runbook, a defect list, and preconditions for attempt two.

**A rollback is not a failure of the project.** It is the control working as
designed. The failure mode this whole document exists to prevent is a business
running on a book of record nobody trusts.

---

## 5. Go / No-Go and approval (OPS-070, OPS-071)

### 5.1 Evidence required before sign-off

No approval is given without these attached:

- [ ] Restore drill passed within the last 30 days, logged (OPS-022)
- [ ] Required consecutive clean parallel-run days achieved, logged (OPS-051)
- [ ] Rehearsal completed end-to-end, runbook corrected (OPS-041)
- [ ] Accountant has closed a representative month on the ERP and confirmed it ties (`03_ACCOUNTING.md` § Acceptance)
- [ ] Monitoring live, every alert has a named responder and a documented response
- [ ] Rollback procedure tested during the rehearsal
- [ ] Zero open blocker-severity defects
- [ ] Rollback deadline set and communicated
- [ ] All cutover roles filled by name

### 5.2 Sign-off

> No production cutover based solely on "it appears to work."

| Approver | Name | Confirms | Signature | Date |
|---|---|---|---|---|
| Owner | | Business is ready; accepts the cutover window and its risk | | |
| Accountant | | Financial data is correct, ties to Odoo, and the ERP can be closed on | | |
| Technical operator | | Stack, backups, restore, monitoring, and rollback are proven | | |

All three are required. Any approver may withhold approval, and withheld
approval means the window does not open — it is not a majority vote.

### 5.3 Gate decisions during the window

| Gate | When | Decision | Signed |
|---|---|---|---|
| G1 — Data integrity | T-1h | GO / ROLLBACK | |
| G2 — Operational viability | T+4h | GO / ROLLBACK | |
| G3 — Acceptance | T+5 days | ACCEPTED / not yet | |

Record the time, the decision, and the reason for every gate — including the
ones that pass easily. The record is what makes the next cutover, if there is
one, better than this one.
