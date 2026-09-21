# NEO‑Guard

**Project:** Explainable Machine Learning System for Near‑Earth Object (NEO) Classification and Close‑Approach Analysis

## Status

**FOUNDATION PHASE** – Repository scaffold and documentation only. No code implementation yet.

## Architecture

```
NASA/JPL → Data Ingestion → Validation → Preprocessing → Feature Engineering → ML Training → Evaluation → Model Registry → Inference API → Backend → Frontend
```
*(All components are **PLANNED** and not implemented.)*

## Planned Features
- Real NEO data ingestion from NASA/JPL sources
- Data validation & preprocessing pipelines
- Feature engineering with strict leakage prevention
- Baseline ML models (Logistic Regression, Random Forest) and advanced models (XGBoost, LightGBM)
- Explainable AI (SHAP, etc.)
- FastAPI inference service
- PostgreSQL persistence
- React + Vite frontend with Apple‑inspired design
- Dockerised development environment
- CI/CD with GitHub Actions

## Technology Stack (planned)
```
Python, FastAPI, scikit‑learn, XGBoost, SHAP, PostgreSQL
React, Vite, Tailwind CSS, Stitch (design system)
Docker, docker‑compose, GitHub Actions
```
*No packages are installed yet; these are future choices.*

## Scientific Integrity
The project adheres to strict scientific integrity principles. See [SCIENTIFIC_INTEGRITY.md](docs/SCIENTIFIC_INTEGRITY.md).

## Development Workflow
Implementation proceeds in controlled phases (see [DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md)).

## Data
Authoritative NASA/JPL sources will be used wherever possible. See [DATA_SOURCE.md](docs/DATA_SOURCE.md) for the policy.

---
*This README is a placeholder; detailed documentation resides in the `docs/` directory.*
