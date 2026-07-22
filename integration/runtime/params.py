"""
3QP Parameter Registry — Single Source of Truth

All model constants used across twin_runner.py, task_performance.py,
run_manifest.py, and sensitivity.py are defined here. No hardcoded
magic numbers should exist outside this file.

Import pattern — flat constants for inline use:
    from params import COORD_STRAIN_WEIGHT, TQ_MULTIPLIERS

Export pattern — full registry for manifest serialization:
    from params import REGISTRY

Schema version — bumped on any behavioral parameter change:
    from params import SCHEMA_VERSION
"""

from typing import Dict

SCHEMA_VERSION = "1.2"


# ---------------------------------------------------------------------------
# Task failure probability coefficients
# Source: task_performance.py TaskPerformanceEngine._evaluate_task()
# ---------------------------------------------------------------------------

ATTN_MONOTONY_WEIGHT        = 0.12   # monotony → attention fail prob
ATTN_SLEEP_DEFICIT_WEIGHT   = 1.00   # normalized sleep deficit → attention fail prob
ATTN_SLEEP_BASELINE         = 0.85   # nominal sleep quality (0=no sleep, 1=perfect)
ATTN_SLEEP_DEFICIT_RANGE    = 0.45   # normalization denominator for sleep deficit
ATTN_DELAY_PROB             = 0.50   # P(DELAYED | attention failure) else ERROR

COORD_STRAIN_WEIGHT         = 1.20   # strain → coordination fail prob
COORD_WEAKEST_LINK_AMP      = 0.80   # per-agent impairment amplifier on coord fail prob

PLAN_STRAIN_WEIGHT          = 0.80   # strain → planning fail prob
PLAN_DELAY_PROB             = 0.40   # P(DELAYED | planning failure) else ERROR

PERSIST_MONOTONY_WEIGHT     = 0.25   # monotony → persistence fail prob

TASK_RNG_SEED_OFFSET        = 9999   # added to event_seed to derive task RNG seed


# ---------------------------------------------------------------------------
# Task dependency graph penalties
# Source: task_performance.py TaskPerformanceEngine.evaluate()
# Rationale: a failed prerequisite task leaves incomplete or corrupted
# information/conditions for dependent tasks.  A skipped or delayed task
# (soft failure) contributes less than an errored task (hard failure).
# ---------------------------------------------------------------------------

DEPENDENCY_FAIL_PENALTY_SOFT = 0.06   # penalty added when dependency was DELAYED or SKIPPED
DEPENDENCY_FAIL_PENALTY_HARD = 0.12   # penalty added when dependency had an ERROR


# ---------------------------------------------------------------------------
# Phase-aware micro-event probability multipliers
# Source: twin_runner.py MicroEventEngine.roll()
# ---------------------------------------------------------------------------

TQ_PHASE_START   = 0.50   # third-quarter window begins (fraction of mission)
TQ_PHASE_END     = 0.75   # third-quarter window ends
LATE_PHASE_START = 0.75   # late-mission phase begins

TQ_MULTIPLIERS: Dict[str, float] = {
    "minor_conflict":     1.8,
    "schedule_slip":      1.3,
    "minor_task_failure": 1.2,
    "novel_task":         0.5,
    "small_win":          0.6,
}

LATE_MULTIPLIERS: Dict[str, float] = {
    "minor_conflict":     1.4,
    "schedule_slip":      1.5,
    "minor_task_failure": 1.4,
    "maintenance_surge":  1.3,
    "sleep_disruption":   1.2,
    "small_win":          0.4,
    "novel_task":         0.3,
}


# ---------------------------------------------------------------------------
# Circadian drift accumulation
# Source: twin_runner.py TwinRunner._run_day() Step 1
# ---------------------------------------------------------------------------

CIRCADIAN_ACCUM_THRESHOLD    = 0.04    # sleep debt level above which drift builds
CIRCADIAN_ACCUM_RATE         = 0.0008  # drift added per unit sleep debt per day
CIRCADIAN_RECOVERY_RATE      = 0.0004  # drift subtracted per undisturbed day


