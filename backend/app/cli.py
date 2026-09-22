"""Database CLI: ``python -m app.cli {load-data,sync-models,set-status}``."""
from __future__ import annotations

import argparse
import json
import sys

from app.db import loader
from app.db.database import get_session_factory
from ml import artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("load-data", help="load data/interim/ (validated JPL data) into the database")
    sub.add_parser("sync-models", help="register ml/artifacts models and experiments in the database")
    status = sub.add_parser("set-status", help="set a model's status (never automatic)")
    status.add_argument("version")
    status.add_argument("status", choices=artifacts.STATUSES)
    args = parser.parse_args(argv)

    try:
        with get_session_factory()() as db:
            if args.command == "load-data":
                print(json.dumps(loader.load_interim(db), indent=2))
            elif args.command == "sync-models":
                print(json.dumps(loader.sync_models(db, artifacts.list_artifacts()), indent=2))
            else:
                loader.set_model_status(db, args.version, args.status)
                print(f"{args.version}: status = {args.status}")
    except (FileNotFoundError, LookupError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
