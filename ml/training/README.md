# ml/training/

**IMPLEMENTED.**

```bash
python -m ml.training [--algorithms logistic_regression random_forest xgboost] [--class-weight none|balanced|both]
```

Fits `Pipeline[build_features → (scaler) → classifier]` on the **train** split only, picks the decision
threshold that maximises F1 on **validation**, and writes an immutable versioned artifact to
`ml/artifacts/<name>/v<N>/` (`model.joblib`, `metadata.json`). Status is always `experimental`. The test split
is not touched here. Fixed parameters, seed 42, no hyper-parameter search — see
[`ML_WORKFLOW.md`](../../docs/ML_WORKFLOW.md).
