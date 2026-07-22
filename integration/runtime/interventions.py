"""
3QP Intervention Library

Provides a catalogue of Mission Control intervention types and factory
functions for constructing MCCommunication instances.

Each intervention is defined by its belief impact profile and any workload
effects. All values are from params.py-grounded defaults — adjust via the
factory function kwargs for scenario-specific tuning.

--- INTERVENTION TYPES ---

Psychological / Communication:
    reassurance         MC acknowledges mission difficulty; moderate MC support boost
    direction           Task redirect or protocol clarification; mild MC support boost
    support             Strong operational + emotional backing; strong MC support boost
    acknowledgment      MC validates crew concerns; mild MC support boost
    celebration         Mission milestone recognition; boosts MC support + crew cohesion
    peer_check          MC prompts mutual support; reinforces cohesion between agents

Resource:
    resupply_announcement  Incoming resupply notification; boosts resupply reliability + MC support

Operational:
    rest_authorization     MC authorizes a reduced-workload day; 25% workload reduction
    schedule_relief        Non-essential tasks deprioritized; 15% workload reduction + mild cohesion

--- USAGE ---

    from interventions import make_comm, INTERVENTION_CATALOGUE

    # Factory function — recommended
    comm = make_comm("celebration", day=120)
    runner.inject_mc_communication(comm)

    # Multiple comms (e.g. recurring rest day)
    comms = make_comm_schedule("rest_authorization", start_day=100, interval=21, count=4)
    for day, comm in comms:
        runner.schedule_mc_communication(day, comm)

    # CLI usage — pass comm type name to --inject-comms
    python run_simulation.py --mode twin --crew-preset fragile_team --days 200 \\
        --inject-comms "celebration:120,rest_authorization:140:14,schedule_relief:160"

--- CATALOGUE SCHEMA ---

    Each entry is a dict with:
        description:                   Plain-English effect summary
        belief_mc_support_delta:       Applied to belief_mission_control_support
        belief_resupply_reliability_delta: Applied to belief_resupply_reliability
        belief_crew_cohesion_delta:    Applied to belief_crew_cohesion
        workload_relief_factor:        Fraction removed from effective_workload (0–0.30)
        content_template:              Default message text
"""

import sys
import os

_HERE        = os.path.dirname(os.path.abspath(__file__))  # integration/runtime/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))    # 3QP/
sys.path.insert(0, _HERE)
sys.path.insert(0, _PROJECT_ROOT)  # needed for 'from mission_control.mc_types import ...'

from typing import Dict, List, Optional, Tuple

# MCCommunication is imported lazily at function call to avoid circular imports
# when this module is imported from run_simulation.py


# ---------------------------------------------------------------------------
# Intervention Catalogue
# ---------------------------------------------------------------------------

INTERVENTION_CATALOGUE: Dict[str, dict] = {

    # -----------------------------------------------------------------------
    # Psychological / Communication
    # -----------------------------------------------------------------------

    "reassurance": {
        "description": "MC acknowledges mission difficulty; moderate morale and MC support boost",
        "belief_mc_support_delta": 0.08,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control acknowledges the challenges you are facing. "
            "Your performance continues to exceed expectations. We're here with you."
        ),
    },

    "direction": {
        "description": "Task redirect or protocol clarification; mild MC support boost",
        "belief_mc_support_delta": 0.05,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control is transmitting updated task priority guidance. "
            "Please review the attached protocol amendments and confirm receipt."
        ),
    },

    "support": {
        "description": "Strong operational and emotional backing; strongest MC support boost",
        "belief_mc_support_delta": 0.10,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control stands with you fully. Your contributions are recognized "
            "at the highest level. You have our complete operational and personal support."
        ),
    },

    "acknowledgment": {
        "description": "MC validates crew concerns; mild MC support boost",
        "belief_mc_support_delta": 0.06,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control has received and reviewed your concerns. "
            "They are being actioned. You are heard."
        ),
    },

    "celebration": {
        "description": (
            "Mission milestone recognition; boosts MC support AND crew cohesion belief. "
            "Use to mark EVA completions, experiment milestones, or halfway points."
        ),
        "belief_mc_support_delta": 0.08,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.06,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control congratulates the entire crew on reaching this mission milestone. "
            "Your teamwork and professionalism have been extraordinary. "
            "This achievement belongs to all of you."
        ),
    },

    "peer_check": {
        "description": (
            "MC prompts crew to check in on each other; mild MC support + cohesion boost. "
            "Most effective when crew is showing early withdrawal signals."
        ),
        "belief_mc_support_delta": 0.04,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.04,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control is requesting an informal crew welfare check-in today. "
            "Please take time to connect with your crewmates before end of shift."
        ),
    },

    # -----------------------------------------------------------------------
    # Resource
    # -----------------------------------------------------------------------

    "resupply_announcement": {
        "description": "Incoming resupply notification; boosts resupply reliability and MC support",
        "belief_mc_support_delta": 0.04,
        "belief_resupply_reliability_delta": 0.10,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.00,
        "content_template": (
            "Mission Control confirms a resupply vehicle is en route. "
            "Estimated arrival in 21 days. Manifest includes priority consumables."
        ),
    },

    # -----------------------------------------------------------------------
    # Operational / Structural
    # -----------------------------------------------------------------------

    "rest_authorization": {
        "description": (
            "MC formally authorizes a reduced-workload recovery day. "
            "Reduces effective workload by 25% for one day + strong MC support boost. "
            "Use for acute fatigue recovery, post-EVA, or high-strain episodes."
        ),
        "belief_mc_support_delta": 0.10,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.00,
        "workload_relief_factor": 0.25,
        "content_template": (
            "Mission Control is authorizing a scheduled rest and recovery period today. "
            "Non-time-critical tasks are suspended. Rest, rehydrate, and recover. "
            "You have earned it and the mission requires it."
        ),
    },

    "schedule_relief": {
        "description": (
            "Non-essential tasks deprioritized by MC. "
            "Moderate workload reduction (15%) + mild cohesion boost from MC showing care. "
            "Use for sustained overload periods rather than acute fatigue."
        ),
        "belief_mc_support_delta": 0.06,
        "belief_resupply_reliability_delta": 0.00,
        "belief_crew_cohesion_delta": 0.02,
        "workload_relief_factor": 0.15,
        "content_template": (
            "Mission Control has reviewed the task manifest and deprioritized "
            "non-essential activities for the next operational period. "
            "Focus on high-priority items only. Pace yourselves."
        ),
    },
}


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

