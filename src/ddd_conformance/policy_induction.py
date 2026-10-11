"""Infer a provisional DDD policy from repository path conventions."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

_SOURCE_SUFFIXES = {".php", ".py", ".ts", ".tsx", ".js", ".jsx"}
_LAYER_NAMES = {
    "domain": "domain_paths",
    "application": "application_paths",
    "app": "application_paths",
    "infrastructure": "infrastructure_paths",
    "infra": "infrastructure_paths",
    "adapters": "infrastructure_paths",
}
_CONTEXT_CONTAINERS = {"src", "modules", "module", "contexts", "context"}
_IGNORED_PATH_PARTS = {".git", "node_modules", "vendor", "venv", ".venv", "dist", "build"}


def _context_name(parts: tuple[str, ...], layer_index: int) -> str:
    before_layer = parts[:layer_index]
    for part in reversed(before_layer):
        if part.lower() not in _CONTEXT_CONTAINERS:
            return part
    return "default"


def infer_policy(repository: Path, *, project: str, revision: str) -> dict[str, Any]:
    """Build a path-evidence-backed, provisional policy without mutating source code."""
    repository = repository.resolve()
    contexts: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for source in sorted(repository.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        relative = source.relative_to(repository)
        if _IGNORED_PATH_PARTS.intersection(relative.parts):
            continue
        parts = relative.parts[:-1]
        for index, part in enumerate(parts):
            target_field = _LAYER_NAMES.get(part.lower())
            if target_field is None:
                continue
            context = _context_name(parts, index)
            prefix = "/".join(parts[: index + 1])
            contexts[context][target_field].add(f"{prefix}/**")
            break

    serialized_contexts = [
        {
            "name": name,
            "domain_paths": sorted(values.get("domain_paths", set())),
            "application_paths": sorted(values.get("application_paths", set())),
            "infrastructure_paths": sorted(values.get("infrastructure_paths", set())),
        }
        for name, values in sorted(contexts.items())
    ]
    return {
        "project": project,
        "revision": revision,
        "inference": {
            "kind": "path-convention",
            "confidence": "hypothesis",
            "evidence": "source-file path conventions only; no architectural intent is inferred",
        },
        "contexts": serialized_contexts,
        "ports": [],
        "shared_kernel": [],
        "acl": [],
        "allow_list": [],
        "allowed_rule_ids": [
            "domain-imports-infrastructure",
            "domain-transport-type",
            "cross-context-import",
        ],
        "exclusions": ["**/tests/**", "**/Test/**", "**/Tests/**", "**/fixtures/**", "**/vendor/**"],
        "rules": [
            {"id": "domain-imports-infrastructure", "expected": "forbidden", "exceptions": ["port", "shared_kernel", "acl"]},
            {"id": "domain-transport-type", "expected": "review", "requires_explicit_classification": True},
            {"id": "cross-context-import", "expected": "forbidden", "exceptions": ["shared_kernel", "published_language", "acl"]},
        ],
    }
