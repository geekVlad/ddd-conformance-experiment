"""Path-and-import baseline metrics for DDD architectural boundaries."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ddd_conformance.model import SourceUnit

_CONTEXT_ROOTS = {"contexts", "modules", "bounded_contexts", "bounded-contexts"}
_SHARED_CONTEXTS = {"shared", "common", "core"}
_LAYER_MARKERS = {
    "domain": "domain",
    "application": "application",
    "infrastructure": "infrastructure",
    "infra": "infrastructure",
    "adapter": "infrastructure",
    "adapters": "infrastructure",
    "persistence": "infrastructure",
    "controller": "infrastructure",
    "controllers": "infrastructure",
    "api": "infrastructure",
    "ui": "infrastructure",
    "framework": "infrastructure",
}


def _segments(value: str) -> tuple[str, ...]:
    return tuple(part.lower() for part in re.split(r"[./\\:]+", value) if part)


def _context(value: str) -> str | None:
    segments = _segments(value)
    for index, segment in enumerate(segments[:-1]):
        if segment in _CONTEXT_ROOTS:
            return segments[index + 1]
    return None


def _layer(value: str) -> str:
    for segment in _segments(value):
        if layer := _LAYER_MARKERS.get(segment):
            return layer
    return "other"


def _score(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def summarize_architecture(units: Iterable[SourceUnit]) -> dict:
    """Return observed DLPI and BCLI signals from normalized import statements."""
    dlpi_observed = 0
    dlpi_violating = 0
    bcli_observed = 0
    bcli_cross = 0
    edges: list[dict[str, str]] = []

    for unit in units:
        source_layer = _layer(unit.path)
        source_context = _context(unit.path)
        for imported in unit.imports:
            target_layer = _layer(imported)
            target_context = _context(imported)

            is_dlpi_edge = source_layer == "domain" and target_layer in {
                "domain",
                "application",
                "infrastructure",
            }
            is_bcli_edge = (
                source_context is not None
                and target_context is not None
                and target_context not in _SHARED_CONTEXTS
            )
            if is_dlpi_edge:
                dlpi_observed += 1
                if target_layer != "domain":
                    dlpi_violating += 1

            if is_bcli_edge:
                bcli_observed += 1
                if source_context != target_context:
                    bcli_cross += 1

            if is_dlpi_edge or is_bcli_edge:
                edges.append(
                    {
                        "source": unit.path,
                        "import": imported,
                        "source_layer": source_layer,
                        "target_layer": target_layer,
                        "source_context": source_context or "",
                        "target_context": target_context or "",
                    }
                )

    dlpi_violation_rate = _score(dlpi_violating, dlpi_observed)
    return {
        "dlpi": {
            "applicable": dlpi_violation_rate is not None,
            "observed_edges": dlpi_observed,
            "violating_edges": dlpi_violating,
            "score": None
            if dlpi_violation_rate is None
            else round(1 - dlpi_violation_rate, 4),
        },
        "bcli": {
            "applicable": bcli_observed > 0,
            "observed_edges": bcli_observed,
            "cross_context_edges": bcli_cross,
            "score": _score(bcli_cross, bcli_observed),
        },
        "edges": edges,
    }
