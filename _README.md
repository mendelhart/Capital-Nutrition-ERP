# Odoo extraction queries

One file per dataset in `capnut_migration.sources.base.DATASETS`. They are plain
SQL on purpose: an accountant or a developer can read them, diff them, and edit
them against the real snapshot without touching Python.

## Rules

* Read only. Never write to the source.
* Always filter by `%(company_id)s` and `%(as_of)s`.
* Always select the source primary key as `source_id`.
* Column aliases must match the dataset's declared `columns`.

## Version tokens

Odoo's schema moved between versions. Instead of forking these files, the
extractor rewrites two tokens at run time based on what it probes in
`information_schema`:

| Token | Odoo <= 15 | Odoo >= 16 |
|---|---|---|
| `{{TR(x)}}` | `x` | `x ->> 'en_US'` (translatable char columns became jsonb) |

Run `capnut-migrate probe` before the first extraction. It reports the detected
Odoo version, which token variants it will use, and any table or column these
queries reference that does not exist in the snapshot.

## Known version differences these queries assume (Odoo 16/17)

* `account_account.account_type` is a varchar (`asset_receivable`,
  `liability_payable`, ...). On <= 14 it is `user_type_id` -> `account_account_type.internal_type`.
* Product cost lives in `ir_property` as `standard_price`.
* `account_move_line.amount_residual` carries the open amount.

If the snapshot is an older version, fix it here — not in the Python.
