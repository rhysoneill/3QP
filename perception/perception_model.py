"""
Perception Layer — Per-agent filtered view of objective resource reality.

Each astronaut perceives the simulation environment through the lens of their
personality, social position, and prior experience with Mission Control.

DESIGN CONTRACT:
    Perception is per-agent and non-shared.
    Two agents observing the same ResourceState may form different PerceivedStates.

    Personality modulates perception:
        - High neuroticism → amplifies scarcity signals
        - High agreeableness → more tolerant of distribution inequality
        - High conscientiousness → more attentive to resource levels
        - High extraversion → more sensitive to social conflict signals

    Social proximity modulates information access:
        - Agents observe their immediate neighbors more accurately than distant agents
        - Distribution fairness is only perceived if the agent has visibility

    MC communications update perceived_mission_support immediately on receipt.
    Comms delay is perceived as a proxy for institutional reliability.

    Perception outputs flow ONLY to BeliefUpdateEngine.
    They never write to ResourceState or agent internal state.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crew.profile import PersonalityScores


# ---------------------------------------------------------------------------
# Supporting input types
# ---------------------------------------------------------------------------

@dataclass
class SocialProximityMap:
    """
    Simplified representation of an agent's social adjacency.

    Provides edge weights to neighbors — no full graph required here.
    Built by the twin runner from the SocialNetworkModule snapshot.

    Attributes:
        agent_id:           The focal agent
        neighbor_weights:   {other_agent_id: edge_weight [0.0, 1.0]}
    """
    agent_id: str
    neighbor_weights: Dict[str, float] = field(default_factory=dict)

    def mean_trust(self) -> float:
        """Average trust level toward all connected neighbors."""
        if not self.neighbor_weights:
            return 0.5  # No data — assume neutral
        return sum(self.neighbor_weights.values()) / len(self.neighbor_weights)

    def min_trust(self) -> float:
        """Minimum trust level among neighbors."""
        if not self.neighbor_weights:
            return 0.5
        return min(self.neighbor_weights.values())


@dataclass
class MCCommSignal:
    """
    Minimal signal representing a Mission Control communication received today.

    Kept separate from MCCommunication (mission_control layer) to avoid
    circular imports. The twin runner converts MCCommunication → MCCommSignal.

    Attributes:
        received:           Whether any communication was received today
        message_type:       "reassurance" | "direction" | "support" | "acknowledgment" | None
        resupply_promised:  Whether a resupply was promised in this comms
        eta_days:           If resupply promised, how many days until arrival
    """
    received: bool = False
    message_type: Optional[str] = None
    resupply_promised: bool = False
    eta_days: Optional[int] = None


# ---------------------------------------------------------------------------
# Perceived State
# ---------------------------------------------------------------------------

@dataclass
class PerceivedState:
    """
    One astronaut's subjective perception of mission resource reality.

    All values are [0.0, 1.0]. These are the agent's perception, NOT objective truth.
    They may diverge significantly from ResourceState depending on personality,
    social position, and communication history.

    Attributes:
        agent_id:                        Which agent holds this perception
        day:                             When this perception was formed
        perceived_coffee_scarcity:       0=plenty perceived, 1=critical scarcity perceived
        perceived_food_quality:          Agent's read of food quality/variety
        perceived_distribution_fairness: 0=unfair, 1=fair (their read of who gets what)
        perceived_comms_reliability:     0=MC unreachable/slow, 1=reliable
        perceived_mission_support:       0=neglected by MC, 1=actively supported
        perceived_social_tension:        0=crew calm, 1=high conflict observed
        perceived_sleep_quality:         Agent's experience of sleep conditions
    """
    agent_id: str
    day: int
    perceived_coffee_scarcity: float = 0.0
    perceived_food_quality: float = 1.0
    perceived_distribution_fairness: float = 1.0
    perceived_comms_reliability: float = 0.8
    perceived_mission_support: float = 0.7
    perceived_social_tension: float = 0.0
    perceived_sleep_quality: float = 0.85

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "perceived_coffee_scarcity": round(self.perceived_coffee_scarcity, 4),
            "perceived_food_quality": round(self.perceived_food_quality, 4),
            "perceived_distribution_fairness": round(self.perceived_distribution_fairness, 4),
            "perceived_comms_reliability": round(self.perceived_comms_reliability, 4),
            "perceived_mission_support": round(self.perceived_mission_support, 4),
            "perceived_social_tension": round(self.perceived_social_tension, 4),
            "perceived_sleep_quality": round(self.perceived_sleep_quality, 4),
        }


# ---------------------------------------------------------------------------
# Perception Engine
# ---------------------------------------------------------------------------

class PerceptionEngine:
    """
    Computes per-agent PerceivedState from objective ResourceState + context.

    Stateless — each call to compute_perception() produces a fresh PerceivedState.
    Personality coefficients are fixed at construction for each agent.
    """

    def __init__(self, agent_id: str, personality: PersonalityScores):
        """
        Args:
            agent_id:    ID of the agent whose perception this engine models
            personality: Big Five personality scores for this agent
        """
        self._agent_id = agent_id
        self._personality = personality

    def compute_perception(
        self,
        resource_state,             # ResourceState from resources layer
        social_proximity: SocialProximityMap,
        mc_signal: MCCommSignal,
        prior_mc_reliability: float,
        day: int,
    ) -> PerceivedState:
        """
        Compute this agent's subjective perception for today.

        Args:
            resource_state:         Objective resource state (ResourceState)
            social_proximity:       This agent's social adjacency weights
            mc_signal:              Any MC communication received today
            prior_mc_reliability:   Yesterday's perceived comms reliability [0.0, 1.0]
            day:                    Current simulation day

        Returns:
            PerceivedState reflecting this agent's perception
        """
        p = self._personality

        # --- Coffee scarcity ---
        # Objective scarcity: inverted stock level for this agent's share
        agent_coffee = resource_state.get_agent_level("coffee", self._agent_id)
        objective_scarcity = 1.0 - agent_coffee
        # Neuroticism amplifies scarcity perception
        scarcity_amplifier = 1.0 + (p.neuroticism - 0.5) * 0.6
        perceived_coffee_scarcity = _clamp(objective_scarcity * scarcity_amplifier)

        # --- Food quality ---
        agent_food = resource_state.get_agent_level("food_variety", self._agent_id)
        # Openness increases enjoyment/tolerance of food variation
        food_tolerance = 1.0 + (p.openness - 0.5) * 0.4
        perceived_food_quality = _clamp(agent_food * food_tolerance)

        # --- Distribution fairness ---
        perceived_fairness = self._compute_fairness_perception(
            resource_state, social_proximity, p
        )

        # --- Comms reliability ---
        # High comms_delay = poor reliability
        # Decay from prior if no comms received; boost if comms received
        comms_delay_penalty = resource_state.comms_delay  # higher = worse
        base_reliability = _clamp(1.0 - comms_delay_penalty)

        if mc_signal.received:
            # Comms received today: reliability perception moves toward reality
            perceived_comms_reliability = _clamp(
                prior_mc_reliability * 0.4 + base_reliability * 0.6 + 0.1
            )
        else:
            # No comms: slow decay toward base reliability
            perceived_comms_reliability = _clamp(
                prior_mc_reliability * 0.85 + base_reliability * 0.15
            )

        # --- Mission support ---
        perceived_mission_support = self._compute_mission_support(
            mc_signal, prior_mc_reliability, day, p, resource_state
        )

        # --- Social tension ---
        # Extraversion makes social conflict more salient
        # Low mean trust in neighbors signals tension
        mean_trust = social_proximity.mean_trust()
        base_tension = _clamp(1.0 - mean_trust)
        tension_amplifier = 1.0 + (p.extraversion - 0.5) * 0.5
        perceived_social_tension = _clamp(base_tension * tension_amplifier)

        # --- Sleep quality ---
        agent_sleep = resource_state.sleep_quality  # sleep is shared environment
        # Neuroticism reduces subjective sleep quality
        sleep_sensitivity = 1.0 - (p.neuroticism - 0.3) * 0.3
        perceived_sleep_quality = _clamp(agent_sleep * sleep_sensitivity)

        return PerceivedState(
            agent_id=self._agent_id,
            day=day,
            perceived_coffee_scarcity=perceived_coffee_scarcity,
            perceived_food_quality=perceived_food_quality,
            perceived_distribution_fairness=perceived_fairness,
            perceived_comms_reliability=perceived_comms_reliability,
            perceived_mission_support=perceived_mission_support,
            perceived_social_tension=perceived_social_tension,
            perceived_sleep_quality=perceived_sleep_quality,
        )

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _compute_fairness_perception(
        self,
        resource_state,
        social_proximity: SocialProximityMap,
        p: PersonalityScores,
    ) -> float:
        """
        Compute perceived_distribution_fairness.

        An agent perceives fairness based on:
        - Their own share relative to equal share
        - Their visibility into other agents' shares (via social proximity)
        - Agreeableness: high agreeableness is more tolerant of inequality

        Returns fairness perception [0.0, 1.0], 1.0 = perfectly fair.
        """
        n_agents = len(social_proximity.neighbor_weights) + 1  # +self
        if n_agents <= 1:
            return 1.0  # Can't perceive fairness with no comparison

        # Own share of coffee as primary fairness signal
        own_share = resource_state.get_agent_share("coffee", self._agent_id)
        equal_share = 1.0 / n_agents
        share_deviation = abs(own_share - equal_share)

        # Unfairness signal: how much does own share deviate from equal?
        # If underprivileged (own < equal): unfairness is high
        # If overprivileged (own > equal): agreeableness mediates guilt
        if own_share < equal_share:
            # Underprivilege — neuroticism amplifies grievance
            raw_unfairness = share_deviation * (1.0 + (p.neuroticism - 0.5) * 0.8)
        else:
            # Overprivilege — agreeableness mediates guilt into fairness concern
            raw_unfairness = share_deviation * (p.agreeableness * 0.4)

        # Social visibility: how well can this agent see others' shares?
        # Strong social connections → more accurate picture of distribution
        visibility = social_proximity.mean_trust()
        # Low visibility → can't see unfairness → perceived fairness stays higher
        perceived_unfairness = raw_unfairness * visibility

        return _clamp(1.0 - perceived_unfairness)

    def _compute_mission_support(
        self,
        mc_signal: MCCommSignal,
        prior_support: float,
        day: int,
        p: PersonalityScores,
        resource_state=None,
    ) -> float:
        """
        Compute perceived_mission_support.

        Support perception:
        - Increases immediately when comms received (especially reassurance/support types)
        - Increases when resupply is promised
        - When no comms: converges toward a resource-anchored baseline rather than
          decaying monotonically. Good living conditions = "no news is fine news."
          Degraded conditions = support perception drifts lower.
        - Minimum floor depends on agreeableness (more agreeable → more baseline trust)
        """
        floor = 0.2 + p.agreeableness * 0.2  # Agreeable agents maintain more baseline trust

        if not mc_signal.received:
            # Derive target baseline from actual mission environment quality
            if resource_state is not None:
                # Good resources → crew infers mission is supported even without comms
                # Degraded resources → absence of comms reads as neglect
                env_quality = (
                    resource_state.food_variety * 0.35
                    + resource_state.sleep_quality * 0.35
                    + (1.0 - resource_state.comms_delay) * 0.30
                )
                baseline_support = 0.30 + env_quality * 0.50  # [0.30, 0.80]
            else:
                baseline_support = floor

            # Convergence rate: how quickly perception moves toward baseline
            # High neuroticism = slower to restore confidence without direct confirmation
            convergence_rate = 0.05 + (1.0 - p.neuroticism) * 0.04
            new_support = prior_support + convergence_rate * (baseline_support - prior_support)
            return _clamp(max(new_support, floor))

        # Comms received — boost based on message type
        type_boosts = {
            "support": 0.15,
            "reassurance": 0.12,
            "acknowledgment": 0.08,
            "direction": 0.05,
        }
        boost = type_boosts.get(mc_signal.message_type or "", 0.06)

        # Resupply promised: additional belief boost
        if mc_signal.resupply_promised:
            boost += 0.10

        new_support = _clamp(prior_support + boost)
        return new_support


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
