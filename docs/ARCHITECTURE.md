# Architecture

> **Status: PLANNED — Nothing is implemented yet.**

## System Architecture

```
NASA/JPL Data Sources
        |
        v
  Data Ingestion          [PLANNED]
        |
        v
  Raw Data (data/raw/)
        |
        v
  Validation              [PLANNED]
        |
        v
  Preprocessing           [PLANNED]
        |
        v
  Feature Engineering      [PLANNED]
        |
        v
  ML Training             [PLANNED]
        |
        v
  Evaluation              [PLANNED]
        |
        v
  Model Registry          [PLANNED]
        |
        v
  Inference API (FastAPI)  [PLANNED]
        |
        v
  Backend                 [PLANNED]
        |
        v
  Frontend (React)        [PLANNED]
```

## Components

| Component | Responsibility | Status |
|-----------|---------------|--------|
| Data Ingestion | Fetch NEO data from NASA/JPL APIs | PLANNED |
| Validation | Schema & quality checks on raw data | PLANNED |
| Preprocessing | Cleaning, normalisation, imputation | PLANNED |
| Feature Engineering | Derive ML-ready features with leakage prevention | PLANNED |
| ML Training | Train baseline and advanced models | PLANNED |
| Evaluation | Metrics, confusion matrix, fairness checks | PLANNED |
| Model Registry | Version and store trained model artifacts | PLANNED |
| Explainability | SHAP values, feature importance | PLANNED |
| Inference API | FastAPI service for predictions | PLANNED |
| Backend | Orchestration, database access, API routing | PLANNED |
| Frontend | React dashboard, explorer, prediction UI | PLANNED |
| Database | PostgreSQL for NEO records, predictions, experiments | PLANNED |

## Data Flow

```
NASA/JPL --> data/raw/ --> data/interim/ --> data/processed/ --> ML pipeline
```

Raw data is immutable. All transformations produce new files in downstream directories.

## ML Flow

```
Processed data --> Train/Val/Test split --> Model training --> Evaluation --> Model artifact --> Inference API
```

## API Flow

```
Frontend --> Backend API --> Database
                         --> ML Inference
                         --> Model metadata
```

## Database Flow

```
Ingestion --> neo_objects, close_approaches
ML        --> models, experiments, predictions
```

## Deployment Architecture (PLANNED)

| Service | Target | Status |
|---------|--------|--------|
| Frontend | Vercel | PLANNED |
| Backend | Render | PLANNED |
| Database | PostgreSQL provider (TBD) | PLANNED |

## Development Architecture

```
Local dev: docker-compose (backend + db + frontend)
CI: GitHub Actions
```
