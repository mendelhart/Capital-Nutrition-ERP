# UI/UX DOMAIN — TASK BACKLOG

Task ID convention per `specs/README.md`: `UI-###`.

Governing specifications: `11_UI_UX.md` (principles), `11_UI_UX_STANDARDS.md`
(rules), `11_UI_UX_SCREENS.md` (screens).

**Numbering is a register, not a schedule.** Build order is in §Sequencing.

**Status key:** `OPEN` · `BLOCKED` · `IN PROGRESS` · `DONE`

---

## Hard blockers

These are not UI tasks and cannot be resolved by the UI stream. They gate the
waves marked below.

| Blocker | Gates |
|---|---|
| `01_ARCHITECTURE.md` does not exist | UI-001 |
| `04_PRODUCTS.md`, `05_INVENTORY.md` do not exist | Wave 3 |
| `07_CUSTOMERS.md`, `08_SALES.md` do not exist | Wave 4 |
| `09_MAGENTO.md`, `12_INTEGRATION_CONTRACTS.md` do not exist | Wave 5 |
| Locale decision (Standards §16 OPEN) | UI-003, and therefore all screen work |
| Dashboard mechanism ADR (Screens §1.4 OPEN) | UI-010 |
| Expiry warning window (Screens §4.3 OPEN) | UI-024 |

---

## Wave 0 — Foundation

Nothing in Waves 1–6 starts before Wave 0 is complete. Building screens first
and standardising later means retrofitting every screen, which is exactly the
failure `11_UI_UX.md` §UI consistency contract exists to prevent.

### UI-001 — UI module scaffold · `BLOCKED`

Create the `capnut_ui` module that owns everything cross-domain in this
specification. Domain modules depend on it; it depends on no domain module.

- **Delivers:** module skeleton, registration, test harness, dependency rule
  documented in the module README.
- **Blocked by:** `01_ARCHITECTURE.md` (module layout and naming are its call).
- **Acceptance:** module installs on a fresh database; a domain module can
  depend on it; it depends on no domain module.

### UI-002 — Terminology override layer · `OPEN`

Implement the canonical lexicon (Standards §1) as label overrides over Tryton's
stock strings.

- **Depends on:** UI-001
- **Delivers:** override records for every term in §1.1 and §1.2; the lexicon
  as a reviewable list in the module.
- **Acceptance:** no screen, menu, button, message or report shows "Supplier",
  "Client", "Picking" or any other forbidden term. Verified by a text sweep of
  rendered views, not by inspection.

### UI-003 — Locale, date and number formatting · `BLOCKED`

- **Blocked by:** the locale OPEN in Standards §16. `03_ACCOUNTING.md` refers
  to a US chart of accounts; the business is Canadian. This must be answered by
  the business, not assumed.
- **Delivers:** language, date format, number format, currency display and
  first-day-of-week configured as loadable fixtures; decimal places fixed per
  quantity and money field.
- **Acceptance:** reproducible on a fresh database; every quantity column shows
  consistent decimal places (Standards §16).

### UI-004 — Shared state and visual library · `OPEN`

- **Depends on:** UI-001
- **Delivers:** one reusable definition of the four `visual` meanings
  (Standards §4.5) and the state vocabulary (§12.1), imported by every domain.
- **Acceptance:** no domain module contains its own copy of a visual
  expression. Enforced by UI-008.

### UI-005 — Menu structure · `OPEN`

- **Depends on:** UI-001, UI-002
- **Delivers:** the nine top-level menus in the order given in Standards §2.1,
  depth capped at three, Configuration populated, every item opening a list.
- **Acceptance:** no menu path exceeds three levels; no two items open the same
  screen; every item opens a list, not a form.

### UI-006 — Roles and access matrix · `OPEN`

- **Depends on:** UI-001, UI-005
- **Delivers:** the three roles (Standards §13.1) as groups; a written matrix
  of model and button access per role; menu visibility following access.
