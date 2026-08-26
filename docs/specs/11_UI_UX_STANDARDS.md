# CAPITAL NUTRITION ERP — UI/UX GLOBAL STANDARDS

Companion to `11_UI_UX.md`. That document states the objective and the
principles. This document is the implementable rule set that satisfies them.

**Authority.** Where this document is specific, it is binding on every domain
chat and every module. Where it is silent, `11_UI_UX.md` principles govern and
the gap must be raised, not improvised — see *Change control* at the end.

**Audience.** Approximately three daily ERP users, all internal, all trained,
all repeating the same workflows many times per day. This is a power-user tool,
not a consumer product. Optimise for the hundredth use, not the first.

---

## 0. Platform constraint

The ERP is built on Tryton 8.0.x. The user interface is Tryton's own client
(Sao web client and/or the desktop client), driven by `ir.ui.view` XML, not a
bespoke front end.

This has a hard consequence that must be understood before reading further:

**We do not design pixels. We design structure.**

What we control:

- which views exist, and which is the default for each action
- the fields on every list and form, their order, grouping and labels
- column widths, expansion, optional/hidden columns, sums
- tabs (notebook pages) and their order
- menu structure, naming and depth
- default filters, default sort order, default context
- buttons, their labels, placement, states and confirmations
- error, warning and validation message text
- access rules, and therefore what each user can see and do
- terminology, everywhere

What we do not control without writing custom client code (which is **out of
scope** unless explicitly approved by ADR):

- typography, spacing, colour palette, iconography beyond Tryton's set
- page layout beyond Tryton's group/notebook/column model
- animation, transitions, toast styling
- the shape of the search bar or the pagination control

Any task that requires changing the second list is not a UI task. It is an
architecture decision and needs an ADR.

### Confirmed platform capabilities

Confirmed against the Tryton 8.0 server documentation
(`docs.tryton.org/latest/server/topics/views/`, which resolves to 8.0):

- **View types:** `form`, `tree`, `list-form`, `graph`, `calendar`, `board`.
- **`<tree>` attributes:** `editable`, `creatable`, `sequence`, `keyword_open`,
  `tree_state`, `visual`, `on_write`.
- **`<field>` in a tree:** `name`, `readonly`, `widget`, `tree_invisible`,
  `optional`, `visual`, `icon`, `sum`, `width`, `expand`, `prefix`, `suffix`,
  `symbol`, `factor`, `help_field`.
- **`visual` values:** `muted`, `success`, `warning`, `danger`.
- **Form layout elements:** `group` (`string`, `rowspan`, `expandable`,
  `homogeneous`, `col`), `notebook` (`colspan`, `states`), `page` (`string`,
  `angle`, `col`), `separator` (`string`, `name`, `colspan`), `newline`,
  `label` (`string`, `name`, `colspan`), `link` (`name`, `icon`, `empty`),
  `image` (`type`, `name`, `size`, `border`).
- **`states`:** PYSON evaluated against the current record, returning
  `invisible`, `required`, `readonly` (plus `icon`, `pre_validate`, `depends`
  on buttons).

### Verification register

The following are used by this specification but were **not** confirmed against
the 8.0 documentation in the session that wrote it (the docs site timed out).
Each must be confirmed by the developer implementing the first task that
depends on it, and this section updated with the result. Do not treat them as
settled.

| Ref | Assumption | Depends on |
|-----|-----------|-----------|
| V-01 | Toolbar keywords `form_action`, `form_relate`, `form_print`, `form_email`, `tree_open` place actions in the client's Action/Relate/Print/Email menus | §7 |
| V-02 | `ir.action.act_window.domain` records produce named filter tabs above a list | §6.3 |
| V-03 | `ModelView` button `confirm` presents a modal the user must accept before the method runs | §8 |
| V-04 | `UserWarning` produces a dismissible "do not ask again" confirmation keyed per user | §9.2 |
| V-05 | The client search bar accepts a typed domain syntax with comparison operators and ranges | §6.1 |
| V-06 | Bookmarks / saved searches are per-user and can be seeded per role | §6.4 |
| V-07 | `_history` models expose an "Open versions" style history browser in the client | §14 |
| V-08 | Documented keyboard shortcuts for new / save / search / next-previous record | §15 |
| V-09 | Records-per-page limit is user-selectable and its default is settable per action | §6.5 |

