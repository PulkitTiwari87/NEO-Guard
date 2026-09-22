# Tests — ML

`test_leakage.py` (audit completeness, target-defining features excluded, split has no overlap, leakage
canary), `test_training.py` (train-only fitting, validation-tuned threshold, reproducibility, valid
probabilities), `test_predict_explain.py` (inference contract, SHAP additivity, train/serve parity),
`test_evaluate.py` (test metrics, idempotent experiment log). Models here are trained on **SYNTHETIC /
TEST DATA** in temp directories — never the real `ml/artifacts/`. Run: `pytest tests/ml`.