- **Acceptance:** logged in as each role, invisible menus and absent buttons
  match the matrix exactly. A refused action names the missing permission
  (Standards §13.2).

### UI-007 — Message catalogue and standard · `OPEN`

- **Depends on:** UI-001
- **Delivers:** the three-part error rule (Standards §9.1) as a written
  standard with worked examples; the mechanism for defining messages; the
  warning-dismissal pattern (§9.2).
- **Acceptance:** the standard is applied in review of every subsequent task;
  no reachable path in any shipped screen produces a raw platform error.

### UI-008 — Convention test harness · `OPEN`

- **Depends on:** UI-001, UI-004
- **Delivers:** automated tests over view definitions asserting the mechanical
  rules: at most nine visible columns per default tree; exactly one `expand`
  per tree; State is the last visible column; every list declares an explicit
  order; sums present on money and quantity columns; no editable tree reachable
  from a menu; no duplicated visual expression.
- **Acceptance:** the harness fails a deliberately non-conforming view. It runs
  in CI on every change.
- **Note:** this is the single highest-leverage task in the backlog. It is what
  makes the consistency contract enforceable rather than aspirational, across
  chats that cannot see each other's work.

### UI-009 — Close the verification register · `OPEN`

- **Depends on:** UI-001
- **Delivers:** V-01 through V-09 in Standards §Verification register each
  confirmed against a running Tryton 8.0.x instance, with the result written
  back into that section. Where an assumption is wrong, the affected sections
  are amended before any dependent task starts.
- **Acceptance:** the register contains no unconfirmed rows.
- **Note:** do this early. Several rules in the standards are written on
  assumptions; discovering one is wrong after five screens are built is
  expensive and entirely avoidable.

---

## Wave 1 — Purchasing

`06_PURCHASING.md` exists, so this domain can be specified end-to-end. It is
first for that reason, and because its nine-step acceptance is the most
demanding UX test in the ERP.

### UI-010 — Dashboard shell · `BLOCKED`

- **Blocked by:** the mechanism ADR (Screens §1.4)
- **Depends on:** UI-001, UI-005
- **Delivers:** the Dashboard shell and the tile-registration mechanism. Tiles
  themselves are contributed by each domain's task.
- **Acceptance:** shell renders empty; a domain can register a tile with a
  count and a drill-through; loads within two seconds.

### UI-011 — PO list · `OPEN`

- **Depends on:** Wave 0, UI-010
- **Delivers:** Screens §3.1 — columns, optional columns, default filter,
  default sort, six named filters, row visuals; registers the overdue-PO
  Dashboard tile.
- **Acceptance:** opens on work not archive; "All" present and last; row count
  matches the Dashboard tile; passes UI-008.

### UI-012 — PO detail · `OPEN`

- **Depends on:** UI-011
- **Delivers:** Screens §3.2 — header, action row, five notebook pages, totals
  block, editable-bottom lines including **Case Pack** and **Price Break
  Applied**, relates per Standards §7.3.
- **Acceptance:** `06_PURCHASING.md` acceptance step 3 — the buyer can see
  which price break was applied without leaving the line. Case-pack violation
  raises a dismissible warning, not a block.

### UI-013 — Receiving · `OPEN`

- **Depends on:** UI-012
- **Delivers:** Screens §3.3 — receipt list and detail, received-defaults-to-
  expected, required lot capture where lot-tracked, over-receipt warning
  stating quantity and percentage variance.
- **Acceptance:** `06_PURCHASING.md` step 5 (partial receipt) completes without
  leaving the screen; over-receipt is possible with confirmation; a lot-tracked
  item cannot be received without a lot.

### UI-014 — Discrepancies · `OPEN`

- **Depends on:** UI-013
- **Delivers:** Screens §3.4 — the discrepancy list sorted by value impact
  descending, four resolution actions, audit of resolver and method; registers
  two Dashboard tiles.
- **Acceptance:** `06_PURCHASING.md` step 7 completes from this screen alone;
  every resolution is attributable.