---

## 1. Terminology

Principle 5 of `11_UI_UX.md` requires consistent terminology. Tryton's stock
labels do not match the language used in `03_ACCOUNTING.md` and
`06_PURCHASING.md`, and they do not match how Capital Nutrition staff speak.
Left alone, the ERP will say one thing, the specifications will say another,
and the users will say a third.

### 1.1 Canonical lexicon

These are the only permitted user-facing terms. They apply to menus, view
labels, button labels, column headers, messages, reports and documentation.

| Canonical term | Never use |
|---|---|
| Customer | Client, Account (as a party), Buyer |
| Vendor | Supplier, Seller |
| Sales Order | SO, Order (unqualified), Sale |
| Purchase Order | PO in labels (fine in help text and messages), Purchase |
| Receipt | Goods receipt, GRN, Incoming shipment |
| Shipment | Delivery, Outgoing shipment, Picking |
| Customer Invoice | AR invoice, Sales invoice |
| Vendor Bill | Supplier invoice, AP invoice, Purchase invoice |
| Credit Note | Refund, Credit memo |
| Payment | Cash entry, Receipt (in the money sense) |
| Item | Product variant, SKU (fine as a column header for the code itself) |
| Lot | Batch, Lot number (as an entity) |
| Location | Bin, Place |
| Warehouse | Site, Facility |
| Case Pack | Pack size, Case qty, Inner |
| Price Break | Quantity discount, Volume price |
| Available | Free qty, On hand (these mean different things — see §1.3) |
| Period | Month (when the fiscal period is meant) |

### 1.2 Tryton label overrides

Tryton ships with "Supplier Invoice", "Purchase", "Party" and similar. Every
one of these must be overridden to the canonical term. This is done once, in a
dedicated UI module, not scattered across domain modules.

**UI-002** delivers this override layer. No domain module may ship its own
label override for a term already in the lexicon.

### 1.3 Terms that must never be conflated

Three inventory quantities are routinely confused, and confusing them causes
real shipping errors. They are distinct columns with distinct labels and each
one carries a `help` string:

- **On Hand** — physical quantity in the location right now.
- **Reserved** — on hand but committed to a confirmed sales order.
- **Available** — on hand minus reserved. This is the number a salesperson may
  promise.

No screen may show a bare "Quantity" column where one of these three is meant.

### 1.4 Lexicon changes

Adding or changing a canonical term is a change to this specification and
follows §17. It is not a domain-chat decision.

---

## 2. Navigation

### 2.1 Menu structure

Top-level menu items, in this order, and only these:

1. **Dashboard**
2. **Sales**
3. **Purchasing**
4. **Inventory**
5. **Accounting**
6. **Products**
7. **Integration**
8. **Reporting**
9. **Configuration**

Rules:

- **Maximum depth is three.** Top level → group → item. If something needs a
  fourth level, it belongs on a screen as a filter or a related action, not in
  the menu.
- **No menu item is a synonym of another.** One route to each screen. Where a
  screen is genuinely reachable from two domains, it lives under its owning
  domain and is reached from the other via a relate action (§7.3).
- **Configuration holds everything an operator touches less than monthly.**
  Chart of accounts, journals, fiscal years, tax configuration, warehouses,
  locations, sequences, users, access rules. Keeping it out of the daily menus
  is what makes the daily menus fast.
- **Menu item labels are nouns, plural**, matching the lexicon: "Sales Orders",
  "Vendor Bills", "Receipts". Not verbs, not "Manage X", not "X Management".
- **Every menu item opens a list, never a form.** Creation happens from the
  list. This keeps one mental model: find first, then act.

### 2.2 What lives directly under each top-level menu

Only the screens named in `11_UI_UX.md` §Core screens are first-class menu
items in the first release. Everything else is reached by relate action or
lives under Configuration. This is deliberate: nine top-level menus with four
to six items each is navigable at a glance; the same nine with twenty items
each is not.

