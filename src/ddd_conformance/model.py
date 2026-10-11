from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClassUnit:
    name: str
    methods: tuple[str, ...]
    fields: tuple[str, ...]
    method_field_accesses: dict[str, tuple[str, ...]]
    method_calls: dict[str, tuple[str, ...]] = field(default_factory=dict)
    bases: tuple[str, ...] = ()
    constructors: tuple[str, ...] = ()
    static_methods: tuple[str, ...] = ()
    accessor_methods: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceUnit:
    language: str
    path: str
    imports: tuple[str, ...]
    classes: tuple[ClassUnit, ...]
