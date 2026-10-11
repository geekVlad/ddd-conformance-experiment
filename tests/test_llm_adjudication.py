import pytest

from ddd_conformance.llm_adjudication import adjudicate_candidate, validate_adjudication

CANDIDATE = {
    "rule_id": "domain-import-infrastructure",
    "path": "src/domain/order.py",
    "line": 12,
    "snippet": "from app.infrastructure.sql import OrderStore",
    "dependency": "app.infrastructure.sql.OrderStore",
}
POLICY = {
    "project": "fixture",
    "allowed_rule_ids": ["domain-import-infrastructure"],
    "architecture": {"domain": ["src/domain"], "infrastructure": ["src/infrastructure"]},
}


def test_adjudication_accepts_config_grounded_confirmed_verdict():
    result = validate_adjudication(
        {
            "verdict": "confirmed",
            "policy_rule": "domain-import-infrastructure",
            "evidence": "The import targets the configured infrastructure namespace.",
        },
        POLICY,
    )

    assert result["verdict"] == "confirmed"


def test_adjudication_rejects_unknown_policy_rule():
    with pytest.raises(ValueError, match="policy rule"):
        validate_adjudication(
            {"verdict": "confirmed", "policy_rule": "invented", "evidence": "x"}, POLICY
        )


def test_uncertain_is_not_a_violation():
    result = validate_adjudication(
        {
            "verdict": "uncertain",
            "policy_rule": "domain-import-infrastructure",
            "evidence": "The configuration does not classify this shared module.",
        },
        POLICY,
    )

    assert result["is_violation"] is False


def test_dry_run_produces_a_reproducible_request_without_network():
    result = adjudicate_candidate(CANDIDATE, POLICY, model="test-model", dry_run=True)

    assert result["mode"] == "dry_run"
    assert result["input_sha256"]
    assert result["request"]["model"] == "test-model"
    assert "confirmed" in result["request"]["response_schema"]["verdict"]
