"""
Task Performance Layer — Mission Risk Integration

Translates physics-layer accumulation variables into observable task-level
failure outcomes.

This layer is READ-ONLY with respect to agent state. It derives operational
risk metrics from existing simulation outputs and does not write to beliefs,
internal state, or physics.

Design contract:
    Reads:  core_strain, core_monotony, sleep_quality, circadian_drift,
            per_agent_impairment (from TwinRunner._run_day),
            prior_day_outcomes (optional, for task dependency graph)
    Writes: DayTaskOutcomes (per-day performance log, attached to DayState)
    Never:  modifies agent state, beliefs, or physics inputs

Input variable rationale:
    core_strain         — physics-layer accumulated strain (0–~0.25): drives
                          executive function impairment → coordination errors
    core_monotony       — physics-layer monotony accumulation (0–1): drives
                          persistence failure → maintenance avoidance
    sleep_quality       — resource-layer sleep conditions (0–1): drives
                          attentional failure → checklist misses
    circadian_drift     — accumulated circadian baseline erosion: causal trace
                          node between chronic sleep disruption and attention
    per_agent_impairment — Dict[agent_id, composite_impairment]; for
                          coordination tasks, max over agents (weakest-link)
                          amplifies base fail_prob via COORD_WEAKEST_LINK_AMP
    prior_day_outcomes  — Optional[DayTaskOutcomes]; if provided, dependent
                          tasks receive a fail_prob penalty when their
                          prerequisite task failed the previous day

Failure probability equations (all coefficients from params.py):
    attention:    fail_prob = core_monotony × ATTN_MONOTONY_WEIGHT
                            + sleep_deficit × ATTN_SLEEP_DEFICIT_WEIGHT
                            [+ dependency penalty if upstream task failed]
    coordination: fail_prob = core_strain × COORD_STRAIN_WEIGHT
                            × (1 + max_agent_impairment × COORD_WEAKEST_LINK_AMP)
                            [+ dependency penalty if upstream task failed]
    planning:     fail_prob = core_strain × PLAN_STRAIN_WEIGHT
                            [+ dependency penalty if upstream task failed]
    persistence:  fail_prob = core_monotony × PERSIST_MONOTONY_WEIGHT

Causal failure traces:
    Each non-completed task records its causal chain:
        sleep_quality → circadian_drift → impairment_channel → task outcome
    For coordination tasks: weakest_link_agent and max_agent_impairment included.
    For tasks with dependency penalties: upstream_task_id and penalty included.

Task dependency graph:
    Some tasks depend on other tasks scheduled within the daily rotation.
    If a prerequisite task failed on DAY N-1, the dependent task on DAY N
    receives an elevated fail_prob:
        SOFT failure (delayed/skipped): +DEPENDENCY_FAIL_PENALTY_SOFT
        HARD failure (error):           +DEPENDENCY_FAIL_PENALTY_HARD
    Rationale: incomplete or corrupted outputs from one task degrade the
    information or environmental conditions available to the next task.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from params import (
    ATTN_MONOTONY_WEIGHT, ATTN_SLEEP_DEFICIT_WEIGHT,
    ATTN_SLEEP_BASELINE, ATTN_SLEEP_DEFICIT_RANGE, ATTN_DELAY_PROB,
    COORD_STRAIN_WEIGHT, COORD_WEAKEST_LINK_AMP,
    PLAN_STRAIN_WEIGHT, PLAN_DELAY_PROB,
    PERSIST_MONOTONY_WEIGHT,
    TASK_RNG_SEED_OFFSET,
    DEPENDENCY_FAIL_PENALTY_SOFT, DEPENDENCY_FAIL_PENALTY_HARD,
)


# ---------------------------------------------------------------------------
# Task Ontology
# ---------------------------------------------------------------------------

@dataclass
class MissionTask:
    """
    A classified mission activity.

    Vulnerability determines which impairment channel degrades performance:
        attention    — circadian drift:    sleep fragmentation → attentional lapses
        planning     — exec_impairment:    multi-step planning → errors and latency
        coordination — exec_impairment:    joint action/handoffs → breakdown
        persistence  — burnout:            sustained effort → avoidance and skips

    depends_on: list of task_ids that this task relies on.
        If a prerequisite task failed on the previous day, this task receives
        an elevated fail_prob (DEPENDENCY_FAIL_PENALTY_SOFT or _HARD).
        Rationale: incomplete or corrupted upstream outputs degrade the
        information or conditions available to the downstream task.
    """
    task_id: str
    criticality: str     # low | medium | high
    execution_mode: str  # solo | coordination
    vulnerability: str   # attention | planning | persistence | coordination
    depends_on: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mission Task Catalogue
# ---------------------------------------------------------------------------

MISSION_TASK_CATALOGUE: List[MissionTask] = [
    # High criticality
    MissionTask("eva_prep_checklist",        "high",   "solo",         "attention"),
    MissionTask("habitat_repair_plan",       "high",   "solo",         "planning",
                depends_on=["equipment_inspection"]),
    # If equipment_inspection was skipped, the repair plan is built on incomplete
    # diagnostics — higher probability of planning errors.
    MissionTask("navigation_recalculation",  "high",   "solo",         "planning",
                depends_on=["comms_window_prep"]),
    # Fresh navigation data arrives via the comms window; if that prep failed,
    # nav recalculation works from stale data.
    MissionTask("science_sequence_handoff",  "high",   "coordination", "coordination",
                depends_on=["sample_analysis_brief"]),
    # The handoff packages results from the analysis brief; if the brief was
    # incomplete or errored, the handoff is missing critical context.
    # Medium criticality
    MissionTask("equipment_inspection",      "medium", "solo",         "persistence"),
    MissionTask("sample_analysis_brief",     "medium", "coordination", "coordination"),
    MissionTask("emergency_protocol_review", "medium", "solo",         "attention",
                depends_on=["maintenance_log_review"]),
    # Protocol review is predicated on current maintenance logs; a skipped log
    # review leaves gaps in failure-mode awareness.
    MissionTask("crew_health_assessment",    "medium", "coordination", "coordination"),
    # Low criticality
    MissionTask("maintenance_log_review",    "low",    "solo",         "persistence"),
    MissionTask("comms_window_prep",         "low",    "solo",         "attention"),
]

# Fast lookup by task_id — used by dependency resolution in evaluate()
_TASK_BY_ID: Dict[str, MissionTask] = {t.task_id: t for t in MISSION_TASK_CATALOGUE}

# Weekly rotation: 3 tasks per day by catalogue index.
# Fixed schedule keeps workload constant across phases — performance drift
# is attributable entirely to impairment, not to a harder task queue.
_DAILY_ROTATION: List[Tuple[int, int, int]] = [
    (0, 4, 3),   # Day mod 0: eva_prep(attn), equip_insp(persist), sci_handoff(coord)
    (1, 9, 7),   # Day mod 1: hab_repair(plan), comms_prep(attn), crew_health(coord)
    (2, 6, 8),   # Day mod 2: navigation(plan), emerg_protocol(attn), maint_log(persist)
    (3, 5, 0),   # Day mod 3: sci_handoff(coord), sample_brief(coord), eva_prep(attn)
    (4, 1, 7),   # Day mod 4: equip_insp(persist), hab_repair(plan), crew_health(coord)
    (8, 6, 2),   # Day mod 5: maint_log(persist), emerg_protocol(attn), navigation(plan)
    (9, 3, 4),   # Day mod 6: comms_prep(attn), sci_handoff(coord), equip_insp(persist)
]


def daily_task_queue(day: int) -> List[MissionTask]:
    """
    Return the 3 tasks scheduled for this mission day (1-indexed).

    Deterministic weekly rotation — identical workload every phase.
    """
    rotation_idx = (day - 1) % len(_DAILY_ROTATION)
    return [MISSION_TASK_CATALOGUE[i] for i in _DAILY_ROTATION[rotation_idx]]


# ---------------------------------------------------------------------------
# Outcome constants
# ---------------------------------------------------------------------------

OUTCOME_COMPLETED = "completed"
OUTCOME_DELAYED   = "delayed"
OUTCOME_ERROR     = "error"
OUTCOME_SKIPPED   = "skipped"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class TaskOutcome:
    """Result of evaluating one task instance on one day."""
    task_id: str
    criticality: str
    vulnerability: str
    outcome: str        # completed | delayed | error | skipped
    failure_prob: float


@dataclass
class DayTaskOutcomes:
    """
    Aggregate task performance outcomes for one simulation day.

    Per-task results plus phase-level summary rates. Attached to DayState
    for JSON output and downstream analysis.
    """
    day: int
    task_results: List[TaskOutcome]

    # Aggregate failure rates across today's task queue
    checklist_miss_rate:       float   # fraction of attention tasks failed
    coordination_failure_rate: float   # fraction of coordination tasks failed
    planning_error_rate:       float   # fraction of planning tasks with errors
    maintenance_skip_rate:     float   # fraction of persistence tasks skipped

    # Impairment inputs used (for auditability)
    core_strain:      float
    core_monotony:    float
    sleep_quality:    float
    circadian_drift:  float

    # Causal failure traces (#7): one entry per non-completed task.
    # Each trace records the causal chain:
    #   sleep_quality → circadian_drift → impairment_channel → outcome
    causal_traces: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "task_results": [
                {
                    "task_id":       t.task_id,
                    "criticality":   t.criticality,
                    "vulnerability": t.vulnerability,
                    "outcome":       t.outcome,
                    "failure_prob":  round(t.failure_prob, 4),
                }
                for t in self.task_results
            ],
            "metrics": {
                "checklist_miss_rate":       round(self.checklist_miss_rate, 4),
                "coordination_failure_rate": round(self.coordination_failure_rate, 4),
                "planning_error_rate":       round(self.planning_error_rate, 4),
                "maintenance_skip_rate":     round(self.maintenance_skip_rate, 4),
            },
            "impairment": {
                "core_strain":     round(self.core_strain, 4),
                "core_monotony":   round(self.core_monotony, 4),
                "sleep_quality":   round(self.sleep_quality, 4),
                "circadian_drift": round(self.circadian_drift, 5),
            },
            "causal_traces": self.causal_traces,
        }


# ---------------------------------------------------------------------------
# Task Performance Engine
# ---------------------------------------------------------------------------

class TaskPerformanceEngine:
    """
    Evaluates daily task performance from runtime impairment values.

    Maps circadian drift, executive impairment, and burnout to per-task
    failure probabilities, then samples outcomes from a deterministic RNG.

    The RNG seed is offset (+9999) from the mission event seed to avoid
    correlation with micro-event draws while preserving reproducibility.

    Args:
        seed: Base seed (should match mission random_seed or hash).
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed + TASK_RNG_SEED_OFFSET)

    def evaluate(
        self,
        day: int,
        core_strain: float,
        core_monotony: float,
        sleep_quality: float,
        circadian_drift: float = 0.0,
        per_agent_impairment: Optional[Dict[str, float]] = None,
        prior_day_outcomes: Optional["DayTaskOutcomes"] = None,
    ) -> "DayTaskOutcomes":
        """
        Evaluate all scheduled tasks for this day.

        Args:
            day:                  Current simulation day (1-indexed)
            core_strain:          Physics-layer strain (self._S in TwinRunner)
            core_monotony:        Physics-layer monotony (self._M in TwinRunner)
            sleep_quality:        Resource-layer sleep quality
            circadian_drift:      Accumulated circadian drift (self._circadian_drift)
            per_agent_impairment: Dict[agent_id → composite impairment 0–1].
                                  If provided, coordination tasks use the
                                  maximum (weakest-link) impairment to amplify
                                  base fail_prob via COORD_WEAKEST_LINK_AMP.
            prior_day_outcomes:   DayTaskOutcomes from the previous day.
                                  If provided, tasks with `depends_on` entries
                                  receive fail_prob penalties when their
                                  prerequisites failed yesterday.

        Returns:
            DayTaskOutcomes with per-task results, aggregate metrics, and
            causal failure traces for all non-completed tasks.
        """
        tasks = daily_task_queue(day)
        results: List[TaskOutcome] = []
        causal_traces: List[dict] = []

        # Compute weakest-link agent impairment for coordination tasks
        max_agent_impairment = 0.0
        weakest_link_agent   = None
        if per_agent_impairment:
            weakest_link_agent = max(per_agent_impairment, key=per_agent_impairment.get)
            max_agent_impairment = per_agent_impairment[weakest_link_agent]

        # Build failed-yesterday lookup: task_id → outcome (only non-completed)
        failed_yesterday: Dict[str, str] = {}
        if prior_day_outcomes is not None:
            for tr in prior_day_outcomes.task_results:
                if tr.outcome != OUTCOME_COMPLETED:
                    failed_yesterday[tr.task_id] = tr.outcome

        for task in tasks:
            fail_prob, outcome, driver_value, extra_trace = self._evaluate_task(
                task, core_strain, core_monotony, sleep_quality,
                max_agent_impairment=max_agent_impairment,
                weakest_link_agent=weakest_link_agent,
                failed_yesterday=failed_yesterday,
            )
            results.append(TaskOutcome(
                task_id=task.task_id,
                criticality=task.criticality,
                vulnerability=task.vulnerability,
                outcome=outcome,
                failure_prob=fail_prob,
            ))

            # Causal trace: emitted for every non-completed task
            if outcome != OUTCOME_COMPLETED:
                trace = {
                    "task_id":    task.task_id,
                    "criticality": task.criticality,
                    "outcome":    outcome,
                    "chain": {
                        "sleep_quality":      round(sleep_quality, 4),
                        "circadian_drift":    round(circadian_drift, 5),
                        "impairment_channel": task.vulnerability,
                        "driver_value":       round(driver_value, 4),
                        "fail_prob":          round(fail_prob, 4),
                    },
                }
                if extra_trace:
                    trace["chain"].update(extra_trace)
                causal_traces.append(trace)

        return DayTaskOutcomes(
            day=day,
            task_results=results,
            checklist_miss_rate=       self._failure_rate(results, "attention"),
            coordination_failure_rate= self._failure_rate(results, "coordination"),
            planning_error_rate=       self._failure_rate(results, "planning"),
            maintenance_skip_rate=     self._failure_rate(results, "persistence"),
            core_strain=core_strain,
            core_monotony=core_monotony,
            sleep_quality=sleep_quality,
            circadian_drift=circadian_drift,
            causal_traces=causal_traces,
        )

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _evaluate_task(
        self,
        task: MissionTask,
        core_strain: float,
        core_monotony: float,
        sleep_quality: float,
        max_agent_impairment: float = 0.0,
        weakest_link_agent: Optional[str] = None,
        failed_yesterday: Optional[Dict[str, str]] = None,
    ) -> Tuple[float, str, float, Optional[dict]]:
        """
        Compute failure probability and sample an outcome for one task.

        Returns (failure_prob, outcome_str, driver_value, extra_trace).

        driver_value is the primary impairment signal for this vulnerability:
            attention   → sleep_deficit (normalized acute deficit)
            coordination → core_strain
            planning    → core_strain
            persistence → core_monotony
        extra_trace is merged into the causal chain dict for non-completed tasks.
        For coordination tasks it carries weakest_link_agent and max_agent_impairment.
        For tasks with dependency penalties it carries upstream_failed and dep_penalty.

        Input calibration:
            core_strain:   0–~0.25 over 200-day mission
            core_monotony: 0–0.86 over 200-day mission
            sleep_quality: 0.85 nominal, drops during disruption events

        Failure mode logic:
            attention   → DELAYED (50%) or ERROR (50%)
            coordination → ERROR (coordination breakdown)
            planning    → DELAYED (40%) or ERROR (60%)
            persistence → SKIPPED (task omission)

        Dependency penalty logic:
            If any depends_on task appeared in failed_yesterday:
                SOFT failure (delayed/skipped): +DEPENDENCY_FAIL_PENALTY_SOFT
                HARD failure (error):           +DEPENDENCY_FAIL_PENALTY_HARD
            Penalties are summed across all failed dependencies.
        """
        v = task.vulnerability

        if v == "attention":
            # Dual driver: monotony-induced fatigue + acute sleep deficit
            sleep_deficit = max(0.0, ATTN_SLEEP_BASELINE - sleep_quality) / ATTN_SLEEP_DEFICIT_RANGE
            fail_prob = min(1.0, core_monotony * ATTN_MONOTONY_WEIGHT + sleep_deficit * ATTN_SLEEP_DEFICIT_WEIGHT)
            fail_mode = OUTCOME_DELAYED if self._rng.random() < ATTN_DELAY_PROB else OUTCOME_ERROR
            driver_value = sleep_deficit
            extra_trace = None

        elif v == "coordination":
            # Strain degrades joint planning and handoff quality;
            # weakest-link agent impairment amplifies base fail_prob
            base_prob = core_strain * COORD_STRAIN_WEIGHT
            fail_prob = min(1.0, base_prob * (1.0 + max_agent_impairment * COORD_WEAKEST_LINK_AMP))
            fail_mode = OUTCOME_ERROR
            driver_value = core_strain
            extra_trace = {
                "weakest_link_agent":   weakest_link_agent,
                "max_agent_impairment": round(max_agent_impairment, 4),
            }

        elif v == "planning":
            # Strain drives errors and latency in multi-step cognition
            fail_prob = min(1.0, core_strain * PLAN_STRAIN_WEIGHT)
            fail_mode = OUTCOME_DELAYED if self._rng.random() < PLAN_DELAY_PROB else OUTCOME_ERROR
            driver_value = core_strain
            extra_trace = None

        elif v == "persistence":
            # Monotony accumulation drives maintenance avoidance and omission
            fail_prob = min(1.0, core_monotony * PERSIST_MONOTONY_WEIGHT)
            fail_mode = OUTCOME_SKIPPED
            driver_value = core_monotony
            extra_trace = None

        else:
            return 0.0, OUTCOME_COMPLETED, 0.0, None

        # --- Dependency penalty ---
        # Apply *after* computing base fail_prob so the penalty is additive
        # and clearly separable in the causal trace.
        dep_penalty = 0.0
        upstream_failed: List[str] = []
        if failed_yesterday and task.depends_on:
            for dep_id in task.depends_on:
                prior_outcome = failed_yesterday.get(dep_id)
                if prior_outcome is not None:
                    upstream_failed.append(dep_id)
                    if prior_outcome == OUTCOME_ERROR:
                        dep_penalty += DEPENDENCY_FAIL_PENALTY_HARD
                    else:
                        dep_penalty += DEPENDENCY_FAIL_PENALTY_SOFT

        if dep_penalty > 0.0:
            fail_prob = min(1.0, fail_prob + dep_penalty)
            dep_info = {
                "upstream_failed": upstream_failed,
                "dependency_penalty": round(dep_penalty, 4),
            }
            extra_trace = {**(extra_trace or {}), **dep_info}

        if self._rng.random() < fail_prob:
            return fail_prob, fail_mode, driver_value, extra_trace
        return fail_prob, OUTCOME_COMPLETED, driver_value, None

    @staticmethod
    def _failure_rate(results: List[TaskOutcome], vulnerability: str) -> float:
        """Fraction of tasks with the given vulnerability that did not complete."""
        matching = [r for r in results if r.vulnerability == vulnerability]
        if not matching:
            return 0.0
        return sum(1 for r in matching if r.outcome != OUTCOME_COMPLETED) / len(matching)
