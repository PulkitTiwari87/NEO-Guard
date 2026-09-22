# Makefile — NEO-Guard backend + ML
# Windows without `make`: run the underlying commands shown in each recipe.
PY ?= python

.PHONY: help setup test lint format migrate run pipeline

help:
	@echo "make setup     - install dependencies (+ editable ml/app packages)"
	@echo "make test      - run the test suite"
	@echo "make lint      - ruff check"
	@echo "make format    - ruff format"
	@echo "make migrate   - alembic upgrade head (needs DATABASE_URL)"
	@echo "make run       - start the API on http://localhost:8000"
	@echo "make pipeline  - ingest -> validate -> preprocess -> train -> evaluate -> explain"

setup:
	$(PY) -m pip install -r backend/requirements-dev.txt
	$(PY) -m pip install -e . --no-deps

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check ml backend tests

format:
	$(PY) -m ruff format ml backend tests

migrate:
	alembic -c backend/alembic.ini upgrade head

run:
	uvicorn app.main:app --reload

pipeline:
	$(PY) -m ml.ingestion
	$(PY) -m ml.validation
	$(PY) -m ml.preprocessing
	$(PY) -m ml.training
	$(PY) -m ml.evaluation
	$(PY) -m ml.explainability