### 2.3 Landing

The client opens on the Dashboard. The Dashboard is the only screen a user is
expected to look at without having decided what they want to do.

### 2.4 Tabs

Users work in multiple tabs. Nothing in the design may assume a single open
screen — in particular, no screen may depend on state set by another screen
having been visited first.

---

## 3. Page hierarchy

Every screen is one of four kinds. There are no others.

| Kind | Purpose | Opened by |
|---|---|---|
| **List** | Find and triage records | Menu item |
| **Detail** | Read and edit one record | Double-clicking a list row |
| **Wizard** | Complete a multi-step or parameterised operation | A button |
| **Report** | Read-only output, printed or exported | Print action |

Rules:

- A list never edits, with the single exception of the designated editable
  lists in §4.6.
- A detail form never contains a second, unrelated record's editing surface.
- A wizard is used whenever an operation needs input the record does not
  already hold, or whenever it is irreversible and needs a deliberate act.
- A report is never the only place a number appears. If a user needs a figure
  to do their job, it belongs on a screen.

---

## 4. Tables

Tables are where these three users will spend most of their day. This is the
most important section in this document.

### 4.1 Column budget

**A list has at most nine visible columns by default.** Above that, users stop
scanning and start hunting.

Additional columns are shipped as `optional="1"`, hidden by default and
available from the client's column chooser. Shipping a column as optional is
cheap; shipping it visible is expensive. When in doubt, ship it optional.

### 4.2 Column order

Left to right, invariably:

1. **Identifier** — the number or code the user says out loud. Narrow, fixed.
2. **Date** — the date that drives the workflow (order date, invoice date,
   receipt date). Narrow, fixed.
3. **Party** — customer or vendor. This is the `expand="1"` column.
4. **Descriptive columns** — reference, description, warehouse.
5. **Quantities**
6. **Amounts**
7. **State** — always last.

Rationale: identifier and date are what the user scans; party is what varies in
width; state is what they check once they have found the row. Putting state
first, which is a common instinct, wastes the most scannable position on the
least informative field.

### 4.3 Widths and expansion

- **Exactly one column per tree carries `expand="1"`**, normally the party or
  description column. Two expanding columns produce a layout that shifts as
  data changes, which defeats scanning.
- Identifier, date, quantity, amount and state columns carry explicit `width`.
- Numeric columns are right-aligned; this is Tryton's default for numeric
  fields and must not be overridden.

### 4.4 Sums

Any list whose rows are money or countable quantity carries `sum="1"` on those
columns. A user filtering a list is very often asking "how much is this" and
should not have to export to find out.

Specifically required: order totals, invoice totals, bill totals, payment
amounts, quantities on receipts and shipments, and aging bucket amounts.

### 4.5 Row state colouring

`visual` is the only permitted mechanism, and it carries exactly one meaning
across the whole ERP:

| `visual` | Meaning | Used for |
|---|---|---|
| `danger` | Requires human intervention now; something is wrong | Failed integration message, discrepancy on receipt, overdue past terms, posting error |
| `warning` | Needs attention soon, or is an exception but not an error | Approaching due date, partially received, on hold, back-ordered |
| `success` | Terminal and correct; no action needed | Paid, posted, shipped complete, reconciled |
| `muted` | Cancelled, superseded, draft-and-abandoned | Cancelled orders, voided documents |

Rules:

- **Colour is never the only carrier of meaning.** The State column always
  says the same thing in words. This is both an accessibility requirement and
  a practical one — colour meaning is forgotten between uses.
- `visual` is applied per row from the record's state and exception flags, and
  the same PYSON expression is reused across domains. It is defined once in the
  UI module (**UI-004**) and imported, not copy-pasted.
- No domain may introduce a fifth visual meaning.

### 4.6 Editable lists

Editable trees (`editable="top"` or `editable="bottom"`) are permitted **only**
for line-item entry inside a parent form:

