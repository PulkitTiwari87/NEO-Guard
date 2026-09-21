# Data Leakage Prevention Policy

## Purpose

Prevent any form of data leakage that would produce inflated or unreliable model evaluation metrics.

---

## Leakage Types

### 1. Target Leakage
A feature directly encodes or is derived from the target variable.

### 2. Train/Test Contamination
Training data overlaps with test data, or preprocessing uses information from the test set.

### 3. Temporal Leakage
Future information is used to predict past events. If the dataset has a time dimension, splits must respect chronological order.

### 4. Duplicate Leakage
Identical or near-identical records appear in both training and test sets.

### 5. Preprocessing Leakage
Statistics (mean, std, min, max) are computed on the full dataset including the test set before splitting.

### 6. Feature Leakage
A feature is only available after the prediction target is known (e.g., post-outcome measurement).

### 7. Derived-Target Leakage
A feature is mathematically derived from the target (e.g., a binary flag that is equivalent to the label).

### 8. Post-Outcome Information Leakage
Information that is recorded after the event being predicted is used as input.

---

## Prevention Rules

1. **Split before preprocessing.** Never fit scalers, encoders, or imputers on the full dataset.
2. **Temporal splits when applicable.** If data has a time dimension, use time-based splits.
3. **Deduplicate before splitting.** Remove exact and near-duplicate records before creating train/test sets.
4. **Audit every feature.** Use the feature-audit template below before adding any feature.
5. **Validate pipeline order.** Preprocessing must happen inside cross-validation folds, not before.

---

## Feature-Audit Template

```
Feature:
Source:
Type:
Available before prediction:
Contains target information:
Temporal risk:
Allowed:
Reason:
```

Every feature used in training must have a completed audit record in the feature registry before it is accepted.
