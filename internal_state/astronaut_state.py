"""
Internal State Drift — Per-astronaut psychological and physiological state.

DESIGN CONTRACT:
    Internal state variables are driven ONLY by:
        - AstronautBeliefState (named beliefs from the belief layer)
        - PerceivedState (for perception inputs not yet encoded as beliefs)
        - SocialProximityMap (current dyadic trust weights)

    Internal state does NOT:
        - Read from objective ResourceState directly
        - Have time-indexed drift terms (no += f(day))
        - Respond to simulation day number

    Behavioral drift invariants enforced here:
        - All state changes trace to a named belief or perception input
        - Agents can improve any state variable if supporting beliefs improve
        - Isolation duration and scarcity alone do not push state in any direction
        - cooperation_threshold is derived — never set directly
"""

from dataclasses import dataclass
from typing import Optional

from crew.profile import PersonalityScores
from beliefs.belief_engine import AstronautBeliefState
from perception.perception_model import PerceivedState, SocialProximityMap


# ---------------------------------------------------------------------------
# Drift Coefficients (all named, no magic numbers)
# ---------------------------------------------------------------------------

# Stress drivers (per unit of belief input, per day)
STRESS_SCARCITY_RATE       = 0.060   # belief_coffee_scarcity drives stress
STRESS_MC_NEGLECT_RATE     = 0.030   # (1 - belief_mc_support) drives stress
STRESS_UNFAIRNESS_RATE     = 0.040   # (1 - belief_distribution_fairness) drives stress

# Stress recovery
STRESS_MORALE_RECOVERY     = 0.025   # High morale counters stress accumulation
STRESS_INERTIA             = 0.80    # How quickly stress changes

# Morale drivers
MORALE_VIABILITY_RATE      = 0.050   # belief_mission_viability boosts morale
MORALE_SUPPORT_RATE        = 0.025   # belief_mc_support boosts morale
MORALE_COHESION_RATE       = 0.025   # belief_crew_cohesion boosts morale
MORALE_STRESS_DRAG         = 0.030   # High stress pulls morale down
MORALE_INERTIA             = 0.82

# Fatigue drivers
FATIGUE_STRESS_RATE        = 0.045   # Stress accumulates fatigue
FATIGUE_TASK_LOAD_RATE     = 0.030   # High task load increases fatigue
FATIGUE_SLEEP_RECOVERY     = 0.055   # Good sleep recovers fatigue
FATIGUE_INERTIA            = 0.85    # Fatigue changes slowly

# Boredom drivers
BOREDOM_DISENGAGEMENT_RATE = 0.040   # Low viability → boredom
BOREDOM_SCARCITY_RATE      = 0.015   # Scarcity without novelty adds boredom
BOREDOM_ENGAGEMENT_RECOVERY = 0.050  # Engagement (high cooperation) reduces boredom
BOREDOM_INERTIA            = 0.88    # Boredom is very sticky

# Frustration drivers
FRUSTRATION_SCARCITY_RATE  = 0.055   # Scarcity belief drives frustration
FRUSTRATION_FAIRNESS_RATE  = 0.065   # Unfairness belief drives frustration
FRUSTRATION_RECOVERY_RATE  = 0.035   # MC support reduces frustration
FRUSTRATION_INERTIA        = 0.78    # Frustration resolves fairly quickly with evidence

# Cooperation threshold computations (higher = harder to cooperate)
COOP_THRESHOLD_STRESS_WEIGHT     = 0.45
COOP_THRESHOLD_FATIGUE_WEIGHT    = 0.25
COOP_THRESHOLD_FRUSTRATION_WEIGHT = 0.30

# Personality modulation of drift sensitivity
NEUROTICISM_SENSITIVITY    = 0.20    # How much neuroticism amplifies negative inputs
AGREEABLENESS_BUFFER       = 0.15    # How much agreeableness buffers negative inputs


# ---------------------------------------------------------------------------
# Internal State
# ---------------------------------------------------------------------------

