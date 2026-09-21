# ML Workflow

> **Status: PLANNED — NOT IMPLEMENTED**

## Process

```
Data
  |
  v
Split (train / validation / test)
  |
  v
Preprocessing (inside each fold)
  |
  v
Baseline models
  |
  v
Model experiments
  |
  v
Evaluation
  |
  v
Explainability (SHAP, feature importance)
  |
  v
Model selection
  |
  v
Model artifact (versioned)
  |
  v
Inference API
```

## Baseline Models

| Model | Library | Purpose |
|-------|---------|---------|
| Logistic Regression | scikit-learn | Simple interpretable baseline |
| Random Forest | scikit-learn | Non-linear tree-based baseline |

## Potential Advanced Models

| Model | Library | Purpose |
|-------|---------|---------|
| XGBoost | xgboost | Gradient boosting |
| LightGBM | lightgbm | Efficient gradient boosting |

Neural networks are optional and must be justified experimentally. Do NOT prescribe a model as the winner beforehand.

## Evaluation Metrics

The ML system must report, where applicable:

- Accuracy
- Precision
- Recall
- F1 score
- ROC-AUC
- PR-AUC
- Confusion matrix

The exact metrics used should depend on the target variable and class distribution. Do NOT fabricate expected scores.

## Experiment Tracking

Every experiment must be logged per the template in [EXPERIMENTS.md](EXPERIMENTS.md).

## Model Artifacts

Trained models must be versioned and stored with:
- Model file (pickle / joblib / ONNX)
- Training configuration
- Feature list
- Preprocessing pipeline
- Evaluation metrics
- Timestamp
