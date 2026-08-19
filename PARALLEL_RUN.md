# RUNBOOK — PARALLEL RUN

Covers: `OPS-050` … `OPS-052`
Status: **DRAFT** — required clean-day count (Q6) and tolerances (Q7) not yet agreed.

## Purpose

Run Odoo and the ERP over the same business activity and prove they agree.
The parallel run is the evidence that replaces "it appears to work."

## What "parallel" means here

Both systems process the same day's business, independently, and are compared
at end of day. Whether entry is dual (staff enter twice) or replicated
(automated feed into the ERP) is a decision to record here — it changes both
the effort and what the comparison actually proves.

**Decision required:** dual entry, or replicated feed?

Dual entry is expensive but tests the people and the process as well as the
software. A replicated feed is cheap but proves only that the data moved —
it will not surface the workflow gaps that a dual-entry run finds on day two.

---

## Daily comparison

Run at end of business, same cut-off time both systems, same timezone
(see OPS-003 — a timezone mismatch shows up as a systematic one-day
difference that people waste days chasing).

### C1 — Inventory

| Check | Tolerance |
|---|---|
| Total quantity on hand, all items | Zero |
| Quantity by item — count of items differing | Zero |
| Total inventory valuation | Zero / TBD (Q7) |
| Valuation by item — count of items differing | Zero |
| Quantity by location | Zero |
| Items with negative stock | Zero in both, or explained |

### C2 — Accounts receivable

| Check | Tolerance |
|---|---|
| Total AR balance | Zero |
| AR by customer — count of customers differing | Zero |
| Aging buckets (current / 30 / 60 / 90 / 90+) | Zero |
| Open invoice count | Zero |
| Unapplied credits / payments | Zero |

### C3 — Accounts payable

| Check | Tolerance |
|---|---|
| Total AP balance | Zero |
| AP by vendor — count of vendors differing | Zero |
| Aging buckets | Zero |
| Open bill count | Zero |

### C4 — Profit and loss

| Check | Tolerance |
|---|---|
| Revenue, period to date | Zero |
| COGS, period to date | Zero / TBD if costing methods differ |
| Gross margin | Derived |
| Each expense account, period to date | Zero |
| Net result | Zero |

If the two systems use different costing policies, COGS will diverge by
construction. That is not a tolerance — it is a mapping decision that must be
recorded before the run starts, not discovered on day three.
See `03_ACCOUNTING.md` § Open questions (costing policy).

### C5 — Sales

| Check | Tolerance |
|---|---|
| Order count | Zero |
| Gross sales | Zero |
| Tax | Zero |
| Net sales | Zero |
| Discounts | Zero |
| Returns / credit notes | Zero |
| Sales by channel (direct vs. Magento) | Zero |

### C6 — Operational orders

| Check | Tolerance |
|---|---|
| Open sales orders: count and value | Zero |
| Open purchase orders: count and value | Zero |
| Shipments today: count, lines, quantity | Zero |
| Receipts today: count, lines, quantity | Zero |
| Backorders | Zero |

### C7 — Magento state

| Check | Tolerance |
|---|---|
| Magento orders received today, both systems | Zero |
| Stock published to Magento vs. ERP on-hand | Zero |
| Sync errors | Zero, or explained |
| Dead-letter queue | Zero |

### C8 — Trial balance

| Check | Tolerance |
|---|---|
| Debits = credits, both systems | Exact, both |
| Balance by account | Zero |
| Count of accounts differing | Zero |

---

## Clean day (OPS-051)

A day is **clean** when:

1. Every comparison above is within its documented tolerance, **and**
2. Every difference outside tolerance has a written explanation that has been
   accepted by the accountant, **and**
3. The explanation identifies a specific cause — not a category of cause.

Accepted explanation: *"Invoice INV-1043 was entered in Odoo at 17:12 and in
the ERP at 09:04 the next morning; timing only, no data difference. Confirmed
by comparing line detail."*

Not an accepted explanation: *"Small rounding difference."* / *"Probably the
timezone."* / *"It resolved itself the next day."*

A difference that resolves itself without being understood has not been
explained. It has been outlived, and it will return during the close.

### The counter

- Required consecutive clean days: **TBD (Q6)**
- The counter **resets to zero** on any non-clean day. It does not pause and it does not resume.
- Resetting is not a punishment; it is the whole mechanism. A run of clean days interrupted by an unexplained difference proves nothing about the days on either side of it.

---

## Daily log

`docs/ops/parallel-run-log.md`, one row per day:

| Day | Date | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | Clean? | Consecutive | Differences and explanations | Signed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Signed daily by the accountant. Same day — a comparison reviewed a week later
is a comparison nobody can investigate.

---

## Handling a difference

1. **Record it before investigating.** Differences that get fixed before being written down disappear from the evidence and from the pattern.
2. **Classify:**
   - **Timing** — same data, different moment. Verify by comparing line detail, not just the total.
   - **Mapping** — accounts, taxes, or units configured differently. Fix the configuration; re-run the comparison.
   - **Logic** — the two systems compute differently. Decide which is correct. If the ERP is wrong, it is a defect.
   - **Data** — the migrated data is wrong. Fix the migration, not the record. Fixing a record by hand hides a migration bug that will recur at cutover.
   - **Human** — entered differently in one system. Common with dual entry, and itself useful information about where the process is ambiguous.
3. **Fix the cause.** Adjusting a value to make today's comparison tie, without changing what produced it, converts a visible defect into an invisible one.
4. **Re-run the comparison** after the fix.
5. **Record the resolution**, and whether the day is clean.

## Automate the comparison

Write the comparison as a script (`scripts/compare_odoo_erp.py`) producing a
dated report, rather than assembling it by hand each day.

Manual comparison degrades. By day four, someone is checking the totals and
skipping the by-item breakdown, which is exactly where the difference will be.

---

## Exit

The parallel run is complete when:

- [ ] The required number of consecutive clean days is achieved (Q6)
- [ ] Every difference encountered during the run is closed with a recorded cause
- [ ] The accountant confirms in writing that the ERP is reliable for the period
- [ ] No open defect is capable of causing a financial difference

This is a precondition for the cutover window opening. See
`CUTOVER_RUNBOOK.md` § Before the window opens.
