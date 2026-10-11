"""Lexical semantic baselines for DDD class placement."""

from __future__ import annotations

import re
from collections.abc import Iterable

_TEST_MARKERS = {"test", "tests", "spec", "specs", "behat", "fixture", "fixtures"}


def _tokens(value: str) -> set[str]:
    return {
        token.lower()
        for token in re.split(r"[^A-Za-z0-9]+|(?<=[a-z])(?=[A-Z])", value)
        if token
    }


def _path_layer(path: str) -> str:
    parent = path.replace("\\", "/").rsplit("/", maxsplit=1)[0]
    tokens = _tokens(parent)
    for layer in ("domain", "application", "infrastructure"):
        if layer in tokens:
            return layer
    if tokens & {"usecase", "usecases", "handler", "handlers"}:
        return "application"
    if tokens & {
        "infra",
        "adapter",
        "adapters",
        "persistence",
        "controller",
        "controllers",
        "api",
        "ui",
        "framework",
    }:
        return "infrastructure"
    return "other"


def _is_test(path: str, class_name: str) -> bool:
    return bool(_tokens(path) & _TEST_MARKERS) or bool(
        re.search(r"(?:Test|Tests|Mock|Stub|Fake|Fixture)$", class_name)
    )


def _name_hint(class_name: str) -> str | None:
    name = class_name.lower()
    for suffix, hint in (
        ("controller", "controller"),
        ("adapter", "adapter"),
        ("repository", "repository"),
        ("dto", "dto"),
        ("request", "request"),
        ("response", "response"),
        ("handler", "handler"),
        ("usecase", "use_case"),
        ("interactor", "interactor"),
        ("aggregateroot", "aggregate"),
        ("aggregate", "aggregate"),
        ("valueobject", "value_object"),
        ("domainservice", "domain_service"),
        ("specification", "specification"),
        ("policy", "policy"),
    ):
        if name.endswith(suffix):
            return hint
    return None


def _contradiction(path_layer: str, name_hint: str | None) -> str | None:
    if path_layer == "domain" and name_hint in {
        "controller",
        "adapter",
        "dto",
        "request",
        "response",
        "use_case",
        "interactor",
    }:
        return "domain path with infrastructure/transport/application name"
    if path_layer == "infrastructure" and name_hint in {
        "aggregate",
        "value_object",
        "domain_service",
        "specification",
        "policy",
    }:
        return "infrastructure path with domain-model name"
    if path_layer == "application" and name_hint in {"controller", "adapter"}:
        return "application path with infrastructure/transport name"
    return None


def summarize_srpc(class_rows: Iterable[dict[str, object]]) -> dict:
    """Compute Semantic Role–Placement Consistency from class paths and names."""
    eligible = 0
    signals: list[dict[str, str]] = []
    for row in class_rows:
        path = str(row["path"])
        class_name = str(row["class"])
        if _is_test(path, class_name):
            continue
        eligible += 1
        path_layer = _path_layer(path)
        name_hint = _name_hint(class_name)
        if rule := _contradiction(path_layer, name_hint):
            signals.append(
                {
                    "path": path,
                    "class": class_name,
                    "path_layer": path_layer,
                    "name_hint": name_hint or "",
                    "rule": rule,
                }
            )

    return {
        "applicable": eligible > 0,
        "eligible_classes": eligible,
        "contradictory_classes": len(signals),
        "score": None if eligible == 0 else round(1 - len(signals) / eligible, 4),
        "signals": signals,
    }
