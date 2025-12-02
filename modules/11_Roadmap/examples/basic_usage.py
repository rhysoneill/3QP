"""
Example: Basic Roadmap Usage

This example demonstrates basic usage of the Implementation Roadmap module
for tracking project progress.
"""

from roadmap import RoadmapManager, StatusTracker, ModuleStatus, Phase


def main():
    """Basic roadmap usage example."""
    
    # Initialize the roadmap manager
    print("Initializing Roadmap Manager...")
    manager = RoadmapManager()
    
    print(f"Current Phase: {manager.get_current_phase().value}")
    print(f"Current Maturity: {manager.get_current_maturity().value}")
    print()
    
    # Update some module statuses
    print("Updating module statuses...")
    manager.update_module_status("01", ModuleStatus.UNIT_TESTED, "Core completed")
    manager.update_module_status("09", ModuleStatus.UNIT_TESTED, "Logging completed")
    print("✓ Modules 01 and 09 marked as unit tested")
    print()
    
    # Check module readiness
    print("Checking Module 03 (Architecture) readiness:")
    ready, blockers = manager.get_module_readiness("03")
    print(f"  Ready: {ready}")
    if blockers:
        print(f"  Blockers: {blockers}")
    print()
    
    # Mark dependencies as integrated
    manager.update_module_status("01", ModuleStatus.INTEGRATED)
    manager.update_module_status("09", ModuleStatus.INTEGRATED)
    
    # Check again
    ready, blockers = manager.get_module_readiness("03")
    print("After marking dependencies as integrated:")
    print(f"  Ready: {ready}")
    print()
    
    # Get project state and generate report
    print("Generating status report...")
    tracker = StatusTracker(manager.get_project_state())
    metrics = tracker.calculate_metrics()
    
    print(f"\nProject Metrics:")
    print(f"  Completion: {metrics.completion_percentage:.1f}%")
    print(f"  Modules Completed: {metrics.modules_completed}/{metrics.modules_total}")
    print(f"  Current Phase: {metrics.current_phase.value}")
    
    print("\n" + "="*60)
    print("See demo.py for more comprehensive examples")
    print("="*60)


if __name__ == "__main__":
    main()
