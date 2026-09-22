# ml/validation/

**IMPLEMENTED.** Validates raw snapshots and normalises them to the internal schema.

```bash
python -m ml.validation      # data/raw/ -> data/interim/
```

* `schema.py` — pydantic `NEORecord` / `CloseApproachRecord` and the source→internal field maps.
* `validate.py` — per-record validation, duplicate and referential checks, PHA-rule audit, interim writers/readers.
* Output: `neo_objects.csv`, `close_approaches.csv`, `rejected_*.jsonl` (reason + original row),
  `validation_report.json` (provenance, counts, dataset version).

Rejections are recorded, never silent. Field rules: [`DATA_DICTIONARY.md`](../../docs/DATA_DICTIONARY.md).
