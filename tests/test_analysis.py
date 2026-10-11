from pathlib import Path

from ddd_conformance.analysis import analyze_repository


def test_repository_analysis_uses_language_adapters_and_reports_lcom4(tmp_path: Path) -> None:
    (tmp_path / "order.py").write_text(
        """
class Order:
    def add(self):
        self.items.append(1)
    def total(self):
        return len(self.items)
""",
        encoding="utf-8",
    )
    (tmp_path / "customer.ts").write_text(
        """
class Customer {
  private name: string;
  rename(): void { this.name = 'Alice'; }
}
""",
        encoding="utf-8",
    )
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "vendor.ts").write_text("class Vendor {}", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_order.py").write_text("class TestOrder: pass", encoding="utf-8")

    report = analyze_repository(tmp_path)

    assert report["summary"] == {
        "files_analyzed": 2,
        "parse_errors": 0,
        "classes": 2,
    }
    assert [(item["language"], item["class"], item["lcom4"]) for item in report["classes"]] == [
        ("typescript", "Customer", 1),
        ("python", "Order", 1),
    ]
    assert [item["lcom4_eligible"] for item in report["classes"]] == [False, True]
    assert [item["lcom4_adjusted"] for item in report["classes"]] == [1, 1]
    assert [item["behavior_methods"] for item in report["classes"]] == [1, 2]
    assert [item["lcom4_adjusted_eligible"] for item in report["classes"]] == [
        False,
        True,
    ]
    assert [(item["class"], item["role"]) for item in report["classes"]] == [
        ("Customer", "other"),
        ("Order", "other"),
    ]


def test_repository_analysis_includes_architecture_metrics(tmp_path: Path) -> None:
    domain = tmp_path / "contexts" / "orders" / "domain"
    domain.mkdir(parents=True)
    (domain / "order.py").write_text(
        "from contexts.orders.infrastructure.repository import Repository\n\nclass Order: pass\n",
        encoding="utf-8",
    )

    report = analyze_repository(tmp_path)

    assert report["architecture"]["dlpi"] == {
        "applicable": True,
        "observed_edges": 1,
        "violating_edges": 1,
        "score": 0.0,
    }


def test_repository_analysis_includes_semantic_role_placement_baseline(
    tmp_path: Path,
) -> None:
    domain = tmp_path / "domain"
    domain.mkdir()
    (domain / "OrderController.py").write_text("class OrderController: pass\n", encoding="utf-8")

    report = analyze_repository(tmp_path)

    assert report["semantic"]["srpc"]["score"] == 0.0
    assert report["semantic"]["srpc"]["contradictory_classes"] == 1
