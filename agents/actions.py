"""
Action Model - Phase B

Defines the finite set of agent actions and state representation
for the agentic layer.

Actions represent semantic behaviors, not psychological updates.
They influence interaction patterns, not internal state.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActionType(Enum):
    """
    Finite set of agent actions.
    
    Each action represents a behavioral stance that influences
    interaction patterns without directly modifying psychological state.
    """
    WITHDRAW = "withdraw"       # Reduce interaction frequency
    ENGAGE = "engage"           # Increase interaction frequency
    SUPPORT = "support"         # Strengthen positive interactions
    ESCALATE = "escalate"       # Increase intensity/visibility of issues
    MAINTAIN = "maintain"       # Continue current behavior pattern
    
    def __str__(self):
        return self.value


@dataclass
class AgentState:
    """
    Snapshot of agent's current state for decision-making.
    
    This is a read-only view extracted from the core dynamics
    for use in action selection. Does NOT modify core state.
    
    Attributes:
        agent_id: Agent identifier (or "crew" for single-agent mode)
        day: Current mission day
        strain: Current psychological strain S(t)
        cohesion: Current social cohesion C(t)
        monotony: Current monotony M(t)
        tq_pressure: Current third quarter pressure Q(t)
        mission_progress: Fraction of mission completed (0.0 to 1.0)
    """
    agent_id: str
    day: int
    strain: float
    cohesion: float
    monotony: float
    tq_pressure: float
    mission_progress: float
    
    def to_dict(self):
        """Convert to dictionary for logging."""
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "strain": self.strain,
            "cohesion": self.cohesion,
            "monotony": self.monotony,
            "tq_pressure": self.tq_pressure,
            "mission_progress": self.mission_progress,
        }


@dataclass
class AgentAction:
    """
    Action selected by an agent at a specific timestep.
    
    Attributes:
        agent_id: Agent identifier
        day: Day when action was selected
        action_type: The action selected
        state_snapshot: State that led to this action selection
        metadata: Additional context (e.g., threshold values)
    """
    agent_id: str
    day: int
    action_type: ActionType
    state_snapshot: AgentState
    metadata: Optional[dict] = None
    
    def to_dict(self):
        """Convert to dictionary for logging."""
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "action_type": str(self.action_type),
            "state": self.state_snapshot.to_dict(),
            "metadata": self.metadata or {},
        }
