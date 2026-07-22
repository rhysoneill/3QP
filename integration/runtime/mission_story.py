"""
Mission Story — Narrative Summary from Causal Failure Traces

Promotes per-task causal traces into a mission-level "why things broke" summary.
Written to output/{mission_name}/mission_story.json by TwinRunner.run() or
called directly via compute_mission_story(day_states).

Design contract:
    Reads:  List[DayState] — task_outcomes.causal_traces only
    Writes: mission_story.json
    Never:  accesses agent beliefs, internal state, or physics directly

Output structure:
    top_failures         — top 5 failure events ranked by criticality × outcome severity
    phase_stories        — one representative failure chain per mission phase (early/TQ/late)
    summary_sentences    — 3–5 plain-English sentences explaining the mission arc

Failure impact scoring:
    criticality  high=3, medium=2, low=1
    outcome      error=1.5, skipped=1.2, delayed=1.0
    impact_score = criticality_weight × outcome_weight × fail_prob

Phase boundaries:
    early   days 1 to T//3
    tq      days T//3+1 to 2*T//3
    late    days 2*T//3+1 to T
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Impact scoring
# ---------------------------------------------------------------------------

_CRIT_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}
_OUTCOME_WEIGHT = {"error": 1.5, "skipped": 1.2, "delayed": 1.0}

_TASK_LABELS: Dict[str, str] = {
    "eva_prep_checklist":        "EVA preparation checklist",
    "habitat_repair_plan":       "habitat repair planning",
    "navigation_recalculation":  "navigation recalculation",
    "science_sequence_handoff":  "science sequence handoff",
    "equipment_inspection":      "equipment inspection",
    "sample_analysis_brief":     "sample analysis briefing",
    "emergency_protocol_review": "emergency protocol review",
    "crew_health_assessment":    "crew health assessment",
    "maintenance_log_review":    "maintenance log review",
    "comms_window_prep":         "communications window preparation",
}

_OUTCOME_LABELS: Dict[str, str] = {
    "error":   "completed with errors",
    "delayed": "completed behind schedule",
    "skipped": "skipped entirely",
}


def _impact_score(trace: dict) -> float:
    crit    = trace.get("criticality", "low")
    outcome = trace.get("outcome", "delayed")
    chain   = trace.get("chain", {})
    fp      = chain.get("fail_prob", 0.5)
    return _CRIT_WEIGHT.get(crit, 1.0) * _OUTCOME_WEIGHT.get(outcome, 1.0) * fp


# ---------------------------------------------------------------------------
# Human-readable sentence generation
# ---------------------------------------------------------------------------

def _narrative_sentence(day: int, trace: dict) -> str:
    """
    Produce one plain-English sentence describing a failure event.

    Uses the causal chain fields to describe the mechanism without jargon.
    """
    task_id = trace.get("task_id", "unknown task")
    label   = _TASK_LABELS.get(task_id, task_id.replace("_", " "))
    crit    = trace.get("criticality", "low")
    outcome = trace.get("outcome", "delayed")
    chain   = trace.get("chain", {})
    channel = chain.get("impairment_channel", "")
    driver  = chain.get("driver_value", 0.0)
    sleep_q = chain.get("sleep_quality", 0.85)
    fp      = chain.get("fail_prob", 0.0)

    outcome_phrase = _OUTCOME_LABELS.get(outcome, outcome)
    crit_phrase = {"high": "critical", "medium": "moderate", "low": "routine"}.get(crit, crit)

    if channel == "attention":
        sleep_pct = round(sleep_q * 100)
        deficit_pct = round(driver * 100)
        sentence = (
            f"Day {day}: The {crit_phrase} task '{label}' was {outcome_phrase}. "
            f"Sleep quality had fallen to {sleep_pct}% of baseline, producing an "
            f"attentional deficit of {deficit_pct}% — enough to cause a checklist lapse "
            f"(failure probability {fp:.0%})."
        )

    elif channel == "coordination":
        wl_agent = chain.get("weakest_link_agent")
        imp = chain.get("max_agent_impairment", 0.0)
        agent_note = (
            f" Crew member {wl_agent} was the most impaired ({imp:.0%} composite)."
            if wl_agent else ""
        )
        sentence = (
            f"Day {day}: The {crit_phrase} coordination task '{label}' broke down. "
            f"Accumulated crew strain (level {driver:.3f}) degraded joint planning and "
            f"handoff quality, pushing failure probability to {fp:.0%}.{agent_note}"
        )

    elif channel == "planning":
        sentence = (
            f"Day {day}: The {crit_phrase} planning task '{label}' was {outcome_phrase}. "
            f"Multi-step cognitive demands were compromised by accumulated strain "
            f"(level {driver:.3f}), raising the probability of error to {fp:.0%}."
        )

    elif channel == "persistence":
        monotony_pct = round(driver * 100)
        sentence = (
            f"Day {day}: The {crit_phrase} maintenance task '{label}' was skipped. "
            f"Crew monotony had reached {monotony_pct}% of its range, eroding the "
            f"motivation needed to complete routine upkeep (skip probability {fp:.0%})."
        )

    else:
        sentence = (
            f"Day {day}: Task '{label}' was {outcome_phrase} "
            f"(failure probability {fp:.0%})."
        )

    return sentence


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_mission_story(day_states: list) -> Optional[dict]:
    """
    Generate a mission narrative from accumulated DayState objects.

    Args:
        day_states: List of DayState objects from TwinRunner.run()

    Returns:
        Mission story dict, or None if no task outcome data is present.
    """
    if not day_states:
        return None

    T = len(day_states)
    early_end = T // 3
    tq_end    = (2 * T) // 3

    # ── Collect all failure traces across the mission ──
    all_failures: List[dict] = []   # {day, trace, impact_score, phase}

    for ds in day_states:
        to = ds.task_outcomes if isinstance(ds.task_outcomes, dict) else None
        if to is None:
            continue
        day = ds.day
        phase = "early" if day <= early_end else ("tq" if day <= tq_end else "late")
        for trace in to.get("causal_traces", []):
            all_failures.append({
                "day":          day,
                "phase":        phase,
                "trace":        trace,
                "impact_score": _impact_score(trace),
            })

    if not all_failures:
        return None

    # ── Top 5 failures by impact ──
    top5 = sorted(all_failures, key=lambda x: x["impact_score"], reverse=True)[:5]
    top_failures = []
    for entry in top5:
        trace = entry["trace"]
        top_failures.append({
            "day":          entry["day"],
            "phase":        entry["phase"],
            "task_id":      trace.get("task_id"),
            "criticality":  trace.get("criticality"),
            "outcome":      trace.get("outcome"),
            "impact_score": round(entry["impact_score"], 4),
            "causal_chain": trace.get("chain", {}),
            "sentence":     _narrative_sentence(entry["day"], trace),
        })

    # ── One representative failure per phase ──
    phase_rep: Dict[str, Optional[dict]] = {"early": None, "tq": None, "late": None}
    for phase in ("early", "tq", "late"):
        candidates = [e for e in all_failures if e["phase"] == phase]
        if candidates:
            best = max(candidates, key=lambda x: x["impact_score"])
            phase_rep[phase] = {
                "day":      best["day"],
                "task_id":  best["trace"].get("task_id"),
                "outcome":  best["trace"].get("outcome"),
                "sentence": _narrative_sentence(best["day"], best["trace"]),
            }

    # ── Summary sentences ──
    n_failures    = len(all_failures)
    n_errors      = sum(1 for e in all_failures if e["trace"].get("outcome") == "error")
    n_skips       = sum(1 for e in all_failures if e["trace"].get("outcome") == "skipped")
    n_delays      = sum(1 for e in all_failures if e["trace"].get("outcome") == "delayed")
    n_high_crit   = sum(1 for e in all_failures if e["trace"].get("criticality") == "high")
    tq_failures   = sum(1 for e in all_failures if e["phase"] == "tq")
    late_failures = sum(1 for e in all_failures if e["phase"] == "late")
    early_fail    = sum(1 for e in all_failures if e["phase"] == "early")

    sentences = []

    # Mission arc sentence
    if tq_failures > early_fail and tq_failures >= late_failures:
        arc = (
            f"Over the {T}-day mission, task failures concentrated in the middle phase "
            f"({tq_failures} of {n_failures} total failures), consistent with third-quarter "
            f"degradation: elevated conflict and schedule pressure while the end of the mission "
            f"remained distant."
        )
    elif late_failures > early_fail:
        arc = (
            f"Over the {T}-day mission, task performance degraded progressively, with "
            f"{late_failures} of {n_failures} failures occurring in the final third. "
            f"Accumulated fatigue and monotony compounded as the mission stretched on."
        )
    else:
        arc = (
            f"Over the {T}-day mission, task performance was relatively stable, "
            f"with {n_failures} total task failures spread across phases."
        )
    sentences.append(arc)

    # Error/skip breakdown
    if n_errors > 0 or n_skips > 0:
        breakdown = (
            f"Failure modes: {n_errors} tasks completed with errors, "
            f"{n_skips} maintenance tasks skipped, "
            f"and {n_delays} tasks delayed."
        )
        sentences.append(breakdown)

    # High-criticality sentence
    if n_high_crit > 0:
        sentences.append(
            f"{n_high_crit} of the failures involved high-criticality tasks — "
            f"those directly tied to EVA safety, navigation, or crew health."
        )

    # Dominant failure driver sentence
    attn_count  = sum(1 for e in all_failures if e["trace"].get("chain", {}).get("impairment_channel") == "attention")
    coord_count = sum(1 for e in all_failures if e["trace"].get("chain", {}).get("impairment_channel") == "coordination")
    plan_count  = sum(1 for e in all_failures if e["trace"].get("chain", {}).get("impairment_channel") == "planning")
    pers_count  = sum(1 for e in all_failures if e["trace"].get("chain", {}).get("impairment_channel") == "persistence")
    driver_counts = {
        "sleep fragmentation and circadian drift": attn_count,
        "accumulated crew strain": coord_count + plan_count,
        "monotony-driven maintenance avoidance": pers_count,
    }
    dominant_driver = max(driver_counts, key=driver_counts.get)
    sentences.append(
        f"The primary failure driver was {dominant_driver}."
    )

    return {
        "total_failures": n_failures,
        "top_failures":   top_failures,
        "phase_stories":  {
            "early": phase_rep["early"],
            "tq":    phase_rep["tq"],
            "late":  phase_rep["late"],
        },
        "summary_sentences": sentences,
    }


# ---------------------------------------------------------------------------
# File writer
# ---------------------------------------------------------------------------

def write_mission_story(day_states: list, output_path: Path) -> Optional[dict]:
    """
    Compute and write mission_story.json to output_path.

    Args:
        day_states:  List of DayState objects from TwinRunner.run()
        output_path: Directory to write mission_story.json into

    Returns:
        The story dict, or None if no data.
    """
    story = compute_mission_story(day_states)
    if story is None:
        return None
    story_file = output_path / "mission_story.json"
    with open(story_file, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2)
    return story