# ---------------------------------------------------------------------------
# Sleep debt decay
# Source: twin_runner.py TwinRunner._run_day() Step 1
# ---------------------------------------------------------------------------

SLEEP_DEBT_DECAY_FACTOR = 0.55   # daily multiplier (half-life ≈ 1.5 days)


# ---------------------------------------------------------------------------
# Executive function degradation
# Source: twin_runner.py TwinRunner._run_day() Step 7
# ---------------------------------------------------------------------------

EXEC_FATIGUE_WEIGHT     = 0.55   # fatigue share of composite
EXEC_STRESS_WEIGHT      = 0.45   # stress share of composite
EXEC_THRESHOLD          = 0.35   # composite below this → zero impairment
EXEC_SCALE              = 1.40   # scale factor above threshold
EXEC_WORKLOAD_AMP       = 0.25   # effective workload increase per impairment unit
EXEC_RECOVERY_SUPPRESS  = 0.20   # effective recovery decrease per impairment unit


# ---------------------------------------------------------------------------
# Structural competence (effort quality)
# Source: twin_runner.py TwinRunner._run_day() Step 7
# ---------------------------------------------------------------------------

EFFORT_BURNOUT_THRESHOLD = 0.30   # burnout composite below this → no degradation
EFFORT_BURNOUT_SCALE     = 1.30   # scale factor above threshold


# ---------------------------------------------------------------------------
# MC communication compliance scaling
# Source: twin_runner.py _apply_comm_deltas()
# ---------------------------------------------------------------------------

COMPLIANCE_STRAIN_THRESHOLD      = 0.50
COMPLIANCE_STRAIN_SCALE          = 0.60
COMPLIANCE_FRUSTRATION_THRESHOLD = 0.50
COMPLIANCE_FRUSTRATION_SCALE     = 0.40
COMPLIANCE_FLOOR                 = 0.35   # minimum compliance fraction


# ---------------------------------------------------------------------------
# Per-agent impairment (Item #4)
# Source: twin_runner.py _run_day() — per-agent composite passed to task engine
# ---------------------------------------------------------------------------

AGENT_IMPAIRMENT_FATIGUE_WEIGHT = 0.50
AGENT_IMPAIRMENT_STRESS_WEIGHT  = 0.50


# ---------------------------------------------------------------------------
# Backlog dynamics (Item #5)
# Source: twin_runner.py TwinRunner._run_day() backlog feed-forward
# ---------------------------------------------------------------------------

BACKLOG_WORKLOAD_PER_SKIP = 0.008   # workload added per accumulated skip item
BACKLOG_MAX_LOAD          = 0.10    # cap on total backlog-driven workload addition
BACKLOG_NATURAL_DECAY     = 0.97    # daily decay (items resolved or caught up)


# ---------------------------------------------------------------------------
# Reputation memory / dyadic conflict (Item #7)
# Source: twin_runner.py TwinRunner._run_day() dyad conflict tracking
# ---------------------------------------------------------------------------

DYAD_CONFLICT_INCREMENT  = 0.12   # conflict added to a dyad on a conflict event
DYAD_CONFLICT_DECAY      = 0.97   # daily multiplicative decay of conflict history
DYAD_TRUST_SUPPRESSOR    = 0.30   # max belief_crew_cohesion reduction from conflict


# ---------------------------------------------------------------------------
# Full registry — serialized to run_manifest.json
# Maps parameter names to {value, units, description}
# ---------------------------------------------------------------------------