- sales order lines
- purchase order lines
- receipt lines
- invoice and bill lines
- journal entry lines
- inventory count lines

They are forbidden on any top-level list opened from a menu. A menu list that
edits in place makes accidental modification easy and undoable changes
invisible, which violates principle 6.

Where a list is editable, `editable="bottom"` is used for documents that are
built up in order (order lines, invoice lines) so the cursor lands where the
next line goes.

### 4.7 Default sort

Every list declares its default order explicitly. It is never left to the
model's default.

- **Work lists** (things to act on): oldest first. Ascending date. The thing
  that has waited longest is at the top.
- **Reference lists** (things to look up): most recent first. Descending date.
- **Master data** (products, customers, vendors, accounts): by code or name,
  ascending.

### 4.8 Row action

Double-clicking a row opens the detail form. Always. `keyword_open` is not used
to open anything other than the record's own form.

---

## 5. Forms

### 5.1 Anatomy

Every document form has the same four zones, in this order top to bottom:

1. **Header** — identifier, state, and the two or three fields that identify
   the record (party, date, reference). Never inside a notebook page.
2. **Action row** — the workflow buttons for this document (§7.1).
3. **Notebook** — everything else, in tabs.
4. **Totals** — for financial documents, the amount block, outside the
   notebook and always visible.

Putting totals inside a tab is forbidden. A user reviewing a document must be
able to see the amount without navigating.

### 5.2 Notebook pages

Standard page order for document forms:

1. **Lines** — the line items. First, because it is what the user came for.
2. **Related** — linked documents (shipments, invoices, payments, the source
   order). Read-only lists with drill-through.
3. **Other Info** — terms, dates, shipping method, salesperson, references.
4. **Notes** — free text and attachments.

Pages beyond these four require justification. A page that is empty for a given
record type is hidden with `states`, not left as an empty tab — an empty tab
costs a click to discover.

### 5.3 Field grouping

- Fields are grouped by `<group>` with a `string`, not separated by bare
  `<separator>` runs. A named group tells the user what the fields have in
  common; a separator only tells them something changed.
- Two columns is the default form layout. Three is permitted only for short
  fields (dates, codes, checkboxes).
- Related fields sit adjacent. Date ordered and date required go together;
  neither goes next to the salesperson.

### 5.4 Required and readonly

- `required` in `states` is used for genuine data requirements. A field that is
  only required at a later workflow step is made required at that step by
  PYSON, not required from creation. Demanding data before the user can
  possibly have it is the single most common cause of workaround values.
- `readonly` in `states` is driven by document state. Once a document is
  confirmed or posted, its fields are readonly — this is principle 6 expressed
  in the UI, and it is not negotiable for accounting documents.
- A readonly field is still visible. Hiding fields as they become readonly
  makes documents look different depending on state, which destroys the users'
  ability to scan them.

### 5.5 Help text

Every field whose meaning is not obvious from its label carries `help`. In
particular: every quantity field (§1.3), every date field where "which date is
this" is ambiguous, every field that affects accounting, and every field with a
non-obvious default.

Help text is one sentence, states what the field does, and does not repeat the
label.

---

## 6. Filters, search, sorting, pagination

### 6.1 Search bar

The client's search bar is the primary find mechanism. Every list declares
`searchable` fields deliberately: the identifier, the party, the reference, and
the state at minimum.

`[V-05]` The typed domain syntax must be confirmed and then documented in the
user guide with five worked examples drawn from real Capital Nutrition
workflows. Power users will use this constantly; leaving it undocumented wastes
the single biggest efficiency win the platform offers.

### 6.2 Default filters

**Every list opens filtered to the work, not to the archive.** This is the
highest-leverage decision in this document.

| List | Default filter |
|---|---|
| Sales Orders | Not cancelled, not fully invoiced-and-shipped |
| Purchase Orders | Not cancelled, not fully received-and-billed |
| Receipts | Pending and in-progress |
| Customer Invoices | Unpaid or partially paid |
| Vendor Bills | Unpaid or partially paid |
| Payments | Current period |
| Integration Queue | Not successfully processed |
| Stock Moves | Last 90 days |

