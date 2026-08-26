# ADR-0011: Module and package naming

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** ERP Architect chat (`FND-002`), Morris Hart
- **Answers:** `STATUS.md` next-action 8 — reconcile module naming

## Context

Three naming conventions are in use for the same kind of thing.

| Where | Name |
|---|---|
| On disk | `modules/capital_nutrition_base`, `modules/capital_nutrition_sale` |
| `docs/ARCHITECTURE.md` (pristine package text) | `capnut_core`, `capnut_purchasing`, `capnut_magento`, `capnut_report` |
| `docs/tasks/PURCHASING_TASKS.md` | `capnut_purchase` |
| `migration/` | distribution `capnut-migration`, package `capnut_migration`, script `capnut-migrate` |

A Tryton module name is not cosmetic. It is the directory under
`trytond/modules`, the `depends` entry in every dependent module's `tryton.cfg`,
the prefix of every XML id, and part of the model names it registers. Renaming
one after it holds data means a data migration, not a `git mv`. Two independent
chats implementing Purchasing and Magento from the current documents would
create modules that could not both be right.

## Decision

**Tryton modules are named `capital_nutrition_<domain>`**, with the model and XML
prefix `capital_nutrition.`.

The sanctioned set is listed in `docs/ARCHITECTURE.md` § 4.3. The two modules
already on disk are correct and are not renamed.

**Standalone Python distributions that run outside the Tryton runtime keep the
short form** — `capnut-migration`, console script `capnut-migrate`. They are not
Tryton modules, they are not discovered by `trytond`, and shortening a
command an operator types is worth more there than symmetry.

`capnut_core`, `capnut_purchasing`, `capnut_purchase`, `capnut_magento` and
`capnut_report` are superseded as Tryton module names. `capnut_core`'s role is
already filled by `capital_nutrition_base`.

## Consequences

### Accepted costs

- `capital_nutrition_purchase` is eleven characters longer than `capnut_purchase`
  in every `depends` list and every import.
- Two conventions coexist in one repository. The rule that separates them is
  "does `trytond` load it" — mechanical, checkable, and it needs no judgement.
- `docs/tasks/PURCHASING_TASKS.md` still says `capnut_purchase` in four places.
  It is corrected by the Purchasing chat when `PUR-001` starts, and the
  correction is one word. It is left as documented drift rather than edited by an
  architecture chat that owns no purchasing work.

### Rejected alternatives

- **Adopt `capnut_*` for Tryton modules too** — shorter, and it matches the
  migration package. Rejected: `capital_nutrition_base` and
  `capital_nutrition_sale` already exist, the second is referenced by
  `docs/specs/08_SALES.md`, and renaming a module that registers models and XML
  ids costs more than the characters saved.
- **Force `capital_nutrition_migration` for the toolkit too.** Rejected: it is
  not a Tryton module, nothing depends on its name, and operators type
  `capnut-migrate`.
- **Leave it open and let each domain choose.** Rejected: that is the current
  state, and it is why two chats would build incompatible modules.

## Verification

Wrong if a Tryton limit or a packaging tool turns out to reject names of this
length, or if the two-convention rule proves ambiguous for something that is
neither clearly a Tryton module nor clearly standalone.

Check: `ls modules/` matches `capital_nutrition_*` for every entry, and no
`tryton.cfg` `depends` line names a `capnut_*` module.
