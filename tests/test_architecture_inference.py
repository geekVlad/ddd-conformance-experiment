from pathlib import Path

from ddd_conformance.architecture_inference import analyze_repository


def _source(root: Path, relative: str, text: str = "pass\n") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_architecture_agent_uses_layers_packages_and_fallback_contexts(tmp_path: Path):
    repository = tmp_path / "mixed"
    _source(repository, "src/modules/billing/domain/invoice.py")
    _source(repository, "src/modules/billing/adapters/http.py")
    _source(repository, "libs/repo-orm/src/database/mongo/client.ts")
    _source(repository, "src/Projecting/Projector.php")
    _source(repository, "vendor/package/domain/ignored.php")

    result = analyze_repository(repository, project="mixed", revision="abc123")

    contexts = {context["name"]: context for context in result["contexts"]}
    assert contexts["billing"]["role_counts"] == {"adapter": 1, "domain": 1}
    assert contexts["repo-orm"]["role_counts"] == {"infrastructure": 1}
    assert contexts["Projecting"]["role_counts"] == {"application": 1}
    assert result["coverage"] == 1.0
    assert result["policy"]["inference"]["kind"] == "multi-signal-path-role"
    assert all("ignored" not in str(context) for context in result["contexts"])


def test_architecture_agent_policy_is_not_file_specific(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/modules/billing/domain/invoice.py")
    _source(repository, "src/modules/billing/domain/payment.py")

    result = analyze_repository(repository, project="shop", revision="abc123")

    policy_context = result["policy"]["contexts"][0]
    assert policy_context["domain_paths"] == ["src/modules/billing/domain/**"]
    assert policy_context["evidence_file_count"] == 2


def test_architecture_agent_counts_import_evidence(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/domain/order.py", "from shop.adapters.sql import Store\n")
    _source(repository, "src/application/handler.ts", "import { Store } from '../infrastructure/store';\n")

    result = analyze_repository(repository, project="shop", revision="abc123")

    assert result["import_edge_count"] == 2


def test_architecture_agent_assigns_other_support_instead_of_unknown(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/misc/clock.php")

    result = analyze_repository(repository, project="shop", revision="abc123")

    assert result["coverage"] == 1.0
    assert result["semantic_role_coverage"] == 0.0
    assert result["contexts"][0]["role_counts"] == {"other_support": 1}


def test_architecture_agent_classifies_support_and_dependency_edges(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/common/clock.php")
    _source(repository, "src/config/settings.py")
    _source(repository, "src/application/handler.ts", "import { Store } from '../infrastructure/store';\n")
    _source(repository, "src/infrastructure/store.ts")

    result = analyze_repository(repository, project="shop", revision="abc123")

    roles = {record["path"]: record["role"] for record in result["files"]}
    assert roles["src/common/clock.php"] == "utility"
    assert roles["src/config/settings.py"] == "configuration"
    assert result["edges"] == [
        {
            "source": "src/application/handler.ts",
            "target": "src/infrastructure/store.ts",
            "source_context": "application",
            "target_context": "infrastructure",
            "source_role": "application",
            "target_role": "infrastructure",
            "verdict": "allowed",
            "confidence": "high",
        }
    ]


def test_architecture_agent_classifies_specific_support_roles(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/framework/kernel.php")
    _source(repository, "src/generated/client.php")
    _source(repository, "src/migrations/one.php")
    _source(repository, "src/cli/reindex.php")
    _source(repository, "src/integration/payment.php")
    _source(repository, "src/read_model/dashboard.php")
    _source(repository, "src/shared/clock.php")

    result = analyze_repository(repository, project="shop", revision="abc123")

    roles = {record["path"]: record["role"] for record in result["files"]}
    assert roles == {
        "src/cli/reindex.php": "cli",
        "src/framework/kernel.php": "framework",
        "src/generated/client.php": "generated",
        "src/integration/payment.php": "integration",
        "src/migrations/one.php": "migration",
        "src/read_model/dashboard.php": "read_model",
        "src/shared/clock.php": "shared_kernel_candidate",
    }


def test_architecture_agent_marks_cross_context_domain_edge_low_confidence(tmp_path: Path):
    repository = tmp_path / "shop"
    _source(repository, "src/modules/orders/domain/order.ts", "import { Payment } from '../../payments/domain/payment';\n")
    _source(repository, "src/modules/payments/domain/payment.ts")

    result = analyze_repository(repository, project="shop", revision="abc123")

    assert result["edges"][0]["verdict"] == "low_confidence"
    assert result["edges"][0]["confidence"] == "medium"
