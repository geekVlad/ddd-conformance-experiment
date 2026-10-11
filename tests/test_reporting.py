from ddd_conformance.reporting import summarize_roles


def test_summarize_roles_calculates_distribution_by_role() -> None:
    rows = [
        {"role": "entity", "lcom4": 1, "lcom4_eligible": True},
        {"role": "entity", "lcom4": 3, "lcom4_eligible": False},
        {"role": "infrastructure", "lcom4": 2, "lcom4_eligible": True},
    ]

    summary = summarize_roles(rows)

    assert summary["entity"] == {
        "classes": 2,
        "eligible_classes": 1,
        "lcom4_mean": 1.0,
        "lcom4_median": 1.0,
        "lcom4_p90": 1,
        "lcom4_max": 1,
        "lcom4_gt1": 0,
        "lcom4_gt1_pct": 0.0,
    }
    assert summary["infrastructure"]["classes"] == 1


def test_summarize_roles_supports_adjusted_lcom4() -> None:
    rows = [
        {
            "role": "value_object",
            "lcom4_adjusted": 1,
            "lcom4_adjusted_eligible": True,
        },
        {
            "role": "value_object",
            "lcom4_adjusted": 0,
            "lcom4_adjusted_eligible": False,
        },
    ]

    summary = summarize_roles(
        rows,
        metric="lcom4_adjusted",
        eligibility="lcom4_adjusted_eligible",
    )

    assert summary["value_object"]["eligible_classes"] == 1
    assert summary["value_object"]["lcom4_adjusted_median"] == 1.0
    assert summary["value_object"]["lcom4_adjusted_gt1_pct"] == 0.0
