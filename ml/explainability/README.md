# ml/explainability/

**IMPLEMENTED.** SHAP explanations.

```bash
python -m ml.explainability [--model-version xgboost-v1 ...]   # writes shap_global.json per artifact
```

`explain.py`: `Explainer` (Tree explainer for RF/XGBoost, Linear explainer for LR) for local per-prediction
contributions, plus global mean-|SHAP| importance on a validation sample. Units: log-odds (LR, XGBoost) or
probability (RF); contributions add up to the model output (tested). SHAP describes model behaviour, not
causes.
