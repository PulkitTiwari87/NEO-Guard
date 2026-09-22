"""CLI: ``python -m ml.preprocessing`` — build data/processed/ from data/interim/."""
from __future__ import annotations

import sys

from ml.preprocessing import dataset


def main() -> int:
    try:
        m = dataset.run()
    except FileNotFoundError as exc:
        print(f"PREPROCESSING FAILED: {exc}. Run: python -m ml.validation", file=sys.stderr)
        return 1
    print(f"dataset_version: {m['dataset_version']}  feature_version: {m['feature_version']}")
    print(f"rows: {m['rows']} (excluded: {m['excluded_missing_target']} missing target, "
          f"{m['excluded_missing_features']} missing features, "
          f"{m['excluded_duplicate_feature_vectors']} duplicate vectors)")
    for name, s in m["splits"].items():
        print(f"  {name:<10} {s['rows']:>6} rows  {s['positives']:>5} positives "
              f"({s['positive_rate']:.2%})  years {s['first_obs_year_min']}-{s['first_obs_year_max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
