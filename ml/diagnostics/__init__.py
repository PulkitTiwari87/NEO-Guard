"""Diagnostic (non-production) scientific analyses: distribution shift, subgroup evaluation,
calibration, and the definition-reconstruction comparison. See docs/EXPERIMENTS.md.

Nothing here is registered by ``python -m app.cli sync-models`` (which only scans
``ml.config.ARTIFACTS_DIR``) and nothing here is loaded by ``ml.inference`` for the live API.
"""
