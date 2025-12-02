"""
Data type definitions for the Stressor Model.

Defines input and output data structures according to the data contract.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class StressorCategory(Enum):
    """Categories of stressors in the mission environment."""
    OPERATIONAL = "operational"
    ENVIRONMENTAL = "environmental"
    TEMPORAL = "temporal"
    MONOTONY = "monotony"


class EventType(Enum):
    """Types of mission events that can trigger stressor changes."""
    EVA = "eva"
    MAINTENANCE = "maintenance"
    RESUPPLY = "resupply"
    CREW_CHANGE = "crew_change"
    MILESTONE = "milestone"
    ANOMALY = "anomaly"


class PhaseType(Enum):
    """Mission phase types."""
    COMMISSIONING = "commissioning"
    STEADY_STATE = "steady_state"
    CREW_ROTATION = "crew_rotation"
    CLOSEOUT = "closeout"


class NoiseType(Enum):
    """Types of stochastic noise for stressor perturbations."""
    ORNSTEIN_UHLENBECK = "ornstein_uhlenbeck"
    WHITE = "white"
    NONE = "none"


@dataclass
class NoiseConfig:
    """Configuration for stochastic noise in stressor signals."""
    noise_type: NoiseType = NoiseType.NONE
    intensity: float = 0.0
    correlation_time: Optional[float] = None  # days
    
    def __post_init__(self):
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"noise intensity must be in [0, 1], got {self.intensity}")


@dataclass
class SpikeEvent:
    """Scheduled spike in stressor intensity."""
    trigger_time: float  # days from mission start
    magnitude: float  # [0, 1]
    duration: float  # days
    
    def __post_init__(self):
        if self.trigger_time < 0:
            raise ValueError(f"trigger_time must be non-negative, got {self.trigger_time}")
        if not 0.0 <= self.magnitude <= 1.0:
            raise ValueError(f"magnitude must be in [0, 1], got {self.magnitude}")
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")


@dataclass
class StressorParameterSet:
    """Parameters defining a stressor's behavior."""
    stressor_id: str
    category: StressorCategory
    enabled: bool = True
    
    # Intensity parameters
    baseline: float = 0.0
    max_intensity: float = 1.0
    
    # Temporal dynamics
    decay_tau: Optional[float] = None  # days
    accumulation_rate: Optional[float] = None  # per day
    
    # Periodic cadence
    cadence_period: Optional[float] = None  # days
    cadence_amplitude: Optional[float] = None
    cadence_phase_offset: float = 0.0  # radians
    
    # Scheduled spikes
    spike_schedule: List[SpikeEvent] = field(default_factory=list)
    
    # Stochastic perturbations
    noise_parameters: NoiseConfig = field(default_factory=NoiseConfig)
    
    def __post_init__(self):
        """Validate parameter constraints."""
        if not 0.0 <= self.baseline <= 1.0:
            raise ValueError(f"baseline must be in [0, 1], got {self.baseline}")
        if not 0.0 <= self.max_intensity <= 1.0:
            raise ValueError(f"max_intensity must be in [0, 1], got {self.max_intensity}")
        if self.baseline > self.max_intensity:
            raise ValueError(
                f"baseline ({self.baseline}) must be <= max_intensity ({self.max_intensity})"
            )
        if self.decay_tau is not None and self.decay_tau <= 0:
            raise ValueError(f"decay_tau must be positive, got {self.decay_tau}")
        if self.cadence_period is not None and self.cadence_period <= 0:
            raise ValueError(f"cadence_period must be positive, got {self.cadence_period}")


@dataclass
class StressorModifier:
    """Modification to stressor intensity from an event."""
    stressor_id: str
    intensity_delta: float  # [-1, 1]
    duration: float  # days


@dataclass
class ScheduledEvent:
    """Scheduled mission event that affects stressors."""
    event_id: str
    event_time: float  # days from mission start
    event_type: EventType
    stressor_modifiers: List[StressorModifier] = field(default_factory=list)


@dataclass
class PhaseDefinition:
    """Definition of a mission phase."""
    phase_id: str
    start_day: float
    end_day: float
    phase_type: PhaseType
    
    def __post_init__(self):
        if self.start_day < 0:
            raise ValueError(f"start_day must be non-negative, got {self.start_day}")
        if self.end_day <= self.start_day:
            raise ValueError(f"end_day ({self.end_day}) must be > start_day ({self.start_day})")


