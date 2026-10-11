from ddd_conformance.reporting import summarize_semantic_reports


def test_semantic_summary_is_weighted_by_eligible_classes() -> None:
    summary = summarize_semantic_reports(
        [
            {
                "semantic": {
                    "srpc": {
                        "applicable": True,
                        "eligible_classes": 2,
                        "contradictory_classes": 1,
                        "score": 0.5,
                    }
                }
            },
            {
                "semantic": {
                    "srpc": {
                        "applicable": True,
                        "eligible_classes": 8,
                        "contradictory_classes": 1,
                        "score": 0.875,
                    }
                }
            },
        ]
    )

    assert summary == {
        "srpc": {
            "applicable_repositories": 2,
            "eligible_classes": 10,
            "contradictory_classes": 2,
            "score": 0.8,
        }
    }
