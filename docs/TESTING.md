# Testing Strategy

> **Status: PLANNED — NOT IMPLEMENTED**

## Unit Tests

Target areas:
- Data parsing and schema validation
- Validation functions
- Feature engineering transformations
- Model inference (prediction shape, type)
- API service functions

Location: `tests/unit/`

## Integration Tests

Target flows:
- Ingestion to database
- Backend to database (CRUD operations)
- Backend to ML model (prediction pipeline)
- Frontend to backend API (contract compliance)

Location: `tests/integration/`

## ML Tests

Target areas:
- Schema validation (input/output shapes)
- Feature consistency (same features at train and predict time)
- Model loading and deserialization
- Prediction shape and type
- Leakage detection tests (verify no train/test overlap)

Location: `tests/ml/`

## End-to-End Tests (Future)

```
User
  |
  v
Frontend
  |
  v
API
  |
  v
Database
  |
  v
ML Model
  |
  v
Response
```

E2E tests will validate the full flow from user interaction to response.

## Synthetic Data for Testing

- Synthetic/mock data is allowed in tests.
- It must be clearly labelled as `SYNTHETIC / TEST DATA`.
- It must never be represented as NASA data.

## Test Execution

```bash
# Future commands (not yet functional)
make test           # Run all tests
pytest tests/unit/  # Run unit tests only
pytest tests/ml/    # Run ML tests only
```
