from ddd_conformance.adapters.python import parse_python


def test_python_adapter_extracts_class_methods_fields_and_imports() -> None:
    source = """
from domain.shared import Money

class Order(AggregateRoot):
    def __init__(self, total: Money):
        self.total = total

    def confirm(self) -> None:
        if self.total:
            self.status = "confirmed"
"""

    unit = parse_python(source, path="sales/domain/order.py")

    assert unit.language == "python"
    assert unit.path == "sales/domain/order.py"
    assert unit.imports == ("domain.shared.Money",)
    assert len(unit.classes) == 1
    order = unit.classes[0]
    assert order.name == "Order"
    assert order.bases == ("AggregateRoot",)
    assert order.methods == ("__init__", "confirm")
    assert order.fields == ("status", "total")
    assert order.method_field_accesses == {
        "__init__": ("total",),
        "confirm": ("status", "total"),
    }


def test_python_adapter_extracts_internal_method_calls() -> None:
    unit = parse_python(
        """
class Order:
    def confirm(self):
        self.record_event()
    def record_event(self):
        self.events.append("confirmed")
""",
        path="order.py",
    )

    assert unit.classes[0].method_calls == {
        "confirm": ("record_event",),
        "record_event": (),
    }


def test_python_adapter_extracts_method_metadata() -> None:
    unit = parse_python(
        """
class Value:
    def __init__(self): self._value = 1
    @staticmethod
    def create(): return Value()
    @property
    def value(self): return self._value
    def run(self): self._value += 1
""",
        path="value.py",
    )

    value = unit.classes[0]
    assert value.constructors == ("__init__",)
    assert value.static_methods == ("create",)
    assert value.accessor_methods == ("value",)
