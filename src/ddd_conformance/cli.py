import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ddd_conformance.analysis import analyze_repository


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze DDD-related structural code metrics")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    report = analyze_repository(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
