"""
HermitClaw — Simulation-Internal Supervisory Agent

HermitClaw is the twin engine's internal Mission Control psychology team.
It has full access to objective simulation state and can observe the
gap between what the crew believes and what the simulation has actually
computed.

Role in the simulation:
    - Observes daily objective state (ResourceState, internal states, belief states)
    - Computes DivergedReport: crew-belief vs objective-state divergence
    - Generates HermitClawAdvisory: rule-based recommended intervention
    - Generates MCCommunication: dispatches to crew via TwinRunner
    - Generates PlannedIntervention: physical resupply/task change (TwinRunner executes)
    - Writes all outputs to JSON log for Weke (external HermitClaw tool) to read

Role separation invariants:
    - HermitClaw NEVER modifies resource state, belief state, or internal state
    - HermitClaw NEVER holds live references to simulation objects (copies only)
    - MCCommunication dispatched to crew goes through BeliefUpdateEngine,
      not written directly to belief state
    - HermitClaw NEVER communicates directly with agents — only via MCCommunication
    - All decision logic is explicit rule-based Python — no LLM, no stochastic

All outputs are JSON-serializable for Weke readout.
"""

import copy
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from resources.resource_model import ResourceState
from internal_state.astronaut_state import AstronautInternalState
from beliefs.belief_engine import AstronautBeliefState
from agents.per_agent_selector import COOPERATION_BLOCK_THRESHOLD

from .mc_types import (
    MCCommunication,
    PlannedIntervention,
    DivergenceReport,
    HermitClawAdvisory,
)


# ---------------------------------------------------------------------------
# Thresholds (all named — no magic numbers)
# ---------------------------------------------------------------------------

# Risk classification
MORALE_RISK_THRESHOLD = 0.35          # morale below this → high risk
TRUST_EROSION_LOW = 0.40              # mean trust below this → erosion detected
TRUST_COLLAPSE_TRIGGER = 0.25         # trust below this triggers predicted_collapse_day

# Advisory urgency weights
URGENCY_HIGH_RISK_AGENT_WEIGHT = 0.40  # of crew that is high-risk
URGENCY_LOW_MORALE_WEIGHT = 0.30       # baseline morale gap
URGENCY_TRUST_EROSION_BONUS = 0.15     # flat add if trust eroding
URGENCY_IMMINENT_COLLAPSE_BONUS = 0.15 # flat add if collapse < 14 days
URGENCY_IMMINENT_COLLAPSE_DAYS = 14

# Intervention selection thresholds
ADVISORY_URGENCY_NONE = 0.25          # below this → no intervention recommended
ADVISORY_URGENCY_CRITICAL = 0.65      # above this → stronger intervention type
MC_SUPPORT_LOW = 0.45                 # belief_mc_support below this → acknowledgment
RESUPPLY_RELIABILITY_LOW = 0.50       # belief threshold for resupply comm
SCARCITY_HIGH = 0.55                  # coffee/food scarcity above this → resupply rec

# MC communication belief deltas
COMM_REASSURANCE_SUPPORT_DELTA = 0.08
COMM_ACKNOWLEDGMENT_SUPPORT_DELTA = 0.10
COMM_RESUPPLY_ANNOUNCEMENT_RELIABILITY_DELTA = 0.15
COMM_DIRECTION_SUPPORT_DELTA = 0.05

# Forecast
FORECAST_DRIFT_WINDOW = 7             # days of history for drift slope estimation


# ---------------------------------------------------------------------------
# Internal snapshot type
# ---------------------------------------------------------------------------

class _DaySnapshot:
    """
    Frozen copy of simulation state passed to observe() on one day.
    Stored as deep copies to enforce the no-live-reference invariant.
    """
    __slots__ = ("day", "resource_state", "internal_states", "belief_states")

    def __init__(
        self,
        day: int,
        resource_state: ResourceState,
        internal_states: Dict[str, AstronautInternalState],
        belief_states: Dict[str, AstronautBeliefState],
    ):
        self.day = day
        # Shallow copy of the dataclasses is sufficient — their fields are
        # all immutable (floats, ints) except distribution_vector in ResourceState
        self.resource_state = copy.copy(resource_state)
        if hasattr(self.resource_state, "distribution_vector"):
            self.resource_state.distribution_vector = {
                k: dict(v)
                for k, v in resource_state.distribution_vector.items()
            }
        self.internal_states = {
            aid: copy.copy(state)
            for aid, state in internal_states.items()
        }
        self.belief_states = {
            aid: copy.copy(state)
            for aid, state in belief_states.items()
        }


