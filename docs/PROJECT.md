# Project Overview

**NEO‑Guard** – Explainable Machine Learning System for Near‑Earth Object (NEO) Classification and Close‑Approach Analysis.

### Purpose
Provide a scientific, transparent platform for ingesting authoritative NASA/JPL NEO data, building explainable ML models, and exposing results via a documented API and interactive frontend.

### Problem Statement
Current NEO data is publicly available but lacks a unified, explainable ML pipeline that can classify objects, predict close approaches, and present results with scientific rigor.

### Scope
- Real data ingestion from NASA/JPL.
- Data validation, preprocessing, feature engineering.
- Explainable ML model training and evaluation.
- API for predictions and model metadata.
- Frontend explorer and dashboards.

### Non‑goals
- Direct asteroid impact prediction (requires separate validation).
- Real‑time mission‑critical alerts.

### Major Features (future)
- Data pipelines, ML baselines, model registry, SHAP explanations, Dockerised dev environment, CI/CD, etc.

### Technology Direction
Python, FastAPI, PostgreSQL, scikit‑learn, XGBoost, SHAP, React, Vite, Tailwind, Stitch, Docker.

### Scientific Limitations
All data and results must be sourced from authoritative NASA/JPL datasets. Synthetic data is only for testing and is clearly labelled.

### Team Responsibilities
- **Antigravity** – Repo scaffolding, documentation, handoff.
- **Claude Code** – Backend & ML implementation.
- **Human** – Approve major changes, provide credentials, final scientific review.

### Development Phases
See [DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md).
