# Data Pipeline

> **Status: PLANNED — NOT IMPLEMENTED**

## Pipeline Stages

```
SOURCE (NASA/JPL)
      |
      v
INGESTION (ml/ingestion/)
      |
      v
RAW (data/raw/)
      |
      v
VALIDATION (ml/validation/)
      |
      v
INTERIM (data/interim/)
      |
      v
CLEANING / PREPROCESSING (ml/preprocessing/)
      |
      v
FEATURE ENGINEERING (ml/features/)
      |
      v
PROCESSED (data/processed/)
      |
      v
TRAINING (ml/training/)
```

## Immutability Rule

> **RAW DATA MUST NEVER BE MODIFIED.**

- Files in `data/raw/` are write-once.
- All transformations produce new files in `data/interim/` or `data/processed/`.
- If raw data needs to be re-fetched, the old files should be archived or versioned, not overwritten.

## Directory Mapping

| Stage | Directory | Description |
|-------|-----------|-------------|
| Raw | `data/raw/` | Original data as received from source |
| Interim | `data/interim/` | Validated and partially cleaned data |
| Processed | `data/processed/` | ML-ready features and labels |
| External | `data/external/` | Third-party reference data (if any) |

## Provenance

Every dataset file should be accompanied by metadata recording:
- Source URL
- Retrieval timestamp
- Record count
- Schema version
- Any filters applied during retrieval