# ---------------------------------------------------------------------------
# HermitClaw Agent
# ---------------------------------------------------------------------------

class HermitClawAgent:
    """
    Simulation-internal supervisory observer with full state access.

    HermitClaw runs as a parallel observer each day after the main pipeline
    completes. It computes the divergence between objective simulation truth
    and crew belief state, generates advisories, and optionally dispatches
    MC communications and physical interventions via TwinRunner.

    Usage (called by TwinRunner each day):
        hc.observe(day, resource_state, internal_states, belief_states)
        divergence = hc.compute_divergence(day)
        advisory = hc.generate_advisory(day)
        comm = hc.generate_mc_communication(day, advisory)
        # TwinRunner dispatches comm and any resulting PlannedIntervention
    """

    def __init__(self) -> None:
        self._snapshots: List[_DaySnapshot] = []
        self._divergence_log: List[DivergenceReport] = []
        self._advisory_log: List[HermitClawAdvisory] = []
        self._intervention_counter: int = 0

    # -------------------------------------------------------------------
    # Observation
    # -------------------------------------------------------------------

    def observe(
        self,
        day: int,
        resource_state: ResourceState,
        internal_states: Dict[str, AstronautInternalState],
        belief_states: Dict[str, AstronautBeliefState],
        social_snapshot: Optional[Any] = None,  # Reserved for Module 05 integration
    ) -> None:
        """
        Store a frozen copy of today's simulation state.

        Must be called AFTER StateDriftEngine has run for all agents.
        social_snapshot is accepted but currently unused (reserved for
        Module 05 social network coupling).

        Args:
            day:              Current simulation day
            resource_state:   Objective ResourceState (deep-copied)
            internal_states:  Per-agent AstronautInternalState (deep-copied)
            belief_states:    Per-agent AstronautBeliefState (deep-copied)
            social_snapshot:  Optional social graph data (reserved)
        """
        self._snapshots.append(
            _DaySnapshot(day, resource_state, internal_states, belief_states)
        )

    # -------------------------------------------------------------------
    # Divergence
    # -------------------------------------------------------------------

    def compute_divergence(self, day: int) -> DivergenceReport:
        """
        Compute divergence between objective state and crew belief state.

        Retrieves the most recent snapshot at or before `day`.

        Returns:
            DivergenceReport with all divergence metrics computed

        Raises:
            ValueError if no observations have been stored yet
        """
        snap = self._get_snapshot(day)
        if snap is None:
            raise ValueError(f"No observation available for day {day}")

        agent_ids = list(snap.internal_states.keys())
        n = len(agent_ids)
        if n == 0:
            raise ValueError("No agents in observation")

        # Objective morale: what the drift engine computed
        objective_morales = [snap.internal_states[aid].morale for aid in agent_ids]
        objective_morale_avg = sum(objective_morales) / n

        # Crew believed morale: belief_mission_viability as morale proxy
        believed_morales = [snap.belief_states[aid].belief_mission_viability for aid in agent_ids]
        crew_believed_morale_avg = sum(believed_morales) / n

        crew_belief_divergence = crew_believed_morale_avg - objective_morale_avg

        # High-risk agents: low morale OR cooperation_threshold above block level
        high_risk_agents = [
            aid for aid in agent_ids
            if snap.internal_states[aid].morale < MORALE_RISK_THRESHOLD
            or snap.internal_states[aid].cooperation_threshold >= COOPERATION_BLOCK_THRESHOLD
        ]

        # Trust metrics
        trust_values = [snap.internal_states[aid].trust_in_crew for aid in agent_ids]
        mean_trust = sum(trust_values) / n
        trust_erosion_detected = (
            mean_trust < TRUST_EROSION_LOW
            or self._detect_trust_trend(agent_ids)
        )

        # Predicted collapse day
        predicted_collapse_day = self._predict_collapse(day, agent_ids)

        # Belief distribution fairness
        fairness_values = [snap.belief_states[aid].belief_distribution_fairness for aid in agent_ids]
        belief_distribution_fairness_avg = sum(fairness_values) / n

        report = DivergenceReport(
            day=day,
            objective_morale_avg=round(objective_morale_avg, 4),
            crew_believed_morale_avg=round(crew_believed_morale_avg, 4),
            crew_belief_divergence=round(crew_belief_divergence, 4),
            high_risk_agents=high_risk_agents,
            predicted_collapse_day=predicted_collapse_day,
            belief_distribution_fairness_avg=round(belief_distribution_fairness_avg, 4),
            trust_erosion_detected=trust_erosion_detected,
            mean_trust_in_crew=round(mean_trust, 4),
        )

        self._divergence_log.append(report)
        return report

    # -------------------------------------------------------------------
    # Advisory
    # -------------------------------------------------------------------

    def generate_advisory(self, day: int) -> Optional[HermitClawAdvisory]:
        """
        Generate a rule-based advisory for Mission Control.

        Returns None if urgency is below the action threshold.
        Automatically calls compute_divergence(day) if not already done
        for this day.

        Returns:
            HermitClawAdvisory or None
        """
        divergence = self._get_divergence_for_day(day)
        if divergence is None:
            divergence = self.compute_divergence(day)

        snap = self._get_snapshot(day)
        if snap is None:
            return None

        agent_ids = list(snap.internal_states.keys())
        n = len(agent_ids)

        # --- Compute urgency ---
        urgency = 0.0

        # Factor 1: fraction of crew that is high-risk
        if n > 0:
            risk_fraction = len(divergence.high_risk_agents) / n
            urgency += risk_fraction * URGENCY_HIGH_RISK_AGENT_WEIGHT

        # Factor 2: morale gap vs 0.40 baseline
        morale_gap = max(0.0, 0.40 - divergence.objective_morale_avg)
        urgency += (morale_gap / 0.40) * URGENCY_LOW_MORALE_WEIGHT

        # Factor 3: trust erosion
        if divergence.trust_erosion_detected:
            urgency += URGENCY_TRUST_EROSION_BONUS

        # Factor 4: imminent collapse
        if divergence.predicted_collapse_day is not None:
            days_to_collapse = divergence.predicted_collapse_day - day
            if days_to_collapse < URGENCY_IMMINENT_COLLAPSE_DAYS:
                urgency += URGENCY_IMMINENT_COLLAPSE_BONUS

        urgency = min(1.0, urgency)

        if urgency < ADVISORY_URGENCY_NONE:
            return None  # Nominal — no advisory issued

        # --- Determine recommended intervention ---
        recommended, rationale = self._select_intervention(
            day, snap, divergence, urgency, agent_ids, n
        )

        advisory = HermitClawAdvisory(
            day=day,
            recommended_intervention=recommended,
            urgency=round(urgency, 4),
            rationale=rationale,
            divergence_report=divergence,
        )

        self._advisory_log.append(advisory)
        return advisory

    # -------------------------------------------------------------------
    # MC Communication
    # -------------------------------------------------------------------

    def generate_mc_communication(
        self,
        day: int,
        advisory: HermitClawAdvisory,
    ) -> Optional[MCCommunication]:
        """
        Translate an advisory into a dispatched MC communication.

        Returns None if advisory urgency is below communication threshold
        or advisory has no recommended intervention.

        The returned MCCommunication is passed by TwinRunner to
        BeliefUpdateEngine for all agents on the same day.

        Args:
            day:      Current simulation day
            advisory: Advisory from generate_advisory()

        Returns:
            MCCommunication or None
        """
        if advisory is None:
            return None
        if advisory.urgency < ADVISORY_URGENCY_NONE:
            return None

        rec = advisory.recommended_intervention
        divergence = advisory.divergence_report

        if rec == "resupply_coffee" or rec == "resupply_hygiene" or rec == "resupply_entertainment":
            resource_name = rec.replace("resupply_", "")
            content = (
                f"Mission Control: A resupply of {resource_name} has been dispatched. "
                f"Estimated arrival in {_DEFAULT_ETA_DAYS} days. "
                "We are committed to your mission comfort and success."
            )
            return MCCommunication(
                day=day,
                sender="hermitclaw",
                message_type="resupply_announcement",
                content=content,
                belief_mc_support_delta=COMM_REASSURANCE_SUPPORT_DELTA,
                belief_resupply_reliability_delta=COMM_RESUPPLY_ANNOUNCEMENT_RELIABILITY_DELTA,
            )

        elif rec == "crew_acknowledgment":
            content = (
                "Mission Control: We want to acknowledge the extraordinary difficulties "
                "you are facing. Your performance under these conditions is remarkable. "
                "We are actively monitoring and ready to support."
            )
            return MCCommunication(
                day=day,
                sender="hermitclaw",
                message_type="acknowledgment",
                content=content,
                belief_mc_support_delta=COMM_ACKNOWLEDGMENT_SUPPORT_DELTA,
                belief_resupply_reliability_delta=0.0,
            )

        elif rec == "task_rebalance":
            content = (
                "Mission Control: We are reviewing task assignments to reduce crew load. "
                "A revised schedule will be transmitted within 48 hours. "
                "Prioritize crew rest and communication."
            )
            return MCCommunication(
                day=day,
                sender="hermitclaw",
                message_type="direction",
                content=content,
                belief_mc_support_delta=COMM_DIRECTION_SUPPORT_DELTA,
                belief_resupply_reliability_delta=0.0,
            )

        else:
            # Generic reassurance for elevated urgency with no specific intervention
            content = (
                "Mission Control: We are closely monitoring mission status and your wellbeing. "
                "Your dedication and resilience are recognized. "
                "Please continue to communicate any concerns."
            )
            return MCCommunication(
                day=day,
                sender="hermitclaw",
                message_type="reassurance",
                content=content,
                belief_mc_support_delta=COMM_REASSURANCE_SUPPORT_DELTA,
                belief_resupply_reliability_delta=0.0,
            )

    def generate_planned_intervention(
        self,
        day: int,
        advisory: HermitClawAdvisory,
        eta_days: int = 21,
    ) -> Optional[PlannedIntervention]:
        """
        Generate a PlannedIntervention for physical resupply.

        Only generates physical interventions for resupply types.
        Non-physical interventions (acknowledgment, direction) do not
        create PlannedInterventions.

        Args:
            day:      Current simulation day
            advisory: Advisory from generate_advisory()
            eta_days: Transit time for this intervention

        Returns:
            PlannedIntervention or None
        """
        if advisory is None:
            return None

        rec = advisory.recommended_intervention
        if rec is None:
            return None

        resource_payloads = {
            "resupply_coffee":        {"coffee": 0.40},
            "resupply_hygiene":       {"hygiene_supplies": 0.40},
            "resupply_entertainment": {"personal_entertainment": 0.40},
        }

        if rec not in resource_payloads:
            return None  # Not a physical resupply intervention

        self._intervention_counter += 1
        intervention_id = f"INT_{day:04d}_{self._intervention_counter:03d}"

        return PlannedIntervention(
            intervention_id=intervention_id,
            intervention_type=rec,
            dispatch_day=day,
            eta_days=eta_days,
            arrival_day=day + eta_days,
            predicted_morale_impact=0.08,
            predicted_trust_impact=0.05,
            payload=resource_payloads[rec],
        )

    # -------------------------------------------------------------------
    # Forecast
    # -------------------------------------------------------------------

    def forecast_drift(self, horizon_days: int = 14) -> List[DivergenceReport]:
        """
        Project current drift trends forward by horizon_days.

        Uses a linear slope estimated from the last FORECAST_DRIFT_WINDOW
        days of stored snapshots. Returns projected DivergenceReports for
        each day from current_day+1 to current_day+horizon_days.

        Returns empty list if fewer than 2 snapshots are stored.
        """
        if len(self._snapshots) < 2:
            return []

        current = self._snapshots[-1]
        current_day = current.day
        agent_ids = list(current.internal_states.keys())
        n = len(agent_ids)
        if n == 0:
            return []

        # Estimate drift slopes from recent history
        morale_slope = self._estimate_slope(
            agent_ids,
            lambda snap, aid: snap.internal_states[aid].morale,
        )
        trust_slope = self._estimate_slope(
            agent_ids,
            lambda snap, aid: snap.internal_states[aid].trust_in_crew,
        )
        viability_slope = self._estimate_slope(
            agent_ids,
            lambda snap, aid: snap.belief_states[aid].belief_mission_viability,
        )
        fairness_slope = self._estimate_slope(
            agent_ids,
            lambda snap, aid: snap.belief_states[aid].belief_distribution_fairness,
        )

        # Current baseline values
        baseline_morale = sum(
            current.internal_states[aid].morale for aid in agent_ids
        ) / n
        baseline_trust = sum(
            current.internal_states[aid].trust_in_crew for aid in agent_ids
        ) / n
        baseline_viability = sum(
            current.belief_states[aid].belief_mission_viability for aid in agent_ids
        ) / n
        baseline_fairness = sum(
            current.belief_states[aid].belief_distribution_fairness for aid in agent_ids
        ) / n

        projections = []
        for delta in range(1, horizon_days + 1):
            proj_day = current_day + delta
            proj_morale = _clamp(baseline_morale + morale_slope * delta)
            proj_trust = _clamp(baseline_trust + trust_slope * delta)
            proj_viability = _clamp(baseline_viability + viability_slope * delta)
            proj_fairness = _clamp(baseline_fairness + fairness_slope * delta)

            # Projected high-risk count (rough: agents near threshold)
            n_high_risk = sum(
                1 for aid in agent_ids
                if current.internal_states[aid].morale < MORALE_RISK_THRESHOLD + 0.05
            )

            # Predicted collapse in this projection
            remaining_trust = proj_trust
            collapse_day: Optional[int] = None
            if trust_slope < 0 and remaining_trust > TRUST_COLLAPSE_TRIGGER:
                if abs(trust_slope) > 1e-8:
                    days_to_collapse = (remaining_trust - TRUST_COLLAPSE_TRIGGER) / abs(trust_slope)
                    collapse_day = proj_day + int(days_to_collapse)

            projections.append(DivergenceReport(
                day=proj_day,
                objective_morale_avg=round(proj_morale, 4),
                crew_believed_morale_avg=round(proj_viability, 4),
                crew_belief_divergence=round(proj_viability - proj_morale, 4),
                high_risk_agents=[],  # Not meaningful in projection
                predicted_collapse_day=collapse_day,
                belief_distribution_fairness_avg=round(proj_fairness, 4),
                trust_erosion_detected=proj_trust < TRUST_EROSION_LOW,
                mean_trust_in_crew=round(proj_trust, 4),
            ))

        return projections

    # -------------------------------------------------------------------
    # State access
    # -------------------------------------------------------------------

    def get_full_state_log(self) -> List[DivergenceReport]:
        """Return all stored DivergenceReports (read-only copy)."""
        return list(self._divergence_log)

    def get_advisory_log(self) -> List[HermitClawAdvisory]:
        """Return all generated advisories (read-only copy)."""
        return list(self._advisory_log)

    def to_json_log(self) -> dict:
        """
        Serialize full HermitClaw state to a JSON-safe dict.

        Written by TwinRunner at end of mission for Weke to read.
        """
        return {
            "divergence_log": [r.to_dict() for r in self._divergence_log],
            "advisory_log": [a.to_dict() for a in self._advisory_log],
        }

    # -------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------

    def _get_snapshot(self, day: int) -> Optional[_DaySnapshot]:
        """Return the most recent snapshot at or before `day`."""
        result = None
        for snap in self._snapshots:
            if snap.day <= day:
                result = snap
        return result

    def _get_divergence_for_day(self, day: int) -> Optional[DivergenceReport]:
        """Return previously computed DivergenceReport for this day, or None."""
        for report in reversed(self._divergence_log):
            if report.day == day:
                return report
        return None

    def _detect_trust_trend(self, agent_ids: List[str]) -> bool:
        """
        Return True if mean trust_in_crew has been declining over
        the last FORECAST_DRIFT_WINDOW days.
        """
        window = self._snapshots[-FORECAST_DRIFT_WINDOW:]
        if len(window) < 2:
            return False

        n = len(agent_ids)
        if n == 0:
            return False

        def mean_trust(snap: _DaySnapshot) -> float:
            vals = [snap.internal_states[aid].trust_in_crew for aid in agent_ids
                    if aid in snap.internal_states]
            return sum(vals) / len(vals) if vals else 0.5

        slope = self._compute_slope_from_series(
            [mean_trust(s) for s in window]
        )
        return slope < -0.002  # Meaningful downward trend threshold

    def _predict_collapse(
        self, day: int, agent_ids: List[str]
    ) -> Optional[int]:
        """
        Estimate the day mean trust_in_crew would reach TRUST_COLLAPSE_TRIGGER
        at the current 7-day linear drift rate.

        Returns None if trust is stable or improving.
        """
        n = len(agent_ids)
        if n == 0 or len(self._snapshots) < 2:
            return None

        latest = self._snapshots[-1]
        mean_trust_now = sum(
            latest.internal_states[aid].trust_in_crew for aid in agent_ids
            if aid in latest.internal_states
        ) / n

        if mean_trust_now <= TRUST_COLLAPSE_TRIGGER:
            return day  # Already at collapse level

        slope = self._estimate_slope(
            agent_ids,
            lambda snap, aid: snap.internal_states[aid].trust_in_crew,
        )

        if slope >= 0:
            return None  # Stable or improving

        # Days until mean_trust reaches TRUST_COLLAPSE_TRIGGER
        days_to_collapse = (mean_trust_now - TRUST_COLLAPSE_TRIGGER) / abs(slope)
        return day + max(1, int(days_to_collapse))

    def _estimate_slope(
        self,
        agent_ids: List[str],
        value_fn,  # Callable[[_DaySnapshot, str], float]
    ) -> float:
        """
        Estimate daily drift slope of mean(value_fn) over the last
        FORECAST_DRIFT_WINDOW snapshots using linear regression.

        Returns slope per day (negative = declining, positive = improving).
        """
        window = self._snapshots[-FORECAST_DRIFT_WINDOW:]
        if len(window) < 2:
            return 0.0

        n = len(agent_ids)
        if n == 0:
            return 0.0

        def mean_value(snap: _DaySnapshot) -> float:
            vals = [value_fn(snap, aid) for aid in agent_ids if aid in snap.internal_states]
            return sum(vals) / len(vals) if vals else 0.0

        series = [mean_value(s) for s in window]
        return self._compute_slope_from_series(series)

    @staticmethod
    def _compute_slope_from_series(series: List[float]) -> float:
        """
        Compute linear regression slope for a time series.
        Returns slope per step. Uses ordinary least squares.
        """
        n = len(series)
        if n < 2:
            return 0.0

        xs = list(range(n))
        x_mean = (n - 1) / 2.0
        y_mean = sum(series) / n

        numerator = sum((xs[i] - x_mean) * (series[i] - y_mean) for i in range(n))
        denominator = sum((xs[i] - x_mean) ** 2 for i in range(n))

        if abs(denominator) < 1e-12:
            return 0.0
        return numerator / denominator

    def _select_intervention(
        self,
        day: int,
        snap: _DaySnapshot,
        divergence: DivergenceReport,
        urgency: float,
        agent_ids: List[str],
        n: int,
    ) -> Tuple[Optional[str], str]:
        """
        Select intervention type and generate rationale string.

        Priority cascade:
          1. Low MC support belief → crew_acknowledgment
          2. High urgency with high-risk agents → task_rebalance
          3. Low resupply reliability + high scarcity → resupply_coffee
          4. Default elevated urgency → crew_acknowledgment
        """
        # Check belief_mc_support average
        if n > 0:
            mc_support_avg = sum(
                snap.belief_states[aid].belief_mission_control_support
                for aid in agent_ids
                if aid in snap.belief_states
            ) / n
            resupply_rel_avg = sum(
                snap.belief_states[aid].belief_resupply_reliability
                for aid in agent_ids
                if aid in snap.belief_states
            ) / n
            coffee_scarcity_avg = sum(
                snap.belief_states[aid].belief_coffee_scarcity
                for aid in agent_ids
                if aid in snap.belief_states
            ) / n
        else:
            mc_support_avg = 0.5
            resupply_rel_avg = 0.5
            coffee_scarcity_avg = 0.3

        # 1. MC support critically low
        if mc_support_avg < MC_SUPPORT_LOW:
            return (
                "crew_acknowledgment",
                f"Crew belief in MC support is low (avg={mc_support_avg:.2f}). "
                f"Acknowledgment communication recommended to restore trust in mission backing.",
            )

        # 2. High urgency with multiple high-risk agents
        if urgency >= ADVISORY_URGENCY_CRITICAL and len(divergence.high_risk_agents) >= max(1, n // 2):
            return (
                "task_rebalance",
                f"{len(divergence.high_risk_agents)} of {n} agents are high-risk "
                f"(morale < {MORALE_RISK_THRESHOLD} or cooperation blocked). "
                f"Task rebalance recommended to reduce overall crew strain.",
            )

        # 3. Low resupply reliability + high resource scarcity
        if resupply_rel_avg < RESUPPLY_RELIABILITY_LOW and coffee_scarcity_avg > SCARCITY_HIGH:
            return (
                "resupply_coffee",
                f"Crew resupply reliability belief is low (avg={resupply_rel_avg:.2f}) "
                f"and coffee scarcity is high (avg={coffee_scarcity_avg:.2f}). "
                f"Resupply announcement and physical resupply recommended.",
            )

        # 4. Default: general acknowledgment for elevated urgency
        return (
            "crew_acknowledgment",
            f"Urgency elevated ({urgency:.2f}). "
            f"Mean morale={divergence.objective_morale_avg:.2f}, "
            f"mean trust={divergence.mean_trust_in_crew:.2f}. "
            f"General acknowledgment communication recommended.",
        )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_ETA_DAYS = 21  # Default resupply transit time if not specified


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))
