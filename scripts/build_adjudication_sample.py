"""Build a small deterministic Semgrep sample for paid LLM adjudication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ddd_conformance.adjudication_sampling import build_stratified_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/semgrep"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--output", type=Path, default=Path("results/adjudication/semgrep-sample.json"))
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    candidates = build_stratified_candidates(args.results, args.corpus, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(candidates)} candidates to {args.output}")


if __name__ == "__main__":
    main()
