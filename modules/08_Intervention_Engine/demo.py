"""
Demonstration of the Intervention Engine module.

Shows basic usage patterns for different intervention types.
"""

from intervention_engine import (
    InterventionEngine,
    InterventionConfig,
    ThresholdCondition,
    TemporalCondition,
    EventCondition,
    CompoundCondition,
    Schedule,
    Duration,
    RecurrencePattern,
    ConditionOperator,
    CadenceType,
    LogicOperator,
    Event
)


def demo_threshold_intervention():
    """Demonstrate threshold-based intervention."""
    print("\n=== Threshold Intervention Demo ===")
    
    engine = InterventionEngine()
    
    # Create a threshold-based intervention
    config = InterventionConfig(
        id="threshold_demo",
        category="reactive",
        type_tag="threshold_example",
        activation_conditions=ThresholdCondition(
            signal_id="signal_alpha",
            operator=ConditionOperator.GT,
            threshold_value=0.7,
            duration_required=2
        ),
        schedule=Schedule(
            cadence_type=CadenceType.CONTINUOUS,
            active_duration=5
        ),
        duration=Duration()
    )
    
    engine.register_intervention(config)
    print(f"Registered intervention: {config.id}")
    
    # Simulate time-steps
    signals_sequence = [
        {"signal_alpha": 0.5},  # t=1: Below threshold
        {"signal_alpha": 0.8},  # t=2: Above threshold (1st step)
        {"signal_alpha": 0.8},  # t=3: Above threshold (2nd step) -> ACTIVATES
        {"signal_alpha": 0.6},  # t=4: Active
        {"signal_alpha": 0.6},  # t=5: Active
        {"signal_alpha": 0.6},  # t=6: Active
        {"signal_alpha": 0.6},  # t=7: Active
        {"signal_alpha": 0.6},  # t=8: Expires
    ]
    
    for t, signals in enumerate(signals_sequence, start=1):
        effects = engine.update(t, signals)
        state = engine.get_state("threshold_demo")
        
        print(f"t={t}: signal_alpha={signals['signal_alpha']:.1f}, "
              f"state={state.current_state.value}, effects={len(effects)}")
        
        for effect in effects:
            print(f"  -> {effect.effect_type.value}: {effect.signal_values}")


def demo_temporal_intervention():
    """Demonstrate time-based intervention."""
    print("\n=== Temporal Intervention Demo ===")
    
    engine = InterventionEngine()
    
    # Create a recurrent temporal intervention
    config = InterventionConfig(
        id="temporal_demo",
        category="recurrent",
        type_tag="scheduled_example",
        activation_conditions=TemporalCondition(
            start_time=5,
            recurrence_pattern=RecurrencePattern(
                interval=10,
                count=3
            )
        ),
        schedule=Schedule(
            cadence_type=CadenceType.PULSED,
            active_duration=1,
            inactive_duration=5
        ),
        duration=Duration()
    )
    
    engine.register_intervention(config)
    print(f"Registered intervention: {config.id}")
    print("Activates at t=5, 15, 25 (pulsed)")
    
    # Simulate time-steps
    for t in range(1, 30):
        effects = engine.update(t, {})
        
        if effects:
            state = engine.get_state("temporal_demo")
            print(f"t={t}: state={state.current_state.value}, effects={len(effects)}")
            for effect in effects:
                print(f"  -> {effect.effect_type.value}")


def demo_event_intervention():
    """Demonstrate event-based intervention."""
    print("\n=== Event Intervention Demo ===")
    
    engine = InterventionEngine()
    
    # Create an event-triggered intervention
    config = InterventionConfig(
        id="event_demo",
        category="reactive",
        type_tag="event_example",
        activation_conditions=EventCondition(
            event_id="critical_event",
            event_filter={"severity": "high"},
            cooldown_period=5
        ),
        schedule=Schedule(
            cadence_type=CadenceType.CONTINUOUS,
            active_duration=3
        ),
        duration=Duration()
    )
    
    engine.register_intervention(config)
    print(f"Registered intervention: {config.id}")
    
    # Simulate time-steps with events
    event_times = [3, 6, 12]  # Events at these time-steps
    
    for t in range(1, 15):
        # Generate events
        events = []
        if t in event_times:
            events.append(Event(
                event_id="critical_event",
                timestamp=t,
                attributes={"severity": "high"}
            ))
        
        effects = engine.update(t, {}, events=events)
        state = engine.get_state("event_demo")
        
        if effects or events:
            print(f"t={t}: events={len(events)}, state={state.current_state.value}, "
                  f"effects={len(effects)}")
            for effect in effects:
                print(f"  -> {effect.effect_type.value}")


