"""
Main Intervention Engine implementation.

Coordinates intervention lifecycle management, condition evaluation,
and effect emission.
"""

from typing import Dict, List, Optional
from .types import (
    InterventionConfig,
    InterventionEffect,
    InterventionState,
    InterventionStateInfo,
    EffectType,
    Event,
    StateTransitionRecord
)
from .registry import InterventionRegistry
from .conditions import ConditionEvaluator, EvaluationContext


class InterventionEngine:
    """
    Main engine for managing intervention lifecycles.
    
    Provides the primary interface for the Intervention Engine subsystem.
    Coordinates condition evaluation, state transitions, and effect emission.
    """
    
    def __init__(self):
        """Initialize the intervention engine."""
        self._registry = InterventionRegistry()
        self._current_time_step = 0
    
    def update(
        self,
        time_step: int,
        input_signals: Dict[str, float],
        events: Optional[List[Event]] = None
    ) -> List[InterventionEffect]:
        """
        Execute one time-step update cycle.
        
        Args:
            time_step: Current simulation time-step index
            input_signals: Signal values from other modules
            events: Discrete events that occurred this time-step
            
        Returns:
            List of intervention effects emitted during this time-step
        """
        # Validate inputs
        if time_step < self._current_time_step:
            raise ValueError(
                f"time_step must be monotonically increasing: "
                f"got {time_step}, expected >= {self._current_time_step}"
            )
        
        self._current_time_step = time_step
        events = events or []
        effects = []
        
        # Phase 1: Evaluate activation conditions for ARMED interventions
        armed_interventions = self._registry.list_by_state(InterventionState.ARMED)
        
        for intervention_id in armed_interventions:
            record = self._registry.get(intervention_id)
            if record is None:
                continue
            
            # Build evaluation context
            context = EvaluationContext(
                time_step=time_step,
                input_signals=input_signals,
                events=events,
                intervention_history=record.condition_history
            )
            
            # Evaluate activation condition
            config = record.config
            if ConditionEvaluator.evaluate(config.activation_conditions, context):
                # Check phase alignment if specified
                if config.schedule.phase_alignment is not None:
                    if time_step % config.schedule.phase_alignment != 0:
                        continue
                
                # Activate the intervention
                if self._registry.activate(
                    intervention_id,
                    time_step,
                    f"Condition satisfied at t={time_step}"
                ):
                    # Set initial active duration
                    record = self._registry.get(intervention_id)
                    record.active_duration_elapsed = 1
                    
                    # Emit activation effect
                    effect = self._create_activation_effect(intervention_id, time_step)
                    effects.append(effect)
        
        # Phase 2: Update active interventions
        active_interventions = self._registry.list_by_state(InterventionState.ACTIVE)
        
        for intervention_id in active_interventions:
            record = self._registry.get(intervention_id)
            if record is None:
                continue
            
            # Skip interventions that just activated this time-step
            if record.time_activated == time_step:
                continue
            
            # Increment active duration
            record.active_duration_elapsed += 1
            
            # Check if intervention should expire
            schedule = record.config.schedule
            duration = record.config.duration
            
            # Check schedule active_duration
            should_expire = False
            if record.active_duration_elapsed >= schedule.active_duration:
                should_expire = True
            
            # Check max_duration if specified
            if duration.max_duration is not None:
                if record.active_duration_elapsed >= duration.max_duration:
                    should_expire = True
            
            if should_expire:
                # Expire the intervention
                if self._registry.expire(intervention_id, time_step):
                    # Emit deactivation effect
                    effect = self._create_deactivation_effect(intervention_id, time_step)
                    effects.append(effect)
        
        # Phase 3: Handle recurrent interventions
        expired_interventions = self._registry.list_by_state(InterventionState.EXPIRED)
        
        for intervention_id in expired_interventions:
            record = self._registry.get(intervention_id)
            if record is None:
                continue
            
            config = record.config
            
            # Check if this is a recurrent intervention
            if config.category == "recurrent":
                # Check if it's time to re-arm
                if record.next_activation_time is None:
                    # First expiration - schedule next activation
                    next_time = time_step + config.schedule.inactive_duration
                    record.next_activation_time = next_time
                
                if time_step >= record.next_activation_time:
                    # Reset to ARMED state
                    self._registry.reset(intervention_id, time_step)
        
        # Phase 4: Sort effects by priority (high to low)
        effects.sort(key=lambda e: self._get_priority(e.intervention_id), reverse=True)
        
        return effects
    
    def register_intervention(self, config: InterventionConfig) -> str:
        """
        Register a new intervention.
        
        Args:
            config: Complete intervention configuration
            
        Returns:
            Intervention ID
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate signal references
        # TODO: Integrate with TQP Core to verify signals exist
        
        return self._registry.register(config)
    
    def modify_intervention(
        self,
        intervention_id: str,
        updates: Dict[str, any]
    ) -> bool:
        """
        Modify an existing intervention.
        
        Args:
            intervention_id: ID of intervention to modify
            updates: Partial configuration updates
            
        Returns:
            True if modified, False if intervention not found
            
        Note:
            Modifications are limited to metadata and schedule parameters.
            Changing activation conditions is not supported for active interventions.
        """
        record = self._registry.get(intervention_id)
        if record is None:
            return False
        
        # Only allow modifications to specific fields
        allowed_fields = {'metadata', 'priority'}
        
        for key, value in updates.items():
            if key not in allowed_fields:
                raise ValueError(f"Cannot modify field '{key}'")
            
            if key == 'metadata':
                record.config.metadata.update(value)
            elif key == 'priority':
                record.config.priority = value
        
        return True
    
    def remove_intervention(self, intervention_id: str) -> bool:
        """
        Remove an intervention from the engine.
        
        Args:
            intervention_id: ID of intervention to remove
            
        Returns:
            True if removed, False if not found
        """
        return self._registry.remove(intervention_id)
    
    def get_state(self, intervention_id: str) -> Optional[InterventionStateInfo]:
        """
        Get current state information for an intervention.
        
        Args:
            intervention_id: ID of intervention
            
        Returns:
            State information, or None if not found
        """
        return self._registry.get_state_info(intervention_id)
    
    def list_active_interventions(self) -> List[str]:
        """
        List all interventions currently in ACTIVE state.
        
        Returns:
            List of intervention IDs, ordered by activation time
        """
        active_ids = self._registry.list_by_state(InterventionState.ACTIVE)
        
        # Sort by activation time (earliest first)
        def get_activation_time(intervention_id: str) -> int:
            record = self._registry.get(intervention_id)
            if record is None or record.time_activated is None:
                return float('inf')
            return record.time_activated
        
        active_ids.sort(key=get_activation_time)
        
        return active_ids
    
    def get_intervention_history(
        self,
        intervention_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[StateTransitionRecord]:
        """
        Get state transition history for an intervention.
        
        Args:
            intervention_id: ID of intervention
            start_time: Start of time range (inclusive, optional)
            end_time: End of time range (inclusive, optional)
            
        Returns:
            List of state transition records
        """
        return self._registry.get_history(intervention_id, start_time, end_time)
    
    def _create_activation_effect(
        self,
        intervention_id: str,
        time_step: int
    ) -> InterventionEffect:
        """Create an activation effect for an intervention."""
        record = self._registry.get(intervention_id)
        
        # Emit abstract activation signal
        signal_values = {
            f"{intervention_id}_active": 1.0
        }
        
        return InterventionEffect(
            intervention_id=intervention_id,
            effect_type=EffectType.ACTIVATION,
            timestamp=time_step,
            signal_values=signal_values
        )
    
    def _create_deactivation_effect(
        self,
        intervention_id: str,
        time_step: int
    ) -> InterventionEffect:
        """Create a deactivation effect for an intervention."""
        # Emit abstract deactivation signal
        signal_values = {
            f"{intervention_id}_active": 0.0
        }
        
        return InterventionEffect(
            intervention_id=intervention_id,
            effect_type=EffectType.DEACTIVATION,
            timestamp=time_step,
            signal_values=signal_values
        )
    
    def _get_priority(self, intervention_id: str) -> int:
        """Get priority of an intervention."""
        record = self._registry.get(intervention_id)
        if record is None:
            return 0
        return record.config.priority
    
    # Additional query methods for debugging and monitoring
    
    def get_all_interventions(self) -> List[str]:
        """Get IDs of all registered interventions."""
        return list(self._registry._interventions.keys())
    
    def get_interventions_by_state(self, state: InterventionState) -> List[str]:
        """Get all interventions in a specific state."""
        return self._registry.list_by_state(state)
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get engine statistics.
        
        Returns:
            Dictionary with various statistics
        """
        all_interventions = self.get_all_interventions()
        
        stats = {
            'total_interventions': len(all_interventions),
            'current_time_step': self._current_time_step,
            'state_distribution': {
                state.value: len(self._registry.list_by_state(state))
                for state in InterventionState
            },
            'active_count': len(self.list_active_interventions())
        }
        
        return stats
