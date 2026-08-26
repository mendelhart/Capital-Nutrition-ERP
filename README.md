# Capital Nutrition ERP

Company-owned ERP for Capital Nutrition on **Tryton 8.0.x** and **PostgreSQL 16**.

Scope and discipline are set by
[`docs/spec-package/00_MASTER_BUILD.md`](docs/spec-package/00_MASTER_BUILD.md).
This README covers only how to run the code — read `CLAUDE.md` before changing
anything.

> **Ship APL is out of scope for this build.** Do not design, implement, or
> create dependencies for it.

## Layout

```
modules/     Capital Nutrition Tryton modules, one directory each
scripts/     developer scripts
etc/         trytond configuration template (the real config is git-ignored)
tests/       harness guards and cross-domain scenarios
docs/        the repository's memory — specifications, ADRs, tasks, status
```

## Getting started

Python 3.11+ and either Docker or a local PostgreSQL 16.

```bash
make install                    # create .venv and install dependencies
docker compose up -d postgres   # or: make db-start
make link                       # symlink modules/ into trytond/modules
make test                       # run the suite against PostgreSQL
make lint
```

`make link` symlinks each directory under `modules/` into the virtualenv's
`trytond/modules/`, which is how Tryton discovers them (ADR-0003). Re-run it
after adding a module; not after editing one.

## Running a development server

```bash
cp etc/trytond.conf.template etc/trytond.conf   # then edit; it is git-ignored
.venv/bin/trytond-admin -c etc/trytond.conf -d capital_nutrition --all
.venv/bin/trytond -c etc/trytond.conf
```

## Tests

Tests run against **real PostgreSQL**, never sqlite. `tests/test_backend.py`
fails the suite on any other backend — sqlite tolerates constraint and typing
behaviour PostgreSQL does not, so a green sqlite run would prove nothing about
production.

```bash
TRYTOND_DATABASE_URI=postgresql://tryton:tryton@127.0.0.1:5432/ \
DB_NAME=test_capital_nutrition \
  .venv/bin/python -m pytest tests modules/capital_nutrition_base/tests -v
```

Each module's suite subclasses Tryton's `ModuleTestCase`, which also validates
views, model access, selection fields, field dependencies and menu actions.

## Secrets

No production credentials belong in this repository. `etc/trytond.conf` and
`.env` are git-ignored; the committed shapes are `etc/trytond.conf.template`
and `.env.example`.
