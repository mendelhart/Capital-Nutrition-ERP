# ADR-0001: Tryton 8.0.x and PostgreSQL 16 as the foundation

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** Capital Nutrition

## Context

Capital Nutrition is replacing Odoo with a company-owned ERP. The system will
be operated by roughly three users and must remain maintainable by its owner
rather than by a vendor. `docs/spec-package/00_MASTER_BUILD.md` fixes the framework and database.

## Decision

Build on **Tryton 8.0.x** and **PostgreSQL 16**.

The Tryton dependency is pinned to the 8.0 series (`trytond[postgresql]>=8.0,<8.1`).
Within the series we take patch and minor upgrades; moving to 8.1 or later is a
deliberate project with its own ADR, not a routine dependency bump.

PostgreSQL is the only supported backend. Tests run against it, and the suite
refuses to run on sqlite (`tests/test_backend.py`).

## Consequences

### Accepted costs

- Tryton's smaller ecosystem means fewer ready-made integrations than Odoo;
  Magento connectivity is ours to build.
- Pinning to 8.0 means we deliberately lag upstream features until we choose to
  move.
- Requiring PostgreSQL for tests makes the suite slower and needs a database in
  CI. This is the point: sqlite tolerates constraint and type behaviour that
  PostgreSQL does not, and a green sqlite run would tell us nothing about
  production.

### Rejected alternatives

- **Stay on Odoo.** Rejected: the migration away from it is the premise of the
  project.
- **Track Tryton latest.** Rejected: a three-person team cannot absorb an
  annual breaking upgrade cycle during a build.
- **sqlite for tests, PostgreSQL for production.** Rejected: it would let
  constraint violations and typing differences reach production untested, and
  database-enforced invariants are a core principle of this build.

## Verification

This decision is wrong if the 8.0 series stops receiving security fixes before
the ERP reaches production, or if a required capability turns out to exist only
in a later series. Review at each quality gate.
