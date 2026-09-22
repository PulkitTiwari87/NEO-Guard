"""CLI: ``python -m ml.validation`` — validate the latest raw snapshots into data/interim/."""
from __future__ import annotations

import sys

from ml.validation import validate


def main() -> int:
    try:
        report = validate.run()
    except FileNotFoundError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    neo = report["neo_objects"]
    print(f"dataset_version: {report['dataset_version']}")
    print(f"neo_objects: {neo['valid']} valid / {neo['rejected']} rejected of {neo['raw_records']}")
    if "close_approaches" in report:
        cad = report["close_approaches"]
        print(f"close_approaches: {cad['valid']} valid / {cad['rejected']} rejected "
              f"of {cad['raw_records']}")
    audit = report["pha_rule_audit"]
    print(f"PHA rule audit: {audit['agree']}/{audit['rows_with_flag']} agree "
          f"({audit['disagree']} disagree)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
