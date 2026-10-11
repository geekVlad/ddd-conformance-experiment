from ddd_conformance.reporting import summarize_architecture_reports


def test_architecture_summary_uses_edge_weighted_scores() -> None:
    summary = summarize_architecture_reports(
        [
            {
                "id": "clean",
                "architecture": {
                    "dlpi": {
                        "applicable": True,
                        "observed_edges": 2,
                        "violating_edges": 0,
                        "score": 1.0,
                    },
                    "bcli": {
                        "applicable": True,
                        "observed_edges": 8,
                        "cross_context_edges": 2,
                        "score": 0.25,
                    },
                },
            },
            {
                "id": "leaky",
                "architecture": {
                    "dlpi": {
                        "applicable": True,
                        "observed_edges": 3,
                        "violating_edges": 1,
                        "score": 0.6667,
                    },
                    "bcli": {
                        "applicable": False,
                        "observed_edges": 0,
                        "cross_context_edges": 0,
                        "score": None,
                    },
                },
            },
        ]
    )

    assert summary == {
        "dlpi": {
            "applicable_repositories": 2,
            "observed_edges": 5,
            "violating_edges": 1,
            "score": 0.8,
        },
        "bcli": {
            "applicable_repositories": 1,
            "observed_edges": 8,
            "cross_context_edges": 2,
            "score": 0.25,
        },
    }
