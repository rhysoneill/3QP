"""
Belief Engine — Per-agent named belief state updated from perception only.

DESIGN CONTRACT:
    Beliefs are updated exclusively from PerceivedState.
    They NEVER read from objective ResourceState directly.
    The causal chain is:
        ResourceState → PerceivedState → AstronautBeliefState → InternalStateDrift

    Key behavioral properties:
        - Beliefs have inertia: they change slowly unless perception is extreme
        - Personality modulates inertia (neuroticism reduces it, conscientiousness increases it)
        - MC comms immediately update belief_mc_support and belief_resupply_reliability
        - A promised resupply that is overdue degrades reliability belief sharply
        - Agents can stabilize or improve belief_mission_viability under scarcity
          if belief_distribution_fairness and belief_resupply_reliability remain high
        - No time-indexed drift terms anywhere in this module
"""

from dataclasses import dataclass
from typing import Optional

from crew.profile import PersonalityScores
from perception.perception_model import PerceivedState
from beliefs.belief_types import (
    INERTIA_COFFEE_SCARCITY,
    INERTIA_DISTRIBUTION_FAIRNESS,
    INERTIA_RESUPPLY_RELIABILITY,
    INERTIA_MC_SUPPORT,
    INERTIA_CREW_COHESION,
    INERTIA_MISSION_VIABILITY,
    MC_SUPPORT_BOOST_REASSURANCE,
    MC_SUPPORT_BOOST_ACKNOWLEDGMENT,
    MC_SUPPORT_BOOST_DIRECTION,
    MC_SUPPORT_BOOST_SUPPORT,
    MC_SUPPORT_BOOST_DEFAULT,
    MC_RELIABILITY_BOOST_PROMISE,
    MC_RELIABILITY_BOOST_ARRIVAL,
    MC_RELIABILITY_DECAY_OVERDUE,
    MC_SUPPORT_DECAY_OVERDUE,
    VIABILITY_SCARCITY_WEIGHT,
    VIABILITY_FAIRNESS_WEIGHT,
    VIABILITY_MC_SUPPORT_WEIGHT,
    VIABILITY_COHESION_WEIGHT,
    NEUROTICISM_INERTIA_FACTOR,
    CONSCIENTIOUSNESS_INERTIA_FACTOR,
)


# ---------------------------------------------------------------------------
# Belief State
# ---------------------------------------------------------------------------

@dataclass
class AstronautBeliefState:
    """
    Per-astronaut named belief state.

    All values are [0.0, 1.0]. These are subjective beliefs, not objective facts.
    They are updated from PerceivedState only.

    Attributes:
        agent_id:                     Which agent holds these beliefs
        day:                          When this state was computed
        belief_coffee_scarcity:       0=believe plenty available, 1=believe critically scarce
        belief_distribution_fairness: 0=believe distribution is unfair, 1=believe it is fair
        belief_resupply_reliability:  0=believe MC will not deliver, 1=believe MC will deliver
        belief_mission_control_support: 0=believe MC doesn't care, 1=believe MC is engaged
        belief_crew_cohesion:         0=believe crew is fragmented, 1=believe crew is united
        belief_mission_viability:     0=resigned/hopeless, 1=hopeful/mission meaningful
    """
    agent_id: str
    day: int
    belief_coffee_scarcity: float = 0.0
    belief_distribution_fairness: float = 1.0
    belief_resupply_reliability: float = 0.8
    belief_mission_control_support: float = 0.7
    belief_crew_cohesion: float = 0.9
    belief_mission_viability: float = 0.8

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "belief_coffee_scarcity": round(self.belief_coffee_scarcity, 4),
            "belief_distribution_fairness": round(self.belief_distribution_fairness, 4),
            "belief_resupply_reliability": round(self.belief_resupply_reliability, 4),
            "belief_mission_control_support": round(self.belief_mission_control_support, 4),
            "belief_crew_cohesion": round(self.belief_crew_cohesion, 4),
            "belief_mission_viability": round(self.belief_mission_viability, 4),
        }

    @classmethod
    def default(cls, agent_id: str, day: int = 0) -> "AstronautBeliefState":
        """Return default initial belief state for a new mission."""
        return cls(agent_id=agent_id, day=day)


# ---------------------------------------------------------------------------
# Belief Update Engine
# ---------------------------------------------------------------------------

