import json
from pathlib import Path

from ddd_conformance.adjudication_sampling import build_stratified_candidates


def _write_semgrep_result(path: Path, findings: list[dict]) -> None:
    path.write_text(json.dumps({"results": findings}), encoding="utf-8")


def test_build_stratified_candidates_selects_one_per_rule_before_duplicates(tmp_path: Path):
    corpus = tmp_path / "corpus"
    (corpus / "repo-a" / "src/domain").mkdir(parents=True)
    (corpus / "repo-b" / "src/domain").mkdir(parents=True)
    (corpus / "repo-a" / "src/domain/order.py").write_text("from app.infrastructure.sql import Store\n")
    (corpus / "repo-b" / "src/domain/response.py").write_text("class OrderResponse:\n    pass\n")
    results = tmp_path / "results"
    results.mkdir()
    _write_semgrep_result(
        results / "repo-a.json",
        [
            {
                "check_id": "ddd-domain-imports-infrastructure",
                "path": str(corpus / "repo-a/src/domain/order.py"),
                "start": {"line": 1},
            }
        ],
    )
    _write_semgrep_result(
        results / "repo-b.json",
        [
            {
                "check_id": "ddd-domain-transport-type",
                "path": str(corpus / "repo-b/src/domain/response.py"),
                "start": {"line": 1},
            }
        ],
    )

    candidates = build_stratified_candidates(results, corpus, limit=2)

    assert [candidate["rule_id"] for candidate in candidates] == [
        "domain-imports-infrastructure",
        "domain-transport-type",
    ]
    assert candidates[0]["snippet"] == "from app.infrastructure.sql import Store"
    assert candidates[1]["repository"] == "repo-b"


def test_build_stratified_candidates_strips_semgrep_configuration_prefix(tmp_path: Path):
    corpus = tmp_path / "corpus"
    (corpus / "repo" / "src/domain").mkdir(parents=True)
    source = corpus / "repo" / "src/domain/order.py"
    source.write_text("from app.infrastructure.sql import Store\n")
    results = tmp_path / "results"
    results.mkdir()
    _write_semgrep_result(
        results / "repo.json",
        [{"check_id": "tools.semgrep.ddd-domain-imports-infrastructure", "path": str(source), "start": {"line": 1}}],
    )

    candidates = build_stratified_candidates(results, corpus, limit=1)

    assert candidates[0]["rule_id"] == "domain-imports-infrastructure"


def test_build_stratified_candidates_accepts_relative_paths(tmp_path: Path, monkeypatch):
    corpus = tmp_path / "corpus"
    (corpus / "repo" / "src/domain").mkdir(parents=True)
    source = corpus / "repo" / "src/domain/order.py"
    source.write_text("from app.infrastructure.sql import Store\n")
    results = tmp_path / "results"
    results.mkdir()
    _write_semgrep_result(
        results / "repo.json",
        [{"check_id": "ddd-domain-imports-infrastructure", "path": str(source), "start": {"line": 1}}],
    )
    monkeypatch.chdir(tmp_path)

    candidates = build_stratified_candidates(Path("results"), Path("corpus"), limit=1)

    assert candidates[0]["repository"] == "repo"
