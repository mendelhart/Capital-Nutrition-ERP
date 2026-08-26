# Handoff — MIG-001 → MIG-002

## What a new chat needs to know

The migration toolkit lives in `migration/` and runs end to end today against
fixture data. It has never seen real Odoo data.

## First actions for whoever picks this up

1. Restore a `pg_dump` of Odoo to a local or staging PostgreSQL. Do not point the
   toolkit at production.
2. `cp migration/config/migration.example.toml migration/config/migration.toml`,
   set `[source] dsn` and `company_id`, set `[run] cutover_date`.
3. `capnut-migrate probe`. It prints the Odoo version, the companies, and
   warnings about queries that will not work on that version. Expect edits in
   `migration/sql/extract/*.sql` — the queries target Odoo 16/17.
4. `capnut-migrate extract` then `capnut-migrate profile`. Read the `flags`
   section before anything else: an out-of-balance source or unexpected
   currencies invalidate everything downstream.
5. `capnut-migrate map stub`, then hand `config/mappings/accounts.csv`,
   `journals.csv` and `taxes.csv` to the accountant. Nothing loads until those
   are approved with a reviewer name.

## Traps

* The extraction SQL is written for Odoo 16/17. Odoo ≤ 14 uses
  `user_type_id` → `account_account_type.internal_type` instead of
  `account_account.account_type`; `probe` says so explicitly.
* Product cost comes from `ir_property`, not from the product table.
* `amount_residual` sign conventions differ between AR and AP; the AP query
  negates so that "positive means we owe".
* The `tryton` load target is a stub. Rehearsals run against the `jsonl` target;
  the documents and reconciliation are identical, only the destination differs.

## Do not

* Do not add a fallback that maps an unknown account to itself.
* Do not migrate opening inventory from Odoo quants.
* Do not commit `migration/config/migration.toml`.