### UI-015 — Vendor history · `OPEN`

- **Depends on:** UI-011
- **Delivers:** Screens §3.5 as a relate action, including the vendor item list
  with SKU, price, breaks, case pack and lead time.
- **Acceptance:** reachable by relate from a PO and from the vendor; never a
  menu item.

---

## Wave 2 — Accounting

`03_ACCOUNTING.md` exists. Its acceptance criteria are the test.

### UI-016 — Customer invoices · `OPEN`
Screens §5.1. Registers the overdue-AR Dashboard tile.
**Acceptance:** aging visible without running a report; overdue rows `danger`.

### UI-017 — Vendor bills · `OPEN`
Screens §5.2, including the three-way Match column and Discrepancies filter
carried from `06_PURCHASING.md`. Registers the match-failure Dashboard tile.
**Acceptance:** `06_PURCHASING.md` step 6 (match the bill) is visible here.

### UI-018 — Payments · `OPEN`
Screens §5.3, including unallocated as a named filter and Dashboard tile.
**Acceptance:** unallocated money is discoverable without a report.

### UI-019 — Reconciliation · `OPEN`
Screens §5.4 — two panes, suggested matches, always-visible running difference,
confirmation stating any accepted difference.
**Acceptance:** `03_ACCOUNTING.md` scenario 3 completes; difference is never
hidden.

### UI-020 — Period status and reporting · `OPEN`
Screens §5.5 and §5.6 — the pre-close checklist with drill-through per check;
the eight standard reports with parameters on output, export, and drill-through
to entries.
**Acceptance:** `03_ACCOUNTING.md` acceptance — an accountant confirms every
tie from screens and reports, reaching the entries behind any figure.
Scenario 11 (modify posted move → refused) produces a comprehensible message,
not a platform error.

### UI-021 — Keyboard-efficient line entry · `OPEN`

Cross-cutting, sits here because Waves 1–2 deliver every line-entry surface.

- **Depends on:** UI-012, UI-013, UI-016, UI-017
- **Delivers:** tab order matching visual order on every line list; a complete
  line enterable and the next started without the mouse; platform shortcuts
  confirmed (V-08) and documented.
- **Acceptance:** a timed run — twenty order lines entered without touching the
  mouse — passes on order lines, bill lines and receipt lines.

---

## Wave 3 — Inventory

**Blocked by:** `04_PRODUCTS.md` and `05_INVENTORY.md`.

### UI-022 — Stock lookup · `BLOCKED`
Screens §4.1. Search-first; the three quantity columns per Standards §1.3, each
with `help`.
**Acceptance:** a user can answer "can I promise this" in one screen and cannot
mistake on-hand for available.

### UI-023 — Warehouse and location view · `BLOCKED`
Screens §4.2 — hierarchical tree with roll-up, persisted expansion.

### UI-024 — Lot information and traceability · `BLOCKED`
Screens §4.3. Also blocked by the expiry warning window decision.
**Acceptance:** from a lot, every customer shipment containing it is reachable;
from a shipment, every lot. This is the recall test and it is pass/fail.

### UI-025 — Movement history · `BLOCKED`
Screens §4.4 — 90-day default, date descending, every row drills to its source.

### UI-026 — Availability · `BLOCKED`
Screens §4.5 — projected availability by date, feeding the reorder review that
`06_PURCHASING.md` requires be human-approved.
**Acceptance:** a buyer can review and trust a reorder suggestion before
ordering.

---

## Wave 4 — Sales

**Blocked by:** `07_CUSTOMERS.md` and `08_SALES.md`. Also depends on UI-026 —
sales line entry shows availability, which must exist first.

### UI-027 — Sales order list · `BLOCKED`
Screens §2.1 with the fulfillment and payment columns of §2.2. Registers the
on-hold and late Dashboard tiles.

