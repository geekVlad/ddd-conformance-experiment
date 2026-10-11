"""Configuration-grounded LLM adjudication for DDD candidates."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from typing import Any
from urllib.request import Request, urlopen

VERDICTS = {"confirmed", "allowed", "uncertain"}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _response_schema() -> dict[str, list[str]]:
    return {
        "verdict": sorted(VERDICTS),
        "policy_rule": ["must match a configured allowed_rule_id"],
        "evidence": ["cite only supplied configuration and code"],
    }


def validate_adjudication(response: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an LLM result; `uncertain` is never promoted to a violation."""
    verdict = response.get("verdict")
    if verdict not in VERDICTS:
        raise ValueError("verdict must be confirmed, allowed, or uncertain")
    policy_rule = response.get("policy_rule")
    allowed_rule_ids = set(policy.get("allowed_rule_ids", []))
    if policy_rule not in allowed_rule_ids:
        raise ValueError("policy rule is not configured for this project")
    evidence = response.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("evidence is required")
    return {
        "verdict": verdict,
        "policy_rule": policy_rule,
        "evidence": evidence.strip(),
        "is_violation": verdict == "confirmed",
    }


def _build_request(candidate: Mapping[str, Any], policy: Mapping[str, Any], model: str) -> dict[str, Any]:
    system = (
        "You adjudicate a static DDD candidate only against supplied policy. "
        "Do not invent architecture policy. Return JSON matching the schema. "
        "Use uncertain when the policy or evidence is insufficient."
    )
    user = {"candidate": dict(candidate), "policy": dict(policy), "response_schema": _response_schema()}
    allowed_rule_ids = list(policy.get("allowed_rule_ids", []))
    api_schema = {
        "name": "ddd_adjudication",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": sorted(VERDICTS)},
                "policy_rule": {"type": "string", "enum": allowed_rule_ids},
                "evidence": {"type": "string", "minLength": 1},
            },
            "required": ["verdict", "policy_rule", "evidence"],
            "additionalProperties": False,
        },
    }
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_schema", "json_schema": api_schema},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": _canonical_json(user)},
        ],
        "response_schema": _response_schema(),
    }


def adjudicate_candidate(
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    model: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a deterministic request or call an OpenAI-compatible endpoint."""
    request = _build_request(candidate, policy, model)
    input_sha256 = hashlib.sha256(_canonical_json({"candidate": candidate, "policy": policy}).encode()).hexdigest()
    if dry_run:
        return {"mode": "dry_run", "input_sha256": input_sha256, "request": request}

    api_key = os.environ.get("EDUCATION_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("EDUCATION_OPENAI_API_KEY or OPENAI_API_KEY is required unless --dry-run is used")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    # `response_schema` is local validation metadata, not a Chat Completions parameter.
    api_request = {key: value for key, value in request.items() if key != "response_schema"}
    payload = json.dumps(api_request).encode()
    http_request = Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(http_request, timeout=60) as response:
        body = json.load(response)
    content = body["choices"][0]["message"]["content"]
    result = validate_adjudication(json.loads(content), policy)
    return {"mode": "live", "input_sha256": input_sha256, "model": model, "result": result}
