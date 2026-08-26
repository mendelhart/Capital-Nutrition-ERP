# ADR-0003: Modules in-repo, symlinked into trytond for development

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** Capital Nutrition

## Context

Tryton discovers modules under `trytond/modules` in the installed package, or
via the `trytond.modules` entry-point group. Capital Nutrition's modules must
live in this repository — the repository is the project's memory — while still
being discoverable by a running `trytond`.

## Decision

Modules live in `modules/<name>/` in this repository. `make link`
(`scripts/link_modules.py`) symlinks each into the virtualenv's `trytond/modules/`.

Registration uses the Tryton 8.0 `[register]` section of `tryton.cfg` rather
than `Pool.register()` calls in `__init__.py`.

## Consequences

### Accepted costs

- A fresh virtualenv needs `make link` before anything works. It is in the
  README and in the `test` target's prerequisites, so it is hard to forget.
- Symlinks are awkward on Windows without developer mode. Development is on
  Linux; if that changes, replace the symlink step with editable installs
  declaring `[project.entry-points."trytond.modules"]`.

### Rejected alternatives

- **Editable pip installs per module.** Rejected for now: it needs a
  `pyproject.toml` per module and an editable-install hook into a package
  namespace `trytond` already owns, which is more machinery than three
  developers need. It stays the fallback if symlinks become a problem.
- **Develop directly inside `.venv/lib/.../trytond/modules/`.** Rejected: the
  code would live outside version control.

## Verification

Wrong if deployment ever needs a packaging step the symlink layout cannot
produce. Revisit when the production deployment method is decided (Gate 3).