@dataclass
class AstronautInternalState:
    """
    Per-astronaut psychological and physiological state for one day.

    All values are [0.0, 1.0]. Changes trace to belief inputs, never to time.

    Attributes:
        agent_id:               Which agent holds this state
        day:                    When this state was computed
        stress:                 Psychological stress load (0=calm, 1=overwhelmed)
        morale:                 Motivation and positive affect (0=depleted, 1=high)
        fatigue:                Physical and mental exhaustion (0=rested, 1=exhausted)
        boredom:                Disengagement from mission (0=engaged, 1=disengaged)
        trust_in_crew:          Felt trust toward crew (0=no trust, 1=full trust)
        frustration_scarcity:   Resource-related grievance level (0=none, 1=extreme)
        future_outlook:         Hope vs resignation (0=resigned, 1=hopeful)
        cooperation_threshold:  Derived: friction to cooperative behavior (0=easy, 1=blocked)
    """
    agent_id: str
    day: int
    stress: float = 0.15
    morale: float = 0.80
    fatigue: float = 0.20
    boredom: float = 0.10
    trust_in_crew: float = 0.85
    frustration_scarcity: float = 0.05
    future_outlook: float = 0.80
    cooperation_threshold: float = 0.25

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "stress": round(self.stress, 4),
            "morale": round(self.morale, 4),
            "fatigue": round(self.fatigue, 4),
            "boredom": round(self.boredom, 4),
            "trust_in_crew": round(self.trust_in_crew, 4),
            "frustration_scarcity": round(self.frustration_scarcity, 4),
            "future_outlook": round(self.future_outlook, 4),
            "cooperation_threshold": round(self.cooperation_threshold, 4),
        }

    @classmethod
    def default(cls, agent_id: str, day: int = 0) -> "AstronautInternalState":
        """Return initial internal state for mission start."""
        return cls(agent_id=agent_id, day=day)


# ---------------------------------------------------------------------------
# State Drift Engine
# ---------------------------------------------------------------------------

