"""
Type definitions for the BDI Cognitive Cycle module.

Defines all data structures used for beliefs, desires, intentions,
and input/output contracts.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from enum import Enum


@dataclass
class BeliefAssertion:
    """
    A belief assertion to be integrated into the agent's belief set.
    
    Attributes:
        predicate: Symbolic identifier for the belief type
        arguments: Ordered list of typed values specifying belief content
        confidence: Belief strength in [0.0, 1.0]
        source: Origin of the belief
    """
    predicate: str
    arguments: List[Any]
    confidence: float
    source: str
    
    def __post_init__(self):
        """Validate field constraints."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0.0, 1.0], got {self.confidence}")
        
        valid_sources = {"perception", "inference", "memory", "communication", "external"}
        if self.source not in valid_sources:
            # Default to external if unrecognized
            self.source = "external"


@dataclass
class Belief:
    """
    A belief in the agent's current belief set.
    
    Attributes:
        predicate: Symbolic identifier for the belief type
        arguments: Ordered list of typed values specifying belief content
        confidence: Belief strength in [0.0, 1.0]
        timestamp: Timestep at which belief was last updated
        source: Origin of the belief
    """
    predicate: str
    arguments: List[Any]
    confidence: float
    timestamp: int
    source: str
    
    def __post_init__(self):
        """Validate field constraints."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0.0, 1.0], got {self.confidence}")
        if self.timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {self.timestamp}")
    
    def key(self) -> tuple:
        """Return unique key for this belief (predicate + arguments)."""
        # Convert arguments to tuple for hashing
        args_tuple = tuple(str(arg) for arg in self.arguments)
        return (self.predicate, args_tuple)


@dataclass
class ConstraintSpec:
    """Constraint specification for desires."""
    predicate: str
    arguments: List[Any]


@dataclass
class Desire:
    """
    A desire representing a candidate goal state.
    
    Attributes:
        goal_predicate: Symbolic identifier for the goal type
        goal_arguments: Typed values specifying the goal state
        priority: Goal importance in [0.0, 1.0]
        utility: Expected value of achieving the goal
        constraints: Preconditions or restrictions
        timestamp: Timestep at which desire was generated
    """
    goal_predicate: str
    goal_arguments: List[Any]
    priority: float
    utility: float
    constraints: List[ConstraintSpec]
    timestamp: int
    
    def __post_init__(self):
        """Validate field constraints."""
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(f"Priority must be in [0.0, 1.0], got {self.priority}")
        if self.timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {self.timestamp}")
    
    def key(self) -> tuple:
        """Return unique key for this desire."""
        args_tuple = tuple(str(arg) for arg in self.goal_arguments)
        return (self.goal_predicate, args_tuple)


@dataclass
class Intention:
    """
    An intention representing a committed goal.
    
    Attributes:
        goal_predicate: Symbolic identifier for the committed goal
        goal_arguments: Typed values specifying the goal state
        commitment_level: Commitment strength in [0.0, 1.0]
        resources: Resource identifiers allocated to this intention
        plan_id: Optional reference to an execution plan
        timestamp: Timestep at which intention was adopted
    """
    goal_predicate: str
    goal_arguments: List[Any]
    commitment_level: float
    resources: List[str]
    plan_id: Optional[str]
    timestamp: int
    
    def __post_init__(self):
        """Validate field constraints."""
        if not 0.0 <= self.commitment_level <= 1.0:
            raise ValueError(f"Commitment level must be in [0.0, 1.0], got {self.commitment_level}")
        if self.timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {self.timestamp}")
    
    def key(self) -> tuple:
        """Return unique key for this intention."""
        args_tuple = tuple(str(arg) for arg in self.goal_arguments)
        return (self.goal_predicate, args_tuple)


@dataclass
class ConfigurationUpdate:
    """Configuration parameter change."""
    parameter_name: str
    parameter_value: Any


class ControlSignal(Enum):
    """Control signals for BDI cycle execution."""
    RUN = "run"
    PAUSE = "pause"
    RESET = "reset"
    STEP = "step"


@dataclass
class BDIInput:
    """
    Input structure for the BDI module at each timestep.
    
    Attributes:
        timestep: Current simulation timestep
        new_beliefs: Beliefs to be integrated into belief set
        configuration_update: Optional configuration parameter change
        control_signal: Cycle control signal
    """
    timestep: int
    new_beliefs: List[BeliefAssertion]
    configuration_update: Optional[ConfigurationUpdate] = None
    control_signal: ControlSignal = ControlSignal.RUN
    
    def __post_init__(self):
        """Validate field constraints."""
        if self.timestep < 0:
            raise ValueError(f"Timestep must be non-negative, got {self.timestep}")


@dataclass
class CycleStatistics:
    """
    Statistics about BDI cycle execution.
    
    Attributes:
        beliefs_added: Number of beliefs added this cycle
        beliefs_removed: Number of beliefs removed this cycle
        beliefs_updated: Number of beliefs updated this cycle
        desires_added: Number of desires added this cycle
        desires_removed: Number of desires removed this cycle
        intentions_added: Number of intentions added this cycle
        intentions_removed: Number of intentions removed this cycle
        inference_rule_applications: Number of inference rules applied
        conflicts_resolved: Number of conflicts resolved
        cycle_duration_ms: Execution time in milliseconds
    """
    beliefs_added: int = 0
    beliefs_removed: int = 0
    beliefs_updated: int = 0
    desires_added: int = 0
    desires_removed: int = 0
    intentions_added: int = 0
    intentions_removed: int = 0
    inference_rule_applications: int = 0
    conflicts_resolved: int = 0
    cycle_duration_ms: float = 0.0


@dataclass
class Status:
    """
    BDI cycle execution status.
    
    Attributes:
        code: Status code (success, warning, error, skipped)
        message: Optional human-readable description
    """
    code: str  # "success", "warning", "error", "skipped"
    message: Optional[str] = None
    
    def __post_init__(self):
        """Validate status code."""
        valid_codes = {"success", "warning", "error", "skipped"}
        if self.code not in valid_codes:
            raise ValueError(f"Invalid status code: {self.code}")


@dataclass
class BDIOutput:
    """
    Output structure from the BDI module at each timestep.
    
    Attributes:
        timestep: Timestep at which this output was generated
        beliefs: Current belief set
        desires: Current desire set
        intentions: Current intention set
        cycle_statistics: Statistics about cycle execution
        status: Execution status
    """
    timestep: int
    beliefs: List[Belief]
    desires: List[Desire]
    intentions: List[Intention]
    cycle_statistics: CycleStatistics
    status: Status
    
    def __post_init__(self):
        """Validate field constraints."""
        if self.timestep < 0:
            raise ValueError(f"Timestep must be non-negative, got {self.timestep}")


@dataclass
class BDIConfig:
    """
    Configuration parameters for the BDI module.
    
    All parameters have reasonable defaults and can be updated at runtime.
    """
    # Belief revision parameters
    confidence_decay_rate: float = 0.0  # No decay by default
    minimum_confidence_threshold: float = 0.1
    inference_depth_limit: int = 3
    belief_retention_window: int = 100  # timesteps
    max_belief_set_size: int = 1000
    
    # Desire formation parameters
    desire_retention_window: int = 50  # timesteps
    max_desire_set_size: int = 100
    minimum_priority_threshold: float = 0.0
    
    # Intention selection parameters
    max_intention_set_size: int = 10
    intention_selection_policy: str = "priority"  # "priority", "utility", "constraint_sat"
    commitment_threshold: float = 0.5
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0.0 <= self.confidence_decay_rate <= 1.0:
            raise ValueError("confidence_decay_rate must be in [0.0, 1.0]")
        if not 0.0 <= self.minimum_confidence_threshold <= 1.0:
            raise ValueError("minimum_confidence_threshold must be in [0.0, 1.0]")
        if self.inference_depth_limit < 0:
            raise ValueError("inference_depth_limit must be non-negative")
        if self.belief_retention_window < 1:
            raise ValueError("belief_retention_window must be at least 1")
        if self.max_belief_set_size < 1:
            raise ValueError("max_belief_set_size must be at least 1")
        if self.desire_retention_window < 1:
            raise ValueError("desire_retention_window must be at least 1")
        if self.max_desire_set_size < 1:
            raise ValueError("max_desire_set_size must be at least 1")
        if self.max_intention_set_size < 1:
            raise ValueError("max_intention_set_size must be at least 1")
        
        valid_policies = {"priority", "utility", "constraint_sat"}
        if self.intention_selection_policy not in valid_policies:
            raise ValueError(f"Invalid intention_selection_policy: {self.intention_selection_policy}")
    
    def update_parameter(self, name: str, value: Any) -> None:
        """Update a configuration parameter."""
        if not hasattr(self, name):
            raise ValueError(f"Unknown configuration parameter: {name}")
        setattr(self, name, value)
        # Re-validate after update
        self.__post_init__()


@dataclass
class PredicateSchema:
    """
    Schema definition for a belief/goal predicate.
    
    Attributes:
        name: Predicate name
        argument_types: Expected types for arguments
        description: Human-readable description
        category: Predicate category (state, goal, constraint)
    """
    name: str
    argument_types: List[type]
    description: str
    category: str  # "state", "goal", "constraint"


class DomainOntology:
    """
    Domain ontology defining valid predicates and their schemas.
    """
    
    def __init__(self):
        """Initialize empty ontology."""
        self.predicates: Dict[str, PredicateSchema] = {}
    
    def register_predicate(self, schema: PredicateSchema) -> None:
        """Register a predicate schema."""
        self.predicates[schema.name] = schema
    
    def is_valid_predicate(self, predicate: str) -> bool:
        """Check if a predicate is registered."""
        return predicate in self.predicates
    
    def validate_arguments(self, predicate: str, arguments: List[Any]) -> bool:
        """Validate arguments against predicate schema."""
        if not self.is_valid_predicate(predicate):
            return False
        
        schema = self.predicates[predicate]
        if len(arguments) != len(schema.argument_types):
            return False
        
        # Type checking is relaxed for flexibility
        # In production, could enforce strict type checking
        return True
    
    def get_schema(self, predicate: str) -> Optional[PredicateSchema]:
        """Get schema for a predicate."""
        return self.predicates.get(predicate)