Every defaulted list must offer a one-click route to the unfiltered set. A
default filter the user cannot see or escape is a bug report waiting to happen.

### 6.3 Named filters

`[V-02]` Named filter tabs are provided for the standard triage cuts of each
work list — for example, on Purchase Orders: *Awaiting Receipt*, *Partially
Received*, *Awaiting Bill*, *Discrepancies*, *All*.

Rules:

- **"All" is always present and always last.** Users need a guaranteed escape
  from every filter.
- Filter names are the language of the work, not of the data model.
- Maximum six named filters per list.

### 6.4 Saved searches

`[V-06]` Where per-user bookmarks exist, each of the three users gets their
starting set seeded at go-live rather than being left to discover the feature.
This is a cutover task, not a build task — see **UI-030**.

### 6.5 Pagination

`[V-09]` Default page size is set per action, not left to the global default:

- work lists: large enough that the normal working set fits on one page
- reference and archive lists: the platform default

If a work list routinely paginates, the default filter is wrong. Treat
pagination on a work list as a signal to revisit §6.2.

---

## 7. Actions and buttons

### 7.1 Button hierarchy

Every form has at most **one primary action** — the thing the user came to do
next in the happy path. Confirm. Post. Receive. Pay.

Everything else is secondary. The primary action is the leftmost button in the
action row and is the only one whose label is a bare imperative verb.

Rules:

- Buttons appear only when they can be used. `states` hides a button that is
  not applicable to the current state rather than showing it disabled. A
  disabled button invites a click and teaches nothing.
- Buttons that undo or cancel are placed **right**, separated from the forward
  path. Never adjacent to the primary action.
- Destructive and irreversible actions are never the leftmost button, whatever
  the workflow shape.
- Button labels are verbs in the imperative: "Confirm", "Post", "Receive",
  "Cancel". Not "Confirmation", not "Do Post", not "OK".

### 7.2 Button labels must match the lexicon

A button that creates a Vendor Bill says "Create Vendor Bill", not "Generate
Supplier Invoice", regardless of what the underlying Tryton method is called.

### 7.3 Relate actions

`[V-01]` Drill-through between related documents uses the client's relate
menu. Required relations, at minimum:

- Sales Order → its shipments, its invoices, the customer's history
- Purchase Order → its receipts, its bills, the vendor's history
- Customer / Vendor → their orders, invoices, payments, aging
- Invoice / Bill → its payments, its source document, its GL entries
- Product → stock by location, movement history, vendor pricing, sales history
- Receipt → its purchase order, its bill, its stock moves
- Any accounting document → its GL move

**A user must never have to navigate to a menu to see something directly
related to the record in front of them.** This is principle 2 in its most
concrete form, and it is the acceptance test for this section.

### 7.4 Print and email

`[V-01]` Documents that go to a customer or vendor carry both a print and an
email action: sales order confirmation, invoice, credit note, purchase order,
statement. The email body is a template, not free text typed each time.

---

## 8. Dialogs and confirmation

### 8.1 When to confirm

`[V-03]` Confirmation is required for, and only for:

- irreversible actions (posting, closing a period, cancelling a confirmed
  document)
- actions with financial consequence beyond the record in view (paying,
  reconciling, revaluing inventory)
- bulk actions affecting more than one record
- anything that will produce a document a third party sees

Confirmation is **not** used for saving, for navigating, or for reversible
state changes. Confirming everything trains users to click through
confirmations, which is worse than confirming nothing.

### 8.2 Confirmation content

A confirmation states, in this order:

1. what will happen, in the lexicon
2. how many records it will happen to
3. whether it can be undone

"Post 14 vendor bills? Posted bills cannot be modified." — not "Are you sure?"

### 8.3 Wizards

Wizards are used when an operation needs input. A wizard:

- states its purpose in the window title
- shows what it will act on before asking for input
- has a final step that summarises what is about to happen
- never has more than three steps for a daily-use operation

---

## 9. Notifications, errors, warnings

### 9.1 Errors

Every user-facing error message must answer three questions. A message that
answers fewer is not finished.

