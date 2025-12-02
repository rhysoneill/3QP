"""
Data types for the Intervention Engine.

All types defined here are structural - no semantic interpretation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class InterventionState(Enum):
    """Lifecycle states for an intervention."""
    UNINITIALIZED = "uninitialized"
    ARMED = "armed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class EffectType(Enum):
    """Types of effects an intervention can emit."""
    ACTIVATION = "activation"
    DEACTIVATION = "deactivation"
    STATE_CHANGE = "state_change"


class ConditionOperator(Enum):
    """Comparison operators for threshold conditions."""
    GT = "gt"    # Greater than
    LT = "lt"    # Less than
    EQ = "eq"    # Equal to
    NEQ = "neq"  # Not equal to
    GTE = "gte"  # Greater than or equal
    LTE = "lte"  # Less than or equal


class CadenceType(Enum):
    """Types of intervention cadences."""
    CONTINUOUS = "continuous"
    INTERMITTENT = "intermittent"
    PULSED = "pulsed"


class DecayType(Enum):
    """Types of decay for intervention effects."""
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


class LogicOperator(Enum):
    """Logical operators for compound conditions."""
    AND = "and"
    OR = "or"
    XOR = "xor"


@dataclass
class RecurrencePattern:
    """Pattern for recurring interventions."""
    interval: int  # Time-steps between activations
    count: Optional[int] = None  # Number of repetitions (None = infinite)
    offset: int = 0  # Phase offset from start_time


@dataclass
class ThresholdCondition:
    """Threshold-based activation condition."""
    signal_id: str
    operator: ConditionOperator
    threshold_value: float
    duration_required: int = 1  # Time-steps signal must satisfy condition
    hysteresis_buffer: float = 0.0  # Deadband for noise rejection
    
    def __post_init__(self):
        """Validate threshold condition."""
        if self.duration_required < 0:
            raise ValueError("duration_required must be non-negative")
        if self.hysteresis_buffer < 0:
            raise ValueError("hysteresis_buffer must be non-negative")


@dataclass
class TemporalCondition:
    """Time-based activation condition."""
    start_time: int  # Simulation time-step index
    end_time: Optional[int] = None  # Optional expiration time
    recurrence_pattern: Optional[RecurrencePattern] = None
    
    def __post_init__(self):
        """Validate temporal condition."""
        if self.start_time < 0:
            raise ValueError("start_time must be non-negative")
        if self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")


@dataclass
class EventCondition:
    """Event-based activation condition."""
    event_id: str
    event_filter: Optional[Dict[str, Any]] = None
    cooldown_period: int = 0  # Minimum time-steps between activations
    
    def __post_init__(self):
        """Validate event condition."""
        if self.cooldown_period < 0:
            raise ValueError("cooldown_period must be non-negative")


@dataclass
class CompoundCondition:
    """Compound activation condition combining multiple conditions."""
    conditions: List[Union['ThresholdCondition', 'TemporalCondition', 'EventCondition', 'CompoundCondition']]
    logic_operator: LogicOperator
    evaluation_order: Optional[List[int]] = None
    
    def __post_init__(self):
        """Validate compound condition."""
        if len(self.conditions) < 2:
            raise ValueError("CompoundCondition must have at least 2 conditions")
        if self.evaluation_order is not None:
            if len(self.evaluation_order) != len(self.conditions):
                raise ValueError("evaluation_order must match number of conditions")


# Type alias for any condition type
ActivationCondition = Union[ThresholdCondition, TemporalCondition, EventCondition, CompoundCondition]


@dataclass
class Schedule:
    """Schedule definition for interventions."""
    cadence_type: CadenceType
    active_duration: int  # Time-steps intervention remains active
    inactive_duration: int = 0  # Time-steps before re-arming (recurrent only)
    phase_alignment: Optional[int] = None  # Alignment to simulation phase boundaries
    
    def __post_init__(self):
        """Validate schedule."""
        if self.active_duration <= 0:
            raise ValueError("active_duration must be positive")
        if self.inactive_duration < 0:
            raise ValueError("inactive_duration must be non-negative")
        if self.phase_alignment is not None and self.phase_alignment <= 0:
            raise ValueError("phase_alignment must be positive")


@dataclass
class Duration:
    """Duration specification for interventions."""
    max_duration: Optional[int] = None  # Maximum time-steps (None = infinite)
    decay_type: DecayType = DecayType.NONE
    decay_rate: float = 0.0  # Rate parameter for decay function
    
    def __post_init__(self):
        """Validate duration."""
        if self.max_duration is not None and self.max_duration <= 0:
            raise ValueError("max_duration must be positive or None")
        if self.decay_type != DecayType.NONE and self.decay_rate <= 0:
            raise ValueError("decay_rate must be positive when decay_type is not NONE")


@dataclass
class InterventionConfig:
    """Complete configuration for an intervention instance."""
    id: str
    category: str  # scheduled, reactive, compound, recurrent, one-shot
    type_tag: str  # Type descriptor for filtering/grouping
    activation_conditions: ActivationCondition
    schedule: Schedule
    duration: Duration
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = processed first
    
    def __post_init__(self):
        """Validate intervention config."""
        if not self.id:
            raise ValueError("id must be non-empty string")
        if not self.type_tag:
            raise ValueError("type_tag must be non-empty string")
        if self.category not in ["scheduled", "reactive", "compound", "recurrent", "one-shot"]:
            raise ValueError(f"Invalid category: {self.category}")


@dataclass
class InterventionEffect:
    """Effect emitted by an intervention upon state change."""
    intervention_id: str
    effect_type: EffectType
    timestamp: int  # Time-step index when effect occurred
    signal_values: Dict[str, float]  # Abstract output signals
    
    def __post_init__(self):
        """Validate intervention effect."""
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
        for key, value in self.signal_values.items():
            if not isinstance(key, str) or not key:
                raise ValueError("signal_values keys must be non-empty strings")
            if not isinstance(value, (int, float)):
                raise ValueError("signal_values must be numeric")


@dataclass
class Event:
    """
    Discrete event structure for event-based activation.
    Matches the Event type from TQP Core EventBus.
    """
    event_id: str
    timestamp: int
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransitionRecord:
    """Record of a state transition for history tracking."""
    timestamp: int
    from_state: InterventionState
    to_state: InterventionState
    trigger: Optional[str] = None  # Description of what caused transition


@dataclass
class InterventionStateInfo:
    """Complete state information for an intervention."""
    id: str
    current_state: InterventionState
    time_activated: Optional[int] = None  # null if never activated
    time_last_transition: Optional[int] = None
    active_duration_elapsed: int = 0  # time-steps in ACTIVE state
