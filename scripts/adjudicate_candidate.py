"""Run the configuration-grounded LLM adjudicator for one candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from ddd_conformance.llm_adjudication import adjudicate_candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    policy = yaml.safe_load(args.policy.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = adjudicate_candidate(candidate, policy, model=args.model, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