1. **What went wrong**, in the lexicon, naming the specific record.
2. **Why**, in business terms rather than data-model terms.
3. **What to do about it.**

Bad: `The value of the field "party" on "account.invoice" is not valid
according to its domain.`

Good: `Cannot post this vendor bill: no payable account is set for vendor
Acme Foods. Set a payable account on the vendor before posting.`

Rules:

- No message contains a model name, a field technical name, a traceback, or an
  internal ID unless it also contains the human-readable identifier.
- Every message names the record by the number the user would say out loud.
- Where the fix is a specific screen, the message says which screen.
- Error message text is reviewed as part of task acceptance. A task with a raw
  platform error on a reachable path is not complete.

### 9.2 Warnings

`[V-04]` Warnings are for "this is unusual but may be correct" — over-receipt,
back-dated document, price outside the expected break, shipping below available
quantity.

A warning is dismissible and remembers the dismissal per user. A warning that
appears every single time becomes invisible within a week and stops protecting
anyone.

If a condition is *always* wrong, it is an error, not a warning. If a condition
is *usually* fine, it is neither — leave it alone.

### 9.3 Validation

Validation fires as early as it honestly can. Validating an order line on
document confirmation, when the problem was knowable at line entry, means the
user has to find the bad line among fifty.

---

## 10. Empty states

An empty list is ambiguous: no records, or a filter hiding them?

Every list resolves that ambiguity. Where the platform allows the empty message
to be set, it states which of the two is the case and offers the next action:

- *No purchase orders awaiting receipt.* — nothing to do, this is good news
- *No sales orders match this filter. Clear the filter to see all orders.*

Where the platform's empty rendering cannot be customised, the list's named
filters (§6.3) must make the active filter visible at a glance, so an empty
result is never mistaken for empty data.

New-install empty states — no products, no customers, no chart of accounts —
are a cutover concern and are covered by the cutover runbook, not here.

---

## 11. Loading states

Constraints on responsiveness, in the absence of control over the client's
spinner:

- **No default list view may require an aggregate the database cannot serve
  quickly.** Computed availability, aging and roll-up totals on a default list
  must be backed by stored or indexed values, not per-row computation.
- Expensive figures belong on the detail form or a report, not on a list that
  opens dozens of times a day.
- Any operation expected to exceed a few seconds is a wizard with an explicit
  start, not a button that appears to hang.
- List performance is an acceptance criterion, not a nice-to-have: every core
  list must open within two seconds against production-volume data. This is
  tested during parallel run.

---

## 12. Status representation

### 12.1 One state vocabulary

Document states use one vocabulary across all domains:

`Draft → Confirmed → Processing → Done`, with `Cancelled` available from any
pre-Done state.

Accounting documents additionally use `Posted`, which is terminal and readonly.

Domains may not invent parallel vocabularies — no "Validated" in one domain and
"Approved" in another for the same concept.

### 12.2 State is always a word

The State column shows the state as text, always, on every list. `visual`
colouring (§4.5) supplements it and never replaces it.

### 12.3 Exception flags are separate from state

"Has a discrepancy", "is on hold", "failed to sync" are not states. They are
flags shown as their own indicator, because a record can be Confirmed *and*
have a discrepancy. Collapsing flags into the state vocabulary is how state
machines become unmaintainable.

---

## 13. Permissions

### 13.1 Roles

Three users, but roles are still defined by function, not by person, so that
cover and turnover do not require re-engineering:

- **Operations** — sales, purchasing, inventory. Read on accounting.
- **Accounting** — full accounting, period close. Read on sales, purchasing,
  inventory.
- **Administrator** — configuration, users, integration replay.

Role assignment per named user is an operational decision recorded in
`ops/`, not in this specification.

### 13.2 UI consequence

- A user who cannot use a menu does not see it.
- A user who cannot perform an action does not see its button.
- Read-only access shows the record fully, with editing disabled — not a
  reduced or different view. Two users discussing the same record must be
  looking at the same thing.
- Where an action is refused by a record rule, the message says which
  permission is missing and who to ask, not "access denied".

