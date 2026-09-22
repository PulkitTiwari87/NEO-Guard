"""CLI: ``python -m ml.training [--algorithms ...] [--class-weight none|balanced|both]``."""
from __future__ import annotations

import argparse
import sys

from ml.training import train


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.training", description=__doc__)
    parser.add_argument("--algorithms", nargs="+", choices=train.ALGORITHMS,
                        default=list(train.ALGORITHMS))
    parser.add_argument("--class-weight", choices=[*train.CLASS_WEIGHTS, "both"], default="both")
    args = parser.parse_args(argv)
    weights = train.CLASS_WEIGHTS if args.class_weight == "both" else (args.class_weight,)
    try:
        results = train.run(tuple(args.algorithms), weights)
    except FileNotFoundError as exc:
        print(f"TRAINING FAILED: {exc}. Run: python -m ml.preprocessing", file=sys.stderr)
        return 1
    print(f"{'version':<28}{'thr':>8}{'val PR-AUC':>12}{'val ROC-AUC':>13}{'val F1':>9}")
    for m in results:
        v = m["metrics"]["validation"]
        print(f"{m['model_version']:<28}{m['threshold']:>8.3f}{v['pr_auc']:>12.4f}"
              f"{v['roc_auc']:>13.4f}{v['f1']:>9.4f}")
    print("Next: python -m ml.evaluation   (held-out test evaluation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
