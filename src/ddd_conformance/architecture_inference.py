"""Deterministic multi-signal architecture hypothesis agent."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

_SOURCE_SUFFIXES = {".php", ".py", ".ts", ".tsx", ".js", ".jsx"}
_IGNORED_PATH_PARTS = {".git", "node_modules", "vendor", "venv", ".venv", "dist", "build", "tests", "test", "fixtures"}
_LAYER_ROLES = {
    "domain": "domain",
    "application": "application",
    "app": "application",
    "infrastructure": "infrastructure",
    "infra": "infrastructure",
    "adapters": "adapter",
    "adapter": "adapter",
    "repository": "repository",
    "repositories": "repository",
    "dto": "transport",
    "transport": "transport",
    "http": "transport",
    "api": "transport",
    "controller": "transport",
    "controllers": "transport",
    "database": "infrastructure",
    "persistence": "infrastructure",
    "orm": "infrastructure",
    "event": "event",
    "events": "event",
    "common": "utility",
    "utils": "utility",
    "utilities": "utility",
    "helpers": "utility",
    "config": "configuration",
    "configuration": "configuration",
    "migrations": "migration",
    "migration": "migration",
    "generated": "generated",
    "framework": "framework",
    "cli": "cli",
    "integration": "integration",
    "integrations": "integration",
    "read_model": "read_model",
    "read-model": "read_model",
    "shared": "shared_kernel_candidate",
}
_CONTEXT_CONTAINERS = {"modules", "module", "contexts", "context", "apps", "packages", "libs"}
_FILENAME_ROLE_MARKERS = {
    "application": ("command", "query", "handler", "projector", "projecting", "usecase", "use_case"),
    "domain": ("aggregate", "entity", "valueobject", "value_object"),
    "infrastructure": ("repository", "persistence", "database", "orm"),
    "transport": ("controller", "request", "response", "serializer", "dto", "schema"),
    "event": ("event",),
}
_ROLE_TO_POLICY_FIELD = {
    "domain": "domain_paths",
    "application": "application_paths",
    "infrastructure": "infrastructure_paths",
    "adapter": "infrastructure_paths",
    "repository": "infrastructure_paths",
    "transport": "infrastructure_paths",
}


def _role(parts: tuple[str, ...], filename: str) -> tuple[str, int | None]:
    for index, part in enumerate(parts):
        role = _LAYER_ROLES.get(part.lower())
        if role:
            return role, index
    normalized_filename = filename.lower().replace("-", "_")
    for role, markers in _FILENAME_ROLE_MARKERS.items():
        if any(marker in normalized_filename for marker in markers):
            return role, None
    return "other_support", None


def _context(parts: tuple[str, ...], role_index: int | None) -> str:
    if role_index is not None:
        for part in reversed(parts[:role_index]):
            if part.lower() not in {"src", *_CONTEXT_CONTAINERS}:
                return part
    for index, part in enumerate(parts[:-1]):
        if part.lower() in _CONTEXT_CONTAINERS:
            return parts[index + 1]
    if parts and parts[0].lower() == "src" and len(parts) > 1:
        return parts[1]
    return parts[0] if parts else "default"


def _count_imports(source: Path) -> int:
    content = source.read_text(encoding="utf-8", errors="replace")
    if source.suffix.lower() == ".py":
        pattern = r"^\s*(?:from\s+\S+\s+import\s+|import\s+\S+)"
    elif source.suffix.lower() == ".php":
        pattern = r"^\s*(?:use\s+|require(?:_once)?\s*\()"
    else:
        pattern = r"^\s*import(?:\s|\{)"
    return sum(bool(re.match(pattern, line)) for line in content.splitlines())


def _extract_import_specs(source: Path) -> list[str]:
    content = source.read_text(encoding="utf-8", errors="replace")
    if source.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"}:
        return re.findall(r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]", content)
    if source.suffix.lower() == ".py":
        matches = re.findall(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", content, re.MULTILINE)
        return [first or second for first, second in matches]
    if source.suffix.lower() == ".php":
        return re.findall(r"^\s*(?:use\s+|require(?:_once)?\s*\(?\s*['\"])([^;'\")]+)", content, re.MULTILINE)
    return []


def _resolve_relative_import(repository: Path, source: Path, spec: str) -> str | None:
    if not spec.startswith("."):
        return None
    base = (source.parent / spec).resolve()
    candidates = [base, *(base.with_suffix(suffix) for suffix in _SOURCE_SUFFIXES)]
    candidates.extend(base / f"index{suffix}" for suffix in _SOURCE_SUFFIXES)
    for candidate in candidates:
        if candidate.is_file() and candidate.is_relative_to(repository):
            return candidate.relative_to(repository).as_posix()
    return None


def _edge_verdict(source_role: str, target_role: str, source_context: str, target_context: str) -> tuple[str, str]:
    if source_role == "domain" and target_role in {"infrastructure", "adapter", "repository", "transport"}:
        return "violation", "high"
    generic_contexts = {"domain", "application", "infrastructure", "adapter", "transport", "repository"}
    if source_context != target_context and target_context != "external" and {source_context, target_context}.isdisjoint(generic_contexts):
        return "low_confidence", "medium"
    if source_role == "other_support" or target_role in {"other_support", "external"}:
        return "low_confidence", "low"
    return "allowed", "high"


def _policy_context(name: str, values: dict[str, Any]) -> dict[str, Any]:
    paths = values["paths"]
    return {
        "name": name,
        "domain_paths": sorted(paths["domain_paths"]),
        "application_paths": sorted(paths["application_paths"]),
        "infrastructure_paths": sorted(paths["infrastructure_paths"]),
        "evidence_file_count": values["file_count"],
    }


def analyze_repository(repository: Path, *, project: str, revision: str) -> dict[str, Any]:
    """Infer contexts and file roles from paths without external inference calls."""
    repository = repository.resolve()
    contexts: dict[str, dict[str, Any]] = defaultdict(lambda: {"roles": Counter(), "paths": defaultdict(set), "file_count": 0})
    total_files = 0
    semantic_role_files = 0
    import_edge_count = 0
    file_records: dict[str, dict[str, str]] = {}
    source_paths: dict[str, Path] = {}
    for source in sorted(repository.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        relative = source.relative_to(repository)
        if _IGNORED_PATH_PARTS.intersection(part.lower() for part in relative.parts):
            continue
        total_files += 1
        import_edge_count += len(_extract_import_specs(source))
        parts = relative.parts[:-1]
        role, role_index = _role(parts, source.stem)
        if role != "other_support":
            semantic_role_files += 1
        context_name = _context(parts, role_index)
        relative_path = relative.as_posix()
        file_records[relative_path] = {"path": relative_path, "role": role, "context": context_name}
        source_paths[relative_path] = source
        context = contexts[context_name]
        context["roles"][role] += 1
        context["file_count"] += 1
        policy_field = _ROLE_TO_POLICY_FIELD.get(role)
        if policy_field and role_index is not None:
            prefix = "/".join(parts[: role_index + 1])
            context["paths"][policy_field].add(f"{prefix}/**")

    edges = []
    for source_path, source in source_paths.items():
        for spec in _extract_import_specs(source):
            target_path = _resolve_relative_import(repository, source, spec)
            source_record = file_records[source_path]
            if target_path is not None and target_path in file_records:
                target_record = file_records[target_path]
            else:
                target_path = spec
                target_record = {"context": "external", "role": "external"}
            verdict, confidence = _edge_verdict(
                source_record["role"], target_record["role"], source_record["context"], target_record["context"]
            )
            edges.append(
                {
                    "source": source_path,
                    "target": target_path,
                    "source_context": source_record["context"],
                    "target_context": target_record["context"],
                    "source_role": source_record["role"],
                    "target_role": target_record["role"],
                    "verdict": verdict,
                    "confidence": confidence,
                }
            )

    serialized_contexts = [
        {
            "name": name,
            "file_count": values["file_count"],
            "role_counts": dict(sorted(values["roles"].items())),
        }
        for name, values in sorted(contexts.items())
    ]
    policy_contexts = [_policy_context(name, values) for name, values in sorted(contexts.items())]
    policy = {
        "project": project,
        "revision": revision,
        "inference": {
            "kind": "multi-signal-path-role",
            "confidence": "hypothesis",
            "evidence": "path, package, and role-name signals; no per-file exception rules",
        },
        "contexts": policy_contexts,
        "allowed_rule_ids": ["domain-imports-infrastructure", "domain-transport-type", "cross-context-import"],
        "allow_list": [],
        "shared_kernel": [],
        "acl": [],
    }
    return {
        "project": project,
        "revision": revision,
        "source_file_count": total_files,
        "import_edge_count": import_edge_count,
        "classified_file_count": total_files,
        "semantic_role_file_count": semantic_role_files,
        "coverage": 1.0 if total_files else 0.0,
        "semantic_role_coverage": semantic_role_files / total_files if total_files else 0.0,
        "files": list(file_records.values()),
        "edges": edges,
        "contexts": serialized_contexts,
        "policy": policy,
    }
