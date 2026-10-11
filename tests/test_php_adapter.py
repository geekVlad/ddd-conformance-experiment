from ddd_conformance.adapters.php import parse_php


def test_php_adapter_extracts_class_methods_fields_and_imports() -> None:
    source = """<?php
namespace Sales\\Domain;
use Shared\\Money;

final class Order extends AggregateRoot
{
    private Money $total;

    public function confirm(): void
    {
        $this->total = new Money();
    }
}
"""

    unit = parse_php(source, path="src/Sales/Domain/Order.php")

    assert unit.language == "php"
    assert unit.imports == ("Shared\\Money",)
    assert len(unit.classes) == 1
    order = unit.classes[0]
    assert order.name == "Order"
    assert order.bases == ("AggregateRoot",)
    assert order.methods == ("confirm",)
    assert order.fields == ("total",)
    assert order.method_field_accesses == {"confirm": ("total",)}


def test_php_adapter_extracts_internal_method_calls() -> None:
    unit = parse_php(
        "<?php class Order { function confirm(){ $this->recordEvent(); } function recordEvent(){ $this->events = []; } }",
        path="Order.php",
    )

    assert unit.classes[0].method_calls == {
        "confirm": ("recordEvent",),
        "recordEvent": (),
    }


def test_php_adapter_extracts_method_metadata() -> None:
    unit = parse_php(
        "<?php class Value { public function __construct(){} public static function create(){ return new self(); } public function getValue(){ return $this->value; } public function run(){ $this->value++; } }",
        path="Value.php",
    )

    value = unit.classes[0]
    assert value.constructors == ("__construct",)
    assert value.static_methods == ("create",)
    assert value.accessor_methods == ("getValue",)
