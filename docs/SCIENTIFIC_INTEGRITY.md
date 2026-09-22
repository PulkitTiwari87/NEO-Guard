# Scientific Integrity

## Mandatory Principles

1. **No fabricated NASA data.** All data must come from verifiable sources.
2. **No fabricated ML results.** Metrics must come from actual experiments.
3. **No fabricated citations.** References must be real and verifiable.
4. **No fabricated benchmark results.** Comparisons must use real baselines.
5. **Synthetic data must be labelled.** Any test/mock data must be marked `SYNTHETIC / TEST DATA`.
6. **Every dataset must have provenance.** Source, retrieval date, and version must be recorded.
7. **Every model must have a version.** No unversioned models in production.
8. **Every reported metric must come from an actual experiment.** See [EXPERIMENTS.md](EXPERIMENTS.md).
9. **Predictions must identify the model version.** Users must know which model produced a prediction.
10. **Limitations must be explicitly documented.** See [LIMITATIONS.md](LIMITATIONS.md).
11. **Correlations are not causation.** Model correlations must not automatically be presented as causal scientific findings.
12. **No overstated capability.** The system must not overstate its predictive capability.

## Scope Disclaimer

> This project is NOT an asteroid impact prediction system unless future scientific validation establishes that capability. The initial scope is NEO classification, analysis, and explainable ML based on documented source data. The ML component is more precisely described as an **orbital-geometry-based approximation of JPL's Potentially Hazardous Asteroid (PHA) classification** — see `docs/EXPERIMENTS.md` and `docs/LIMITATIONS.md` for what that approximation can and cannot capture.
