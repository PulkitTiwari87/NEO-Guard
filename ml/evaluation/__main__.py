"""CLI: ``python -m ml.evaluation [--model-version X ...]`` — held-out test evaluation."""
from __future__ import annotations

import argparse
import sys

from ml.evaluation import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.evaluation", description=__doc__)
    parser.add_argument("--model-version", nargs="+", help="default: every artifact")
    args = parser.parse_args(argv)
    try:
        results = evaluate.run(args.model_version)
    except (FileNotFoundError, ValueError) as exc:
        print(f"EVALUATION FAILED: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("No artifacts evaluated. Run: python -m ml.training", file=sys.stderr)
        return 1
    print(f"{'version':<34}{'test PR-AUC':>12}{'test ROC-AUC':>14}{'test F1':>9}{'recall':>8}")
    for m in results:
        t = m["metrics"]["test"]
        print(f"{m['model_version']:<34}{t['pr_auc']:>12.4f}{t['roc_auc']:>14.4f}"
              f"{t['f1']:>9.4f}{t['recall']:>8.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
