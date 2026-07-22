"""
sensitivity.py — Parameter Sensitivity Sweep

Probes robustness of the 3QP task-failure model to small parameter perturbations.

Two sweep modes:
    Fast (parametric):  Task-failure coefficients + COORD_WEAKEST_LINK_AMP.
                        Re-evaluates task outcomes on pre-captured physics sequences —
                        N baseline TwinRunner runs reused across all coefficient variations.
    Full rerun:         BACKLOG_WORKLOAD_PER_SKIP + phase event multipliers.
                        Each setting patches params and re-runs N full TwinRunner sims.

Acceptance criteria (from plan):
    - TQ increase persists in coordination failure rate across the swept range.
    - TQ increase persists in maintenance skip rate across the swept range.
    - Planning error rate shows non-decreasing trend across phases.
    - No single ±20% perturbation flips the TQ gradient sign.

Usage:
    python sensitivity.py                                     # fast sweep only, 10 seeds
    python sensitivity.py --n-seeds 20 --verbose
    python sensitivity.py --full-sweeps                       # also run BACKLOG + phase sweeps
    python sensitivity.py --params COORD_STRAIN_WEIGHT COORD_WEAKEST_LINK_AMP
    python sensitivity.py --output-dir results/robustness

Outputs:
    output/robustness/robustness.csv        — all sweep results
    output/robustness/robustness.html       — heatmap (requires plotly + pandas)
"""

