from ddd_conformance.metrics.cohesion import adjusted_methods, lcom4, lcom4_adjusted
from ddd_conformance.model import ClassUnit


def test_lcom4_is_one_when_methods_share_a_field() -> None:
    unit = ClassUnit(
        name="Order",
        methods=("add_item", "total"),
        fields=("items",),
        method_field_accesses={"add_item": ("items",), "total": ("items",)},
    )

    assert lcom4(unit) == 1


def test_lcom4_counts_disconnected_method_groups() -> None:
    unit = ClassUnit(
        name="MixedResponsibilities",
        methods=("add_item", "total", "send_email"),
        fields=("items", "mailer"),
        method_field_accesses={
            "add_item": ("items",),
            "total": ("items",),
            "send_email": ("mailer",),
        },
    )

    assert lcom4(unit) == 2


def test_lcom4_connects_methods_that_call_each_other() -> None:
    unit = ClassUnit(
        name="Order",
        methods=("confirm", "record_event"),
        fields=("events",),
        method_field_accesses={"confirm": (), "record_event": ("events",)},
        method_calls={"confirm": ("record_event",), "record_event": ()},
    )

    assert lcom4(unit) == 1


def test_lcom4_is_zero_for_class_without_methods() -> None:
    unit = ClassUnit(name="Marker", methods=(), fields=(), method_field_accesses={})

    assert lcom4(unit) == 0


def test_adjusted_lcom4_excludes_constructor_static_and_accessor_methods() -> None:
    unit = ClassUnit(
        name="Money",
        methods=("constructor", "create", "value", "increase", "decrease"),
        fields=("amount",),
        method_field_accesses={
            "constructor": ("amount",),
            "create": (),
            "value": ("amount",),
            "increase": ("amount",),
            "decrease": ("amount",),
        },
        constructors=("constructor",),
        static_methods=("create",),
        accessor_methods=("value",),
    )

    assert lcom4(unit) == 2
    assert adjusted_methods(unit) == ("increase", "decrease")
    assert lcom4_adjusted(unit) == 1


def test_adjusted_lcom4_is_zero_when_no_behavior_methods_remain() -> None:
    unit = ClassUnit(
        name="Identifier",
        methods=("constructor", "value"),
        fields=("value",),
        method_field_accesses={"constructor": ("value",), "value": ("value",)},
        constructors=("constructor",),
        accessor_methods=("value",),
    )

    assert adjusted_methods(unit) == ()
    assert lcom4_adjusted(unit) == 0
