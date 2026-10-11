import re
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class RoleClassification:
    role: str
    confidence: str
    rule: str


def _normalized(path: str) -> tuple[str, set[str]]:
    normalized = path.replace("\\", "/").lower()
    tokens = {
        token
        for part in PurePosixPath(normalized).parts
        for token in re.split(r"[^a-z0-9]+", part)
        if token
    }
    return normalized, tokens


def _result(role: str, confidence: str, rule: str) -> RoleClassification:
    return RoleClassification(role=role, confidence=confidence, rule=rule)


def classify_class_role(
    path: str, class_name: str, bases: tuple[str, ...] = ()
) -> RoleClassification:
    normalized, tokens = _normalized(path)
    lower_name = class_name.lower()
    base_roots = tuple(
        re.split(r"[<\[]", base, maxsplit=1)[0]
        .rsplit("\\", maxsplit=1)[-1]
        .rsplit(".", maxsplit=1)[-1]
        .lower()
        for base in bases
    )
    is_domain = "domain" in tokens
    is_infrastructure = bool(
        tokens
        & {
            "infrastructure",
            "infra",
            "adapter",
            "adapters",
            "persistence",
            "orm",
            "controller",
            "controllers",
            "api",
            "ui",
            "framework",
        }
    )

    if tokens & {"test", "tests", "spec", "specs", "behat", "fixture", "fixtures"} or re.search(
        r"(?:Test|Tests|Mock|Stub|Fake|Fixture)$", class_name
    ):
        return _result("test_support", "high", "test path or test-double class name")

    if "repository" in normalized or "repositories" in tokens or re.search(
        r"(?:Repository|Repositories|Storage)(?:Interface|Protocol)?$", class_name
    ):
        return _result("repository", "high", "repository/storage path or class name")

    if any("exception" in base or base.endswith("error") for base in base_roots):
        role = "domain_other" if is_domain else "other"
        return _result(role, "high", "exception/error inheritance")

    if is_domain and (
        "aggregate" in tokens
        or re.search(r"Aggregate(?:Root)?$", class_name)
        or any(base in {"aggregate", "aggregateroot"} for base in base_roots)
    ):
        return _result("aggregate", "high", "explicit aggregate path or class name")

    if re.search(r"value[-_]?objects?", normalized) or "valueobject" in lower_name or any(base.endswith("valueobject") for base in base_roots) or (
        "vo" in tokens and "domain" in tokens
    ):
        return _result("value_object", "high", "explicit value-object path or class name")

    if is_infrastructure:
        return _result("infrastructure", "high", "infrastructure/adapter/framework path")

    if is_domain and re.search(r"(?:Error|Exception)$", class_name):
        return _result("domain_other", "high", "domain error/exception is not a domain entity")

    if is_domain and (
        tokens & {"entity", "entities"}
        or re.search(r"Entity$", class_name)
        or any(base in {"entity", "domainentity"} for base in base_roots)
    ):
        return _result("entity", "high", "explicit entity path or class name")

    if is_domain and re.search(
        r"(?:DomainService|Service|Policy|Specification|Calculator|Manager|Validator)$",
        class_name,
    ):
        return _result("domain_service", "medium", "service-like class inside domain path")

    if (
        tokens & {"application", "usecase", "usecases", "interactor", "interactors", "handler", "handlers"}
        and re.search(r"(?:Handler|Service|UseCase|Interactor)$", class_name)
    ):
        return _result("application_service", "high", "application path and service/handler name")

    if tokens & {
        "command",
        "commands",
        "query",
        "queries",
        "event",
        "events",
        "dto",
        "dtos",
        "request",
        "requests",
        "response",
        "responses",
        "payload",
        "payloads",
        "projection",
        "projections",
        "readmodel",
    } or re.search(
        r"(?:Command|Query|Event|Dto|DTO|Request|Response|Payload|Projection|ReadModel)$",
        class_name,
    ):
        return _result("message_dto", "high", "message/DTO path or class name")

    if tokens & {"interface", "interfaces", "protocol", "protocols", "port", "ports", "contract", "contracts"} or re.search(
        r"(?:Interface|Protocol|Port|Contract|Definition)$", class_name
    ):
        return _result("interface_protocol", "high", "interface/protocol/port signal")


    if is_domain or tokens & {"model", "models"}:
        return _result("domain_other", "medium", "domain/model path without a more specific signal")

    return _result("other", "low", "no explicit role signal")
