"""
Intervention registry and state machine management.

Manages intervention lifecycle states and transitions.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import heapq
from .types import (
    InterventionState,
    InterventionConfig,
    StateTransitionRecord,
    InterventionStateInfo,
    TemporalCondition
)


# State transition matrix: (from_state, trigger) -> to_state
# Legal transitions defined in spec.md
STATE_TRANSITION_TABLE = {
    (InterventionState.UNINITIALIZED, "configure"): InterventionState.ARMED,
    (InterventionState.ARMED, "activate"): InterventionState.ACTIVE,
    (InterventionState.ACTIVE, "suspend"): InterventionState.SUSPENDED,
    (InterventionState.SUSPENDED, "resume"): InterventionState.ACTIVE,
    (InterventionState.ACTIVE, "expire"): InterventionState.EXPIRED,
    (InterventionState.ACTIVE, "cancel"): InterventionState.CANCELLED,
    (InterventionState.EXPIRED, "reset"): InterventionState.ARMED,
    (InterventionState.CANCELLED, "reset"): InterventionState.ARMED,
}


@dataclass
class InterventionRecord:
    """Internal record for an intervention with state tracking."""
    config: InterventionConfig
    current_state: InterventionState = InterventionState.UNINITIALIZED
    time_activated: Optional[int] = None
    time_last_transition: Optional[int] = None
    active_duration_elapsed: int = 0
    next_activation_time: Optional[int] = None
    
    # Condition evaluation history
    condition_history: Dict[str, Any] = field(default_factory=dict)
    
    # State transition history (limited to recent transitions)
    transition_history: List[StateTransitionRecord] = field(default_factory=list)


class InterventionRegistry:
    """
    Central registry for all intervention instances.
    
    Manages storage, indexing, and state transitions for interventions.
    """
    
    def __init__(self):
        """Initialize the registry."""
        # Primary storage: intervention_id -> InterventionRecord
        self._interventions: Dict[str, InterventionRecord] = {}
        
        # State index: state -> set of intervention_ids
        self._state_index: Dict[InterventionState, Set[str]] = {
            state: set() for state in InterventionState
        }
        
        # Signal index: signal_id -> set of intervention_ids that monitor it
        self._signal_index: Dict[str, Set[str]] = {}
        
        # Event index: event_id -> set of intervention_ids that respond to it
        self._event_index: Dict[str, Set[str]] = {}
        
        # Priority queue for time-based activations: (activation_time, intervention_id)
        self._temporal_queue: List[tuple] = []
    
    def register(self, config: InterventionConfig) -> str:
        """
        Register a new intervention.
        
        Args:
            config: Intervention configuration
            
        Returns:
            Intervention ID
            
        Raises:
            ValueError: If intervention with same ID already exists
        """
        if config.id in self._interventions:
            raise ValueError(f"Intervention with ID '{config.id}' already exists")
        
        # Create intervention record
        record = InterventionRecord(config=config)
        self._interventions[config.id] = record
        
        # Add to state index
        self._state_index[InterventionState.UNINITIALIZED].add(config.id)
        
        # Build signal and event indices
        self._index_intervention(config)
        
        # Transition to ARMED state
        self._transition(config.id, "configure", time_step=0)
        
        return config.id
    
    def _index_intervention(self, config: InterventionConfig):
        """Build indices for signal and event lookup."""
        from .types import ThresholdCondition, EventCondition, CompoundCondition
        
        def index_condition(condition):
            """Recursively index a condition."""
            if isinstance(condition, ThresholdCondition):
                # Add to signal index
                signal_id = condition.signal_id
                if signal_id not in self._signal_index:
                    self._signal_index[signal_id] = set()
                self._signal_index[signal_id].add(config.id)
            
            elif isinstance(condition, EventCondition):
                # Add to event index
                event_id = condition.event_id
                if event_id not in self._event_index:
                    self._event_index[event_id] = set()
                self._event_index[event_id].add(config.id)
            
            elif isinstance(condition, TemporalCondition):
                # Add to temporal queue
                heapq.heappush(
                    self._temporal_queue,
                    (condition.start_time, config.id)
                )
            
            elif isinstance(condition, CompoundCondition):
                # Recursively index sub-conditions
                for sub_condition in condition.conditions:
                    index_condition(sub_condition)
        
        index_condition(config.activation_conditions)
    
    def remove(self, intervention_id: str) -> bool:
        """
        Remove an intervention from the registry.
        
        Args:
            intervention_id: ID of intervention to remove
            
        Returns:
            True if removed, False if not found
        """
        if intervention_id not in self._interventions:
            return False
        
        record = self._interventions[intervention_id]
        
        # Remove from state index
        self._state_index[record.current_state].discard(intervention_id)
        
        # Remove from signal/event indices
        for signal_set in self._signal_index.values():
            signal_set.discard(intervention_id)
        for event_set in self._event_index.values():
            event_set.discard(intervention_id)
        
        # Remove from temporal queue (lazy removal - will be filtered when popped)
        
        # Remove from primary storage
        del self._interventions[intervention_id]
        
        return True
    
    def get(self, intervention_id: str) -> Optional[InterventionRecord]:
        """Get an intervention record by ID."""
        return self._interventions.get(intervention_id)
    
    def get_state_info(self, intervention_id: str) -> Optional[InterventionStateInfo]:
        """Get state information for an intervention."""
        record = self.get(intervention_id)
        if record is None:
            return None
        
        return InterventionStateInfo(
            id=intervention_id,
            current_state=record.current_state,
            time_activated=record.time_activated,
            time_last_transition=record.time_last_transition,
            active_duration_elapsed=record.active_duration_elapsed
        )
    
    def list_by_state(self, state: InterventionState) -> List[str]:
        """List all intervention IDs in a given state."""
        return list(self._state_index[state])
    
    def get_by_signal(self, signal_id: str) -> Set[str]:
        """Get interventions monitoring a specific signal."""
        return self._signal_index.get(signal_id, set())
    
    def get_by_event(self, event_id: str) -> Set[str]:
        """Get interventions responding to a specific event."""
        return self._event_index.get(event_id, set())
    
    def get_temporal_candidates(self, time_step: int) -> List[str]:
        """
        Get interventions eligible for temporal activation.
        
        Args:
            time_step: Current simulation time-step
            
        Returns:
            List of intervention IDs
        """
        candidates = []
        
        # Pop all interventions whose activation time has arrived
        while self._temporal_queue and self._temporal_queue[0][0] <= time_step:
            activation_time, intervention_id = heapq.heappop(self._temporal_queue)
            
            # Check if intervention still exists (lazy deletion)
            if intervention_id in self._interventions:
                record = self._interventions[intervention_id]
                # Only include if in ARMED state
                if record.current_state == InterventionState.ARMED:
                    candidates.append(intervention_id)
        
        return candidates
    
    def _transition(
        self,
        intervention_id: str,
        trigger: str,
        time_step: int,
        trigger_description: Optional[str] = None
    ) -> bool:
        """
        Execute a state transition.
        
        Args:
            intervention_id: ID of intervention
            trigger: Transition trigger (e.g., "activate", "expire")
            time_step: Current simulation time-step
            trigger_description: Optional description of what caused transition
            
        Returns:
            True if transition executed, False if illegal transition
        """
        record = self._interventions.get(intervention_id)
        if record is None:
            return False
        
        current_state = record.current_state
        
        # Check if transition is legal
        transition_key = (current_state, trigger)
        if transition_key not in STATE_TRANSITION_TABLE:
            # Illegal transition - log error but don't crash
            # TODO: Emit logging event via Logging_System interface
            return False
        
        next_state = STATE_TRANSITION_TABLE[transition_key]
        
        # Update state indices
        self._state_index[current_state].discard(intervention_id)
        self._state_index[next_state].add(intervention_id)
        
        # Update record
        record.current_state = next_state
        record.time_last_transition = time_step
        
        # Special state-specific updates
        if next_state == InterventionState.ACTIVE:
            record.time_activated = time_step
            record.active_duration_elapsed = 0  # Starts at 0, incremented each update
        
        # Record transition in history
        transition_record = StateTransitionRecord(
            timestamp=time_step,
            from_state=current_state,
            to_state=next_state,
            trigger=trigger_description or trigger
        )
        record.transition_history.append(transition_record)
        
        # Limit history size (keep last 100 transitions)
        if len(record.transition_history) > 100:
            record.transition_history = record.transition_history[-100:]
        
        return True
    
    def activate(
        self,
        intervention_id: str,
        time_step: int,
        trigger_description: Optional[str] = None
    ) -> bool:
        """Transition intervention to ACTIVE state."""
        return self._transition(intervention_id, "activate", time_step, trigger_description)
    
    def expire(
        self,
        intervention_id: str,
        time_step: int
    ) -> bool:
        """Transition intervention to EXPIRED state."""
        return self._transition(intervention_id, "expire", time_step, "Duration elapsed")
    
    def suspend(
        self,
        intervention_id: str,
        time_step: int
    ) -> bool:
        """Transition intervention to SUSPENDED state."""
        return self._transition(intervention_id, "suspend", time_step)
    
    def resume(
        self,
        intervention_id: str,
        time_step: int
    ) -> bool:
        """Resume a suspended intervention."""
        return self._transition(intervention_id, "resume", time_step)
    
    def cancel(
        self,
        intervention_id: str,
        time_step: int
    ) -> bool:
        """Cancel an intervention."""
        return self._transition(intervention_id, "cancel", time_step)
    
    def reset(
        self,
        intervention_id: str,
        time_step: int
    ) -> bool:
        """Reset an expired or cancelled intervention (for recurrent interventions)."""
        record = self.get(intervention_id)
        if record is None:
            return False
        
        # Calculate next activation time for recurrent interventions
        if record.config.category == "recurrent":
            next_time = time_step + record.config.schedule.inactive_duration
            record.next_activation_time = next_time
            
            # Re-add to temporal queue
            heapq.heappush(self._temporal_queue, (next_time, intervention_id))
        
        return self._transition(intervention_id, "reset", time_step)
    
    def get_history(
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
            List of transition records
        """
        record = self.get(intervention_id)
        if record is None:
            return []
        
        history = record.transition_history
        
        # Filter by time range
        if start_time is not None:
            history = [r for r in history if r.timestamp >= start_time]
        if end_time is not None:
            history = [r for r in history if r.timestamp <= end_time]
        
        return history
