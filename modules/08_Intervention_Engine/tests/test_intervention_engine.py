"""
Unit tests for Intervention Engine.

Tests condition evaluation, state transitions, and intervention lifecycle.
"""

import unittest
from intervention_engine import (
    InterventionEngine,
    InterventionConfig,
    InterventionState,
    ThresholdCondition,
    TemporalCondition,
    EventCondition,
    CompoundCondition,
    Schedule,
    Duration,
    RecurrencePattern,
    ConditionOperator,
    CadenceType,
    DecayType,
    LogicOperator,
    Event
)


class TestThresholdConditions(unittest.TestCase):
    """Test threshold-based activation conditions."""
    
    def test_threshold_gt(self):
        """Test greater-than threshold condition."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_001",
            category="reactive",
            type_tag="threshold_test",
            activation_conditions=ThresholdCondition(
                signal_id="signal_alpha",
                operator=ConditionOperator.GT,
                threshold_value=0.7
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=5
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Signal below threshold - should not activate
        effects = engine.update(1, {"signal_alpha": 0.5})
        self.assertEqual(len(effects), 0)
        
        # Signal above threshold - should activate
        effects = engine.update(2, {"signal_alpha": 0.8})
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].intervention_id, "test_001")
    
    def test_threshold_duration_requirement(self):
        """Test threshold condition with duration requirement."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_002",
            category="reactive",
            type_tag="duration_test",
            activation_conditions=ThresholdCondition(
                signal_id="signal_beta",
                operator=ConditionOperator.GT,
                threshold_value=0.5,
                duration_required=3
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=5
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Signal above threshold for only 1 step - should not activate
        effects = engine.update(1, {"signal_beta": 0.6})
        self.assertEqual(len(effects), 0)
        
        # Second step - still not enough
        effects = engine.update(2, {"signal_beta": 0.6})
        self.assertEqual(len(effects), 0)
        
        # Third step - now should activate
        effects = engine.update(3, {"signal_beta": 0.6})
        self.assertEqual(len(effects), 1)


class TestTemporalConditions(unittest.TestCase):
    """Test time-based activation conditions."""
    
    def test_single_activation(self):
        """Test single-time activation."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_003",
            category="scheduled",
            type_tag="temporal_test",
            activation_conditions=TemporalCondition(
                start_time=10
            ),
            schedule=Schedule(
                cadence_type=CadenceType.PULSED,
                active_duration=1
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Before activation time
        effects = engine.update(5, {})
        self.assertEqual(len(effects), 0)
        
        # At activation time
        effects = engine.update(10, {})
        self.assertEqual(len(effects), 1)
        
        # After activation (pulsed = single step)
        effects = engine.update(11, {})
        self.assertEqual(len(effects), 1)  # Deactivation effect
    
    def test_recurrent_activation(self):
        """Test recurrent temporal activation."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_004",
            category="recurrent",
            type_tag="recurrent_test",
            activation_conditions=TemporalCondition(
                start_time=5,
                recurrence_pattern=RecurrencePattern(
                    interval=10,
                    count=3
                )
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=2,
                inactive_duration=5
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # First activation at t=5
        effects = engine.update(5, {})
        self.assertEqual(len(effects), 1)

        # Active for 2 steps (t=5 and t=6), expires at end of t=6
        effects = engine.update(6, {})
        self.assertEqual(len(effects), 1)  # Deactivation
        
        state_info = engine.get_state("test_004")
        self.assertEqual(state_info.current_state, InterventionState.EXPIRED)
        
        # Re-activation at t=15 (5 + 10)
        for t in range(7, 15):
            engine.update(t, {})
        
        effects = engine.update(15, {})
        self.assertEqual(len(effects), 1)  # Second activation


class TestEventConditions(unittest.TestCase):
    """Test event-based activation conditions."""
    
    def test_event_activation(self):
        """Test event-triggered activation."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_005",
            category="reactive",
            type_tag="event_test",
            activation_conditions=EventCondition(
                event_id="event_gamma"
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=3
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # No event - should not activate
        effects = engine.update(1, {}, events=[])
        self.assertEqual(len(effects), 0)
        
        # With matching event - should activate
        events = [Event(event_id="event_gamma", timestamp=2)]
        effects = engine.update(2, {}, events=events)
        self.assertEqual(len(effects), 1)
    
    def test_event_filter(self):
        """Test event activation with filtering."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_006",
            category="reactive",
            type_tag="filtered_event_test",
            activation_conditions=EventCondition(
                event_id="event_delta",
                event_filter={"severity": "high"}
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=2
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Event with wrong severity - should not activate
        events = [Event(
            event_id="event_delta",
            timestamp=1,
            attributes={"severity": "low"}
        )]
        effects = engine.update(1, {}, events=events)
        self.assertEqual(len(effects), 0)
        
        # Event with correct severity - should activate
        events = [Event(
            event_id="event_delta",
            timestamp=2,
            attributes={"severity": "high"}
        )]
        effects = engine.update(2, {}, events=events)
        self.assertEqual(len(effects), 1)


class TestCompoundConditions(unittest.TestCase):
    """Test compound activation conditions."""
    
    def test_and_condition(self):
        """Test AND compound condition."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_007",
            category="compound",
            type_tag="and_test",
            activation_conditions=CompoundCondition(
                conditions=[
                    ThresholdCondition(
                        signal_id="signal_a",
                        operator=ConditionOperator.GT,
                        threshold_value=0.5
                    ),
                    ThresholdCondition(
                        signal_id="signal_b",
                        operator=ConditionOperator.LT,
                        threshold_value=0.3
                    )
                ],
                logic_operator=LogicOperator.AND
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=5
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Only first condition met
        effects = engine.update(1, {"signal_a": 0.6, "signal_b": 0.5})
        self.assertEqual(len(effects), 0)
        
        # Both conditions met
        effects = engine.update(2, {"signal_a": 0.6, "signal_b": 0.2})
        self.assertEqual(len(effects), 1)
    
    def test_or_condition(self):
        """Test OR compound condition."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_008",
            category="compound",
            type_tag="or_test",
            activation_conditions=CompoundCondition(
                conditions=[
                    ThresholdCondition(
                        signal_id="signal_x",
                        operator=ConditionOperator.GT,
                        threshold_value=0.8
                    ),
                    ThresholdCondition(
                        signal_id="signal_y",
                        operator=ConditionOperator.GT,
                        threshold_value=0.8
                    )
                ],
                logic_operator=LogicOperator.OR
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=3
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config)
        
        # Neither condition met
        effects = engine.update(1, {"signal_x": 0.5, "signal_y": 0.5})
        self.assertEqual(len(effects), 0)
        
        # First condition met
        effects = engine.update(2, {"signal_x": 0.9, "signal_y": 0.5})
        self.assertEqual(len(effects), 1)


class TestInterventionLifecycle(unittest.TestCase):
    """Test complete intervention lifecycle."""
    
    def test_activation_and_expiration(self):
        """Test intervention activates and expires correctly."""
        engine = InterventionEngine()
        
        config = InterventionConfig(
            id="test_009",
            category="reactive",
            type_tag="lifecycle_test",
            activation_conditions=ThresholdCondition(
                signal_id="signal_z",
                operator=ConditionOperator.GT,
                threshold_value=0.5
            ),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=3
            ),
            duration=Duration()
        )
        
        intervention_id = engine.register_intervention(config)
        
        # Check initial state
        state_info = engine.get_state(intervention_id)
        self.assertEqual(state_info.current_state, InterventionState.ARMED)
        
        # Activate
        effects = engine.update(1, {"signal_z": 0.7})
        self.assertEqual(len(effects), 1)
        
        state_info = engine.get_state(intervention_id)
        self.assertEqual(state_info.current_state, InterventionState.ACTIVE)
        
        # Active for 3 steps
        engine.update(2, {"signal_z": 0.7})
        state_info = engine.get_state(intervention_id)
        self.assertEqual(state_info.current_state, InterventionState.ACTIVE)
        self.assertEqual(state_info.active_duration_elapsed, 2)
        
        # Should expire after active_duration
        effects = engine.update(4, {"signal_z": 0.7})
        state_info = engine.get_state(intervention_id)
        self.assertEqual(state_info.current_state, InterventionState.EXPIRED)
    
    def test_list_active_interventions(self):
        """Test listing active interventions."""
        engine = InterventionEngine()
        
        # Register multiple interventions
        config1 = InterventionConfig(
            id="test_010",
            category="scheduled",
            type_tag="list_test",
            activation_conditions=TemporalCondition(start_time=1),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=10
            ),
            duration=Duration()
        )
        
        config2 = InterventionConfig(
            id="test_011",
            category="scheduled",
            type_tag="list_test",
            activation_conditions=TemporalCondition(start_time=2),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=10
            ),
            duration=Duration()
        )
        
        engine.register_intervention(config1)
        engine.register_intervention(config2)
        
        # Activate first
        engine.update(1, {})
        active = engine.list_active_interventions()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0], "test_010")
        
        # Activate second
        engine.update(2, {})
        active = engine.list_active_interventions()
        self.assertEqual(len(active), 2)
        self.assertIn("test_010", active)
        self.assertIn("test_011", active)


class TestPriorityOrdering(unittest.TestCase):
    """Test priority-based effect ordering."""
    
    def test_priority_ordering(self):
        """Test that effects are emitted in priority order."""
        engine = InterventionEngine()
        
        # Low priority intervention
        config1 = InterventionConfig(
            id="low_priority",
            category="scheduled",
            type_tag="priority_test",
            activation_conditions=TemporalCondition(start_time=1),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=5
            ),
            duration=Duration(),
            priority=1
        )
        
        # High priority intervention
        config2 = InterventionConfig(
            id="high_priority",
            category="scheduled",
            type_tag="priority_test",
            activation_conditions=TemporalCondition(start_time=1),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=5
            ),
            duration=Duration(),
            priority=10
        )
        
        engine.register_intervention(config1)
        engine.register_intervention(config2)
        
        # Both activate at same time
        effects = engine.update(1, {})
        self.assertEqual(len(effects), 2)
        
        # High priority should be first
        self.assertEqual(effects[0].intervention_id, "high_priority")
        self.assertEqual(effects[1].intervention_id, "low_priority")


if __name__ == '__main__':
    unittest.main()