### 13.3 Period lock is a permission, not a UI state

Once a period is closed, the refusal to modify comes from the accounting layer.
The UI reflects it; it does not implement it. `03_ACCOUNTING.md` scenario 11
("attempted modification of posted move → refused") is an accounting test, and
the UI's only job is to make the refusal comprehensible.

---

## 14. Audit visibility

### 14.1 Always available

`[V-07]` Every document form makes reachable, without leaving the record:

- who created it and when
- who last modified it and when
- the version history, where the model is a history model
- the state transition trail: who confirmed, who posted, who cancelled, and
  when

### 14.2 Placement

Audit information lives in a consistent place — the last notebook page or the
form's standard footer. It is never on the first page, and it is never absent.

### 14.3 Accounting documents

Posted accounting documents show the GL move they produced, reachable by relate
action (§7.3). An accountant reviewing a month must be able to get from any
document to its accounting effect and back in two clicks. This is a direct
requirement of the `03_ACCOUNTING.md` acceptance criteria.

---

## 15. Keyboard efficiency

`[V-08]` Principle 8 requires keyboard efficiency be preserved where practical.
Concretely:

- **Tab order follows visual order** on every form. Where the platform's
  default tab order does not match the layout, the layout is wrong and gets
  fixed — the layout serves the keyboard, not the reverse.
- **Line entry is fully keyboardable.** On an editable line list, a user must
  be able to enter a complete line and start the next one without touching the
  mouse. This is tested explicitly (**UI-021**).
- Platform shortcuts for new, save, search and record navigation are confirmed,
  documented in the user guide, and taught at go-live. Three users who know six
  shortcuts are meaningfully faster than three who know none.
- No custom shortcut is introduced that conflicts with a platform one.

---

## 16. Density and accessibility

- **Density over whitespace.** These users compare rows. Default client density
  is used; nothing is added that increases row height.
- **No information conveyed by colour alone** (§4.5, §12.2). This is a hard
  rule.
- **No information conveyed by icon alone.** An icon may accompany a label; it
  may not replace one on any control whose meaning is not universal.
- Numbers use consistent decimal places within a column. A quantity column that
  shows `1`, `1.5` and `1.250` in successive rows cannot be scanned.

**OPEN — locale.** Date format, number format, currency symbol placement and
first day of week are not settled. This affects every screen and must be decided
before **UI-003**. Do not assume; raise it.

The US-vs-Canada part of this note is now settled: the operating jurisdiction is
Canada (ADR-0006), and `03_ACCOUNTING.md` has been corrected. Currency is CAD
unless the accountant states otherwise.

---

## 17. Change control

`11_UI_UX.md` states that no domain chat may invent a conflicting pattern, and
that a new pattern must be documented, evaluated for reuse, folded into the
specification, and applied consistently.

The mechanism:

1. The domain chat writes the proposed pattern into `docs/handoffs/` as a
   `UI-PATTERN-<domain>-<n>.md` note stating the problem, the proposed pattern,
   and which existing pattern it was found insufficient for.
2. It is evaluated against this document. Either an existing pattern covers it
   — in which case the domain uses that — or this document is amended.
3. If amended, the amendment lands here **before** the domain implements it,
   and any already-shipped screen that should adopt it gets a retrofit task.
4. `docs/STATUS.md` records the amendment.

A pattern implemented without going through this is a defect regardless of how
good it is, because the cost of divergence is paid forever by three people who
use this system every day.

---

## Acceptance

This specification is satisfied when:

1. Every core screen in `11_UI_UX_SCREENS.md` conforms to every rule here, and
   deviations are documented amendments rather than accidents.
2. A user can complete the common sales, purchasing, inventory and accounting
   workflows without navigating to a menu for anything related to the record in
   front of them.
3. No reachable path produces a raw platform error message.
4. Every list opens on the work, opens within two seconds, and offers a visible
   route to the unfiltered set.
5. Terminology matches §1 everywhere: menus, labels, buttons, messages,
   reports.
6. Every verification-register item is confirmed or resolved, and this document
   updated accordingly.
