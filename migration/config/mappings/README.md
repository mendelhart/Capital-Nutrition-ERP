# Mapping tables

One CSV per mapping. These files are the migration's decision record: if a
source value is not in here with `status=approved`, the load refuses to run.

## Columns

| Column | Meaning |
|---|---|
| `source_key` | The Odoo value being mapped (GL code, journal code, product code, partner id, ...). Never edited. |
| `source_label` | Human-readable name from Odoo, filled by `map stub`. For review only. |
| `source_context` | Extra context from Odoo (account type, tax scope, balance) to make review possible without opening Odoo. |
| `target_key` | The Tryton value. Required when `status=approved`. |
| `target_label` | Human-readable name of the target. Optional. |
| `status` | `pending` (default, blocks loads), `approved`, or `excluded`. |
| `reviewer` | Who approved it. **Required** for `accounts`, `journals`, `taxes`. |
| `reviewed_on` | Date of approval, `YYYY-MM-DD`. |
| `notes` | Required when `status=excluded`. Say why. |

## Rules enforced by `capnut-migrate map check`

* No row may stay `pending`.
* `approved` requires a non-empty `target_key`.
* Accounting tables (`accounts`, `journals`, `taxes`) require a `reviewer`.
* Two source accounts or journals mapping to the same target is flagged —
  collapsing accounts is allowed but must be a deliberate, noted decision.
* `excluded` requires a note.

## Workflow

```
capnut-migrate map stub     # adds pending rows for every new source value
                            # never overwrites a row you have already reviewed
capnut-migrate map check    # exits non-zero while anything is unresolved
```

`taxes` maps to whichever tax provider is chosen. `03_ACCOUNTING.md` lists the
provider and tax configuration as open questions — until they are answered,
leave tax rows `pending` rather than guessing.