class BeliefUpdateEngine:
    """
    Updates one agent's belief state from their PerceivedState.

    Stateless across calls — prior belief is passed in each update.
    Personality is fixed at construction.

    No time-indexed terms. All drift traces to perception inputs.
    """

    def __init__(self, agent_id: str, personality: PersonalityScores):
        """
        Args:
            agent_id:    ID of the agent whose beliefs this engine manages
            personality: Big Five personality scores (used to modulate inertia)
        """
        self._agent_id = agent_id
        self._personality = personality
        # Precompute personality-adjusted inertia modifier
        # Neuroticism reduces inertia (more reactive to perception)
        # Conscientiousness increases inertia (requires more evidence)
        self._inertia_delta = (
            -(personality.neuroticism - 0.5) * NEUROTICISM_INERTIA_FACTOR
            + (personality.conscientiousness - 0.5) * CONSCIENTIOUSNESS_INERTIA_FACTOR
        )

    def update(
        self,
        perceived: PerceivedState,
        prior: AstronautBeliefState,
        resupply_arrived_today: bool = False,
        resupply_overdue_days: int = 0,
    ) -> AstronautBeliefState:
        """
        Compute new belief state for today.

        Args:
            perceived:               This agent's perceived state for today
            prior:                   Prior belief state (yesterday's output)
            resupply_arrived_today:  Whether a promised resupply physically arrived today
            resupply_overdue_days:   How many days past ETA the promised resupply is (0 = on time)

        Returns:
            New AstronautBeliefState for today
        """
        assert perceived.agent_id == self._agent_id, (
            f"Perceived state agent_id '{perceived.agent_id}' "
            f"does not match engine agent_id '{self._agent_id}'"
        )

        # --- Coffee scarcity belief ---
        coffee_scarcity = self._converge(
            prior.belief_coffee_scarcity,
            perceived.perceived_coffee_scarcity,
            INERTIA_COFFEE_SCARCITY,
        )

        # --- Distribution fairness belief ---
        fairness = self._converge(
            prior.belief_distribution_fairness,
            perceived.perceived_distribution_fairness,
            INERTIA_DISTRIBUTION_FAIRNESS,
        )

        # --- Resupply reliability belief ---
        reliability = self._update_reliability(
            prior.belief_resupply_reliability,
            perceived.perceived_comms_reliability,
            resupply_arrived_today,
            resupply_overdue_days,
        )

        # --- Mission Control support belief ---
        mc_support = self._update_mc_support(
            prior.belief_mission_control_support,
            perceived.perceived_mission_support,
            resupply_overdue_days,
        )

        # --- Crew cohesion belief ---
        # Derived from inverse of perceived social tension
        target_cohesion = 1.0 - perceived.perceived_social_tension
        cohesion = self._converge(
            prior.belief_crew_cohesion,
            target_cohesion,
            INERTIA_CREW_COHESION,
        )

        # --- Mission viability belief ---
        viability = self._update_viability(
            prior.belief_mission_viability,
            coffee_scarcity,
            fairness,
            mc_support,
            cohesion,
        )

        return AstronautBeliefState(
            agent_id=self._agent_id,
            day=perceived.day,
            belief_coffee_scarcity=coffee_scarcity,
            belief_distribution_fairness=fairness,
            belief_resupply_reliability=reliability,
            belief_mission_control_support=mc_support,
            belief_crew_cohesion=cohesion,
            belief_mission_viability=viability,
        )

    # -------------------------------------------------------------------
    # Internal update helpers
    # -------------------------------------------------------------------

    def _converge(self, prior: float, target: float, base_inertia: float) -> float:
        """
        Move prior toward target with personality-adjusted inertia.

        inertia = base_inertia + personality_delta
        new = prior * inertia + target * (1 - inertia)
        """
        inertia = _clamp(base_inertia + self._inertia_delta)
        return _clamp(prior * inertia + target * (1.0 - inertia))

    def _update_reliability(
        self,
        prior: float,
        perceived_comms_reliability: float,
        resupply_arrived: bool,
        overdue_days: int,
    ) -> float:
        """
        Update belief_resupply_reliability.

        - Base: converge toward perceived comms reliability (slow)
        - Resupply arrived on time: significant boost
        - Overdue: decay per day past ETA
        """
        # Base convergence
        base = self._converge(
            prior,
            perceived_comms_reliability,
            INERTIA_RESUPPLY_RELIABILITY,
        )

        if resupply_arrived:
            # Arrived — significant trust boost
            base = _clamp(base + MC_RELIABILITY_BOOST_ARRIVAL)

        if overdue_days > 0:
            # Each day past ETA erodes reliability belief
            decay = overdue_days * MC_RELIABILITY_DECAY_OVERDUE
            base = _clamp(base - decay)

        return base

    def _update_mc_support(
        self,
        prior: float,
        perceived_mission_support: float,
        overdue_days: int,
    ) -> float:
        """
        Update belief_mission_control_support.

        - Base: converge toward perceived mission support
        - Overdue resupply: additional decay per day (broken promise effect)
        """
        base = self._converge(
            prior,
            perceived_mission_support,
            INERTIA_MC_SUPPORT,
        )

        if overdue_days > 0:
            # Broken promise erodes institutional trust
            decay = overdue_days * MC_SUPPORT_DECAY_OVERDUE
            base = _clamp(base - decay)

        return base

    def _update_viability(
        self,
        prior: float,
        coffee_scarcity: float,
        fairness: float,
        mc_support: float,
        cohesion: float,
    ) -> float:
        """
        Update belief_mission_viability (hope vs. resignation).

        Viability target is a weighted composite of current belief conditions.
        Agents CAN maintain or improve viability under scarcity if:
            - Distribution is believed fair
            - MC support is believed reliable
            - Crew cohesion is believed strong

        No time-indexed terms. All drivers are belief inputs.
        """
        # Target viability from current belief environment
        # High scarcity belief pulls down; high fairness, support, cohesion pull up
        target = (
            (1.0 - coffee_scarcity) * VIABILITY_SCARCITY_WEIGHT
            + fairness * VIABILITY_FAIRNESS_WEIGHT
            + mc_support * VIABILITY_MC_SUPPORT_WEIGHT
            + cohesion * VIABILITY_COHESION_WEIGHT
        )
        # Normalize to [0.0, 1.0] (weights already sum to 1.0)
        target = _clamp(target)

        return self._converge(prior, target, INERTIA_MISSION_VIABILITY)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
