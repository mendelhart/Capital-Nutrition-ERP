# Capital Nutrition ERP — developer entry points.
# Every target assumes the virtualenv at .venv.

PY := .venv/bin/python
PIP := .venv/bin/pip
MODULES := capital_nutrition_base

DB_URI ?= postgresql://postgres@127.0.0.1:5432/
TEST_DB ?= test_capital_nutrition

.PHONY: help venv install link unlink test migration-test lint db-start db-stop clean

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

venv: ## create the virtualenv
	python3 -m venv .venv
	$(PIP) install --upgrade pip setuptools wheel

install: venv ## install runtime and dev dependencies
	$(PIP) install -r requirements-dev.txt

link: ## symlink repository modules into trytond/modules
	$(PY) scripts/link_modules.py

unlink: ## remove the module symlinks
	$(PY) scripts/link_modules.py --unlink

db-start: ## start local PostgreSQL 16
	./scripts/dev_postgres.sh start

db-stop: ## stop local PostgreSQL 16
	./scripts/dev_postgres.sh stop

test: link ## run module tests against PostgreSQL (never sqlite)
	TRYTOND_DATABASE_URI=$(DB_URI) DB_NAME=$(TEST_DB) \
		$(PY) -m pytest tests $(foreach m,$(MODULES),modules/$(m)/tests) -v

migration-test: ## run the migration toolkit tests (no database needed)
	cd migration && ../$(PY) -m pytest -q

lint: ## static checks
	.venv/bin/ruff check modules scripts tests migration/src migration/tests

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