@dataclass
class MissionConfig:
    """Complete mission configuration for the Stressor Model."""
    mission_id: str
    mission_start_date: datetime
    mission_duration_days: float
    random_seed: int
    
    phase_definitions: List[PhaseDefinition] = field(default_factory=list)
    stressor_parameters: List[StressorParameterSet] = field(default_factory=list)
    event_schedule: List[ScheduledEvent] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate mission configuration."""
        if self.mission_duration_days <= 0:
            raise ValueError(
                f"mission_duration_days must be positive, got {self.mission_duration_days}"
            )
        
        # Validate phase coverage if phases are defined
        if self.phase_definitions:
            # Check for gaps and overlaps
            sorted_phases = sorted(self.phase_definitions, key=lambda p: p.start_day)
            for i in range(len(sorted_phases) - 1):
                if sorted_phases[i].end_day != sorted_phases[i + 1].start_day:
                    raise ValueError(
                        f"Phase gap/overlap detected between {sorted_phases[i].phase_id} "
                        f"and {sorted_phases[i + 1].phase_id}"
                    )


@dataclass
class TriggeredEvent:
    """Event that occurred in the current timestep."""
    event_id: str
    event_type: EventType
    event_time: float  # days from mission start


@dataclass
class UpdateCycleInput:
    """Input data for a single update cycle."""
    current_time: float  # days from mission start
    delta_time: float  # days since last update
    triggered_events: List[TriggeredEvent] = field(default_factory=list)
    
    def __post_init__(self):
        if self.current_time < 0:
            raise ValueError(f"current_time must be non-negative, got {self.current_time}")
        if self.delta_time <= 0:
            raise ValueError(f"delta_time must be positive, got {self.delta_time}")


@dataclass
class StateFlags:
    """Status flags for a stressor."""
    is_active: bool = True
    is_spiking: bool = False
    is_degraded: bool = False


@dataclass
class StressorValue:
    """Current value and state of a single stressor."""
    stressor_id: str
    current_intensity: float  # [0, 1]
    accumulated_exposure: float  # intensity-days
    last_spike_time: Optional[float] = None  # days from mission start
    spike_count: int = 0
    state_flags: StateFlags = field(default_factory=StateFlags)
    
    def __post_init__(self):
        """Validate stressor value constraints."""
        if not 0.0 <= self.current_intensity <= 1.0:
            self.current_intensity = max(0.0, min(1.0, self.current_intensity))
            self.state_flags.is_degraded = True
        if self.accumulated_exposure < 0:
            raise ValueError(
                f"accumulated_exposure must be non-negative, got {self.accumulated_exposure}"
            )
        if self.spike_count < 0:
            raise ValueError(f"spike_count must be non-negative, got {self.spike_count}")


@dataclass
class SummaryMetrics:
    """Aggregate stressor metrics."""
    total_operational_intensity: float = 0.0
    total_environmental_intensity: float = 0.0
    total_temporal_intensity: float = 0.0
    total_monotony_intensity: float = 0.0
    overall_stressor_load: float = 0.0
    
    def __post_init__(self):
        """Clamp all values to [0, 1]."""
        self.total_operational_intensity = max(0.0, min(1.0, self.total_operational_intensity))
        self.total_environmental_intensity = max(0.0, min(1.0, self.total_environmental_intensity))
        self.total_temporal_intensity = max(0.0, min(1.0, self.total_temporal_intensity))
        self.total_monotony_intensity = max(0.0, min(1.0, self.total_monotony_intensity))
        self.overall_stressor_load = max(0.0, min(1.0, self.overall_stressor_load))


@dataclass
class StressorIntensityVector:
    """Complete stressor state at a point in time."""
    mission_time: float  # days from mission start
    timestamp: datetime
    
    operational_stressors: List[StressorValue] = field(default_factory=list)
    environmental_stressors: List[StressorValue] = field(default_factory=list)
    temporal_stressors: List[StressorValue] = field(default_factory=list)
    monotony_stressors: List[StressorValue] = field(default_factory=list)
    
    summary_metrics: SummaryMetrics = field(default_factory=SummaryMetrics)
    
    def get_stressor(self, stressor_id: str) -> Optional[StressorValue]:
        """Retrieve a specific stressor by ID."""
        for stressor_list in [
            self.operational_stressors,
            self.environmental_stressors,
            self.temporal_stressors,
            self.monotony_stressors,
        ]:
            for stressor in stressor_list:
                if stressor.stressor_id == stressor_id:
                    return stressor
        return None


@dataclass
class ActivationEvent:
    """Record of stressor activation or state change."""
    event_time: float  # days from mission start
    event_type: str  # INITIALIZED, SPIKE_TRIGGERED, PARAMETER_CHANGED, DEACTIVATED


@dataclass
class StatisticalSummary:
    """Statistical summary of stressor over time."""
    mean_intensity: float = 0.0
    max_intensity: float = 0.0
    min_intensity: float = 1.0
    std_dev_intensity: float = 0.0
    time_above_threshold: float = 0.0  # days with intensity > 0.5


@dataclass
class StressorMetadata:
    """Metadata and history for a stressor."""
    stressor_id: str
    category: StressorCategory
    description: str
    current_parameters: StressorParameterSet
    activation_history: List[ActivationEvent] = field(default_factory=list)
    statistical_summary: StatisticalSummary = field(default_factory=StatisticalSummary)
