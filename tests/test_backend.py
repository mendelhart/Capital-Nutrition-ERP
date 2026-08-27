# This file is part of the Capital Nutrition ERP.
"""Guard on the test harness itself.

MASTER_BUILD requires tests to run against PostgreSQL. Tryton falls back to
sqlite when no database URI is configured, and sqlite silently tolerates
things PostgreSQL does not (deferred constraints, type coercion). A green
suite on sqlite would prove nothing about production, so the suite refuses to
run on it.
"""

from trytond import backend


def test_backend_is_postgresql():
    assert backend.name == 'postgresql', (
        "Tests must run against PostgreSQL. Set TRYTOND_DATABASE_URI, "
        "e.g. postgresql://tryton:tryton@127.0.0.1:5432/")
