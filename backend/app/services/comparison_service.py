from typing import List
from app.schemas import (
    ContractAnalysis,
    ClauseComparison,
    ClauseStatus,
    ContractComparison,
)


def compare_contracts(
    comparison_id: str,
    analysis_a: ContractAnalysis,
    analysis_b: ContractAnalysis,
    name_a: str,
    name_b: str,
) -> ContractComparison:
    types_a = {}
    for c in analysis_a.clauses:
        key = c.clause_type.lower().strip()
        if key not in types_a:
            types_a[key] = c

    types_b = {}
    for c in analysis_b.clauses:
        key = c.clause_type.lower().strip()
        if key not in types_b:
            types_b[key] = c

    all_types = sorted(set(list(types_a.keys()) + list(types_b.keys())))
    comparisons: List[ClauseComparison] = []

    for ctype in all_types:
        ca = types_a.get(ctype)
        cb = types_b.get(ctype)

        if ca and cb:
            delta = cb.risk_score - ca.risk_score
            if delta > 10:
                status = ClauseStatus.WORSENED
            elif delta < -10:
                status = ClauseStatus.IMPROVED
            else:
                status = ClauseStatus.UNCHANGED
        elif ca and not cb:
            delta = 0
            status = ClauseStatus.REMOVED
        else:
            delta = 0
            status = ClauseStatus.ADDED

        comparisons.append(ClauseComparison(
            clause_type=ctype.title(),
            clause_a=ca,
            clause_b=cb,
            risk_delta=delta,
            status=status,
        ))

    overall_delta = analysis_b.overall_risk_score - analysis_a.overall_risk_score
    if overall_delta > 5:
        winner = "a"
    elif overall_delta < -5:
        winner = "b"
    else:
        winner = "equal"

    return ContractComparison(
        comparison_id=comparison_id,
        contract_a_name=name_a,
        contract_b_name=name_b,
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        overall_delta=overall_delta,
        winner=winner,
        clause_comparisons=comparisons,
        key_differences=_key_differences(comparisons),
    )


def _key_differences(comparisons: List[ClauseComparison]) -> List[str]:
    diffs = []
    worsened = sorted(
        [c for c in comparisons if c.status == ClauseStatus.WORSENED],
        key=lambda x: x.risk_delta, reverse=True,
    )
    improved = sorted(
        [c for c in comparisons if c.status == ClauseStatus.IMPROVED],
        key=lambda x: x.risk_delta,
    )
    added = [c for c in comparisons if c.status == ClauseStatus.ADDED]
    removed = [c for c in comparisons if c.status == ClauseStatus.REMOVED]

    for c in worsened[:2]:
        diffs.append(f"{c.clause_type}: Contract B scores +{c.risk_delta} pts higher risk")
    for c in improved[:2]:
        diffs.append(f"{c.clause_type}: Contract B scores {c.risk_delta} pts lower risk")
    for c in added[:2]:
        diffs.append(f"{c.clause_type}: Present only in Contract B")
    for c in removed[:2]:
        diffs.append(f"{c.clause_type}: Present only in Contract A")

    return diffs[:6]
