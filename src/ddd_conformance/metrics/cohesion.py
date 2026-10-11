from collections.abc import Iterable

from ddd_conformance.model import ClassUnit


def _component_count(unit: ClassUnit, methods: Iterable[str]) -> int:
    selected = tuple(methods)
    if not selected:
        return 0

    remaining = set(selected)
    field_sets = {
        method: set(unit.method_field_accesses.get(method, ())) for method in selected
    }
    call_sets = {
        method: set(unit.method_calls.get(method, ())) & remaining for method in selected
    }
    components = 0

    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            current = stack.pop()
            connected = {
                candidate
                for candidate in remaining
                if field_sets[current] & field_sets[candidate]
                or candidate in call_sets[current]
                or current in call_sets[candidate]
            }
            remaining.difference_update(connected)
            stack.extend(connected)

    return components


def adjusted_methods(unit: ClassUnit) -> tuple[str, ...]:
    """Return behavior methods used by adjusted LCOM4."""
    excluded = set(unit.constructors) | set(unit.static_methods) | set(unit.accessor_methods)
    return tuple(method for method in unit.methods if method not in excluded)


def lcom4(unit: ClassUnit) -> int:
    """Count connected components across every parsed method."""
    return _component_count(unit, unit.methods)


def lcom4_adjusted(unit: ClassUnit) -> int:
    """LCOM4 over instance behavior, excluding constructors, statics, and accessors."""
    return _component_count(unit, adjusted_methods(unit))
