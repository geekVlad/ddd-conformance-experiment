from ddd_conformance.adapters.typescript import parse_typescript


def test_typescript_adapter_extracts_class_methods_fields_and_imports() -> None:
    source = """
import { Money } from "../shared/money";

export class Order extends AggregateRoot {
    private total: Money;

    confirm(): void {
        this.total = new Money();
    }
}
"""

    unit = parse_typescript(source, path="sales/domain/order.ts")

    assert unit.language == "typescript"
    assert unit.imports == ("../shared/money",)
    assert len(unit.classes) == 1
    order = unit.classes[0]
    assert order.name == "Order"
    assert order.bases == ("AggregateRoot",)
    assert order.methods == ("confirm",)
    assert order.fields == ("total",)
    assert order.method_field_accesses == {"confirm": ("total",)}


def test_typescript_adapter_extracts_internal_method_calls() -> None:
    unit = parse_typescript(
        "class Order { confirm(){ this.recordEvent(); } recordEvent(){ this.events = []; } }",
        path="order.ts",
    )

    assert unit.classes[0].method_calls == {
        "confirm": ("recordEvent",),
        "recordEvent": (),
    }


def test_typescript_adapter_extracts_method_metadata() -> None:
    unit = parse_typescript(
        "class Value { constructor(){} static create(){ return new Value(); } get value(){ return this.x; } run(){ this.x++; } }",
        path="value.ts",
    )

    value = unit.classes[0]
    assert value.constructors == ("constructor",)
    assert value.static_methods == ("create",)
    assert value.accessor_methods == ("value",)


def test_typescript_adapter_uses_tsx_grammar_for_tsx_files() -> None:
    unit = parse_typescript(
        "export const App = () => <main><span>DDD</span></main>;",
        path="frontend/App.tsx",
    )

    assert unit.language == "typescript"
    assert unit.classes == ()
