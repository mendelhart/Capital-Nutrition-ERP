# Migration toolkit — Odoo → Tryton

Implements `docs/specs/13_MIGRATION.md`. Task `MIG-001`.

    extract → stage → map → build → load → reconcile

Every stage writes an artifact, every load is idempotent, and reconciliation is
a gate with an exit code rather than a report someone has to remember to read.

## Install

```bash
cd migration
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[postgres,dev]"
cp config/migration.example.toml config/migration.toml
# edit config/migration.toml — it is gitignored, credentials stay on your machine
```

Python 3.11+. Nothing but `psycopg` is required, and only for the two commands
that talk to a database.

## Commands

| Command | What it does |
|---|---|
| `capnut-migrate probe` | Inspects the source snapshot: Odoo version, companies, which SQL variants apply, warnings |
| `capnut-migrate extract` | Source → `var/<label>/extract/*.jsonl` + `manifest.json` |
| `capnut-migrate stage` | JSONL → PostgreSQL `stg` schema so the source is queryable in SQL (optional) |
| `capnut-migrate profile` | Row counts, money sums, nulls, distinct values, and flags |
| `capnut-migrate map stub` | Adds a `pending` row to the mapping CSVs for every unmapped source value |
| `capnut-migrate map check` | Fails while anything is unreviewed, unapproved, or ambiguous |
| `capnut-migrate build` | Transform only — reports what would be loaded and what is blocking |
| `capnut-migrate load` | Transform + load, idempotent by `migration_ref` |
| `capnut-migrate reconcile` | Runs the checks, writes `var/<label>/reports/reconciliation.md` |
| `capnut-migrate rehearse` | The whole pipeline, with a written record |
| `capnut-migrate history` | Every rehearsal so far (the spec wants at least three) |

Exit codes: `0` fine, `1` a stage failed, `2` reconciliation blocks cutover.
CI and the cutover runbook can both branch on those.

## A rehearsal

```bash
capnut-migrate probe                 # first time, and after any snapshot refresh
capnut-migrate extract
capnut-migrate profile | less
capnut-migrate map stub              # then review the CSVs in config/mappings/
capnut-migrate rehearse
```

`rehearse` stops at the first failing stage. Unreviewed mappings mean nothing
loads at all — that is deliberate.

## How the pieces fit

```
sql/extract/*.sql          reviewable SQL, one file per dataset
sources/                   SourceAdapter: odoo_sql (works), odoo_rpc + csv (stubs)
extract.py                 → var/<label>/extract/*.jsonl  ← the snapshot
staging.py / stage_db.py   → PostgreSQL stg schema (generic table + typed views)
config/mappings/*.csv      the decision record; nothing loads without approval
load/documents.py          pure transforms → load documents
load/targets.py            jsonl target (works), tryton target (stub)
reconcile/                 the checks, and the report that gates cutover
```

### Why JSONL in the middle

The extracted JSONL *is* the controlled snapshot. Everything downstream reads
it and never the source, so a rehearsal can be repeated exactly, two rehearsals
can be diffed, and any reconciliation difference can be traced to a specific
extracted row.

### Idempotency

Every document carries `_ref = "<system>:<model>:<source_id>"` and a content
hash. Loading the same document twice reports `unchanged`; loading a changed one
reports `updated`. Nothing duplicates, so reruns are free.

### The AR/AP decision

The opening journal entry carries every account **except** the AR and AP control
accounts. Those balances are created by the open-item loads, invoice by invoice.
Loading both would double the receivable and payable. `trial_balance` proves the
two halves add back up to the source GL.

## Reconciliation checks

| Check | Blocks cutover | Compares |
|---|---|---|
| `trial_balance` | yes | Source GL balance per mapped account vs opening entry + AR/AP open items |
| `ar_aging` | yes | Source residuals vs loaded open AR, by aging bucket |
| `ap_aging` | yes | Source residuals vs loaded open AP, by aging bucket |
| `open_pos` | yes | Open PO value per order |
| `open_po_count` | yes | Number of approved open POs |
| `inventory_value` | no | Source valuation vs approved physical count — **skipped until a count is loaded** |
| `order_counts` | no | Sales order count by month |
| `sales_totals` | no | Sales total by month |
| `payments` | no | Payments and refunds by month |

Inventory is intentionally never allowed to pass on Odoo data alone: opening
operational inventory comes from the physical count at cutover, so the check
stays `SKIPPED` until count documents exist.

## What is not built yet

| Gap | Why | Unblocked by |
|---|---|---|
| `tryton` load target | The Tryton modules do not exist yet | ACC-### / the foundation build |
| `odoo_rpc` source | Source access decision still open | Choosing live RPC over a snapshot |
| `csv` source | Same, plus it needs an export manifest to be trustworthy | Same |
| Physical count import | Count process not defined | INV-### / the cutover runbook |
| Historical sales/payment migration | Not in the load scope yet | A decision on how much history moves |

Each is a declared stub that raises with a clear message, not a silent
half-implementation.

## Tests

```bash
python -m pytest
```

126 tests, no database required. They cover the money arithmetic, the mapping
rules, the accounting decisions in the transforms, load idempotency, every
reconciliation check, and the CLI exit codes. `test_extraction_sql.py` also
checks that each `.sql` file's aliases still match the dataset catalogue, is
scoped to a company, respects the as-of date, and contains no write statements.
