# Database Schema

> **Status: PLANNED — NOT IMPLEMENTED**
>
> Column details marked `TO BE FINALIZED AFTER DATA INGESTION` depend on the real dataset schema.

---

## Planned Tables

### `neo_objects`

Primary table for Near-Earth Object records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| neo_reference_id | VARCHAR | No | Unique NEO identifier from source |
| name | VARCHAR | Yes | Object name |
| designation | VARCHAR | Yes | Official designation |
| is_potentially_hazardous | BOOLEAN | Yes | PHA flag |
| absolute_magnitude_h | FLOAT | Yes | Absolute magnitude (H) |
| estimated_diameter_km_min | FLOAT | Yes | Min estimated diameter |
| estimated_diameter_km_max | FLOAT | Yes | Max estimated diameter |
| ... | ... | ... | TO BE FINALIZED AFTER DATA INGESTION |

### `close_approaches`

Close-approach records for NEOs.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| neo_id | FK -> neo_objects | No | Foreign key to parent NEO |
| approach_date | DATE / TIMESTAMP | Yes | Date of close approach |
| relative_velocity_km_s | FLOAT | Yes | Relative velocity |
| miss_distance_km | FLOAT | Yes | Miss distance |
| orbiting_body | VARCHAR | Yes | Body being orbited |
| ... | ... | ... | TO BE FINALIZED AFTER DATA INGESTION |

### `predictions`

ML prediction records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| neo_id | FK -> neo_objects | No | Foreign key to NEO |
| model_version | VARCHAR | No | Model version used |
| prediction | VARCHAR | No | Predicted class |
| probability | FLOAT | Yes | Prediction probability |
| explanation | JSONB | Yes | SHAP / explanation data |
| created_at | TIMESTAMP | No | Prediction timestamp |

### `models`

Model registry.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| version | VARCHAR | No | Unique version string |
| name | VARCHAR | Yes | Model name |
| parameters | JSONB | Yes | Hyperparameters |
| metrics | JSONB | Yes | Evaluation metrics |
| features | JSONB | Yes | Feature list |
| created_at | TIMESTAMP | No | Training timestamp |

### `experiments`

Experiment tracking records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| experiment_id | VARCHAR | No | Unique experiment identifier |
| model_version | VARCHAR | Yes | Associated model version |
| dataset_version | VARCHAR | Yes | Dataset version used |
| config | JSONB | Yes | Full experiment configuration |
| metrics | JSONB | Yes | Result metrics |
| created_at | TIMESTAMP | No | Experiment timestamp |

### `data_sources`

Provenance tracking for ingested datasets.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID / SERIAL | No | Primary key |
| source_name | VARCHAR | No | Source identifier |
| url | VARCHAR | Yes | Source URL |
| retrieved_at | TIMESTAMP | No | Retrieval timestamp |
| record_count | INTEGER | Yes | Number of records |
| schema_version | VARCHAR | Yes | Schema version |
| checksum | VARCHAR | Yes | File checksum |

---

## Relationships

```
neo_objects  1 --- * close_approaches
neo_objects  1 --- * predictions
models       1 --- * predictions
models       1 --- * experiments
data_sources (standalone provenance table)
```
