from collections.abc import Callable
from pathlib import Path

from ddd_conformance.adapters.php import parse_php
from ddd_conformance.adapters.python import parse_python
from ddd_conformance.adapters.typescript import parse_typescript
from ddd_conformance.classification import classify_class_role
from ddd_conformance.metrics.architecture import summarize_architecture
from ddd_conformance.metrics.cohesion import adjusted_methods, lcom4, lcom4_adjusted
from ddd_conformance.metrics.semantic import summarize_srpc
from ddd_conformance.model import SourceUnit

Adapter = Callable[[str, str], SourceUnit]

ADAPTERS: dict[str, Adapter] = {
    ".php": parse_php,
    ".py": parse_python,
    ".js": parse_typescript,
    ".jsx": parse_typescript,
    ".ts": parse_typescript,
    ".tsx": parse_typescript,
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "test",
    "tests",
    "vendor",
    "venv",
}


def _is_excluded(path: Path, root: Path) -> bool:
    return bool(set(path.relative_to(root).parts) & EXCLUDED_DIRECTORIES)


def analyze_repository(root: Path) -> dict:
    class_rows: list[dict] = []
    source_units: list[SourceUnit] = []
    errors: list[dict[str, str]] = []
    files_analyzed = 0

    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in ADAPTERS
        and not _is_excluded(path, root)
    )
    for path in paths:
        relative = path.relative_to(root).as_posix()
        adapter = ADAPTERS[path.suffix.lower()]
        try:
            unit = adapter(path.read_text(encoding="utf-8"), relative)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            errors.append({"path": relative, "error": str(exc)})
            continue
        files_analyzed += 1
        source_units.append(unit)
        for class_unit in unit.classes:
            behavior = adjusted_methods(class_unit)
            behavior_fields = {
                field
                for method in behavior
                for field in class_unit.method_field_accesses.get(method, ())
            }
            classification = classify_class_role(
                relative, class_unit.name, bases=class_unit.bases
            )
            class_rows.append(
                {
                    "path": relative,
                    "language": unit.language,
                    "class": class_unit.name,
                    "bases": class_unit.bases,
                    "methods": len(class_unit.methods),
                    "fields": len(class_unit.fields),
                    "lcom4": lcom4(class_unit),
                    "lcom4_eligible": len(class_unit.methods) >= 2 and len(class_unit.fields) >= 1,
                    "lcom4_adjusted": lcom4_adjusted(class_unit),
                    "behavior_methods": len(behavior),
                    "lcom4_adjusted_eligible": len(behavior) >= 2
                    and bool(behavior_fields),
                    "role": classification.role,
                    "role_confidence": classification.confidence,
                    "role_rule": classification.rule,
                }
            )

    return {
        "summary": {
            "files_analyzed": files_analyzed,
            "parse_errors": len(errors),
            "classes": len(class_rows),
        },
        "classes": class_rows,
        "architecture": summarize_architecture(source_units),
        "semantic": {"srpc": summarize_srpc(class_rows)},
        "errors": errors,
    }
