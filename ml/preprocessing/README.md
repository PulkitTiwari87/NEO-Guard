# ml/preprocessing/

**IMPLEMENTED.** Builds the ML dataset from `data/interim/`.

```bash
python -m ml.preprocessing   # data/interim/ -> data/processed/{neo_ml_dataset.csv, split_manifest.json}
```

Steps: keep rows with a known PHA flag and complete inputs → drop duplicate feature vectors → assign a
**chronological** split by first-observation year (whole years; ≈70/15/15). Nothing is fitted here; the
scaler/model are fitted on the train split inside the training pipeline. See
[`DATA_LEAKAGE.md`](../../docs/DATA_LEAKAGE.md).