class StateDriftEngine:
    """
    Computes one day's internal state drift from belief and perception inputs.

    All drift equations are explicit, named, and belief-driven.
    No time-indexed terms anywhere in this class.
    """

    def __init__(self, agent_id: str, personality: PersonalityScores):
        """
        Args:
            agent_id:    ID of the agent whose state this engine models
            personality: Big Five personality scores (modulate drift sensitivity)
        """
        self._agent_id = agent_id
        self._personality = personality

        # Precompute personality sensitivity modifier
        # Neuroticism amplifies negative inputs; agreeableness buffers them
        p = personality
        self._neg_amplifier = 1.0 + (p.neuroticism - 0.5) * NEUROTICISM_SENSITIVITY
        self._pos_buffer    = 1.0 + (p.agreeableness - 0.5) * AGREEABLENESS_BUFFER

    def step(
        self,
        prior: AstronautInternalState,
        belief: AstronautBeliefState,
        perceived: PerceivedState,
        social_proximity: SocialProximityMap,
        day: int,
    ) -> AstronautInternalState:
        """
        Compute new internal state for today.

        Args:
            prior:            Yesterday's internal state
            belief:           Today's belief state (from BeliefUpdateEngine)
            perceived:        Today's perceived state (from PerceptionEngine)
            social_proximity: Current social adjacency weights
            day:              Current simulation day

        Returns:
            New AstronautInternalState for today
        """
        assert prior.agent_id == self._agent_id
        assert belief.agent_id == self._agent_id
        assert perceived.agent_id == self._agent_id

        # 1. Stress
        stress = self._compute_stress(prior.stress, prior.morale, belief)

        # 2. Morale
        morale = self._compute_morale(prior.morale, stress, belief)

        # 3. Fatigue (uses perceived sleep quality as recovery input)
        fatigue = self._compute_fatigue(prior.fatigue, stress, perceived)

        # 4. Boredom
        boredom = self._compute_boredom(prior.boredom, belief, stress)

        # 5. Trust in crew (tracks dyadic social proximity)
        trust_in_crew = self._compute_trust_in_crew(prior.trust_in_crew, social_proximity)

        # 6. Frustration with resource scarcity
        frustration = self._compute_frustration(prior.frustration_scarcity, belief)

        # 7. Future outlook (tracks belief_mission_viability closely)
        future_outlook = self._converge(
            prior.future_outlook,
            belief.belief_mission_viability,
            inertia=0.82,
        )

        # 8. Cooperation threshold (derived from stress, fatigue, frustration)
        cooperation_threshold = self._compute_cooperation_threshold(
            stress, fatigue, frustration
        )

        return AstronautInternalState(
            agent_id=self._agent_id,
            day=day,
            stress=stress,
            morale=morale,
            fatigue=fatigue,
            boredom=boredom,
            trust_in_crew=trust_in_crew,
            frustration_scarcity=frustration,
            future_outlook=future_outlook,
            cooperation_threshold=cooperation_threshold,
        )

    def compute_cooperation_threshold(
        self, state: AstronautInternalState
    ) -> float:
        """
        Compute cooperation_threshold from a state snapshot.
        High threshold = agent will disengage or withdraw.
        Low threshold = agent cooperates readily.
        """
        return self._compute_cooperation_threshold(
            state.stress, state.fatigue, state.frustration_scarcity
        )

    # -------------------------------------------------------------------
    # Individual drift equations (all belief-driven, no time terms)
    # -------------------------------------------------------------------

    def _compute_stress(
        self,
        prior_stress: float,
        prior_morale: float,
        belief: AstronautBeliefState,
    ) -> float:
        """
        Stress target from belief inputs.

        Drivers:
            + belief_coffee_scarcity (scarcity → vigilance → stress)
            + (1 - belief_mc_support) (feeling unsupported → stress)
            + (1 - belief_distribution_fairness) (injustice → stress)
            - morale acts as stress buffer

        No time term. Stress can be zero if beliefs are all positive.
        """
        raw_target = (
            belief.belief_coffee_scarcity * STRESS_SCARCITY_RATE
            + (1.0 - belief.belief_mission_control_support) * STRESS_MC_NEGLECT_RATE
            + (1.0 - belief.belief_distribution_fairness) * STRESS_UNFAIRNESS_RATE
            - prior_morale * STRESS_MORALE_RECOVERY
        )
        target = _clamp(raw_target) * self._neg_amplifier
        return self._converge(prior_stress, _clamp(target), STRESS_INERTIA)

    def _compute_morale(
        self,
        prior_morale: float,
        current_stress: float,
        belief: AstronautBeliefState,
    ) -> float:
        """
        Morale target from belief inputs.

        Drivers:
            + belief_mission_viability (sense of purpose → morale)
            + belief_mc_support (feeling backed up → morale)
            + belief_crew_cohesion (solidarity → morale)
            - stress (high stress erodes morale)
        """
        raw_target = (
            belief.belief_mission_viability * MORALE_VIABILITY_RATE
            + belief.belief_mission_control_support * MORALE_SUPPORT_RATE
            + belief.belief_crew_cohesion * MORALE_COHESION_RATE
            - current_stress * MORALE_STRESS_DRAG
        )
        # Normalize: max possible target is 0.10, needs remapping
        # Use as delta applied to prior rather than absolute target
        delta = raw_target
        new_morale = _clamp(prior_morale + delta * self._pos_buffer)
        # Blend with inertia
        return self._converge(prior_morale, new_morale, MORALE_INERTIA)

    def _compute_fatigue(
        self,
        prior_fatigue: float,
        current_stress: float,
        perceived: PerceivedState,
    ) -> float:
        """
        Fatigue from stress accumulation and sleep quality recovery.

        Drivers:
            + stress (chronic stress → fatigue accumulation)
            + task pressure encoded via stress
            - perceived_sleep_quality (good sleep recovers fatigue)
        """
        raw_target = (
            current_stress * FATIGUE_STRESS_RATE
            - perceived.perceived_sleep_quality * FATIGUE_SLEEP_RECOVERY
        )
        delta = raw_target
        new_fatigue = _clamp(prior_fatigue + delta)
        return self._converge(prior_fatigue, new_fatigue, FATIGUE_INERTIA)

    def _compute_boredom(
        self,
        prior_boredom: float,
        belief: AstronautBeliefState,
        current_stress: float,
    ) -> float:
        """
        Boredom from low mission engagement.

        Drivers:
            + (1 - belief_mission_viability) — resignation maps to boredom
            + belief_coffee_scarcity — scarcity without novelty adds disengagement
            - belief_crew_cohesion — active social bonds reduce boredom
            - stress partially reduces boredom (anxious is not bored)
        """
        target = (
            (1.0 - belief.belief_mission_viability) * BOREDOM_DISENGAGEMENT_RATE
            + belief.belief_coffee_scarcity * BOREDOM_SCARCITY_RATE
            - belief.belief_crew_cohesion * BOREDOM_ENGAGEMENT_RECOVERY
            - current_stress * 0.5 * BOREDOM_ENGAGEMENT_RECOVERY
        )
        target = _clamp(target)
        return self._converge(prior_boredom, target, BOREDOM_INERTIA)

    def _compute_trust_in_crew(
        self,
        prior_trust: float,
        social_proximity: SocialProximityMap,
    ) -> float:
        """
        Trust in crew tracks the social graph mean edge weight.

        Agent with no neighbors defaults to neutral trust.
        High agreeableness buffers trust decay.
        """
        graph_trust = social_proximity.mean_trust()
        # Blend: prior with high inertia (trust changes slowly)
        blended = self._converge(prior_trust, graph_trust, inertia=0.80)
        # Agreeableness provides a floor
        floor = self._personality.agreeableness * 0.25
        return max(blended, floor)

    def _compute_frustration(
        self,
        prior_frustration: float,
        belief: AstronautBeliefState,
    ) -> float:
        """
        Frustration from resource scarcity + perceived unfairness.

        Drivers:
            + belief_coffee_scarcity (scarcity → frustration)
            + (1 - belief_distribution_fairness) (unfairness → frustration)
            - belief_mc_support (feeling supported reduces frustration)
            - belief_resupply_reliability (hope of relief reduces frustration)
        """
        target = (
            belief.belief_coffee_scarcity * FRUSTRATION_SCARCITY_RATE
            + (1.0 - belief.belief_distribution_fairness) * FRUSTRATION_FAIRNESS_RATE
            - belief.belief_mission_control_support * FRUSTRATION_RECOVERY_RATE
            - belief.belief_resupply_reliability * FRUSTRATION_RECOVERY_RATE * 0.5
        )
        target = _clamp(target) * self._neg_amplifier
        return self._converge(prior_frustration, _clamp(target), FRUSTRATION_INERTIA)

    def _compute_cooperation_threshold(
        self,
        stress: float,
        fatigue: float,
        frustration: float,
    ) -> float:
        """
        cooperation_threshold: friction to cooperative behavior.

        High threshold → agent likely to WITHDRAW or ESCALATE.
        Low threshold → agent cooperates readily.

        Derived from stress, fatigue, and frustration with personality buffer.
        No external inputs — purely computed from current state.
        """
        raw = (
            stress * COOP_THRESHOLD_STRESS_WEIGHT
            + fatigue * COOP_THRESHOLD_FATIGUE_WEIGHT
            + frustration * COOP_THRESHOLD_FRUSTRATION_WEIGHT
        )
        # Agreeableness raises the bar before threshold is reached
        buffered = raw / self._pos_buffer
        return _clamp(buffered)

    def _converge(self, prior: float, target: float, inertia: float) -> float:
        """Move prior toward target at given inertia rate."""
        return _clamp(prior * inertia + target * (1.0 - inertia))


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
