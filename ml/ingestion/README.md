# ml/ingestion/

**IMPLEMENTED.** Fetches real data from the JPL SBDB Query API and CAD API and stores it write-once.

```bash
python -m ml.ingestion [--source sbdb|cad|all] [--date-min 2000-01-01] [--date-max 2100-01-01] [--dist-max-au 0.05] [--max-age-hours 24] [--force]
```

* `jpl_client.py` — httpx client: timeouts, bounded retries with exponential backoff, `Retry-After`,
  ≥ 1 s between requests, response-envelope validation. Raises `JPLAPIError`; never returns invented data.
* `raw_store.py` — `data/raw/<source>/<date>/<source>_<stamp>.json` (+ `.meta.json` with sha256, params,
  API version); exclusive-create so raw files can never be overwritten; snapshot cache lookup.

Source details and verification: [`DATA_SOURCE.md`](../../docs/DATA_SOURCE.md).
