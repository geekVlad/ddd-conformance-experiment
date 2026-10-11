from pathlib import Path

from ddd_conformance.policy_induction import infer_policy


def test_infer_policy_discovers_context_layers_and_evidence(tmp_path: Path):
    repository = tmp_path / "shop"
    for relative_path in (
        "src/modules/billing/domain/invoice.py",
        "src/modules/billing/application/create_invoice.py",
        "src/modules/billing/infrastructure/sql_repository.py",
        "src/modules/shipping/domain/shipment.py",
        "src/modules/shipping/adapters/http.py",
    ):
        source = repository / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("pass\n", encoding="utf-8")

    policy = infer_policy(repository, project="shop", revision="abc123")

    assert policy["project"] == "shop"
    assert policy["revision"] == "abc123"
    assert policy["inference"]["kind"] == "path-convention"
    assert policy["inference"]["confidence"] == "hypothesis"
    contexts = {context["name"]: context for context in policy["contexts"]}
    assert contexts["billing"]["domain_paths"] == ["src/modules/billing/domain/**"]
    assert contexts["billing"]["application_paths"] == ["src/modules/billing/application/**"]
    assert contexts["billing"]["infrastructure_paths"] == ["src/modules/billing/infrastructure/**"]
    assert contexts["shipping"]["domain_paths"] == ["src/modules/shipping/domain/**"]
    assert contexts["shipping"]["infrastructure_paths"] == ["src/modules/shipping/adapters/**"]
    assert policy["rules"][0]["id"] == "domain-imports-infrastructure"
    assert policy["allowed_rule_ids"] == [
        "domain-imports-infrastructure",
        "domain-transport-type",
        "cross-context-import",
    ]


def test_infer_policy_ignores_dependency_directories(tmp_path: Path):
    repository = tmp_path / "shop"
    own_source = repository / "src/modules/billing/domain/invoice.py"
    dependency_source = repository / "vendor/package/domain/ignored.php"
    for source in (own_source, dependency_source):
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("pass\n", encoding="utf-8")

    policy = infer_policy(repository, project="shop", revision="abc123")

    assert [context["name"] for context in policy["contexts"]] == ["billing"]
