# Model Card

> **Status: FIRST REAL MODELS TRAINED — all `experimental`, none validated by a domain expert.**
> This card describes `random_forest-v1`, the model served by default (best validation PR-AUC).
> All six trained models are compared in [`EXPERIMENTS.md`](EXPERIMENTS.md). Every number below was
> computed by the pipeline; none was typed in.

## Model details

| Field | Value |
|-------|-------|
| Model name / version | `random_forest` / `random_forest-v1` |
| Trained | 2026-09-21 (UTC) |
| Framework | scikit-learn 1.9.1 (Python 3.12.6), `Pipeline[build_features → RandomForestClassifier]` |
| Parameters | 300 trees, `min_samples_leaf=5`, `max_features="sqrt"`, seed 42, no class weighting |
| Decision threshold | 0.2703 (maximises F1 on the validation split) |
| Status | `experimental` |

## Intended use

Educational/research exploration of which near-Earth-asteroid **orbits** resemble those JPL flags as
potentially hazardous, with explanations. Outputs are statistical estimates that must be read next
to JPL's own PHA designation, which remains authoritative.

## Out-of-scope use

* Impact prediction or risk assessment. * Any safety-critical decision. * Objects outside the
training domain (bound orbits, perihelion < 1.3 au; the API rejects others). * Treating SHAP
attributions as causal explanations.

## Training data

| Field | Value |
|-------|-------|
| Source | JPL SBDB Query API v1.0, retrieved 2026-09-21T12:56Z ([`DATA_SOURCE.md`](DATA_SOURCE.md)) |
| Dataset version | `jpl-sbdb-neo-20260921-c34b5103` |
| Records | 42,351 near-Earth asteroids with a known PHA flag (126 excluded: no flag) |
| Split | chronological by first-observation year: train 1893–2022 (31,545), validation 2023–2024 (5,790), test 2025–2026 (5,016) |
| Feature version | `features-v1` |

## Features

7 orbital elements → 9 model inputs (`a, e, i, q, Q, sin/cos Ω, sin/cos ω`). **Excluded on purpose:**
`H`, `moid` (they define the label), size proxies, and observation-effort metadata
([`FEATURE_POLICY.md`](FEATURE_POLICY.md), [`DATA_LEAKAGE.md`](DATA_LEAKAGE.md)).

## Target variable

| Field | Value |
|-------|-------|
| Name | `is_potentially_hazardous` (JPL `pha`) |
| Definition | Earth MOID ≤ 0.05 au and H ≤ 22.0 (CNEOS) |
| Distribution | 2,549 positive (6.02%) / 39,802 negative; train 7.52%, validation 1.95%, test 1.28% |

## Metrics (real; threshold 0.2703)

| Metric | Validation | Test |
|--------|-----------:|-----:|
| Accuracy | 0.9560 | 0.9551 |
| Precision | 0.2114 | 0.1185 |
| Recall | 0.4602 | 0.3906 |
| F1 | 0.2897 | 0.1818 |
| ROC-AUC | 0.9003 | 0.8978 (95% CI 0.8668–0.9255) |
| PR-AUC | 0.1827 | 0.1461 (95% CI 0.0881–0.2362) |

Confusion matrices — validation: TN 5,483 · FP 194 · FN 61 · TP 52; test: TN 4,766 · FP 186 · FN 39 ·
TP 25. No-skill PR-AUC on test is 0.0128, so the model ranks ~11× better than chance but **most of
its positive calls are wrong**: of 211 test objects flagged, 25 (11.8%) are PHAs, and 39 of 64 PHAs
are missed. Test accuracy (0.9551) is *lower* than the trivial all-negative baseline (0.9872), so
accuracy should be ignored.

## Known limitations and biases

* **Weak by construction.** The model excludes `H` and direct MOID inputs, so it cannot reproduce
  the complete JPL PHA decision rule. The experiment instead measures how much predictive signal
  can be inferred from orbital geometry alone (`docs/LIMITATIONS.md`;
  `docs/EXPERIMENTS.md` Experiment 4 quantifies the gap: giving a model H and MOID raises test
  PR-AUC from 0.146 to 0.992 for this same algorithm).
