# Data Sources

> **Status: VERIFIED and IMPLEMENTED (2026-09-21).** Both sources below were checked against the
> official JPL documentation pages and by live queries before any ingestion code was written.
> Nothing in this project is fabricated: every NEO and close-approach record in `data/` and in the
> database came from these two APIs. Synthetic data exists only inside `tests/` and is labelled
> `SYNTHETIC / TEST DATA`.

## Selected sources

Both are public JPL Solar System Dynamics / CNEOS APIs. **Neither requires an API key**, so the
`NASA_API_KEY` variable from the foundation was removed (it would be unused configuration).

### 1. JPL Small-Body Database (SBDB) Query API — NEO orbits and the PHA flag

| Field | Value |
|-------|-------|
| Source name | JPL SBDB Query API (`jpl_sbdb`) |
| Official documentation | https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html |
| API endpoint | `GET https://ssd-api.jpl.nasa.gov/sbdb_query.api` |
| API version | 1.0 (from the response `signature`; doc page dated August 2021) |
| Access method | Unauthenticated HTTPS GET, JSON |
| Query used | `sb-kind=a` (asteroids), `sb-group=neo` (near-Earth objects), `full-prec=true`, `fields=` the 28 fields below |
| Retrieved | **2026-09-21T12:56:33Z** — 42,477 records, sha256 `c34b51037879…` |
| Dataset version | `jpl-sbdb-neo-20260921-c34b5103` (date + first 8 hex of the raw response hash) |
| Raw file | `data/raw/jpl_sbdb/2026-09-21/jpl_sbdb_20260921T125633Z.json` (+ `.meta.json`), git-ignored |
| Fields retrieved | `spkid, pdes, full_name, name, neo, pha, H, diameter, albedo, e, a, q, ad, i, om, w, ma, n, per, moid, epoch, condition_code, first_obs, last_obs, n_obs_used, data_arc, rms, class` |
| Rate limits | **Not documented** on the API page. The client waits ≥ 1 s between requests, retries 429/5xx with exponential backoff (honouring `Retry-After`), and reuses any snapshot < 24 h old with identical parameters. A full ingestion makes 2 requests. |
| Authentication | None (verified: unauthenticated requests succeed) |
| License / terms | Public NASA/JPL data. **Not verified in this phase:** confirm the current JPL terms before redistributing the data. |

### 2. JPL SBDB Close-Approach Data (CAD) API — predicted Earth close approaches

| Field | Value |
|-------|-------|
| Source name | JPL SBDB Close-Approach Data API (`jpl_cad`) |
| Official documentation | https://ssd-api.jpl.nasa.gov/doc/cad.html |
| API endpoint | `GET https://ssd-api.jpl.nasa.gov/cad.api` |
| API version | 1.5 (from the response `signature`; doc page dated March 2023) |
| Query used | `date-min=2000-01-01`, `date-max=2100-01-01`, `dist-max=0.05` (au), `body=Earth`, `nea=true`, `sort=date` |
| Retrieved | **2026-09-21T12:56:36Z** — 30,828 records, sha256 `7fc39c68a486…` |
| Raw file | `data/raw/jpl_cad/2026-09-21/jpl_cad_20260921T125636Z.json` (+ `.meta.json`), git-ignored |
| Fields retrieved | `des, orbit_id, jd, cd, dist, dist_min, dist_max, v_rel, v_inf, t_sigma_f, h` |
| Rate limits / authentication / license | As above |

The window (2000–2100) and the 0.05 au cut-off are **our choices** (0.05 au is also the PHA MOID
threshold), not properties of the source. Override with `--date-min/--date-max/--dist-max-au`.

### Reference: CNEOS group definitions

https://cneos.jpl.nasa.gov/about/neo_groups.html — defines NEO (perihelion q < 1.3 au), the Atira /
Aten / Apollo / Amor groups and, crucially for this project, **PHAs**: *"all asteroids with an Earth
Minimum Orbit Intersection Distance (MOID) of 0.05 au or less and an absolute magnitude (H) of 22.0
or less"* (about 140 m for an assumed 14% albedo).

## Not used

**NASA NeoWs** (`api.nasa.gov`) was not evaluated in this phase. It would need a `NASA_API_KEY`
and the JPL sources above already provide the orbit, MOID and PHA fields the models need.

## What the verification found

* SBDB holds **42,477** near-Earth asteroids of which **2,549 (6.0%)** are flagged PHA, **39,802**
  are not, and **126 have no flag** (all 126 also lack a MOID).
* The PHA flag agrees with the published CNEOS rule (`moid <= 0.05` and `H <= 22.0`) for
  **42,301 of 42,351** flagged objects. The 50 exceptions (33 flagged although the rule is false, 17
  the reverse) cluster at `H ≈ 22`; the cause is **not established** (possible H updates or rounding).
* All 30,828 CAD designations exist in the SBDB set; no duplicate `(designation, jd)` pairs.
* Source rows pass every validation rule (0 rejected; see `data/interim/validation_report.json`).

## Known limitations of the data

* **Snapshot.** Orbits and flags change as new observations arrive; the SBDB docs warn the database
  "can change between API calls". Re-ingest (`python -m ml.ingestion --force`) to refresh; models
  record the `dataset_version` they were trained on.
* **Sparse physical data.** `diameter` exists for 1,245 objects (2.9%) and `albedo` for 1,203 (2.8%);
  `H` is missing for 2 objects; `data_arc` for 430; `condition_code` for 2.
* **Source quirk.** One object has `first_obs = "2008-??-??"`; only its year is used.
* **CAD scope.** Only approaches within 0.05 au of Earth in 2000–2100 are stored — not every
  close approach. Times are **TDB**, not UTC. Future approaches are predictions with uncertainty
  (`distance_min/max` and `time_uncertainty` are JPL's 3-sigma bounds).
* **Observational bias.** The NEO catalogue is the set of objects humanity has discovered; large and
  bright objects are far more complete than small ones.

## Policy

* Real NASA/JPL data only. If JPL is unreachable, ingestion fails with a clear error and the
  application keeps serving whatever is already in the database; it never substitutes invented data.
* Synthetic data is allowed only in tests, labelled `SYNTHETIC / TEST DATA`, and never placed under
  `data/`.
