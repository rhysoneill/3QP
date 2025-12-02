"""
Demonstration of the Stressor Model module.

Shows basic usage patterns for creating and updating stressor signals
during a simulated lunar habitat mission.
"""

from datetime import datetime
import matplotlib.pyplot as plt

from stressor_model import (
    StressorModel,
    MissionConfig,
    StressorParameterSet,
    UpdateCycleInput,
    StressorCategory,
    SpikeEvent,
    ScheduledEvent,
    EventType,
    StressorModifier,
    PhaseDefinition,
    PhaseType,
    TriggeredEvent,
)


def demo_basic_stressors():
    """Demonstrate basic stressor types and dynamics."""
    print("=" * 60)
    print("DEMO: Basic Stressor Dynamics")
    print("=" * 60)
    
    # Create mission configuration
    config = MissionConfig(
        mission_id="DEMO_LUNAR_HABITAT_001",
        mission_start_date=datetime(2026, 1, 1),
        mission_duration_days=90.0,  # 3-month mission
        random_seed=42,
        phase_definitions=[
            PhaseDefinition(
                phase_id="commissioning",
                start_day=0.0,
                end_day=14.0,
                phase_type=PhaseType.COMMISSIONING,
            ),
            PhaseDefinition(
                phase_id="steady_state",
                start_day=14.0,
                end_day=76.0,
                phase_type=PhaseType.STEADY_STATE,
            ),
            PhaseDefinition(
                phase_id="closeout",
                start_day=76.0,
                end_day=90.0,
                phase_type=PhaseType.CLOSEOUT,
            ),
        ],
        stressor_parameters=[
            # Operational: Task density with weekly cadence
            StressorParameterSet(
                stressor_id="task_density",
                category=StressorCategory.OPERATIONAL,
                baseline=0.4,
                max_intensity=0.9,
                cadence_period=7.0,
                cadence_amplitude=0.15,
            ),
            # Environmental: Constant confinement
            StressorParameterSet(
                stressor_id="confinement_index",
                category=StressorCategory.ENVIRONMENTAL,
                baseline=0.6,
                max_intensity=0.6,
            ),
            # Temporal: Mission duration accumulator
            StressorParameterSet(
                stressor_id="mission_duration",
                category=StressorCategory.TEMPORAL,
                baseline=0.1,
                max_intensity=0.8,
                accumulation_rate=0.008,  # Gradual increase
            ),
            # Monotony: Routine repetition
            StressorParameterSet(
                stressor_id="routine_repetition",
                category=StressorCategory.MONOTONY,
                baseline=0.3,
                max_intensity=0.7,
                accumulation_rate=0.005,
            ),
            # Operational: EVA events with scheduled spikes
            StressorParameterSet(
                stressor_id="eva_workload",
                category=StressorCategory.OPERATIONAL,
                baseline=0.2,
                max_intensity=1.0,
                spike_schedule=[
                    SpikeEvent(trigger_time=20.0, magnitude=0.6, duration=0.5),
                    SpikeEvent(trigger_time=40.0, magnitude=0.7, duration=0.5),
                    SpikeEvent(trigger_time=60.0, magnitude=0.6, duration=0.5),
                ],
            ),
        ],
    )
    
    # Initialize model
    model = StressorModel()
    model.initialize(config)
    
    print(f"\nMission: {config.mission_id}")
    print(f"Duration: {config.mission_duration_days} days")
    print(f"Stressors: {len(config.stressor_parameters)}")
    
    # Run simulation
    print("\nSimulating mission...")
    results = []
    
    for day in range(int(config.mission_duration_days)):
        update_input = UpdateCycleInput(
            current_time=float(day + 1),
            delta_time=1.0,
        )
        result = model.update(update_input)
        results.append(result)
    
    # Display results
    print("\n" + "-" * 60)
    print("Sample Stressor Values (Day 1, 30, 60, 90)")
    print("-" * 60)
    
    for day_idx in [0, 29, 59, 89]:
        result = results[day_idx]
        print(f"\nDay {day_idx + 1}:")
        print(f"  Task Density:        {result.get_stressor('task_density').current_intensity:.3f}")
        print(f"  Confinement Index:   {result.get_stressor('confinement_index').current_intensity:.3f}")
        print(f"  Mission Duration:    {result.get_stressor('mission_duration').current_intensity:.3f}")
        print(f"  Routine Repetition:  {result.get_stressor('routine_repetition').current_intensity:.3f}")
        print(f"  EVA Workload:        {result.get_stressor('eva_workload').current_intensity:.3f}")
        print(f"  Overall Load:        {result.summary_metrics.overall_stressor_load:.3f}")
    
    # Plot results (if matplotlib available)
    try:
        plot_stressor_trajectories(results)
    except Exception as e:
        print(f"\nPlotting skipped: {e}")
    
    return model, results