REGISTRY: Dict[str, object] = {
    "schema_version": SCHEMA_VERSION,
    "task_failure": {
        "ATTN_MONOTONY_WEIGHT":       {"value": ATTN_MONOTONY_WEIGHT,       "units": "prob/monotony_unit",          "desc": "Monotony → attention fail prob"},
        "ATTN_SLEEP_DEFICIT_WEIGHT":  {"value": ATTN_SLEEP_DEFICIT_WEIGHT,  "units": "prob/normalized_deficit",     "desc": "Sleep deficit → attention fail prob"},
        "ATTN_SLEEP_BASELINE":        {"value": ATTN_SLEEP_BASELINE,        "units": "quality [0,1]",               "desc": "Nominal sleep quality baseline"},
        "ATTN_SLEEP_DEFICIT_RANGE":   {"value": ATTN_SLEEP_DEFICIT_RANGE,   "units": "quality fraction",            "desc": "Normalization range for sleep deficit"},
        "ATTN_DELAY_PROB":            {"value": ATTN_DELAY_PROB,            "units": "prob",                        "desc": "P(DELAYED | attention failure)"},
        "COORD_STRAIN_WEIGHT":        {"value": COORD_STRAIN_WEIGHT,        "units": "prob/strain_unit",            "desc": "Strain → coordination fail prob"},
        "COORD_WEAKEST_LINK_AMP":     {"value": COORD_WEAKEST_LINK_AMP,     "units": "multiplier",                  "desc": "Per-agent impairment amplifier on coordination fail prob"},
        "PLAN_STRAIN_WEIGHT":         {"value": PLAN_STRAIN_WEIGHT,         "units": "prob/strain_unit",            "desc": "Strain → planning fail prob"},
        "PLAN_DELAY_PROB":            {"value": PLAN_DELAY_PROB,            "units": "prob",                        "desc": "P(DELAYED | planning failure)"},
        "PERSIST_MONOTONY_WEIGHT":    {"value": PERSIST_MONOTONY_WEIGHT,    "units": "prob/monotony_unit",          "desc": "Monotony → persistence fail prob"},
        "TASK_RNG_SEED_OFFSET":       {"value": TASK_RNG_SEED_OFFSET,       "units": "integer",                     "desc": "RNG seed offset for task engine"},
        "DEPENDENCY_FAIL_PENALTY_SOFT": {"value": DEPENDENCY_FAIL_PENALTY_SOFT, "units": "prob",                      "desc": "Fail prob added when dependency was delayed/skipped"},
        "DEPENDENCY_FAIL_PENALTY_HARD": {"value": DEPENDENCY_FAIL_PENALTY_HARD, "units": "prob",                      "desc": "Fail prob added when dependency had an error"},
    },
    "micro_events": {
        "TQ_PHASE_START":             {"value": TQ_PHASE_START,             "units": "mission fraction",            "desc": "Third-quarter window start"},
        "TQ_PHASE_END":               {"value": TQ_PHASE_END,               "units": "mission fraction",            "desc": "Third-quarter window end"},
        "LATE_PHASE_START":           {"value": LATE_PHASE_START,           "units": "mission fraction",            "desc": "Late-mission phase start"},
        "TQ_MULTIPLIERS":             TQ_MULTIPLIERS,
        "LATE_MULTIPLIERS":           LATE_MULTIPLIERS,
    },
    "circadian_drift": {
        "CIRCADIAN_ACCUM_THRESHOLD":  {"value": CIRCADIAN_ACCUM_THRESHOLD,  "units": "sleep_debt fraction",         "desc": "Debt above which drift accumulates"},
        "CIRCADIAN_ACCUM_RATE":       {"value": CIRCADIAN_ACCUM_RATE,       "units": "drift/debt_unit/day",         "desc": "Drift accumulated per unit debt per day"},
        "CIRCADIAN_RECOVERY_RATE":    {"value": CIRCADIAN_RECOVERY_RATE,    "units": "drift/day",                   "desc": "Drift recovered per undisturbed day"},
    },
    "sleep_debt": {
        "SLEEP_DEBT_DECAY_FACTOR":    {"value": SLEEP_DEBT_DECAY_FACTOR,    "units": "fraction/day",                "desc": "Daily sleep debt decay factor"},
    },
    "exec_impairment": {
        "EXEC_FATIGUE_WEIGHT":        {"value": EXEC_FATIGUE_WEIGHT,        "units": "weight",                      "desc": "Fatigue share of composite"},
        "EXEC_STRESS_WEIGHT":         {"value": EXEC_STRESS_WEIGHT,         "units": "weight",                      "desc": "Stress share of composite"},
        "EXEC_THRESHOLD":             {"value": EXEC_THRESHOLD,             "units": "composite value",             "desc": "Composite below this: zero impairment"},
        "EXEC_SCALE":                 {"value": EXEC_SCALE,                 "units": "multiplier",                  "desc": "Scale factor above threshold"},
        "EXEC_WORKLOAD_AMP":          {"value": EXEC_WORKLOAD_AMP,          "units": "fraction",                    "desc": "Workload increase per impairment unit"},
        "EXEC_RECOVERY_SUPPRESS":     {"value": EXEC_RECOVERY_SUPPRESS,     "units": "fraction",                    "desc": "Recovery decrease per impairment unit"},
    },
    "effort_quality": {
        "EFFORT_BURNOUT_THRESHOLD":   {"value": EFFORT_BURNOUT_THRESHOLD,   "units": "composite value",             "desc": "Burnout below this: no degradation"},
        "EFFORT_BURNOUT_SCALE":       {"value": EFFORT_BURNOUT_SCALE,       "units": "multiplier",                  "desc": "Scale factor above threshold"},
    },
    "compliance_scaling": {
        "COMPLIANCE_STRAIN_THRESHOLD":      {"value": COMPLIANCE_STRAIN_THRESHOLD,      "units": "stress fraction", "desc": "Stress above → reactance begins"},
        "COMPLIANCE_STRAIN_SCALE":          {"value": COMPLIANCE_STRAIN_SCALE,          "units": "reduction/unit",  "desc": "Compliance drop per excess stress unit"},
        "COMPLIANCE_FRUSTRATION_THRESHOLD": {"value": COMPLIANCE_FRUSTRATION_THRESHOLD, "units": "frustration fraction", "desc": "Frustration above → reactance begins"},
        "COMPLIANCE_FRUSTRATION_SCALE":     {"value": COMPLIANCE_FRUSTRATION_SCALE,     "units": "reduction/unit",  "desc": "Compliance drop per excess frustration unit"},
        "COMPLIANCE_FLOOR":                 {"value": COMPLIANCE_FLOOR,                 "units": "fraction",        "desc": "Minimum compliance (interventions never inert)"},
    },
    "per_agent_impairment": {
        "AGENT_IMPAIRMENT_FATIGUE_WEIGHT": {"value": AGENT_IMPAIRMENT_FATIGUE_WEIGHT, "units": "weight", "desc": "Fatigue share of per-agent composite"},
        "AGENT_IMPAIRMENT_STRESS_WEIGHT":  {"value": AGENT_IMPAIRMENT_STRESS_WEIGHT,  "units": "weight", "desc": "Stress share of per-agent composite"},
    },
    "backlog_dynamics": {
        "BACKLOG_WORKLOAD_PER_SKIP":  {"value": BACKLOG_WORKLOAD_PER_SKIP,  "units": "workload/skip",               "desc": "Workload added per accumulated skip"},
        "BACKLOG_MAX_LOAD":           {"value": BACKLOG_MAX_LOAD,           "units": "workload fraction",           "desc": "Cap on total backlog-driven workload"},
        "BACKLOG_NATURAL_DECAY":      {"value": BACKLOG_NATURAL_DECAY,      "units": "fraction/day",                "desc": "Daily backlog decay"},
    },
    "reputation_memory": {
        "DYAD_CONFLICT_INCREMENT":    {"value": DYAD_CONFLICT_INCREMENT,    "units": "conflict score",              "desc": "Conflict added to a dyad per conflict event"},
        "DYAD_CONFLICT_DECAY":        {"value": DYAD_CONFLICT_DECAY,        "units": "fraction/day",                "desc": "Daily multiplicative decay of conflict memory"},
        "DYAD_TRUST_SUPPRESSOR":      {"value": DYAD_TRUST_SUPPRESSOR,      "units": "cohesion fraction",           "desc": "Max cohesion belief reduction from conflict"},
    },
}
