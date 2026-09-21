# CLAUDE.md — Instructions for Claude Code

You are implementing the backend and ML phase of NEO-Guard.

## Before Modifying Anything

1. Read `README.md`
2. Read `docs/PROJECT.md`
3. Read `docs/ARCHITECTURE.md`
4. Read `docs/AGENT_WORKFLOW.md`
5. Read `docs/DATA_SOURCE.md`
6. Read `docs/DATA_LEAKAGE.md`
7. Read `docs/FEATURE_POLICY.md`
8. Read `docs/ML_WORKFLOW.md`
9. Read `docs/API_CONTRACT.md`
10. Read `docs/DATABASE_SCHEMA.md`
11. Read `docs/SCIENTIFIC_INTEGRITY.md`

## Rules

- Do not fabricate data or metrics.
- Do not implement frontend.
- Do not change API contracts without documenting the change.
- Do not silently change scientific assumptions.
- Run tests before completion.
- Update `docs/HANDOFF.md` when finished.

## Scientific Ambiguity

> If a requirement is scientifically ambiguous, stop and document the ambiguity instead of inventing an assumption.

## Code Quality

- DRY, KISS, YAGNI
- Modular architecture
- Minimal dependencies
- Type safety where practical
- Meaningful names
- Small functions
- Explicit error handling
- No unnecessary abstraction
- Do not introduce dependencies without justification

## Development Philosophy

> Understand the problem. Build the smallest correct thing. Test. Improve.

Avoid premature abstraction, unnecessary frameworks, speculative features, excessive dependencies, and over-engineering.

## Synthetic Data

Synthetic data is allowed in tests only. It must be labelled `SYNTHETIC / TEST DATA` and never represented as NASA data.

## Deliverables

1. Working data ingestion from NASA/JPL
2. Validation, preprocessing, feature engineering pipelines
3. Trained baseline models with real metrics
4. Evaluation results logged in `docs/EXPERIMENTS.md`
5. SHAP explanations
6. FastAPI inference API matching `docs/API_CONTRACT.md`
7. PostgreSQL integration matching `docs/DATABASE_SCHEMA.md`
8. Unit, integration, and ML tests
9. Updated `docs/HANDOFF.md`