def demo_compound_intervention():
    """Demonstrate compound condition intervention."""
    print("\n=== Compound Intervention Demo ===")
    
    engine = InterventionEngine()
    
    # Create a compound AND intervention
    config = InterventionConfig(
        id="compound_demo",
        category="compound",
        type_tag="compound_example",
        activation_conditions=CompoundCondition(
            conditions=[
                ThresholdCondition(
                    signal_id="stress_level",
                    operator=ConditionOperator.GT,
                    threshold_value=0.8
                ),
                ThresholdCondition(
                    signal_id="workload",
                    operator=ConditionOperator.GT,
                    threshold_value=0.7
                )
            ],
            logic_operator=LogicOperator.AND
        ),
        schedule=Schedule(
            cadence_type=CadenceType.CONTINUOUS,
            active_duration=4
        ),
        duration=Duration(),
        priority=10
    )
    
    engine.register_intervention(config)
    print(f"Registered intervention: {config.id}")
    print("Activates when BOTH stress_level > 0.8 AND workload > 0.7")
    
    # Simulate time-steps
    signals_sequence = [
        {"stress_level": 0.6, "workload": 0.5},  # t=1: Neither met
        {"stress_level": 0.9, "workload": 0.5},  # t=2: Only stress met
        {"stress_level": 0.9, "workload": 0.8},  # t=3: Both met -> ACTIVATES
        {"stress_level": 0.9, "workload": 0.8},  # t=4: Active
        {"stress_level": 0.9, "workload": 0.8},  # t=5: Active
        {"stress_level": 0.9, "workload": 0.8},  # t=6: Active
        {"stress_level": 0.5, "workload": 0.5},  # t=7: Expires
    ]
    
    for t, signals in enumerate(signals_sequence, start=1):
        effects = engine.update(t, signals)
        state = engine.get_state("compound_demo")
        
        print(f"t={t}: stress={signals['stress_level']:.1f}, "
              f"workload={signals['workload']:.1f}, "
              f"state={state.current_state.value}, effects={len(effects)}")
        
        for effect in effects:
            print(f"  -> {effect.effect_type.value}")


def demo_statistics():
    """Demonstrate engine statistics and queries."""
    print("\n=== Engine Statistics Demo ===")
    
    engine = InterventionEngine()
    
    # Register multiple interventions
    for i in range(5):
        config = InterventionConfig(
            id=f"intervention_{i}",
            category="scheduled" if i % 2 == 0 else "reactive",
            type_tag="stats_demo",
            activation_conditions=TemporalCondition(start_time=i * 2 + 1),
            schedule=Schedule(
                cadence_type=CadenceType.CONTINUOUS,
                active_duration=3
            ),
            duration=Duration()
        )
        engine.register_intervention(config)
    
    # Run simulation
    for t in range(1, 15):
        engine.update(t, {})
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"Total interventions: {stats['total_interventions']}")
    print(f"Current time-step: {stats['current_time_step']}")
    print(f"Active interventions: {stats['active_count']}")
    print("\nState distribution:")
    for state, count in stats['state_distribution'].items():
        if count > 0:
            print(f"  {state}: {count}")
    
    # List active interventions
    active = engine.list_active_interventions()
    print(f"\nActive intervention IDs: {active}")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("Intervention Engine Demonstration")
    print("=" * 60)
    
    demo_threshold_intervention()
    demo_temporal_intervention()
    demo_event_intervention()
    demo_compound_intervention()
    demo_statistics()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
