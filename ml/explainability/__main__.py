"""CLI: ``python -m ml.explainability [--model-version X ...]`` — global SHAP importance."""
from __future__ import annotations

import argparse
import sys

from ml.explainability import explain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml.explainability", description=__doc__)
    parser.add_argument("--model-version", nargs="+", help="default: every artifact")
    args = parser.parse_args(argv)
    try:
        results = explain.run(args.model_version)
    except (FileNotFoundError, ValueError) as exc:
        print(f"EXPLAINABILITY FAILED: {exc}", file=sys.stderr)
        return 1
    for r in results:
        top = ", ".join(f"{i['feature']} ({i['mean_abs_shap']:.3f})" for i in r["importance"][:3])
        print(f"{r['model_version']:<34}[{r['output_space']}] top: {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
