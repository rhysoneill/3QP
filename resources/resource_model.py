"""
Resource Model — Objective consumable tracking for 3QP twin engine.

Tracks mission-critical physical resources as objective simulation variables.

DESIGN CONTRACT:
    Resources are objective facts about the physical environment.
    They do NOT directly cause changes in agent internal state.
    The causal path is always:
        ResourceState → PerceptionModel → BeliefUpdate → InternalStateDrift

    This module tracks:
        - Stock levels (how much is available)
        - Distribution (who gets what share)
        - Depletion (daily consumption)
        - Resupply (delayed arrivals)

    It does NOT:
        - Read agent internal state
        - Write to agent beliefs
        - Call any other simulation layer
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Resource State
# ---------------------------------------------------------------------------

@dataclass
class ResourceState:
    """
    Objective snapshot of all tracked mission resources for one day.

    All stock levels are normalized to [0.0, 1.0]:
        1.0 = fully stocked / nominal
        0.0 = fully depleted / critical

    distribution_vector maps resource_name → {agent_id → share_fraction}
    where share fractions for a given resource sum to 1.0.
    Equal distribution = 1/N per agent for N crew members.

    Attributes:
        day:                     Simulation day this state represents
        coffee:                  Crew beverage / comfort ritual proxy
        food_variety:            Meal quality and variety (not calories)
        sleep_quality:           Ambient conditions supporting sleep
        comms_delay:             Communication latency (1.0 = maximum delay/bad)
        hygiene_supplies:        Personal hygiene consumables
        personal_entertainment:  Individual leisure resources
        task_load:               Objective mission workload level
        distribution_vector:     Per-resource per-agent share fractions
    """
    day: int = 0
    coffee: float = 1.0
    food_variety: float = 1.0
    sleep_quality: float = 1.0
    comms_delay: float = 0.2          # Starts low (good), may increase
    hygiene_supplies: float = 1.0
    personal_entertainment: float = 1.0
    task_load: float = 0.4            # Nominal workload
    distribution_vector: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def get_agent_share(self, resource_name: str, agent_id: str) -> float:
        """
        Return this agent's share fraction for the named resource.
        Returns equal share if no distribution has been set.
        """
        if resource_name not in self.distribution_vector:
            return 1.0  # No distribution data — treat as full access
        agent_shares = self.distribution_vector[resource_name]
        return agent_shares.get(agent_id, 0.0)

    def get_agent_level(self, resource_name: str, agent_id: str) -> float:
        """
        Return the effective resource level this agent experiences.
        = stock_level * agent_share_fraction
        """
        stock = getattr(self, resource_name, 0.0)
        share = self.get_agent_share(resource_name, agent_id)
        return stock * share

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "coffee": round(self.coffee, 4),
            "food_variety": round(self.food_variety, 4),
            "sleep_quality": round(self.sleep_quality, 4),
            "comms_delay": round(self.comms_delay, 4),
            "hygiene_supplies": round(self.hygiene_supplies, 4),
            "personal_entertainment": round(self.personal_entertainment, 4),
            "task_load": round(self.task_load, 4),
            "distribution_vector": self.distribution_vector,
        }


# ---------------------------------------------------------------------------
# Resupply
# ---------------------------------------------------------------------------

@dataclass
class ResourceResupply:
    """
    A scheduled resupply payload that arrives on a specific day.

    Attributes:
        resupply_id:    Unique identifier
        dispatch_day:   Day this was dispatched from Mission Control
        arrival_day:    Day this physically arrives (dispatch + ETA)
        payload:        Resource name → amount to add (clamped to 1.0)
        notified:       Whether crew has been told about this resupply
        applied:        Whether this resupply has been applied to state
    """
    resupply_id: str
    dispatch_day: int
    arrival_day: int
    payload: Dict[str, float]
    notified: bool = False
    applied: bool = False

    def to_dict(self) -> dict:
        return {
            "resupply_id": self.resupply_id,
            "dispatch_day": self.dispatch_day,
            "arrival_day": self.arrival_day,
            "payload": self.payload,
            "notified": self.notified,
            "applied": self.applied,
        }


# ---------------------------------------------------------------------------
# Resource Config
# ---------------------------------------------------------------------------

DEPLETABLE_RESOURCES = [
    "coffee",
    "food_variety",
    "hygiene_supplies",
    "personal_entertainment",
]

MANAGED_RESOURCES = [
    "sleep_quality",
    "comms_delay",
    "task_load",
]

ALL_RESOURCES = DEPLETABLE_RESOURCES + MANAGED_RESOURCES


@dataclass
class ResourceConfig:
    """
    Configuration for resource depletion and initial state.

    Depletion rates are fractions per day subtracted from stock level.
    Managed resources (sleep_quality, comms_delay, task_load) are not
    depleted automatically — they are set externally via the twin runner.

    Attributes:
        coffee_depletion:               Daily depletion rate [0.0, 1.0]
        food_variety_depletion:         Daily depletion rate [0.0, 1.0]
        hygiene_depletion:              Daily depletion rate [0.0, 1.0]
        entertainment_depletion:        Daily depletion rate [0.0, 1.0]
        initial_coffee:                 Starting stock level
        initial_food_variety:           Starting stock level
        initial_sleep_quality:          Starting level (managed externally)
        initial_comms_delay:            Starting delay (managed externally)
        initial_hygiene:                Starting stock level
        initial_entertainment:          Starting stock level
        initial_task_load:              Starting workload (managed externally)
    """
    coffee_depletion: float = 0.005
    food_variety_depletion: float = 0.003
    hygiene_depletion: float = 0.004
    entertainment_depletion: float = 0.006

    initial_coffee: float = 1.0
    initial_food_variety: float = 1.0
    initial_sleep_quality: float = 0.85
    initial_comms_delay: float = 0.2
    initial_hygiene: float = 1.0
    initial_entertainment: float = 1.0
    initial_task_load: float = 0.65   # Nominal sustained workload for lunar mission (0.4 was too low to accumulate strain)


# ---------------------------------------------------------------------------
# Resource Engine
# ---------------------------------------------------------------------------

class ResourceEngine:
    """
    Day-by-day objective resource tracker.

    Manages:
        - Linear depletion of consumable resources each day
        - Application of resupply payloads on arrival day
        - Per-agent distribution tracking (updated externally)
        - Immutable history of all states

    Does NOT:
        - Read or write agent internal state
        - Compute perceptions or beliefs
        - Make decisions about when to resupply
    """

    def __init__(self, config: ResourceConfig, agent_ids: List[str]):
        """
        Args:
            config:     Resource configuration (depletion rates, initial levels)
            agent_ids:  IDs of all agents (used to initialize equal distribution)
        """
        self._config = config
        self._agent_ids = list(agent_ids)
        self._resupply_queue: List[ResourceResupply] = []
        self._state_history: List[ResourceState] = []

        # Build initial equal distribution
        n = len(self._agent_ids)
        equal_share = round(1.0 / n, 6) if n > 0 else 0.0
        initial_distribution: Dict[str, Dict[str, float]] = {
            resource: {agent_id: equal_share for agent_id in self._agent_ids}
            for resource in ALL_RESOURCES
        }

        self._current_state = ResourceState(
            day=0,
            coffee=config.initial_coffee,
            food_variety=config.initial_food_variety,
            sleep_quality=config.initial_sleep_quality,
            comms_delay=config.initial_comms_delay,
            hygiene_supplies=config.initial_hygiene,
            personal_entertainment=config.initial_entertainment,
            task_load=config.initial_task_load,
            distribution_vector=initial_distribution,
        )
        self._state_history.append(self._current_state)

    # -------------------------------------------------------------------
    # Core update
    # -------------------------------------------------------------------

    def step(
        self,
        day: int,
        consumption_modifier: float = 1.0,
        sleep_quality_override: Optional[float] = None,
        comms_delay_override: Optional[float] = None,
        task_load_override: Optional[float] = None,
    ) -> ResourceState:
        """
        Advance resources by one day.

        Applies:
            1. Consumption-scaled depletion to consumable resources.
               consumption_modifier encodes crew activity level — idle crews
               consume less; highly engaged crews consume more.
               If consumption_modifier=0, consumables hold steady (nothing happening).
            2. Optional overrides for managed resources (sleep, comms, task_load).
            3. Any resupply payloads arriving on this day.
            4. Clamps all values to [0.0, 1.0].

        Args:
            day:                    Current simulation day
            consumption_modifier:   Scales daily depletion rates. 1.0 = nominal.
                                    Derived from crew actions + micro-events by
                                    the twin runner.
            sleep_quality_override: Set sleep quality for this day (managed externally)
            comms_delay_override:   Set comms delay for this day (managed externally)
            task_load_override:     Set task load for this day (managed externally)

        Returns:
            New ResourceState for this day
        """
        prev = self._current_state

        # Step 1: deplete consumables proportional to crew activity
        new_coffee = prev.coffee - self._config.coffee_depletion * consumption_modifier
        new_food = prev.food_variety - self._config.food_variety_depletion * consumption_modifier
        new_hygiene = prev.hygiene_supplies - self._config.hygiene_depletion * consumption_modifier
        new_entertainment = prev.personal_entertainment - self._config.entertainment_depletion * consumption_modifier

        # Step 2: managed resources (use override or carry forward)
        new_sleep = sleep_quality_override if sleep_quality_override is not None else prev.sleep_quality
        new_comms = comms_delay_override if comms_delay_override is not None else prev.comms_delay
        new_task = task_load_override if task_load_override is not None else prev.task_load

        # Step 3: carry forward distribution (may be updated externally before next step)
        new_distribution = {
            resource: dict(shares)
            for resource, shares in prev.distribution_vector.items()
        }

        # Build new state before resupply
        new_state = ResourceState(
            day=day,
            coffee=new_coffee,
            food_variety=new_food,
            sleep_quality=new_sleep,
            comms_delay=new_comms,
            hygiene_supplies=new_hygiene,
            personal_entertainment=new_entertainment,
            task_load=new_task,
            distribution_vector=new_distribution,
        )

        # Step 4: apply any resupply arriving today
        for resupply in self._resupply_queue:
            if resupply.arrival_day == day and not resupply.applied:
                new_state = self._apply_resupply(new_state, resupply)
                resupply.applied = True

        # Step 5: clamp all depletable values to [0.0, 1.0]
        new_state.coffee = _clamp(new_state.coffee)
        new_state.food_variety = _clamp(new_state.food_variety)
        new_state.sleep_quality = _clamp(new_state.sleep_quality)
        new_state.comms_delay = _clamp(new_state.comms_delay)
        new_state.hygiene_supplies = _clamp(new_state.hygiene_supplies)
        new_state.personal_entertainment = _clamp(new_state.personal_entertainment)
        new_state.task_load = _clamp(new_state.task_load)

        self._current_state = new_state
        self._state_history.append(new_state)
        return new_state

    # -------------------------------------------------------------------
    # Resupply
    # -------------------------------------------------------------------

    def schedule_resupply(self, resupply: ResourceResupply) -> None:
        """
        Add a resupply to the queue. Will be applied on arrival_day.
        """
        self._resupply_queue.append(resupply)

    def get_pending_resupplies(self) -> List[ResourceResupply]:
        """Return all resupplies not yet applied."""
        return [r for r in self._resupply_queue if not r.applied]

    def get_notifiable_resupplies(self, day: int) -> List[ResourceResupply]:
        """
        Return resupplies dispatched on this day that have not yet been
        communicated to the crew. Caller is responsible for marking them
        as notified after dispatching MCCommunication.
        """
        return [
            r for r in self._resupply_queue
            if r.dispatch_day == day and not r.notified
        ]

    def _apply_resupply(
        self, state: ResourceState, resupply: ResourceResupply
    ) -> ResourceState:
        """Add resupply payload to resource stock levels."""
        for resource_name, amount in resupply.payload.items():
            if hasattr(state, resource_name):
                current = getattr(state, resource_name)
                setattr(state, resource_name, _clamp(current + amount))
        return state

    # -------------------------------------------------------------------
    # Distribution management
    # -------------------------------------------------------------------

    def update_distribution(
        self, resource_name: str, agent_id: str, new_share: float
    ) -> None:
        """
        Adjust one agent's share of a resource.

        Redistributes the remainder equally among all other agents.
        new_share is clamped to [0.0, 1.0] and cannot exceed 1.0.

        Called by twin runner when agent actions indicate hoarding or
        unequal access patterns.
        """
        if resource_name not in self._current_state.distribution_vector:
            return
        if agent_id not in self._agent_ids:
            return

        new_share = _clamp(new_share)
        others = [a for a in self._agent_ids if a != agent_id]
        remainder = _clamp(1.0 - new_share)
        other_share = remainder / len(others) if others else 0.0

        new_dist = dict(self._current_state.distribution_vector[resource_name])
        new_dist[agent_id] = round(new_share, 6)
        for other in others:
            new_dist[other] = round(other_share, 6)

        self._current_state.distribution_vector[resource_name] = new_dist

    def reset_distribution_to_equal(self, resource_name: str) -> None:
        """Reset distribution for one resource to equal shares."""
        if resource_name not in self._current_state.distribution_vector:
            return
        n = len(self._agent_ids)
        equal_share = round(1.0 / n, 6) if n > 0 else 0.0
        self._current_state.distribution_vector[resource_name] = {
            agent_id: equal_share for agent_id in self._agent_ids
        }

    # -------------------------------------------------------------------
    # State access
    # -------------------------------------------------------------------

    def get_state(self) -> ResourceState:
        """Return the current resource state."""
        return self._current_state

    def get_history(self) -> List[ResourceState]:
        """Return immutable copy of full state history."""
        return list(self._state_history)

    def get_state_at_day(self, day: int) -> Optional[ResourceState]:
        """Return state for a specific day, or None if not found."""
        for state in self._state_history:
            if state.day == day:
                return state
        return None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))
