import pytest

from ddd_conformance.classification import classify_class_role


@pytest.mark.parametrize(
    ("path", "class_name", "expected_role"),
    [
        ("src/Sylius/Behat/Page/Admin/Order/ShowPage.php", "ShowPage", "test_support"),
        ("sales/domain/aggregate/Order.php", "Order", "aggregate"),
        ("sales/domain/OrderAggregateRoot.ts", "OrderAggregateRoot", "aggregate"),
        ("sales/domain/value_objects/Money.py", "Money", "value_object"),
        ("sales/domain/UserEntity.ts", "UserEntity", "entity"),
        ("sales/domain/pricing/PriceCalculator.php", "PriceCalculator", "domain_service"),
        ("sales/application/CreateOrderHandler.php", "CreateOrderHandler", "application_service"),
        (
            "sales/infrastructure/persistence/DoctrineOrderRepository.php",
            "DoctrineOrderRepository",
            "repository",
        ),
        ("sales/domain/events/OrderCreated.php", "OrderCreatedEvent", "message_dto"),
        ("sales/domain/ports/PaymentGateway.php", "PaymentGatewayInterface", "interface_protocol"),
        ("sales/infrastructure/http/OrderController.php", "OrderController", "infrastructure"),
        ("sales/domain/model/Order.php", "Order", "domain_other"),
        ("src/helpers/DateFormatter.php", "DateFormatter", "other"),
        (
            "src/Sylius/Bundle/OrderBundle/Twig/AggregateAdjustmentsExtension.php",
            "AggregateAdjustmentsExtension",
            "other",
        ),
        ("src/modules/transaction/infra/entities/transaction.schema.ts", "Transaction", "infrastructure"),
        ("src/Validator/Constraints/HasEnabledEntity.php", "HasEnabledEntity", "other"),
    ],
)
def test_classifies_role_using_ordered_explicit_signals(
    path: str, class_name: str, expected_role: str
) -> None:
    result = classify_class_role(path, class_name)

    assert result.role == expected_role
    assert result.rule
    assert result.confidence in {"high", "medium", "low"}


def test_repository_rule_has_priority_over_interface_rule() -> None:
    result = classify_class_role(
        "sales/domain/repository/OrderRepositoryInterface.php",
        "OrderRepositoryInterface",
    )

    assert result.role == "repository"


def test_inheritance_identifies_aggregate_root_in_generic_entities_module() -> None:
    result = classify_class_role(
        "src/modules/bidding/domain/entities.py",
        "Listing",
        bases=("AggregateRoot[GenericUUID]",),
    )

    assert result.role == "aggregate"


def test_domain_exception_base_prevents_false_entity_label() -> None:
    result = classify_class_role(
        "src/modules/bidding/domain/entities.py",
        "BidCannotBeRetracted",
        bases=("DomainException",),
    )

    assert result.role == "domain_other"


def test_generic_type_arguments_do_not_override_the_actual_class_role() -> None:
    result = classify_class_role(
        "src/modules/transaction/infra/repo/transaction-calculation.mapper.ts",
        "TransactionCalculationToDomain",
        bases=("TMapper<ICalculation, TransactionCalculationValueObject>",),
    )

    assert result.role == "infrastructure"
