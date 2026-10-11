from ddd_conformance.metrics.architecture import summarize_architecture
from ddd_conformance.model import SourceUnit


def source(path: str, *imports: str) -> SourceUnit:
    return SourceUnit(language="python", path=path, imports=imports, classes=())


def test_architecture_summary_detects_domain_to_infrastructure_dependency() -> None:
    result = summarize_architecture(
        [
            source(
                "src/contexts/orders/domain/order.py",
                "contexts.orders.domain.money",
                "contexts.orders.infrastructure.sql_repository",
            )
        ]
    )

    assert result["dlpi"] == {
        "applicable": True,
        "observed_edges": 2,
        "violating_edges": 1,
        "score": 0.5,
    }
    assert result["bcli"] == {
        "applicable": True,
        "observed_edges": 2,
        "cross_context_edges": 0,
        "score": 0.0,
    }
    assert result["edges"] == [
        {
            "source": "src/contexts/orders/domain/order.py",
            "import": "contexts.orders.domain.money",
            "source_layer": "domain",
            "target_layer": "domain",
            "source_context": "orders",
            "target_context": "orders",
        },
        {
            "source": "src/contexts/orders/domain/order.py",
            "import": "contexts.orders.infrastructure.sql_repository",
            "source_layer": "domain",
            "target_layer": "infrastructure",
            "source_context": "orders",
            "target_context": "orders",
        },
    ]


def test_architecture_summary_detects_cross_context_import_but_excludes_shared() -> None:
    result = summarize_architecture(
        [
            source(
                "src/modules/orders/application/place_order.py",
                "modules.orders.domain.order",
                "modules.inventory.application.stock",
                "modules.shared.domain.money",
            )
        ]
    )

    assert result["bcli"] == {
        "applicable": True,
        "observed_edges": 2,
        "cross_context_edges": 1,
        "score": 0.5,
    }


def test_architecture_summary_returns_not_applicable_for_unresolved_imports() -> None:
    result = summarize_architecture(
        [source("src/domain/order.py", "requests", "typing.Optional")]
    )

    assert result["dlpi"] == {
        "applicable": False,
        "observed_edges": 0,
        "violating_edges": 0,
        "score": None,
    }
