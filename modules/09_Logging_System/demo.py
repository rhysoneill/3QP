"""
Demonstration of the 3QP Logging System.

Shows how modules register with the logging system and submit
various types of logs during a simulated execution.
"""

from pathlib import Path
from datetime import datetime
from logging_system import LoggingSystem, LoggingConfig


def demo_logging_system():
    """Demonstrate logging system functionality."""
    
    print("=" * 70)
    print("3QP Logging System Demonstration")
    print("=" * 70)
    
    # Create configuration
    config = LoggingConfig(
        output_directory=Path("./demo_logs"),
        batch_size=10,  # Small batch size for demo
        enable_compression=False,  # Disable for easier inspection
        streaming_mode=True,  # Write immediately for demo
        enable_validation=True
    )
    
    print(f"\nConfiguration:")
    print(f"  Output directory: {config.output_directory}")
    print(f"  Batch size: {config.batch_size} time-steps")
    print(f"  Compression: {'enabled' if config.enable_compression else 'disabled'}")
    print(f"  Streaming mode: {'enabled' if config.streaming_mode else 'disabled'}")
    
    # Initialize logging system
    logging_system = LoggingSystem(config)
    logging_system.initialize(simulation_id="demo_run_001")
    
    print("\n" + "-" * 70)
    print("Module Registration")
    print("-" * 70)
    
    # Register modules
    physiology_logger = logging_system.register_module(
        module_id="physiology",
        module_version="1.0.0",
        log_types=["STATE", "EVENT", "METRIC"],
        event_categories=["arousal_spike", "fatigue_threshold"],
        metric_names=["avg_cortisol", "sleep_quality"]
    )
    print("  ✓ Registered module: physiology")
    
    social_logger = logging_system.register_module(
        module_id="social_network",
        module_version="1.0.0",
        log_types=["STATE", "EVENT"],
        event_categories=["relationship_formed", "conflict_detected"]
    )
    print("  ✓ Registered module: social_network")
    
    bdi_logger = logging_system.register_module(
        module_id="bdi_cycle",
        module_version="1.0.0",
        log_types=["STATE", "EVENT"],
        event_categories=["goal_adopted", "plan_executed"]
    )
    print("  ✓ Registered module: bdi_cycle")
    
    # Simulate a few time-steps
    print("\n" + "-" * 70)
    print("Simulation Execution")
    print("-" * 70)
    
    for timestep in range(15):
        cycle_start = datetime.utcnow()
        
        print(f"\nTime-step {timestep}:")
        
        # Physiology module logs state
        physiology_logger.log_state(
            timestamp=timestep,
            state_dict={
                "cortisol_level": 0.5 + (timestep * 0.02),
                "heart_rate": 70 + timestep,
                "fatigue": 0.3 + (timestep * 0.01)
            }
        )
        print(f"  • Physiology state logged")
        
        # Physiology might log events
        if timestep == 5:
            physiology_logger.log_event(
                timestamp=timestep,
                event_category="arousal_spike",
                event_data={
                    "magnitude": 0.8,
                    "trigger": "external_stressor"
                },
                event_id=f"evt_phys_{timestep}"
            )
            print(f"  • Physiology event logged: arousal_spike")
        
        # Social network logs state
        social_logger.log_state(
            timestamp=timestep,
            state_dict={
                "relationship_count": 5,
                "avg_tie_strength": 0.6,
                "conflict_count": timestep % 3
            }
        )
        print(f"  • Social network state logged")
        
        # Social might log events
        if timestep == 7:
            social_logger.log_event(
                timestamp=timestep,
                event_category="relationship_formed",
                event_data={
                    "agent_a": "agent_1",
                    "agent_b": "agent_2",
                    "initial_strength": 0.4
                },
                event_id=f"evt_social_{timestep}"
            )
            print(f"  • Social network event logged: relationship_formed")
        
        # BDI logs state
        bdi_logger.log_state(
            timestamp=timestep,
            state_dict={
                "active_goals": ["maintain_health", "complete_task"],
                "current_plan": "work_routine",
                "intention_strength": 0.7
            }
        )
        print(f"  • BDI cycle state logged")
        
        # BDI might log events
        if timestep == 10:
            bdi_logger.log_event(
                timestamp=timestep,
                event_category="goal_adopted",
                event_data={
                    "goal_id": "resolve_conflict",
                    "priority": 0.9,
                    "trigger": "social_event"
                },
                event_id=f"evt_bdi_{timestep}",
                caused_by_events=[f"evt_social_7"]
            )
            print(f"  • BDI cycle event logged: goal_adopted")
        
        # Physiology logs metrics every 5 steps
        if timestep > 0 and timestep % 5 == 0:
            physiology_logger.log_metric(
                timestamp_start=timestep - 5,
                timestamp_end=timestep - 1,
                metric_name="avg_cortisol",
                metric_value=0.55,
                metric_unit="normalized",
                aggregation_method="MEAN",
                sample_count=5
            )
            print(f"  • Physiology metric logged: avg_cortisol")
        
        # TQP Core logs cycle completion
        cycle_end = datetime.utcnow()
        logging_system.log_cycle(
            timestamp=timestep,
            cycle_start_time=cycle_start,
            cycle_end_time=cycle_end,
            modules_executed=["physiology", "social_network", "bdi_cycle"],
            cycle_status="COMPLETE"
        )
        print(f"  • Cycle log recorded")
    
    # Finalize
    print("\n" + "-" * 70)
    print("Finalizing Logging System")
    print("-" * 70)
    
    logging_system.finalize()
    print("  ✓ All batch files closed")
    print("  ✓ Manifest updated")
    
    # Show statistics
    print("\n" + "-" * 70)
    print("Logging Statistics")
    print("-" * 70)
    
    stats = logging_system.get_statistics()
    print(f"  Total batches: {stats['total_batches']}")
    print(f"  Total records: {stats['total_records']}")
    print(f"  Total size: {stats['total_size_bytes']} bytes")
    print(f"  Modules: {', '.join(stats['modules'])}")
    print(f"  Log types: {', '.join(stats['log_types'])}")
    print(f"  Time-step range: {stats['timestamp_range']}")
    print(f"  Errors: {stats['error_count']}")
    
    # Show file structure
    print("\n" + "-" * 70)
    print("Generated Files")
    print("-" * 70)
    
    output_dir = config.output_directory
    if output_dir.exists():
        print(f"\n{output_dir}/")
        for log_type_dir in sorted(output_dir.iterdir()):
            if log_type_dir.is_dir():
                print(f"  {log_type_dir.name}/")
                for log_file in sorted(log_type_dir.iterdir()):
                    size = log_file.stat().st_size
                    print(f"    {log_file.name} ({size} bytes)")
        
        manifest_file = output_dir / "manifest.json"
        if manifest_file.exists():
            size = manifest_file.stat().st_size
            print(f"  manifest.json ({size} bytes)")
    
    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)
    print(f"\nInspect logs in: {config.output_directory}")
    print("Each .jsonl file contains newline-delimited JSON records.")
    print("The manifest.json file catalogs all batch files.")


if __name__ == "__main__":
    demo_logging_system()
