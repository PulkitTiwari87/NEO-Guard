# ml/evaluation/

**IMPLEMENTED.**

```bash
python -m ml.evaluation [--model-version xgboost-v1 ...]     # default: every artifact
```

* `metrics.py` — accuracy, precision, recall, F1, ROC-AUC, PR-AUC (reported as `null` + note when undefined),
  confusion matrix, ROC/PR curve points, bootstrap 95% CIs, F1-optimal threshold.
* `evaluate.py` — held-out **test** evaluation using each model's validation-tuned threshold; writes
  `evaluation.json`, updates `metadata.json`, and appends one entry per experiment to
  [`docs/EXPERIMENTS.md`](../../docs/EXPERIMENTS.md) (idempotent). Refuses a model trained on a different dataset version.
