"""Classification metrics for the (imbalanced) PHA task. All values are computed, never assumed."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml import config


def best_f1_threshold(y_true: np.ndarray, proba: np.ndarray) -> float:
    """Probability threshold that maximises F1. Fit on the validation split only."""
    if int(np.sum(y_true)) == 0:
        raise ValueError("Cannot tune a threshold: no positive examples in the split")
    precision, recall, thresholds = precision_recall_curve(y_true, proba)
    denom = precision[:-1] + recall[:-1]
    f1 = np.divide(2 * precision[:-1] * recall[:-1], denom, out=np.zeros_like(denom), where=denom > 0)
    return float(thresholds[int(np.argmax(f1))])


def compute_metrics(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict[str, Any]:
    y_true = np.asarray(y_true).astype(int)
    pred = (proba >= threshold).astype(int)
    n_pos = int(y_true.sum())
    metrics: dict[str, Any] = {
        "n": int(len(y_true)),
        "n_positive": n_pos,
        "prevalence": float(y_true.mean()),  # PR-AUC of a no-skill classifier
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
    }
    if 0 < n_pos < len(y_true):
        metrics["roc_auc"] = float(roc_auc_score(y_true, proba))
        metrics["pr_auc"] = float(average_precision_score(y_true, proba))
    else:  # AUCs are undefined with a single class; say so instead of inventing a value
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
        metrics["note"] = "ROC-AUC/PR-AUC undefined: only one class present"
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    metrics["confusion_matrix"] = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    return metrics


def curves(y_true: np.ndarray, proba: np.ndarray, max_points: int = 200) -> dict[str, Any]:
    """ROC and precision-recall curve points, thinned to at most ``max_points`` each."""
    fpr, tpr, _ = roc_curve(y_true, proba)
    precision, recall, _ = precision_recall_curve(y_true, proba)

    def thin(*arrays: np.ndarray) -> list[list[float]]:
        idx = np.unique(np.linspace(0, len(arrays[0]) - 1, min(max_points, len(arrays[0]))).astype(int))
        return [np.round(a[idx], 6).tolist() for a in arrays]

    fpr_t, tpr_t = thin(fpr, tpr)
    prec_t, rec_t = thin(precision, recall)
    return {"roc": {"fpr": fpr_t, "tpr": tpr_t}, "pr": {"precision": prec_t, "recall": rec_t}}


def bootstrap_ci(
    y_true: np.ndarray,
    proba: np.ndarray,
    n_resamples: int = 1000,
    seed: int = config.RANDOM_SEED,
) -> dict[str, Any]:
    """95% percentile bootstrap intervals for ROC-AUC and PR-AUC (test sets can be small)."""
    y_true = np.asarray(y_true).astype(int)
    rng = np.random.default_rng(seed)
    n = len(y_true)
    roc, pr = [], []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, n)
        pos = y_true[idx].sum()
        if pos == 0 or pos == n:
            continue
        roc.append(roc_auc_score(y_true[idx], proba[idx]))
        pr.append(average_precision_score(y_true[idx], proba[idx]))

    def interval(values: list[float]) -> list[float]:
        return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]

    return {"method": "percentile bootstrap, 95%", "n_resamples": len(roc), "seed": seed,
            "roc_auc": interval(roc), "pr_auc": interval(pr)}
