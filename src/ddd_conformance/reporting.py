import math
import statistics
from collections import defaultdict
from collections.abc import Iterable


def summarize_roles(
    rows: Iterable[dict],
    *,
    metric: str = "lcom4",
    eligibility: str = "lcom4_eligible",
) -> dict[str, dict]:
    totals: dict[str, int] = defaultdict(int)
    eligible: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        role = row["role"]
        totals[role] += 1
        if row.get(eligibility, True):
            eligible[role].append(int(row[metric]))

    summary: dict[str, dict] = {}
    for role in sorted(totals):
        values = sorted(eligible[role])
        count = len(values)
        if not values:
            summary[role] = {
                "classes": totals[role],
                "eligible_classes": 0,
                f"{metric}_mean": None,
                f"{metric}_median": None,
                f"{metric}_p90": None,
                f"{metric}_max": None,
                f"{metric}_gt1": 0,
                f"{metric}_gt1_pct": None,
            }
            continue

        gt1 = sum(value > 1 for value in values)
        p90_index = max(0, math.ceil(0.9 * count) - 1)
        summary[role] = {
            "classes": totals[role],
            "eligible_classes": count,
            f"{metric}_mean": round(statistics.mean(values), 2),
            f"{metric}_median": float(statistics.median(values)),
            f"{metric}_p90": values[p90_index],
            f"{metric}_max": values[-1],
            f"{metric}_gt1": gt1,
            f"{metric}_gt1_pct": round(100 * gt1 / count, 1),
        }
    return summary


def summarize_architecture_reports(reports: Iterable[dict]) -> dict[str, dict]:
    """Aggregate DLPI/BCLI with edge-weighted scores across repositories."""
    dlpi = {"applicable_repositories": 0, "observed_edges": 0, "violating_edges": 0}
    bcli = {"applicable_repositories": 0, "observed_edges": 0, "cross_context_edges": 0}
    for report in reports:
        architecture = report["architecture"]
        for key, counters in (("dlpi", dlpi), ("bcli", bcli)):
            metric = architecture[key]
            if metric["applicable"]:
                counters["applicable_repositories"] += 1
            for counter in counters:
                if counter in metric:
                    counters[counter] += metric[counter]

    return {
        "dlpi": {
            **dlpi,
            "score": None
            if dlpi["observed_edges"] == 0
            else round(1 - dlpi["violating_edges"] / dlpi["observed_edges"], 4),
        },
        "bcli": {
            **bcli,
            "score": None
            if bcli["observed_edges"] == 0
            else round(bcli["cross_context_edges"] / bcli["observed_edges"], 4),
        },
    }


def summarize_semantic_reports(reports: Iterable[dict]) -> dict[str, dict]:
    """Aggregate SRPC with class-weighted scores across repositories."""
    applicable_repositories = 0
    eligible_classes = 0
    contradictory_classes = 0
    for report in reports:
        srpc = report["semantic"]["srpc"]
        if srpc["applicable"]:
            applicable_repositories += 1
        eligible_classes += srpc["eligible_classes"]
        contradictory_classes += srpc["contradictory_classes"]

    return {
        "srpc": {
            "applicable_repositories": applicable_repositories,
            "eligible_classes": eligible_classes,
            "contradictory_classes": contradictory_classes,
            "score": None
            if eligible_classes == 0
            else round(1 - contradictory_classes / eligible_classes, 4),
        }
    }