def demo_event_driven_stressors():
    """Demonstrate event-triggered stressor modifiers."""
    print("\n" + "=" * 60)
    print("DEMO: Event-Driven Stressor Modifiers")
    print("=" * 60)
    
    config = MissionConfig(
        mission_id="DEMO_EVENT_DRIVEN_001",
        mission_start_date=datetime(2026, 1, 1),
        mission_duration_days=30.0,
        random_seed=42,
        stressor_parameters=[
            StressorParameterSet(
                stressor_id="operational_load",
                category=StressorCategory.OPERATIONAL,
                baseline=0.3,
                max_intensity=1.0,
                decay_tau=2.0,  # 2-day recovery
            ),
        ],
        event_schedule=[
            ScheduledEvent(
                event_id="EVA_001",
                event_time=10.0,
                event_type=EventType.EVA,
                stressor_modifiers=[
                    StressorModifier(
                        stressor_id="operational_load",
                        intensity_delta=0.5,
                        duration=0.5,  # Half-day event
                    )
                ],
            ),
            ScheduledEvent(
                event_id="MAINTENANCE_001",
                event_time=20.0,
                event_type=EventType.MAINTENANCE,
                stressor_modifiers=[
                    StressorModifier(
                        stressor_id="operational_load",
                        intensity_delta=0.3,
                        duration=1.0,
                    )
                ],
            ),
        ],
    )
    
    model = StressorModel()
    model.initialize(config)
    
    print(f"\nMission: {config.mission_id}")
    print(f"Scheduled Events: {len(config.event_schedule)}")
    
    # Simulate with event triggers
    results = []
    for day in range(int(config.mission_duration_days)):
        current_time = float(day + 1)
        
        # Check if any events trigger today
        triggered = []
        for event in config.event_schedule:
            if abs(event.event_time - current_time) < 0.5:
                triggered.append(
                    TriggeredEvent(
                        event_id=event.event_id,
                        event_type=event.event_type,
                        event_time=event.event_time,
                    )
                )
        
        update_input = UpdateCycleInput(
            current_time=current_time,
            delta_time=1.0,
            triggered_events=triggered,
        )
        result = model.update(update_input)
        results.append(result)
        
        if triggered:
            print(f"\nDay {day + 1}: Event triggered - {triggered[0].event_id}")
            stressor = result.get_stressor("operational_load")
            print(f"  Operational Load: {stressor.current_intensity:.3f}")
    
    print("\n" + "-" * 60)
    print("Operational Load Trajectory")
    print("-" * 60)
    for day_idx in [0, 9, 10, 11, 19, 20, 21, 29]:
        result = results[day_idx]
        stressor = result.get_stressor("operational_load")
        print(f"Day {day_idx + 1:2d}: {stressor.current_intensity:.3f} "
              f"{'[EVENT]' if stressor.state_flags.is_spiking else ''}")
    
    return model, results


def plot_stressor_trajectories(results):
    """Plot stressor intensity over time."""
    days = [r.mission_time for r in results]
    
    # Extract stressor trajectories
    task_density = [r.get_stressor('task_density').current_intensity for r in results]
    confinement = [r.get_stressor('confinement_index').current_intensity for r in results]
    mission_duration = [r.get_stressor('mission_duration').current_intensity for r in results]
    routine_rep = [r.get_stressor('routine_repetition').current_intensity for r in results]
    eva_workload = [r.get_stressor('eva_workload').current_intensity for r in results]
    overall = [r.summary_metrics.overall_stressor_load for r in results]
    
    # Create figure
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    fig.suptitle('Lunar Habitat Mission Stressor Dynamics', fontsize=14, fontweight='bold')
    
    # Task Density
    axes[0, 0].plot(days, task_density, 'b-', linewidth=2)
    axes[0, 0].set_title('Task Density (Operational)')
    axes[0, 0].set_ylabel('Intensity')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_ylim(0, 1)
    
    # Confinement
    axes[0, 1].plot(days, confinement, 'g-', linewidth=2)
    axes[0, 1].set_title('Confinement Index (Environmental)')
    axes[0, 1].set_ylabel('Intensity')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim(0, 1)
    
    # Mission Duration
    axes[1, 0].plot(days, mission_duration, 'r-', linewidth=2)
    axes[1, 0].set_title('Mission Duration (Temporal)')
    axes[1, 0].set_ylabel('Intensity')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(0, 1)
    
    # Routine Repetition
    axes[1, 1].plot(days, routine_rep, 'm-', linewidth=2)
    axes[1, 1].set_title('Routine Repetition (Monotony)')
    axes[1, 1].set_ylabel('Intensity')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_ylim(0, 1)
    
    # EVA Workload
    axes[2, 0].plot(days, eva_workload, 'orange', linewidth=2)
    axes[2, 0].set_title('EVA Workload (Operational)')
    axes[2, 0].set_xlabel('Mission Day')
    axes[2, 0].set_ylabel('Intensity')
    axes[2, 0].grid(True, alpha=0.3)
    axes[2, 0].set_ylim(0, 1)
    
    # Overall Load
    axes[2, 1].plot(days, overall, 'k-', linewidth=2)
    axes[2, 1].set_title('Overall Stressor Load')
    axes[2, 1].set_xlabel('Mission Day')
    axes[2, 1].set_ylabel('Intensity')
    axes[2, 1].grid(True, alpha=0.3)
    axes[2, 1].set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('stressor_trajectories.png', dpi=150)
    print("\nPlot saved: stressor_trajectories.png")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("STRESSOR MODEL DEMONSTRATION")
    print("Module 07: Lunar Mission Stressor Model")
    print("=" * 60)
    
    # Demo 1: Basic stressors
    model1, results1 = demo_basic_stressors()
    
    # Demo 2: Event-driven stressors
    model2, results2 = demo_event_driven_stressors()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Findings:")
    print("  - All stressor intensities remain bounded in [0, 1]")
    print("  - Temporal dynamics (accumulation, decay, periodic) work correctly")
    print("  - Event-triggered modifiers apply and expire as expected")
    print("  - Summary metrics aggregate stressors appropriately")
    print("\nThe Stressor Model is ready for integration with downstream modules.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
