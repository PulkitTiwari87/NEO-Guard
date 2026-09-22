# ml/features/

**IMPLEMENTED.**

* `engineering.py` — `build_features()`: stateless mapping of 7 SBDB orbital elements to the 9 model inputs
  (angles → sin/cos). Used identically at training and prediction time (inside the sklearn pipeline).
* `audit.py` — `FEATURE_AUDIT`: leakage audit of every candidate column (`feature` / `target` /
  `identifier` / `split_only` / `excluded`, with reasons). `tests/ml/test_leakage.py` fails if a column is
  unaudited or a target-defining column reaches the model.

Policy: [`FEATURE_POLICY.md`](../../docs/FEATURE_POLICY.md), [`DATA_LEAKAGE.md`](../../docs/DATA_LEAKAGE.md).