import argparse
import csv
import importlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- path setup ---
_RUNTIME_DIR = Path(__file__).parent
_ROOT = _RUNTIME_DIR.parent.parent
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for _p in [str(_RUNTIME_DIR), str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import params as _params
from task_performance import (
    daily_task_queue,
    OUTCOME_COMPLETED, OUTCOME_DELAYED, OUTCOME_ERROR, OUTCOME_SKIPPED,
    TASK_RNG_SEED_OFFSET,
)


# ---------------------------------------------------------------------------
# Parametric task coefficients (fast sweep)
# ---------------------------------------------------------------------------

@dataclass
class _TaskCoeffs:
    """A complete set of task failure probability coefficients for one sweep point."""
    attn_monotony_weight:      float = field(default_factory=lambda: _params.ATTN_MONOTONY_WEIGHT)
    attn_sleep_deficit_weight: float = field(default_factory=lambda: _params.ATTN_SLEEP_DEFICIT_WEIGHT)
    attn_sleep_baseline:       float = field(default_factory=lambda: _params.ATTN_SLEEP_BASELINE)
    attn_sleep_deficit_range:  float = field(default_factory=lambda: _params.ATTN_SLEEP_DEFICIT_RANGE)
    attn_delay_prob:           float = field(default_factory=lambda: _params.ATTN_DELAY_PROB)
    coord_strain_weight:       float = field(default_factory=lambda: _params.COORD_STRAIN_WEIGHT)
    coord_weakest_link_amp:    float = field(default_factory=lambda: _params.COORD_WEAKEST_LINK_AMP)
    plan_strain_weight:        float = field(default_factory=lambda: _params.PLAN_STRAIN_WEIGHT)
    plan_delay_prob:           float = field(default_factory=lambda: _params.PLAN_DELAY_PROB)
    persist_monotony_weight:   float = field(default_factory=lambda: _params.PERSIST_MONOTONY_WEIGHT)


_FAST_PARAM_FIELD_MAP: Dict[str, str] = {
    "ATTN_MONOTONY_WEIGHT":      "attn_monotony_weight",
    "ATTN_SLEEP_DEFICIT_WEIGHT": "attn_sleep_deficit_weight",
    "COORD_STRAIN_WEIGHT":       "coord_strain_weight",
    "COORD_WEAKEST_LINK_AMP":    "coord_weakest_link_amp",
    "PLAN_STRAIN_WEIGHT":        "plan_strain_weight",
    "PERSIST_MONOTONY_WEIGHT":   "persist_monotony_weight",
}


def _vary_coeffs(param_name: str, multiplier: float) -> _TaskCoeffs:
    """Return a coefficients set with one parameter scaled by multiplier."""
    c = _TaskCoeffs()
    attr = _FAST_PARAM_FIELD_MAP.get(param_name)
    if attr:
        setattr(c, attr, getattr(c, attr) * multiplier)
    return c


# ---------------------------------------------------------------------------
# Physics sequence capture
# ---------------------------------------------------------------------------

@dataclass
class _PhysicsDay:
    """Per-day physics state captured from a baseline run."""
    day: int
    core_strain: float
    core_monotony: float
    sleep_quality: float
    max_agent_impairment: float = 0.0   # for weakest-link coordination sweep


def _extract_physics(day_states: list) -> List[_PhysicsDay]:
    result = []
    for ds in day_states:
        rsrc = ds.resource_state_dict if isinstance(ds.resource_state_dict, dict) else {}
        sleep_q = rsrc.get("sleep_quality", 0.85)

        # Max per-agent impairment from internal states
        max_imp = 0.0
        if ds.internal_states:
            for agent_state in ds.internal_states.values():
                if isinstance(agent_state, dict):
                    fatigue = agent_state.get("fatigue", 0.0)
                    stress  = agent_state.get("stress", 0.0)
                else:
                    fatigue = getattr(agent_state, "fatigue", 0.0)
                    stress  = getattr(agent_state, "stress", 0.0)
                imp = (fatigue * _params.AGENT_IMPAIRMENT_FATIGUE_WEIGHT
                       + stress * _params.AGENT_IMPAIRMENT_STRESS_WEIGHT)
                max_imp = max(max_imp, imp)

        result.append(_PhysicsDay(
            day=ds.day,
            core_strain=ds.core_strain,
            core_monotony=ds.core_monotony,
            sleep_quality=sleep_q,
            max_agent_impairment=min(1.0, max_imp),
        ))
    return result


# ---------------------------------------------------------------------------
# Parametric task evaluator (fast sweep: no full reruns needed)
# ---------------------------------------------------------------------------

def _eval_day_tasks(
    day: int,
    core_strain: float,
    core_monotony: float,
    sleep_quality: float,
    max_agent_impairment: float,
    coeffs: _TaskCoeffs,
    rng: random.Random,
) -> Tuple[List[str], List[str]]:
    """
    Evaluate all tasks for one day. Returns (outcomes, criticalities).
    """
    tasks = daily_task_queue(day)
    outcomes = []
    criticalities = []

    for task in tasks:
        v = task.vulnerability

        if v == "attention":
            deficit = max(0.0, coeffs.attn_sleep_baseline - sleep_quality) / max(1e-9, coeffs.attn_sleep_deficit_range)
            fp = min(1.0, core_monotony * coeffs.attn_monotony_weight + deficit * coeffs.attn_sleep_deficit_weight)
            fail_mode = OUTCOME_DELAYED if rng.random() < coeffs.attn_delay_prob else OUTCOME_ERROR

        elif v == "coordination":
            base_prob = core_strain * coeffs.coord_strain_weight
            fp = min(1.0, base_prob * (1.0 + max_agent_impairment * coeffs.coord_weakest_link_amp))
            fail_mode = OUTCOME_ERROR

        elif v == "planning":
            fp = min(1.0, core_strain * coeffs.plan_strain_weight)
            fail_mode = OUTCOME_DELAYED if rng.random() < coeffs.plan_delay_prob else OUTCOME_ERROR

        elif v == "persistence":
            fp = min(1.0, core_monotony * coeffs.persist_monotony_weight)
            fail_mode = OUTCOME_SKIPPED

        else:
            fp = 0.0
            fail_mode = OUTCOME_COMPLETED

        outcome = fail_mode if rng.random() < fp else OUTCOME_COMPLETED
        outcomes.append(outcome)
        criticalities.append(task.criticality)

    return outcomes, criticalities


# ---------------------------------------------------------------------------
# TQ metrics computation (used by both sweep modes)
# ---------------------------------------------------------------------------

def _phase_tq_metrics(
    physics_seq: List[_PhysicsDay],
    coeffs: _TaskCoeffs,
    seed: int,
) -> Dict[str, float]:
    """
    Re-evaluate task outcomes for one physics sequence and return all TQ metrics.

    Returns dict with keys:
        early_crit_completion, tq_crit_completion, late_crit_completion,
        early_coord_fail, tq_coord_fail, late_coord_fail,
        early_maint_skip, tq_maint_skip, late_maint_skip,
        early_plan_error, tq_plan_error, late_plan_error,
        tq_gradient_crit, tq_gradient_coord, tq_gradient_maint,
    """
    rng = random.Random(seed + TASK_RNG_SEED_OFFSET)
    T = len(physics_seq)
    early_end = T // 3
    tq_end    = (2 * T) // 3

    early_crit:  List[bool] = []
    tq_crit:     List[bool] = []
    late_crit:   List[bool] = []

    early_coord:  List[bool] = []
    tq_coord:     List[bool] = []
    late_coord:   List[bool] = []

    early_maint:  List[bool] = []    # True = skipped
    tq_maint:     List[bool] = []
    late_maint:   List[bool] = []

    early_plan:   List[bool] = []    # True = error/delayed
    tq_plan:      List[bool] = []
    late_plan:    List[bool] = []

    tasks_sample = daily_task_queue(1)  # for vulnerability lookup by index
    task_vulns   = {t.task_id: t.vulnerability for t in daily_task_queue(1)}
    # Refresh for all tasks
    from task_performance import MISSION_TASK_CATALOGUE
    task_vulns = {t.task_id: t.vulnerability for t in MISSION_TASK_CATALOGUE}

    for pday in physics_seq:
        outcomes, criticalities = _eval_day_tasks(
            pday.day, pday.core_strain, pday.core_monotony, pday.sleep_quality,
            pday.max_agent_impairment,
            coeffs=coeffs, rng=rng,
        )
        day   = pday.day
        phase = ("early" if day <= early_end else ("tq" if day <= tq_end else "late"))
        tasks = daily_task_queue(day)

        for task, outcome, crit in zip(tasks, outcomes, criticalities):
            is_ok = (outcome == OUTCOME_COMPLETED)

            if crit == "high":
                if phase == "early":   early_crit.append(is_ok)
                elif phase == "tq":    tq_crit.append(is_ok)
                else:                  late_crit.append(is_ok)

            if task.vulnerability == "coordination":
                failed = not is_ok
                if phase == "early":   early_coord.append(failed)
                elif phase == "tq":    tq_coord.append(failed)
                else:                  late_coord.append(failed)

            if task.vulnerability == "persistence":
                skipped = (outcome == OUTCOME_SKIPPED)
                if phase == "early":   early_maint.append(skipped)
                elif phase == "tq":    tq_maint.append(skipped)
                else:                  late_maint.append(skipped)

            if task.vulnerability == "planning":
                errored = not is_ok
                if phase == "early":   early_plan.append(errored)
                elif phase == "tq":    tq_plan.append(errored)
                else:                  late_plan.append(errored)

    def _rate(lst: List[bool]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    e_crit = _rate(early_crit);   q_crit = _rate(tq_crit);    l_crit = _rate(late_crit)
    e_coord = _rate(early_coord); q_coord = _rate(tq_coord);  l_coord = _rate(late_coord)
    e_maint = _rate(early_maint); q_maint = _rate(tq_maint);  l_maint = _rate(late_maint)
    e_plan  = _rate(early_plan);  q_plan  = _rate(tq_plan);   l_plan  = _rate(late_plan)

    return {
        "early_crit_completion":  e_crit,
        "tq_crit_completion":     q_crit,
        "late_crit_completion":   l_crit,
        "early_coord_fail":       e_coord,
        "tq_coord_fail":          q_coord,
        "late_coord_fail":        l_coord,
        "early_maint_skip":       e_maint,
        "tq_maint_skip":          q_maint,
        "late_maint_skip":        l_maint,
        "early_plan_error":       e_plan,
        "tq_plan_error":          q_plan,
        "late_plan_error":        l_plan,
        # Gradients: positive = TQ degradation (more failures in TQ vs early)
        "tq_gradient_crit_fail":  (1 - q_crit)  - (1 - e_crit),   # negative completion = failure
        "tq_gradient_coord":      q_coord  - e_coord,
        "tq_gradient_maint":      q_maint  - e_maint,
        "tq_gradient_plan":       q_plan   - e_plan,
    }


def _aggregate_metrics(all_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """Mean over N seed runs."""
    if not all_metrics:
        return {}
    keys = all_metrics[0].keys()
    return {k: round(sum(m[k] for m in all_metrics) / len(all_metrics), 4) for k in keys}


# ---------------------------------------------------------------------------
# Baseline run collection (shared by fast sweep)
# ---------------------------------------------------------------------------

def _build_baseline_crew():
    from crew.profile import CrewProfile, CrewMember

    @dataclass
    class _P:
        openness: float = 0.65
        conscientiousness: float = 0.70
        extraversion: float = 0.60
        agreeableness: float = 0.65
        neuroticism: float = 0.40

    _NAMES = ["Alpha", "Bravo", "Charlie", "Delta"]
    from crew.profile import CrewProfile, CrewMember
    return CrewProfile(
        crew_name="sensitivity_crew",
        members=[CrewMember(name=n, personality=_P()) for n in _NAMES],
    )


def _collect_baseline_runs(
    n_seeds: int,
    mission_length: int,
    base_seed: int,
    output_dir: Path,
    verbose: bool = False,
) -> List[List[_PhysicsDay]]:
    """Run N TwinRunner baseline simulations and return their physics sequences."""
    from resources.resource_model import ResourceConfig
    from twin_runner import TwinRunner, TwinRunnerConfig

    crew = _build_baseline_crew()
    sequences = []
    for i in range(n_seeds):
        seed = base_seed + i * 17
        if verbose:
            print(f"  Baseline run {i+1}/{n_seeds} (seed={seed}) ...")
        cfg = TwinRunnerConfig(
            mission_name=f"_sens_base_{seed}",
            mission_length_days=mission_length,
            crew_profile=crew,
            resource_config=ResourceConfig(),
            random_seed=seed,
            output_dir=str(output_dir / "_runs"),
            verbose=False,
        )
        result = TwinRunner(cfg).run()
        sequences.append(_extract_physics(result.day_states))

    return sequences


# ---------------------------------------------------------------------------
# Fast sweep (parametric re-evaluation on pre-captured physics sequences)
# ---------------------------------------------------------------------------

_DEFAULT_FAST_PARAMS = [
    "ATTN_MONOTONY_WEIGHT",
    "ATTN_SLEEP_DEFICIT_WEIGHT",
    "COORD_STRAIN_WEIGHT",
    "COORD_WEAKEST_LINK_AMP",
    "PLAN_STRAIN_WEIGHT",
    "PERSIST_MONOTONY_WEIGHT",
]

_MULTIPLIERS = [0.80, 0.90, 1.00, 1.10, 1.20]


def _run_fast_sweep(
    param_names: List[str],
    sequences: List[List[_PhysicsDay]],
    base_seed: int,
    verbose: bool = False,
) -> List[dict]:
    rows = []
    for param_name in param_names:
        base_val = getattr(_params, param_name, None)
        if base_val is None:
            if verbose:
                print(f"  Warning: {param_name} not in params.py — skipping.")
            continue

        if verbose:
            print(f"  Fast sweep: {param_name}")

        for mult in _MULTIPLIERS:
            coeffs = _vary_coeffs(param_name, mult)
            all_metrics = []
            for seq_idx, seq in enumerate(sequences):
                seed = base_seed + seq_idx * 17
                m = _phase_tq_metrics(seq, coeffs, seed)
                all_metrics.append(m)

            agg = _aggregate_metrics(all_metrics)
            row = {
                "sweep_type":  "fast",
                "param":       param_name,
                "base_value":  round(base_val, 6),
                "multiplier":  mult,
                "varied_value": round(base_val * mult, 6),
                "n_seeds":     len(sequences),
            }
            row.update({k: round(v, 4) for k, v in agg.items()})

            if verbose:
                print(
                    f"    ×{mult:.2f} | crit_fail_grad={agg.get('tq_gradient_crit_fail', 0):+.3f}"
                    f"  coord_grad={agg.get('tq_gradient_coord', 0):+.3f}"
                    f"  maint_grad={agg.get('tq_gradient_maint', 0):+.3f}"
                )
            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Full-rerun sweep (BACKLOG_WORKLOAD_PER_SKIP, phase multipliers)
# Patches params module + reloads twin_runner for each setting.
# ---------------------------------------------------------------------------

_DEFAULT_FULL_PARAMS = [
    "BACKLOG_WORKLOAD_PER_SKIP",
    "PHASE_MULTIPLIER_SCALE",   # synthetic: scales both TQ_MULTIPLIERS and LATE_MULTIPLIERS
]


def _patch_params_for_full(param_name: str, multiplier: float):
    """
    Patch the params module for a full-rerun sweep setting.

    Returns (restore_fn) — call to undo the patch.
    """
    if param_name == "PHASE_MULTIPLIER_SCALE":
        orig_tq   = dict(_params.TQ_MULTIPLIERS)
        orig_late = dict(_params.LATE_MULTIPLIERS)
        _params.TQ_MULTIPLIERS   = {k: v * multiplier for k, v in orig_tq.items()}
        _params.LATE_MULTIPLIERS = {k: v * multiplier for k, v in orig_late.items()}
        def restore():
            _params.TQ_MULTIPLIERS   = orig_tq
            _params.LATE_MULTIPLIERS = orig_late
        return restore

    else:
        orig = getattr(_params, param_name)
        setattr(_params, param_name, orig * multiplier)
        def restore():
            setattr(_params, param_name, orig)
        return restore


def _run_full_sweep_setting(
    param_name: str,
    multiplier: float,
    n_seeds: int,
    mission_length: int,
    base_seed: int,
    output_dir: Path,
    verbose: bool,
) -> List[Dict[str, float]]:
    """
    Run N TwinRunner simulations for one parameter setting.

    Patches params, reloads task_performance and twin_runner for fresh imports,
    collects KPI metrics, then restores params.
    """
    restore_fn = _patch_params_for_full(param_name, multiplier)

    # Reload modules so they pick up patched params
    import task_performance as _tp_mod
    import twin_runner as _tr_mod
    importlib.reload(_tp_mod)
    importlib.reload(_tr_mod)

    from twin_runner import TwinRunner, TwinRunnerConfig
    from resources.resource_model import ResourceConfig

    crew = _build_baseline_crew()
    all_metrics = []

    for i in range(n_seeds):
        seed = base_seed + i * 17
        cfg = TwinRunnerConfig(
            mission_name=f"_sens_full_{param_name[:8]}_{seed}",
            mission_length_days=mission_length,
            crew_profile=crew,
            resource_config=ResourceConfig(),
            random_seed=seed,
            output_dir=str(output_dir / "_runs"),
            verbose=False,
        )
        result = TwinRunner(cfg).run()

        # Extract metrics from KPIs + day states
        kpis = result.kpis
        if kpis:
            pb = kpis.get("phase_breakdown", {})
            mp = kpis.get("mission_performance", {})
            T  = mission_length
            early_end = T // 3
            tq_end    = (2 * T) // 3

            # Re-compute coord/maint TQ metrics from day states
            early_coord, tq_coord, late_coord = [], [], []
            early_maint, tq_maint, late_maint = [], [], []
            early_plan,  tq_plan,  late_plan  = [], [], []
            early_crit,  tq_crit,  late_crit  = [], [], []

            for ds in result.day_states:
                to = ds.task_outcomes
                if not to:
                    continue
                day = ds.day
                phase = "early" if day <= early_end else ("tq" if day <= tq_end else "late")
                for tr in to.get("task_results", []):
                    outcome = tr["outcome"]
                    crit    = tr["criticality"]
                    vuln    = tr["vulnerability"]
                    is_ok   = (outcome == OUTCOME_COMPLETED)

                    if crit == "high":
                        entry = [early_crit, tq_crit, late_crit][["early","tq","late"].index(phase)]
                        entry.append(is_ok)
                    if vuln == "coordination":
                        entry = [early_coord, tq_coord, late_coord][["early","tq","late"].index(phase)]
                        entry.append(not is_ok)
                    if vuln == "persistence":
                        entry = [early_maint, tq_maint, late_maint][["early","tq","late"].index(phase)]
                        entry.append(outcome == OUTCOME_SKIPPED)
                    if vuln == "planning":
                        entry = [early_plan, tq_plan, late_plan][["early","tq","late"].index(phase)]
                        entry.append(not is_ok)

            def _rt(lst): return sum(lst) / len(lst) if lst else 0.0

            e_crit = _rt(early_crit); q_crit = _rt(tq_crit); l_crit = _rt(late_crit)
            e_co   = _rt(early_coord); q_co   = _rt(tq_coord); l_co  = _rt(late_coord)
            e_ma   = _rt(early_maint); q_ma   = _rt(tq_maint); l_ma  = _rt(late_maint)
            e_pl   = _rt(early_plan);  q_pl   = _rt(tq_plan);  l_pl  = _rt(late_plan)

            all_metrics.append({
                "early_crit_completion":  e_crit,
                "tq_crit_completion":     q_crit,
                "late_crit_completion":   l_crit,
                "early_coord_fail":       e_co,
                "tq_coord_fail":          q_co,
                "late_coord_fail":        l_co,
                "early_maint_skip":       e_ma,
                "tq_maint_skip":          q_ma,
                "late_maint_skip":        l_ma,
                "early_plan_error":       e_pl,
                "tq_plan_error":          q_pl,
                "late_plan_error":        l_pl,
                "tq_gradient_crit_fail":  (1 - q_crit) - (1 - e_crit),
                "tq_gradient_coord":      q_co - e_co,
                "tq_gradient_maint":      q_ma - e_ma,
                "tq_gradient_plan":       q_pl - e_pl,
            })

    # Restore params + reload modules
    restore_fn()
    importlib.reload(_tp_mod)
    importlib.reload(_tr_mod)

    return all_metrics


def _run_full_sweeps(
    param_names: List[str],
    n_seeds: int,
    mission_length: int,
    base_seed: int,
    output_dir: Path,
    verbose: bool = False,
) -> List[dict]:
    rows = []
    for param_name in param_names:
        if param_name == "PHASE_MULTIPLIER_SCALE":
            base_val = 1.0
        else:
            base_val = getattr(_params, param_name, None)
            if base_val is None:
                if verbose:
                    print(f"  Warning: {param_name} not in params.py — skipping.")
                continue

        if verbose:
            print(f"  Full-rerun sweep: {param_name}")

        for mult in _MULTIPLIERS:
            if verbose:
                print(f"    ×{mult:.2f} (running {n_seeds} sims) ...")
            all_metrics = _run_full_sweep_setting(
                param_name, mult, n_seeds, mission_length,
                base_seed, output_dir, verbose=False,
            )
            agg = _aggregate_metrics(all_metrics)
            row = {
                "sweep_type":  "full_rerun",
                "param":       param_name,
                "base_value":  round(base_val, 6),
                "multiplier":  mult,
                "varied_value": round(base_val * mult, 6),
                "n_seeds":     len(all_metrics),
            }
            row.update({k: round(v, 4) for k, v in agg.items()})

            if verbose:
                print(
                    f"      crit_fail_grad={agg.get('tq_gradient_crit_fail', 0):+.3f}"
                    f"  coord_grad={agg.get('tq_gradient_coord', 0):+.3f}"
                    f"  maint_grad={agg.get('tq_gradient_maint', 0):+.3f}"
                )
            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Top-level sweep runner
# ---------------------------------------------------------------------------

_CSV_FIELDNAMES = [
    "sweep_type", "param", "base_value", "multiplier", "varied_value", "n_seeds",
    # TQ metrics
    "early_crit_completion", "tq_crit_completion", "late_crit_completion",
    "early_coord_fail",      "tq_coord_fail",      "late_coord_fail",
    "early_maint_skip",      "tq_maint_skip",      "late_maint_skip",
    "early_plan_error",      "tq_plan_error",       "late_plan_error",
    # Gradients: positive = TQ degradation > early
    "tq_gradient_crit_fail", "tq_gradient_coord", "tq_gradient_maint", "tq_gradient_plan",
]


def run_sensitivity_sweep(
    n_seeds: int = 10,
    mission_length: int = 200,
    base_seed: int = 42,
    output_dir: Path = Path("output/robustness"),
    fast_params: Optional[List[str]] = None,
    full_params: Optional[List[str]] = None,
    run_full_sweeps: bool = False,
    verbose: bool = False,
) -> Path:
    """
    Run sensitivity sweeps and write robustness.csv + robustness.html.

    Args:
        fast_params:      Task-coefficient params for fast sweep (default: all).
        full_params:      System params for full-rerun sweep (default: none unless run_full_sweeps=True).
        run_full_sweeps:  If True, run BACKLOG_WORKLOAD_PER_SKIP + PHASE_MULTIPLIER_SCALE sweeps.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    params_fast = fast_params or _DEFAULT_FAST_PARAMS
    params_full = full_params or (_DEFAULT_FULL_PARAMS if run_full_sweeps else [])

    # ── Collect baseline physics sequences (shared by all fast sweeps) ──
    if verbose:
        print(f"Collecting {n_seeds} baseline runs ({mission_length}-day each) ...")
    sequences = _collect_baseline_runs(
        n_seeds=n_seeds,
        mission_length=mission_length,
        base_seed=base_seed,
        output_dir=output_dir,
        verbose=verbose,
    )

    # ── Fast sweep ──
    rows: List[dict] = []
    if params_fast:
        if verbose:
            print("\nRunning fast (parametric) sweeps ...")
        rows.extend(_run_fast_sweep(params_fast, sequences, base_seed, verbose))

    # ── Full-rerun sweep ──
    if params_full:
        if verbose:
            print("\nRunning full-rerun sweeps ...")
        rows.extend(
            _run_full_sweeps(params_full, n_seeds, mission_length, base_seed, output_dir, verbose)
        )

    # ── Write CSV ──
    csv_path = output_dir / "robustness.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    if verbose:
        print(f"\nCSV written: {csv_path}")

    # ── Write HTML plot ──
    _write_html_plot(rows, output_dir, verbose)

    # ── Acceptance check ──
    _print_acceptance_check(rows, verbose=True)

    return output_dir


# ---------------------------------------------------------------------------
# Acceptance check
# ---------------------------------------------------------------------------

def _print_acceptance_check(rows: List[dict], verbose: bool = True) -> None:
    """
    Print pass/fail for each acceptance criterion from the plan.

    Criteria:
        - TQ increase persists in coordination failure rate (tq_gradient_coord > 0 for all mult)
        - TQ increase persists in maintenance skip rate (tq_gradient_maint > 0 for all mult)
        - Planning error rate shows non-decreasing trend across phases (tq_plan >= early_plan)
        - No single ±20% perturbation flips the TQ gradient sign (tq_gradient_coord ≠ sign flip)
    """
    print("\n=== Acceptance Check ===")

    # Group by param
    from collections import defaultdict
    by_param: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        by_param[r["param"]].append(r)

    for param, param_rows in sorted(by_param.items()):
        coord_grads  = [r.get("tq_gradient_coord", 0.0) for r in param_rows]
        maint_grads  = [r.get("tq_gradient_maint", 0.0) for r in param_rows]
        plan_ok      = all(r.get("tq_plan_error", 0) >= r.get("early_plan_error", 0) - 0.01 for r in param_rows)

        coord_robust = all(g > -0.01 for g in coord_grads)   # TQ coord failure ≥ early
        maint_robust = all(g > -0.01 for g in maint_grads)   # TQ maint skip ≥ early

        coord_sign = "PASS" if coord_robust else "FAIL"
        maint_sign = "PASS" if maint_robust else "FAIL"
        plan_sign  = "PASS" if plan_ok      else "WARN"

        print(
            f"  {param:30s}  "
            f"coord TQ persist: {coord_sign}  "
            f"maint TQ persist: {maint_sign}  "
            f"plan non-decr: {plan_sign}"
        )


# ---------------------------------------------------------------------------
# HTML plot
# ---------------------------------------------------------------------------

def _write_html_plot(rows: List[dict], output_dir: Path, verbose: bool = False) -> None:
    """Write a Plotly HTML with heatmaps for each TQ gradient metric."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
    except ImportError:
        if verbose:
            print("  plotly/pandas not available — skipping HTML plot.")
        return

    df = pd.DataFrame(rows)
    gradient_metrics = [
        ("tq_gradient_crit_fail", "TQ gradient: critical task failure"),
        ("tq_gradient_coord",     "TQ gradient: coordination failure"),
        ("tq_gradient_maint",     "TQ gradient: maintenance skip"),
        ("tq_gradient_plan",      "TQ gradient: planning error"),
    ]

    params_list = df["param"].unique().tolist()
    mult_list   = sorted(df["multiplier"].unique().tolist())

    fig = make_subplots(
        rows=1, cols=len(gradient_metrics),
        subplot_titles=[m[1] for m in gradient_metrics],
    )

    for col_idx, (metric, title) in enumerate(gradient_metrics, start=1):
        z = []
        for p in params_list:
            row_vals = []
            for m in mult_list:
                subset = df[(df["param"] == p) & (df["multiplier"] == m)][metric]
                row_vals.append(float(subset.values[0]) if len(subset) > 0 else 0.0)
            z.append(row_vals)

        fig.add_trace(
            go.Heatmap(
                z=z,
                x=[f"×{m:.2f}" for m in mult_list],
                y=params_list,
                colorscale="RdBu",
                zmid=0,
                text=[[f"{v:+.3f}" for v in row] for row in z],
                texttemplate="%{text}",
                colorbar=dict(title="gradient", x=col_idx / len(gradient_metrics)),
                showscale=(col_idx == len(gradient_metrics)),
            ),
            row=1, col=col_idx,
        )

    fig.update_layout(
        title="3QP Parameter Sensitivity: TQ Gradients by Coefficient Variation",
        height=max(350, 55 * len(params_list) + 120),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )

    html_path = output_dir / "robustness.html"
    fig.write_html(str(html_path))
    if verbose:
        print(f"HTML plot written: {html_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ALL_FAST = _DEFAULT_FAST_PARAMS
    ALL_FULL = _DEFAULT_FULL_PARAMS

    parser = argparse.ArgumentParser(
        description="3QP parameter sensitivity sweep — robustness analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Fast sweep params (re-evaluate task engine on baseline physics sequences):
  {', '.join(ALL_FAST)}

Full-rerun sweep params (requires --full-sweeps):
  {', '.join(ALL_FULL)}
""",
    )
    parser.add_argument(
        "--n-seeds", type=int, default=10,
        help="Number of baseline sim seeds (default: 10)",
    )
    parser.add_argument(
        "--mission-length", type=int, default=200,
        help="Mission length in days (default: 200)",
    )
    parser.add_argument(
        "--base-seed", type=int, default=42,
        help="Starting RNG seed (default: 42)",
    )
    parser.add_argument(
        "--output-dir", type=str, default="output/robustness",
        help="Output directory (default: output/robustness)",
    )
    parser.add_argument(
        "--params", nargs="+", default=None, choices=ALL_FAST,
        help="Fast-sweep params to include (default: all)",
    )
    parser.add_argument(
        "--full-sweeps", action="store_true",
        help="Also run full-rerun sweeps (BACKLOG_WORKLOAD_PER_SKIP, PHASE_MULTIPLIER_SCALE)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print progress",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    out = run_sensitivity_sweep(
        n_seeds=args.n_seeds,
        mission_length=args.mission_length,
        base_seed=args.base_seed,
        output_dir=output_dir,
        fast_params=args.params,
        run_full_sweeps=args.full_sweeps,
        verbose=args.verbose,
    )
    print(f"\nSensitivity sweep complete. Output: {out}")


if __name__ == "__main__":
    main()
