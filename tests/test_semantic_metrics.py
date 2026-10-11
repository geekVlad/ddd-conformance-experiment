from ddd_conformance.metrics.semantic import summarize_srpc


def test_srpc_reports_domain_transport_contradiction() -> None:
    result = summarize_srpc(
        [
            {"path": "src/domain/OrderController.py", "class": "OrderController"},
            {"path": "src/domain/Order.py", "class": "Order"},
            {"path": "tests/domain/OrderTest.py", "class": "OrderTest"},
        ]
    )

    assert result == {
        "applicable": True,
        "eligible_classes": 2,
        "contradictory_classes": 1,
        "score": 0.5,
        "signals": [
            {
                "path": "src/domain/OrderController.py",
                "class": "OrderController",
                "path_layer": "domain",
                "name_hint": "controller",
                "rule": "domain path with infrastructure/transport/application name",
            }
        ],
    }


def test_srpc_reports_infrastructure_domain_model_contradiction() -> None:
    result = summarize_srpc(
        [{"path": "src/infrastructure/OrderAggregate.py", "class": "OrderAggregate"}]
    )

    assert result["score"] == 0.0
    assert result["signals"][0]["name_hint"] == "aggregate"


def test_srpc_does_not_penalize_domain_event_or_test_support() -> None:
    result = summarize_srpc(
        [
            {"path": "src/domain/OrderCreatedEvent.py", "class": "OrderCreatedEvent"},
            {"path": "tests/OrderControllerTest.py", "class": "OrderControllerTest"},
        ]
    )

    assert result == {
        "applicable": True,
        "eligible_classes": 1,
        "contradictory_classes": 0,
        "score": 1.0,
        "signals": [],
    }


def test_srpc_does_not_penalize_domain_repository_port_or_application_dto() -> None:
    result = summarize_srpc(
        [
            {"path": "src/domain/OrderRepository.py", "class": "OrderRepository"},
            {"path": "src/application/CreateOrderDto.py", "class": "CreateOrderDto"},
        ]
    )

    assert result["score"] == 1.0
    assert result["signals"] == []
