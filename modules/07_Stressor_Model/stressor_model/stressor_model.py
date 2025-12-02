"""
Main Stressor Model implementation.

Orchestrates stressor updates, event handling, and output generation
according to the 3QP architecture specifications.
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta

from .types import (
    MissionConfig,
    UpdateCycleInput,
    StressorIntensityVector,
    StressorValue,
    StateFlags,
    SummaryMetrics,
    StressorCategory,
    StressorMetadata,
    SpikeEvent,
)
from .registry import StressorRegistry


class StressorModel:
    """
    Lunar Mission Stressor Model.
    
    Generates time-varying stressor signals representing mission-relevant
    demands without interpreting psychological states or behavioral responses.
    """
    
    def __init__(self):
        self.registry = StressorRegistry()
        self.mission_config: Optional[MissionConfig] = None
        self.current_time: float = 0.0
        self.mission_start_date: Optional[datetime] = None
        
        # Event tracking
        self._scheduled_spikes: Dict[str, List[SpikeEvent]] = {}
        self._active_modifiers: Dict[str, List[tuple[float, float]]] = {}  # (delta, end_time)
    
    def initialize(self, config: MissionConfig):
        """
        Initialize the Stressor Model with mission configuration.
        
        Args:
            config: Mission configuration including stressor parameters
        """
        self.mission_config = config
        self.mission_start_date = config.mission_start_date
        self.current_time = 0.0
        
        # Initialize registry
        self.registry.initialize(config.stressor_parameters, config.random_seed)
        
        # Build scheduled spikes map
        for params in config.stressor_parameters:
            if params.spike_schedule:
                self._scheduled_spikes[params.stressor_id] = sorted(
                    params.spike_schedule, key=lambda s: s.trigger_time
                )
        
        # Initialize active modifiers tracking
        for stressor_id in self.registry.get_all_stressor_ids():
            self._active_modifiers[stressor_id] = []
    
    def update(self, update_input: UpdateCycleInput) -> StressorIntensityVector:
        """
        Update all stressors for the current timestep.
        
        Args:
            update_input: Input data for this update cycle
            
        Returns:
            Complete stressor intensity vector
        """
        # Validate temporal consistency
        if update_input.current_time < self.current_time:
            raise ValueError(
                f"Mission time regression detected: {self.current_time} -> "
                f"{update_input.current_time}"
            )
        
        self.current_time = update_input.current_time
        delta_time = update_input.delta_time
        
        # Process triggered events
        self._process_events(update_input.triggered_events)
        
        # Check for scheduled spikes
        self._check_scheduled_spikes(self.current_time)
        
        # Update all stressors
        stressor_values = self._update_all_stressors(delta_time)
        
        # Assemble output
        return self._assemble_output(stressor_values)
    
    def _process_events(self, triggered_events):
        """
        Process events that occurred in this timestep.
        
        Args:
            triggered_events: List of TriggeredEvent objects
        """
        if self.mission_config is None:
            return
        
        for triggered_event in triggered_events:
            # Find corresponding scheduled event
            matching_events = [
                e for e in self.mission_config.event_schedule
                if e.event_id == triggered_event.event_id
            ]
            
            if not matching_events:
                continue
            
            scheduled_event = matching_events[0]
            
            # Apply stressor modifiers
            for modifier in scheduled_event.stressor_modifiers:
                stressor_id = modifier.stressor_id
                end_time = self.current_time + modifier.duration
                
                if stressor_id in self._active_modifiers:
                    self._active_modifiers[stressor_id].append(
                        (modifier.intensity_delta, end_time)
                    )
    
    def _check_scheduled_spikes(self, current_time: float):
        """
        Check if any scheduled spikes should trigger.
        
        Args:
            current_time: Current mission time
        """
        for stressor_id, spikes in self._scheduled_spikes.items():
            # Find spikes that should trigger
            triggered_spikes = [
                s for s in spikes
                if s.trigger_time <= current_time < s.trigger_time + s.duration
            ]
            
            if triggered_spikes:
                self.registry.trigger_spike(stressor_id, current_time)
    
    def _update_all_stressors(self, delta_time: float) -> Dict[str, StressorValue]:
        """
        Update all registered stressors.
        
        Args:
            delta_time: Time elapsed since last update
            
        Returns:
            Dictionary mapping stressor IDs to StressorValue objects
        """
        stressor_values = {}
        
        for stressor_id in self.registry.get_all_stressor_ids():
            # Check if stressor is enabled
            if not self.registry.is_enabled(stressor_id):
                state = self.registry.get_state(stressor_id)
                stressor_values[stressor_id] = StressorValue(
                    stressor_id=stressor_id,
                    current_intensity=0.0,
                    accumulated_exposure=state.accumulated_exposure if state else 0.0,
                    state_flags=StateFlags(is_active=False),
                )
                continue
            
            # Get current state and intensity function
            state = self.registry.get_state(stressor_id)
            intensity_func = self.registry.get_intensity_function(stressor_id)
            
            if state is None or intensity_func is None:
                continue
            
            # Compute base intensity
            base_intensity = intensity_func.compute(state, self.current_time, delta_time)
            
            # Apply scheduled spikes
            spike_contribution = self._compute_spike_contribution(stressor_id)
            
            # Apply event modifiers
            modifier_contribution = self._compute_modifier_contribution(stressor_id, delta_time)
            
            # Combine contributions
            new_intensity = base_intensity + spike_contribution + modifier_contribution
            
            # Clamp to [0, 1]
            new_intensity = max(0.0, min(1.0, new_intensity))
            
            # Check for degradation (if clamping was needed)
            is_degraded = (
                base_intensity + spike_contribution + modifier_contribution != new_intensity
            )
            
            # Update state
            self.registry.update_state(
                stressor_id, new_intensity, self.current_time, delta_time
            )
            
            # Check if spiking
            is_spiking = spike_contribution > 0.01
            
            # Create StressorValue
            stressor_values[stressor_id] = StressorValue(
                stressor_id=stressor_id,
                current_intensity=new_intensity,
                accumulated_exposure=state.accumulated_exposure,
                last_spike_time=state.last_spike_time,
                spike_count=state.spike_count,
                state_flags=StateFlags(
                    is_active=True,
                    is_spiking=is_spiking,
                    is_degraded=is_degraded,
                ),
            )
        
        return stressor_values
    
    def _compute_spike_contribution(self, stressor_id: str) -> float:
        """
        Compute intensity contribution from scheduled spikes.
        
        Args:
            stressor_id: ID of stressor
            
        Returns:
            Spike contribution to intensity
        """
        if stressor_id not in self._scheduled_spikes:
            return 0.0
        
        total_contribution = 0.0
        
        for spike in self._scheduled_spikes[stressor_id]:
            if spike.trigger_time <= self.current_time < spike.trigger_time + spike.duration:
                # Gaussian pulse
                time_from_spike = self.current_time - spike.trigger_time
                width = spike.duration / 4.0  # 4-sigma width
                contribution = spike.magnitude * (
                    (2.718281828 ** (-((time_from_spike / width) ** 2)))
                )
                total_contribution += contribution
        
        return total_contribution
    
    def _compute_modifier_contribution(self, stressor_id: str, delta_time: float) -> float:
        """
        Compute intensity contribution from event modifiers.
        
        Args:
            stressor_id: ID of stressor
            delta_time: Time elapsed
            
        Returns:
            Modifier contribution to intensity
        """
        if stressor_id not in self._active_modifiers:
            return 0.0
        
        # Clean up expired modifiers
        active = [
            (delta, end_time)
            for delta, end_time in self._active_modifiers[stressor_id]
            if self.current_time < end_time
        ]
        self._active_modifiers[stressor_id] = active
        
        # Sum active modifiers
        total_delta = sum(delta for delta, _ in active)
        return total_delta
    
    def _assemble_output(
        self, stressor_values: Dict[str, StressorValue]
    ) -> StressorIntensityVector:
        """
        Assemble complete output structure.
        
        Args:
            stressor_values: Dictionary of stressor values
            
        Returns:
            StressorIntensityVector with all stressors organized by category
        """
        # Organize by category
        operational = []
        environmental = []
        temporal = []
        monotony = []
        
        for stressor_id, value in stressor_values.items():
            params = self.registry.get_parameters(stressor_id)
            if params is None:
                continue
            
            if params.category == StressorCategory.OPERATIONAL:
                operational.append(value)
            elif params.category == StressorCategory.ENVIRONMENTAL:
                environmental.append(value)
            elif params.category == StressorCategory.TEMPORAL:
                temporal.append(value)
            elif params.category == StressorCategory.MONOTONY:
                monotony.append(value)
        
        # Compute summary metrics
        summary = self._compute_summary_metrics(
            operational, environmental, temporal, monotony
        )
        
        # Calculate timestamp
        timestamp = self.mission_start_date + timedelta(days=self.current_time)
        
        return StressorIntensityVector(
            mission_time=self.current_time,
            timestamp=timestamp,
            operational_stressors=operational,
            environmental_stressors=environmental,
            temporal_stressors=temporal,
            monotony_stressors=monotony,
            summary_metrics=summary,
        )
    
    def _compute_summary_metrics(
        self,
        operational: List[StressorValue],
        environmental: List[StressorValue],
        temporal: List[StressorValue],
        monotony: List[StressorValue],
    ) -> SummaryMetrics:
        """
        Compute aggregate summary metrics.
        
        Args:
            operational: List of operational stressor values
            environmental: List of environmental stressor values
            temporal: List of temporal stressor values
            monotony: List of monotony stressor values
            
        Returns:
            Summary metrics
        """
        def avg_intensity(stressor_list: List[StressorValue]) -> float:
            if not stressor_list:
                return 0.0
            active = [s for s in stressor_list if s.state_flags.is_active]
            if not active:
                return 0.0
            return sum(s.current_intensity for s in active) / len(active)
        
        op_total = avg_intensity(operational)
        env_total = avg_intensity(environmental)
        temp_total = avg_intensity(temporal)
        mono_total = avg_intensity(monotony)
        
        # Overall load is weighted average (equal weights for now)
        overall = (op_total + env_total + temp_total + mono_total) / 4.0
        
        return SummaryMetrics(
            total_operational_intensity=op_total,
            total_environmental_intensity=env_total,
            total_temporal_intensity=temp_total,
            total_monotony_intensity=mono_total,
            overall_stressor_load=overall,
        )
    
    def get_stressor_intensity(self, stressor_id: str, time: Optional[float] = None) -> float:
        """
        Query stressor intensity at a specific time.
        
        Args:
            stressor_id: ID of stressor to query
            time: Mission time (if None, uses current time)
            
        Returns:
            Intensity value
        """
        # For now, only support current time queries
        # Historical queries would require state history storage
        if time is not None and time != self.current_time:
            raise NotImplementedError("Historical queries not yet supported")
        
        state = self.registry.get_state(stressor_id)
        if state is None:
            return 0.0
        
        return state.current_intensity
    
    def get_stressor_metadata(self, stressor_id: str) -> Optional[StressorMetadata]:
        """
        Get metadata for a stressor.
        
        Args:
            stressor_id: ID of stressor
            
        Returns:
            Metadata object or None if not found
        """
        return self.registry.get_metadata(stressor_id)
