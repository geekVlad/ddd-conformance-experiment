"""Deterministically select a small, rule-stratified Semgrep review sample."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _candidate_from_finding(finding: dict[str, Any], corpus_root: Path) -> dict[str, Any] | None:
    check_id = finding.get("check_id")
    path_value = finding.get("path")
    line = finding.get("start", {}).get("line")
    if not isinstance(check_id, str) or not isinstance(path_value, str) or not isinstance(line, int):
        return None
    source_path = Path(path_value)
    try:
        relative_path = source_path.relative_to(corpus_root)
    except ValueError:
        return None
    if len(relative_path.parts) < 2 or not source_path.is_file():
        return None
    source_lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not 1 <= line <= len(source_lines):
        return None
    repository = relative_path.parts[0]
    rule_id = check_id.rsplit(".", 1)[-1].removeprefix("ddd-")
    return {
        "repository": repository,
        "rule_id": rule_id,
        "path": str(relative_path),
        "line": line,
        "snippet": source_lines[line - 1].strip(),
        "tool": "semgrep",
        "tool_rule_id": check_id,
    }


def build_stratified_candidates(results_dir: Path, corpus_root: Path, *, limit: int = 3) -> list[dict[str, Any]]:
    """Return at most ``limit`` candidates, covering distinct rules first."""
    if limit < 1:
        return []
    results_dir = results_dir.resolve()
    corpus_root = corpus_root.resolve()
    by_rule: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result_file in sorted(results_dir.glob("*.json")):
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        for finding in payload.get("results", []):
            candidate = _candidate_from_finding(finding, corpus_root)
            if candidate is not None:
                by_rule[candidate["rule_id"]].append(candidate)
    selected: list[dict[str, Any]] = []
    for rule_id in sorted(by_rule):
        selected.append(by_rule[rule_id][0])
        if len(selected) == limit:
            return selected
    remaining = [candidate for rule_id in sorted(by_rule) for candidate in by_rule[rule_id][1:]]
    return selected + remaining[: limit - len(selected)]
