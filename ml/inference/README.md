# ml/inference/

**IMPLEMENTED.** `predict.py`: `load_model(dir)` (refuses artifacts with a different feature version) and
`predict(model, features, explain=True)` returning `{prediction, probability, threshold, model_version,
explanation}`. Outputs are real model results (`predict_proba` + the artifact's threshold). Used by the
backend's `prediction_service`. Artifacts are pickles: load only from a trusted directory.
