"""
Mission Outcome KPIs — Briefing-Ready Performance Indicators

Aggregates task-level outcomes from TwinRunner day states into mission-summary
KPIs suitable for management review and decision support.

Design contract:
    Reads:  List[DayState] — task_outcomes field only
    Writes: MissionKPIs dataclass
    Never:  accesses agent state, beliefs, physics, or any simulation internals

KPI definitions:
    critical_task_completion_rate —
        Fraction of high-criticality task instances completed without failure.
        High-criticality tasks: eva_prep_checklist, habitat_repair_plan,
        navigation_recalculation, science_sequence_handoff.

    eva_readiness_proxy —
        Success rate of attention + planning tasks (EVA preparation, multi-step
        planning). Proxy for crew readiness for high-consequence extravehicular
        activity where attentional and planning lapses are most consequential.

    comms_reliability_proxy —
        Success rate of coordination tasks (joint handoffs, team communication).
        Proxy for crew-MC and intra-crew communication reliability under
        psychophysiological degradation.

    maintenance_backlog —
        Cumulative count of SKIPPED persistence tasks across the mission.
        Each skip = one deferred maintenance action. Grows monotonically.

    rework_hours_proxy —
        Criticality-weighted count of ERROR outcomes (high=3, medium=2, low=1).
        Proxy for total mission rework cost in notional hours.
"""

from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# MissionKPIs dataclass
# ---------------------------------------------------------------------------

@dataclass
class MissionKPIs:
    """
    Briefing-ready mission performance indicators.

    All rates are fractions (0–1). Backlog and rework counts are absolute.
    Phase breakdown divides mission into equal thirds for trend analysis.
    """
    total_days: int

    # Mission-level aggregates
    critical_task_completion_rate: float
    eva_readiness_proxy:           float
    comms_reliability_proxy:       float
    maintenance_backlog:           int
    rework_hours_proxy:            float

    # Phase breakdown: equal thirds of mission length
    early_critical_completion: float   # Days 1 to T//3
    tq_critical_completion:    float   # Days T//3+1 to 2*T//3
    late_critical_completion:  float   # Days 2*T//3+1 to T

    def to_dict(self) -> dict:
        return {
            "total_days": self.total_days,
            "mission_performance": {
                "critical_task_completion_rate": round(self.critical_task_completion_rate, 4),
                "eva_readiness_proxy":           round(self.eva_readiness_proxy, 4),
                "comms_reliability_proxy":       round(self.comms_reliability_proxy, 4),
                "maintenance_backlog":           self.maintenance_backlog,
                "rework_hours_proxy":            round(self.rework_hours_proxy, 2),
            },
            "phase_breakdown": {
                "early_critical_completion": round(self.early_critical_completion, 4),
                "tq_critical_completion":    round(self.tq_critical_completion, 4),
                "late_critical_completion":  round(self.late_critical_completion, 4),
            },
        }


# ---------------------------------------------------------------------------
# KPI computation
# ---------------------------------------------------------------------------

def compute_kpis(day_states: list) -> Optional[MissionKPIs]:
    """
    Compute mission KPIs from a list of TwinRunner DayState objects.

    Args:
        day_states: List of DayState objects from TwinRunner.run()

    Returns:
        MissionKPIs, or None if no task outcome data is present in day_states.
    """
    if not day_states:
        return None

    T = len(day_states)

    # Phase boundaries: equal thirds of mission
    early_end = T // 3
    tq_end    = (2 * T) // 3

    # Criticality → rework weight
    _crit_weight = {"high": 3, "medium": 2, "low": 1}

    # Accumulation lists
    critical_results: List[bool] = []
    eva_results:      List[bool] = []
    coord_results:    List[bool] = []
    backlog = 0
    rework_hours = 0.0

    early_critical: List[bool] = []
    tq_critical:    List[bool] = []
    late_critical:  List[bool] = []

    has_data = False

    for ds in day_states:
        to = ds.task_outcomes
        if to is None:
            continue
        task_results = to.get("task_results", [])
        if not task_results:
            continue

        has_data = True
        day = ds.day

        for tr in task_results:
            outcome = tr["outcome"]
            crit    = tr["criticality"]
            vuln    = tr["vulnerability"]
            is_ok   = (outcome == "completed")

            # Critical task completion
            if crit == "high":
                critical_results.append(is_ok)
                if day <= early_end:
                    early_critical.append(is_ok)
                elif day <= tq_end:
                    tq_critical.append(is_ok)
                else:
                    late_critical.append(is_ok)

            # EVA readiness: attention + planning tasks
            if vuln in ("attention", "planning"):
                eva_results.append(is_ok)

            # Comms reliability: coordination tasks
            if vuln == "coordination":
                coord_results.append(is_ok)

            # Maintenance backlog: skipped persistence tasks
            if vuln == "persistence" and outcome == "skipped":
                backlog += 1

            # Rework proxy: criticality-weighted error count
            if outcome == "error":
                rework_hours += _crit_weight.get(crit, 1)

    if not has_data:
        return None

    def _rate(lst: List[bool]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    return MissionKPIs(
        total_days=T,
        critical_task_completion_rate=_rate(critical_results),
        eva_readiness_proxy=_rate(eva_results),
        comms_reliability_proxy=_rate(coord_results),
        maintenance_backlog=backlog,
        rework_hours_proxy=rework_hours,
        early_critical_completion=_rate(early_critical),
        tq_critical_completion=_rate(tq_critical),
        late_critical_completion=_rate(late_critical),
    )
