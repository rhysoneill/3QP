"""
Condition evaluators for intervention activation.

Provides abstract condition evaluation logic without semantic interpretation.
"""

from typing import Dict, List, Any, Optional
from .types import (
    ThresholdCondition,
    TemporalCondition,
    EventCondition,
    CompoundCondition,
    ActivationCondition,
    ConditionOperator,
    LogicOperator,
    Event
)


class EvaluationContext:
    """
    Context for condition evaluation.
    
    Encapsulates all data needed to evaluate activation conditions.
    """
    
    def __init__(
        self,
        time_step: int,
        input_signals: Dict[str, float],
        events: List[Event],
        intervention_history: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize evaluation context.
        
        Args:
            time_step: Current simulation time-step
            input_signals: Signal values from other modules
            events: Events that occurred in this time-step
            intervention_history: Historical data for the intervention (optional)
        """
        self.time_step = time_step
        self.input_signals = input_signals
        self.events = events
        self.intervention_history = intervention_history if intervention_history is not None else {}


class ConditionEvaluator:
    """
    Evaluates activation conditions for interventions.
    
    Provides polymorphic evaluation of different condition types.
    """
    
    @staticmethod
    def evaluate(
        condition: ActivationCondition,
        context: EvaluationContext
    ) -> bool:
        """
        Evaluate an activation condition.
        
        Args:
            condition: The condition to evaluate
            context: Evaluation context with signals, events, etc.
            
        Returns:
            True if condition is satisfied, False otherwise
        """
        if isinstance(condition, ThresholdCondition):
            return ConditionEvaluator._evaluate_threshold(condition, context)
        elif isinstance(condition, TemporalCondition):
            return ConditionEvaluator._evaluate_temporal(condition, context)
        elif isinstance(condition, EventCondition):
            return ConditionEvaluator._evaluate_event(condition, context)
        elif isinstance(condition, CompoundCondition):
            return ConditionEvaluator._evaluate_compound(condition, context)
        else:
            raise ValueError(f"Unknown condition type: {type(condition)}")
    
    @staticmethod
    def _evaluate_threshold(
        condition: ThresholdCondition,
        context: EvaluationContext
    ) -> bool:
        """Evaluate a threshold condition."""
        # Check if signal is present
        if condition.signal_id not in context.input_signals:
            return False  # Fail-safe: missing signal = condition not met
        
        signal_value = context.input_signals[condition.signal_id]
        threshold = condition.threshold_value
        
        # Apply hysteresis if specified
        if condition.hysteresis_buffer > 0:
            # Get historical threshold crossings from context
            history = context.intervention_history.get('threshold_history', {})
            last_state = history.get(condition.signal_id, False)
            
            # Adjust threshold based on hysteresis
            if last_state:
                # Was previously satisfied, lower threshold to prevent flapping
                if condition.operator in [ConditionOperator.GT, ConditionOperator.GTE]:
                    threshold = threshold - condition.hysteresis_buffer
                elif condition.operator in [ConditionOperator.LT, ConditionOperator.LTE]:
                    threshold = threshold + condition.hysteresis_buffer
        
        # Evaluate operator
        result = False
        if condition.operator == ConditionOperator.GT:
            result = signal_value > threshold
        elif condition.operator == ConditionOperator.LT:
            result = signal_value < threshold
        elif condition.operator == ConditionOperator.EQ:
            result = abs(signal_value - threshold) < 1e-9  # Float equality tolerance
        elif condition.operator == ConditionOperator.NEQ:
            result = abs(signal_value - threshold) >= 1e-9
        elif condition.operator == ConditionOperator.GTE:
            result = signal_value >= threshold
        elif condition.operator == ConditionOperator.LTE:
            result = signal_value <= threshold
        
        # Check duration requirement
        if condition.duration_required > 1:
            # Ensure duration_counter dict exists
            if 'duration_counter' not in context.intervention_history:
                context.intervention_history['duration_counter'] = {}
            
            counter = context.intervention_history['duration_counter'].get(condition.signal_id, 0)
            
            if result:
                counter += 1
            else:
                counter = 0
            
            # Store updated counter
            context.intervention_history['duration_counter'][condition.signal_id] = counter
            
            # Only satisfied if duration requirement met
            result = counter >= condition.duration_required
        
        return result
    
    @staticmethod
    def _evaluate_temporal(
        condition: TemporalCondition,
        context: EvaluationContext
    ) -> bool:
        """Evaluate a temporal condition."""
        time_step = context.time_step
        
        # Check if we're past end time (if specified)
        if condition.end_time is not None and time_step > condition.end_time:
            return False
        
        # Check recurrence pattern
        if condition.recurrence_pattern is not None:
            pattern = condition.recurrence_pattern
            
            # Check if count limit reached
            if pattern.count is not None:
                activations = context.intervention_history.get('activation_count', 0)
                if activations >= pattern.count:
                    return False
            
            # Calculate if this time-step matches the pattern
            if time_step < condition.start_time:
                return False
            
            time_since_start = time_step - condition.start_time
            if time_since_start < pattern.offset:
                return False
            
            adjusted_time = time_since_start - pattern.offset
            
            # Only activate on exact intervals
            if adjusted_time % pattern.interval == 0:
                # Update activation count
                if 'activation_count' not in context.intervention_history:
                    context.intervention_history['activation_count'] = 0
                context.intervention_history['activation_count'] += 1
                return True
            return False
        else:
            # Non-recurring: activate exactly at start_time
            return time_step == condition.start_time
    
    @staticmethod
    def _evaluate_event(
        condition: EventCondition,
        context: EvaluationContext
    ) -> bool:
        """Evaluate an event condition."""
        # Check cooldown
        if condition.cooldown_period > 0:
            last_activation = context.intervention_history.get('last_event_activation')
            if last_activation is not None:
                if context.time_step - last_activation < condition.cooldown_period:
                    return False
        
        # Check if matching event occurred
        for event in context.events:
            if event.event_id != condition.event_id:
                continue
            
            # Apply filter if specified
            if condition.event_filter is not None:
                # Check if all filter criteria match
                match = True
                for key, expected_value in condition.event_filter.items():
                    if key not in event.attributes:
                        match = False
                        break
                    if event.attributes[key] != expected_value:
                        match = False
                        break
                
                if not match:
                    continue
            
            # Event matched
            return True
        
        return False
    
    @staticmethod
    def _evaluate_compound(
        condition: CompoundCondition,
        context: EvaluationContext
    ) -> bool:
        """Evaluate a compound condition."""
        # Determine evaluation order
        if condition.evaluation_order is not None:
            indices = condition.evaluation_order
        else:
            indices = list(range(len(condition.conditions)))
        
        # Evaluate based on logic operator
        if condition.logic_operator == LogicOperator.AND:
            # Short-circuit evaluation for AND
            for idx in indices:
                sub_condition = condition.conditions[idx]
                if not ConditionEvaluator.evaluate(sub_condition, context):
                    return False
            return True
        
        elif condition.logic_operator == LogicOperator.OR:
            # Short-circuit evaluation for OR
            for idx in indices:
                sub_condition = condition.conditions[idx]
                if ConditionEvaluator.evaluate(sub_condition, context):
                    return True
            return False
        
        elif condition.logic_operator == LogicOperator.XOR:
            # XOR requires evaluating all conditions
            true_count = 0
            for idx in indices:
                sub_condition = condition.conditions[idx]
                if ConditionEvaluator.evaluate(sub_condition, context):
                    true_count += 1
            return true_count == 1
        
        else:
            raise ValueError(f"Unknown logic operator: {condition.logic_operator}")
