"""Fetch pinned sources and run independent structural analyzers; write data only."""

import argparse
import json
import subprocess
from pathlib import Path

import yaml

from ddd_conformance.analysis import analyze_repository as analyze_metrics
from ddd_conformance.architecture_inference import analyze_repository as analyze_architecture
from ddd_conformance.policy_induction import infer_policy
from ddd_conformance.reporting import (
    summarize_architecture_reports,
    summarize_roles,
    summarize_semantic_reports,
)

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", action="append", help="Manifest ID; repeat to select several")
    parser.add_argument("--skip-fetch", action="store_true", help="Require an existing pinned checkout")
    parser.add_argument("--corpus", type=Path, default=ROOT / "corpus")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/repositories.yaml")
    args = parser.parse_args()
    manifest = yaml.safe_load(args.manifest.read_text())
    repositories = [
        row for row in manifest["repositories"] if row["corpus_status"].startswith("accepted")
    ]
    if args.repository:
        wanted = set(args.repository)
        missing = wanted - {row["id"] for row in repositories}
        if missing:
            parser.error(f"Unknown or unaccepted manifest IDs: {sorted(missing)}")
        repositories = [row for row in repositories if row["id"] in wanted]
    rows, reports, agents, policies = [], [], [], []
    for record in repositories:
        identifier, revision = record["id"], record["commit"]
        path = args.corpus / identifier
        if not args.skip_fetch:
            path.mkdir(parents=True, exist_ok=True)
            if not (path / ".git").exists():
                subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
                git(path, "remote", "add", "origin", record["url"])
            if git(path, "remote", "get-url", "origin") != record["url"]:
                raise RuntimeError(f"Unexpected origin for {identifier}")
            # Do not discard modified work or switch an existing unrelated checkout.
            if git(path, "status", "--porcelain"):
                raise RuntimeError(f"Modified checkout: {identifier}")
            git(path, "fetch", "--depth=1", "origin", revision)
            git(path, "checkout", "--detach", revision)
        if git(path, "rev-parse", "HEAD") != revision or git(path, "status", "--porcelain"):
            raise RuntimeError(f"Checkout is not clean at the pinned revision: {identifier}")
        report = analyze_metrics(path)
        report.update(project=identifier, revision=revision, language=record["language"])
        policy = infer_policy(path, project=identifier, revision=revision)
        agent = analyze_architecture(path, project=identifier, revision=revision)
        write_json(args.output / f"{identifier}-py312.json", report)
        write_json(args.output / "architecture-agent" / f"{identifier}.json", agent)
        write_json(args.output / "architecture-agent" / f"{identifier}.policy.json", agent["policy"])
        destination = args.output / "policy-induction" / f"{identifier}.yaml"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        rows.extend(report["classes"])
        reports.append(report)
        agents.append({key: agent[key] for key in (
            "project", "revision", "source_file_count", "import_edge_count", "contexts"
        )})
        policies.append({"project": identifier, "revision": revision, "contexts": policy["contexts"]})
        print(f"Completed {identifier} at {revision}")
    write_json(args.output / "role-summary-py312.json", {
        "repositories": [{"project": r["project"], "summary": r["summary"]} for r in reports],
        "overall": {"raw": summarize_roles(rows), "adjusted": summarize_roles(
            rows, metric="lcom4_adjusted", eligibility="lcom4_adjusted_eligible"
        )},
        "architecture": summarize_architecture_reports(reports),
        "semantic": summarize_semantic_reports(reports),
    })
    write_json(args.output / "architecture-agent-summary.json", {"repositories": agents})
    write_json(args.output / "policy-induction-summary.json", {"repositories": policies})


if __name__ == "__main__":
    main()
