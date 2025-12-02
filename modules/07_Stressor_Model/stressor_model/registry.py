"""
Stressor registry and state management.

Manages the catalog of stressor types, their parameters, and internal state.
"""

from typing import Dict, Optional, List
import random

from .types import (
    StressorCategory,
    StressorParameterSet,
    StressorMetadata,
    ActivationEvent,
    StatisticalSummary,
    NoiseType,
)
from .intensity_functions import (
    StressorState,
    IntensityFunction,
    ConstantIntensity,
    ExponentialDecay,
    LinearAccumulation,
    PeriodicCadence,
    OrnsteinUhlenbeckNoise,
    CompositeIntensity,
)


class StressorRegistry:
    """
    Central catalog of all stressor types and their parameters.
    
    Manages stressor definitions, validation, and metadata.
    """
    
    def __init__(self):
        self._parameters: Dict[str, StressorParameterSet] = {}
        self._states: Dict[str, StressorState] = {}
        self._intensity_functions: Dict[str, IntensityFunction] = {}
        self._activation_history: Dict[str, List[ActivationEvent]] = {}
        self._statistics: Dict[str, StatisticalSummary] = {}
        self._random_state: Optional[random.Random] = None
    
    def initialize(self, parameters: List[StressorParameterSet], random_seed: int):
        """
        Initialize registry with stressor parameters.
        
        Args:
            parameters: List of stressor parameter sets
            random_seed: Seed for random number generation
        """
        self._random_state = random.Random(random_seed)
        
        for param_set in parameters:
            self.register_stressor(param_set)
    
    def register_stressor(self, param_set: StressorParameterSet):
        """
        Register a new stressor type.
        
        Args:
            param_set: Parameter set defining the stressor
        """
        stressor_id = param_set.stressor_id
        
        # Validate parameters
        self._validate_parameters(param_set)
        
        # Store parameters
        self._parameters[stressor_id] = param_set
        
        # Initialize state
        self._states[stressor_id] = StressorState(
            current_intensity=param_set.baseline,
            baseline=param_set.baseline,
            max_intensity=param_set.max_intensity,
            accumulated_exposure=0.0,
            last_update_time=0.0,
            last_spike_time=None,
            spike_count=0,
        )
        
        # Build intensity function
        self._intensity_functions[stressor_id] = self._build_intensity_function(param_set)
        
        # Initialize tracking
        self._activation_history[stressor_id] = [
            ActivationEvent(event_time=0.0, event_type="INITIALIZED")
        ]
        self._statistics[stressor_id] = StatisticalSummary(
            mean_intensity=param_set.baseline,
            max_intensity=param_set.baseline,
            min_intensity=param_set.baseline,
        )
    
    def _validate_parameters(self, param_set: StressorParameterSet):
        """Validate parameter constraints."""
        # Basic validation already done in dataclass __post_init__
        # Add any additional cross-parameter validation here
        pass
    
    def _build_intensity_function(self, param_set: StressorParameterSet) -> IntensityFunction:
        """
        Build intensity function from parameters.
        
        Args:
            param_set: Parameter set
            
        Returns:
            Intensity function instance
        """
        functions = []
        
        # Base dynamics
        if param_set.decay_tau is not None:
            functions.append(ExponentialDecay(param_set.decay_tau))
        elif param_set.accumulation_rate is not None:
            functions.append(LinearAccumulation(param_set.accumulation_rate))
        else:
            functions.append(ConstantIntensity())
        
        # Periodic cadence
        if param_set.cadence_period is not None and param_set.cadence_amplitude is not None:
            functions.append(
                PeriodicCadence(
                    param_set.cadence_period,
                    param_set.cadence_amplitude,
                    param_set.cadence_phase_offset,
                )
            )
        
        # Noise
        if param_set.noise_parameters.noise_type == NoiseType.ORNSTEIN_UHLENBECK:
            functions.append(
                OrnsteinUhlenbeckNoise(
                    param_set.noise_parameters.intensity,
                    param_set.noise_parameters.correlation_time or 1.0,
                    self._random_state,
                )
            )
        
        # Combine functions
        if len(functions) == 1:
            return functions[0]
        else:
            return CompositeIntensity(functions)
    
    def get_state(self, stressor_id: str) -> Optional[StressorState]:
        """Get internal state for a stressor."""
        return self._states.get(stressor_id)
    
    def get_parameters(self, stressor_id: str) -> Optional[StressorParameterSet]:
        """Get parameters for a stressor."""
        return self._parameters.get(stressor_id)
    
    def get_intensity_function(self, stressor_id: str) -> Optional[IntensityFunction]:
        """Get intensity function for a stressor."""
        return self._intensity_functions.get(stressor_id)
    
    def update_state(
        self,
        stressor_id: str,
        new_intensity: float,
        current_time: float,
        delta_time: float,
    ):
        """
        Update internal state after intensity computation.
        
        Args:
            stressor_id: ID of stressor to update
            new_intensity: New intensity value
            current_time: Current mission time
            delta_time: Time elapsed
        """
        state = self._states.get(stressor_id)
        if state is None:
            return
        
        # Update accumulated exposure
        avg_intensity = (state.current_intensity + new_intensity) / 2.0
        state.accumulated_exposure += avg_intensity * delta_time
        
        # Update intensity
        state.current_intensity = new_intensity
        state.last_update_time = current_time
        
        # Update statistics
        stats = self._statistics[stressor_id]
        stats.max_intensity = max(stats.max_intensity, new_intensity)
        stats.min_intensity = min(stats.min_intensity, new_intensity)
        
        # Track time above threshold
        if new_intensity > 0.5:
            stats.time_above_threshold += delta_time
    
    def trigger_spike(self, stressor_id: str, current_time: float):
        """
        Record a spike event.
        
        Args:
            stressor_id: ID of stressor
            current_time: Time of spike
        """
        state = self._states.get(stressor_id)
        if state is None:
            return
        
        state.last_spike_time = current_time
        state.spike_count += 1
        
        self._activation_history[stressor_id].append(
            ActivationEvent(event_time=current_time, event_type="SPIKE_TRIGGERED")
        )
    
    def get_all_stressor_ids(self) -> List[str]:
        """Get list of all registered stressor IDs."""
        return list(self._parameters.keys())
    
    def get_stressors_by_category(self, category: StressorCategory) -> List[str]:
        """Get list of stressor IDs in a specific category."""
        return [
            sid for sid, params in self._parameters.items()
            if params.category == category
        ]
    
    def get_metadata(self, stressor_id: str) -> Optional[StressorMetadata]:
        """
        Get complete metadata for a stressor.
        
        Args:
            stressor_id: ID of stressor
            
        Returns:
            Metadata object or None if stressor not found
        """
        params = self._parameters.get(stressor_id)
        if params is None:
            return None
        
        return StressorMetadata(
            stressor_id=stressor_id,
            category=params.category,
            description=f"{params.category.value} stressor: {stressor_id}",
            current_parameters=params,
            activation_history=self._activation_history.get(stressor_id, []),
            statistical_summary=self._statistics.get(stressor_id, StatisticalSummary()),
        )
    
    def is_enabled(self, stressor_id: str) -> bool:
        """Check if a stressor is enabled."""
        params = self._parameters.get(stressor_id)
        return params.enabled if params else False
