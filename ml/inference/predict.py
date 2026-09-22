"""Inference: load an artifact once, then predict (and explain) single records.

Predictions are real model outputs: ``probability`` is ``predict_proba`` of the positive class
and ``prediction`` applies the artifact's validation-tuned threshold.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from ml import artifacts, config
from ml.explainability.explain import Explainer

log = logging.getLogger(__name__)


class IncompatibleArtifact(RuntimeError):
    """The artifact was trained with a different feature schema than this code expects."""


@dataclass
class LoadedModel:
    directory: Path
    metadata: dict[str, Any]
    pipeline: Any
    _explainer: Explainer | None = field(default=None, repr=False)

    @property
    def version(self) -> str:
        return self.metadata["model_version"]

    def explainer(self) -> Explainer | None:
        """Lazily built SHAP explainer; None if the explainability artifacts are missing."""
        if self._explainer is None:
            background = None
            shap_file = self.directory / artifacts.SHAP_FILE
            if shap_file.exists():
                background = json.loads(shap_file.read_text(encoding="utf-8"))["background_mean"]
            try:
                self._explainer = Explainer(self.pipeline, background)
            except ValueError:
                log.warning("No SHAP background for %s; run python -m ml.explainability", self.version)
                return None
        return self._explainer


def load_model(directory: Path) -> LoadedModel:
    metadata = artifacts.load_metadata(directory)
    if (metadata["feature_version"] != config.FEATURE_VERSION
            or metadata["raw_features"] != config.RAW_FEATURES):
        raise IncompatibleArtifact(
            f"{metadata['model_version']} uses feature_version={metadata['feature_version']}; "
            f"code expects {config.FEATURE_VERSION}")
    log.info("Loading model %s", metadata["model_version"])
    return LoadedModel(directory, metadata, artifacts.load_pipeline(directory))


def predict(model: LoadedModel, features: dict[str, float], explain: bool = True) -> dict[str, Any]:
    missing = [c for c in config.RAW_FEATURES if c not in features]
    if missing:
        raise ValueError(f"missing features: {missing}")
    raw = pd.DataFrame([{c: float(features[c]) for c in config.RAW_FEATURES}])
    probability = float(model.pipeline.predict_proba(raw)[0, 1])
    threshold = float(model.metadata["threshold"])
    result: dict[str, Any] = {
        "prediction": int(probability >= threshold),
        "probability": probability,
        "threshold": threshold,
        "model_version": model.version,
        "explanation": None,
    }
    if explain:
        explainer = model.explainer()
        result["explanation"] = explainer.explain(raw) if explainer else None
    return result
