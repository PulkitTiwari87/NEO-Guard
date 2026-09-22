"""CLI: ``python -m ml.ingestion [--source sbdb|cad|all]``.

Fetches real data from JPL and stores it under data/raw/. A snapshot younger than
``--max-age-hours`` with identical query parameters is reused instead of calling the API
again (use ``--force`` to bypass the cache).
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import timedelta

from ml import config
from ml.ingestion import raw_store
from ml.ingestion.jpl_client import JPLAPIError, JPLClient, cad_params, sbdb_params


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.ingestion", description=__doc__)
    parser.add_argument("--source", choices=["sbdb", "cad", "all"], default="all")
    parser.add_argument("--date-min", default=config.CAD_DATE_MIN, help="CAD window start")
    parser.add_argument("--date-max", default=config.CAD_DATE_MAX, help="CAD window end")
    parser.add_argument("--dist-max-au", type=float, default=config.CAD_DIST_MAX_AU)
    parser.add_argument("--max-age-hours", type=float, default=24.0)
    parser.add_argument("--force", action="store_true", help="ignore cached snapshots")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    max_age = timedelta(hours=0 if args.force else args.max_age_hours)
    jobs = []
    if args.source in ("sbdb", "all"):
        jobs.append((config.SBDB_SOURCE, sbdb_params(), lambda c: c.fetch_sbdb_neos()))
    if args.source in ("cad", "all"):
        jobs.append(
            (
                config.CAD_SOURCE,
                cad_params(args.date_min, args.date_max, args.dist_max_au),
                lambda c: c.fetch_close_approaches(args.date_min, args.date_max, args.dist_max_au),
            )
        )

    try:
        with JPLClient() as client:
            for source, params, fetch in jobs:
                cached = raw_store.find_recent(source, params, max_age)
                if cached:
                    print(f"[cache] {source}: reusing {cached.data_path.name} "
                          f"({cached.meta['record_count']} records)")
                    continue
                snapshot = raw_store.save_snapshot(source, fetch(client), params)
                print(f"[fetched] {source}: {snapshot.meta['record_count']} records -> "
                      f"{snapshot.data_path} (sha256 {snapshot.meta['sha256'][:12]})")
    except JPLAPIError as exc:
        print(f"INGESTION FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