### UI-028 — Sales order detail · `BLOCKED`
Screens §2.3, including **Available** at line entry.
**Acceptance:** a salesperson cannot promise stock without seeing availability.

### UI-029 — Customer history · `BLOCKED`
Screens §2.4, including items bought with last price and last order date.
**Acceptance:** the §2.5 phone-call test passes without leaving the screen.

### UI-030 — Seed saved searches and bookmarks · `OPEN`
Cutover task (Standards §6.4). Each of the three users gets their starting set
seeded and is shown how to add their own.
**Acceptance:** at go-live, no user starts from an empty bookmark list.

---

## Wave 5 — Integration

**Blocked by:** `09_MAGENTO.md` and `12_INTEGRATION_CONTRACTS.md`.

### UI-031 — Queue · `BLOCKED`
Screens §6.1. Reference is the `expand` column and is not optional.

### UI-032 — Failures and dead letters · `BLOCKED`
Screens §6.2 and §6.3 — attempt, error and resulting business state all shown;
dead letters require explicit audited disposition and cannot be silently
deleted. Registers two `danger` Dashboard tiles.

### UI-033 — Replay wizard · `BLOCKED`
Screens §6.4 — four steps, duplicate warning, outcome recorded per message.
**Acceptance:** replay cannot be triggered without seeing what it will affect.

### UI-034 — Integration reconciliation · `BLOCKED`
Screens §6.5 — differences both ways, drill-through to both sides, nothing
auto-resolves.

---

## Wave 6 — Hardening

### UI-035 — Error message sweep · `OPEN`
Every reachable path exercised; every raw platform message replaced per
Standards §9.1.
**Acceptance:** zero raw platform errors on any reachable path.

### UI-036 — Empty state sweep · `OPEN`
Standards §10 — no list can be ambiguous between "no records" and "filtered".

### UI-037 — List performance · `OPEN`
Standards §11 — every core list opens within two seconds against
production-volume data. Run during parallel run, not before.
**Acceptance:** measured, recorded in `ops/parallel-run-log.md`, no core list
over two seconds.

### UI-038 — End-to-end workflow runs · `OPEN`
The five scripted runs in Screens §Cross-screen acceptance, each performed by
the user who will do that job, with navigation counted.
**Acceptance:** no run requires returning to a menu mid-task. Any that does is
a finding against the specification.
- **Note:** this is the acceptance criterion of `11_UI_UX.md` itself. Until
  UI-038 passes, the UI/UX domain is not done regardless of task status.

---

## Sequencing

```
Wave 0  UI-001 → UI-002 ─┬→ UI-005 → UI-006
        UI-003 ──────────┤
        UI-004 ──────────┤
        UI-009 (early!) ─┴→ UI-007, UI-008
Wave 1  UI-010 → UI-011 → UI-012 → UI-013 → UI-014
                 UI-015
Wave 2  UI-016, UI-017, UI-018 → UI-019 → UI-020 → UI-021
Wave 3  UI-022 → UI-023, UI-024, UI-025 → UI-026
Wave 4  UI-027 → UI-028 → UI-029;  UI-030 at cutover
Wave 5  UI-031 → UI-032 → UI-033 → UI-034
Wave 6  UI-035, UI-036, UI-037, UI-038
```

Two notes on order:

- **UI-009 before anything is built.** The standards rest on nine unverified
  platform assumptions. Confirming them costs a day; discovering one is wrong
  after Wave 1 costs a rebuild.
- **UI-008 before Wave 1.** The consistency contract is only real if it is
  enforced automatically. Domain chats cannot see each other's work; the test
  harness is what stands in for that.

---

## Handoff protocol

Per `specs/README.md`, the repository is the memory between chats. A UI task is
not complete until:

1. the change is in the module
2. `docs/STATUS.md` is updated
3. any pattern not already in `11_UI_UX_STANDARDS.md` has gone through
   Standards §17 — documented in `docs/handoffs/`, evaluated, and folded into
   the specification **before** it ships
4. UI-008 passes