def make_comm(
    intervention_type: str,
    day: int,
    sender: str = "mission_control",
    content_override: Optional[str] = None,
) -> "MCCommunication":
    """
    Create an MCCommunication from a named intervention type.

    Args:
        intervention_type: Key from INTERVENTION_CATALOGUE
        day:               Simulation day this comm is dispatched
        sender:            Sender identifier (default: "mission_control")
        content_override:  Custom message text; uses catalogue default if None

    Returns:
        MCCommunication ready for runner.inject_mc_communication()

    Raises:
        ValueError: If intervention_type is not in INTERVENTION_CATALOGUE

    Example:
        comm = make_comm("celebration", day=120)
        runner.inject_mc_communication(comm)
    """
    from mission_control.mc_types import MCCommunication  # late import to avoid circular

    if intervention_type not in INTERVENTION_CATALOGUE:
        known = ", ".join(sorted(INTERVENTION_CATALOGUE))
        raise ValueError(
            f"Unknown intervention type '{intervention_type}'. "
            f"Known types: {known}"
        )

    spec = INTERVENTION_CATALOGUE[intervention_type]
    return MCCommunication(
        day=day,
        sender=sender,
        message_type=intervention_type,
        content=content_override or spec["content_template"],
        belief_mc_support_delta=spec["belief_mc_support_delta"],
        belief_resupply_reliability_delta=spec["belief_resupply_reliability_delta"],
        belief_crew_cohesion_delta=spec["belief_crew_cohesion_delta"],
        workload_relief_factor=spec["workload_relief_factor"],
    )


def make_comm_schedule(
    intervention_type: str,
    start_day: int,
    interval: int,
    count: int,
    **kwargs,
) -> List[Tuple[int, "MCCommunication"]]:
    """
    Create a recurring series of MCCommunication instances.

    Args:
        intervention_type: Key from INTERVENTION_CATALOGUE
        start_day:         First dispatch day
        interval:          Days between dispatches
        count:             Total number of comms to generate
        **kwargs:          Passed to make_comm()

    Returns:
        List of (day, MCCommunication) tuples

    Example:
        # Rest authorization every 14 days from day 100
        schedule = make_comm_schedule("rest_authorization", 100, 14, 6)
        for day, comm in schedule:
            runner.schedule_mc_communication(day, comm)
    """
    return [
        (start_day + i * interval, make_comm(intervention_type, start_day + i * interval, **kwargs))
        for i in range(count)
    ]


def list_interventions() -> None:
    """Print a formatted table of all available intervention types."""
    print(f"\n{'TYPE':<26} {'WORKLOAD':<10} {'MC SUPP':<9} {'COHESION':<10} DESCRIPTION")
    print("-" * 90)
    for name, spec in sorted(INTERVENTION_CATALOGUE.items()):
        wl = f"-{spec['workload_relief_factor']*100:.0f}%" if spec["workload_relief_factor"] else "—"
        mc = f"+{spec['belief_mc_support_delta']:.2f}"
        coh = f"+{spec['belief_crew_cohesion_delta']:.2f}" if spec["belief_crew_cohesion_delta"] else "—"
        desc = spec["description"].split(";")[0][:52]
        print(f"{name:<26} {wl:<10} {mc:<9} {coh:<10} {desc}")
    print()


if __name__ == "__main__":
    list_interventions()