* **Misses obvious PHAs.** Observed via the API: Apophis (JPL-flagged PHA; H = 19.09, Earth MOID
  0.000108 au) is scored 0.176 < 0.270 → predicted *not* PHA, even though its MOID is ~460× below the
  0.05 au threshold. (Apophis is an Aten-class orbit, a = 0.92 au; such orbits are a minority of the
  training set.) A recall of 39% means misses like this are expected, not exceptional. Full case
  study below.
* **Not demonstrated to be calibrated.** `docs/EXPERIMENTS.md` Experiment 3: on validation, this
  model's Brier score (0.0234) is *worse* than always predicting the base rate (0.0191). The output
  is useful for ranking, not for reading as a true probability — see "Model score, not probability"
  below.
* **Distribution shift.** Trained on a 7.5% PHA rate, tested on 1.3%; the threshold was tuned at 1.95%.
* **Small test set** (64 positives): all differences between the six models are within noise.
* **Discovery bias.** Trained on discovered objects only; not a random sample of the NEO population.
* **Untuned.** Fixed default hyper-parameters; no search, no calibration step.
* **Snapshot.** Labels/orbits will drift as observations accumulate.

## Explainability

SHAP (probability units for this model). Global attribution on validation: `perihelion_distance_au`
(mean |SHAP| 0.042) > `eccentricity` (0.023) > `inclination_deg` (0.018) > `ascending_node_sin`
(0.009). This says how the model uses its inputs, not why asteroids are hazardous.

## Model score, not probability

The API field is still named `probability` (kept for backward compatibility — see
`docs/API_CONTRACT.md`), but Experiment 3 (`docs/EXPERIMENTS.md`) found it is **not demonstrated
to be a calibrated probability**: its Brier score on validation (0.0234) is worse than the
no-skill baseline (0.0191), and it is overconfident in its highest-scoring decile (mean predicted
27.9%, observed frequency 13.0%). Read the output as a **model score** — useful for ranking
objects, not as "this object has an X% chance of being a PHA." The frontend and this card use
"Model Score" language accordingly.

## Subgroup evaluation (by orbital class)

Full results, reproducibility command, and the `INSUFFICIENT SAMPLE` rule:
`docs/EXPERIMENTS.md` Experiment 2. Summary: only **Apollo** orbits have enough positives (≥10)
in both validation and test to evaluate; its test PR-AUC (0.166) and ROC-AUC (0.876) track the
overall test figures (0.146 / 0.898) closely. Amor, Aten and Atira are `INSUFFICIENT SAMPLE` in
both splits — no per-subgroup claim is made for them.

## Apophis case study (qualitative — one real-world example, not a validation)

Recomputed via `python -m ml.diagnostics.case_study` against the live model
(`ml/diagnostics/output/apophis_case_study.json`), not retyped:

| Field | Value |
|---|---|
| Designation | 99942 Apophis (2004 MN4) |
| JPL PHA status | `true` |
| Orbit class | Aten (`ATE`) |
| H / Earth MOID | 19.09 / 0.000108 au |
| Model score | 0.1763 |
| Decision threshold | 0.2703 |
| Model decision | `not_potentially_hazardous` (miss) |

Apophis is a real, JPL-flagged PHA that this model misses — consistent with its measured 39% test
recall. **One object does not prove the model works or fails overall**; it illustrates concretely
what a false negative looks like and why recall, not just accuracy or PR-AUC, matters here.

## Definition-reconstruction diagnostic (context, not this model)

`docs/EXPERIMENTS.md` Experiment 4 trains separate diagnostic-only models with H and MOID added
to the same feature set. They are **not** `random_forest-v1`, are stored outside the production
artifact registry, and are never selectable by the API. They exist only to show how much of the
task becomes trivial once the label-defining variables are visible (test PR-AUC up to 0.997),
which is why `random_forest-v1` (orbital-only, PR-AUC 0.146) looks weak by comparison — it is
solving a strictly harder problem by design.

## Reproducibility

Seed 42; dependency versions pinned in `backend/requirements.txt` and recorded in
`ml/artifacts/random_forest/v1/metadata.json`; `python -m ml.training` reproduces the model
(verified by a test, to within 1e-12).

## Dataset provenance

See [`DATA_SOURCE.md`](DATA_SOURCE.md) — raw response hash `c34b51037879…`, retrieved 2026-09-21.
