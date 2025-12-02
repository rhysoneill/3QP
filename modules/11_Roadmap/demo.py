"""
Demonstration of the Implementation Roadmap module capabilities.

This script demonstrates:
- Initializing the roadmap manager
- Tracking module implementation progress
- Managing phase transitions
- Monitoring integration steps
- Generating status reports
- Managing risks and milestones
"""

from datetime import datetime, timedelta
from roadmap import (
    RoadmapManager,
    StatusTracker,
    Phase,
    PhaseStatus,
    ModuleStatus,
    IntegrationStatus,
    MaturityLevel,
    GateCondition,
    ProjectState,
)
from roadmap.types import (
    RiskInfo,
    RiskLevel,
    MilestoneInfo,
)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_initialization():
    """Demonstrate roadmap initialization."""
    print_section("ROADMAP INITIALIZATION")
    
    manager = RoadmapManager()
    
    print(f"Current Phase: {manager.get_current_phase().value}")
    print(f"Current Maturity: {manager.get_current_maturity().value}")
    print(f"Total Modules: {len(manager.project_state.modules)}")
    print(f"Integration Steps: {len(manager.project_state.integration_steps)}")
    
    return manager


def demo_module_tracking(manager):
    """Demonstrate module status tracking."""
    print_section("MODULE STATUS TRACKING")
    
    # Show initial module states
    print("\nInitial Module States:")
    for module_id in ["01", "09", "03"]:
        module = manager.project_state.modules[module_id]
        print(f"  Module {module_id} ({module.module_name}): {module.status.value}")
    
    # Check module readiness
    print("\nModule 01 Readiness Check:")
    ready, blockers = manager.get_module_readiness("01")
    print(f"  Ready: {ready}")
    if blockers:
        print(f"  Blockers: {blockers}")
    
    # Update module status
    print("\nUpdating Module 01 to UNIT_TESTED...")
    manager.update_module_status(
        "01",
        ModuleStatus.UNIT_TESTED,
        "Core agent abstraction implemented and tested"
    )
    
    module = manager.project_state.modules["01"]
    print(f"  Status: {module.status.value}")
    print(f"  Completion Date: {module.completion_date}")
    print(f"  Notes: {module.notes}")


def demo_phase_gates(manager):
    """Demonstrate phase gate management."""
    print_section("PHASE GATE MANAGEMENT")
    
    current_phase = manager.get_current_phase()
    print(f"\nCurrent Phase: {current_phase.value}")
    
    # Check exit readiness
    print("\nChecking Phase Exit Conditions:")
    can_exit, failures = manager.check_phase_exit_ready(current_phase)
    print(f"  Can Exit: {can_exit}")
    if failures:
        print(f"  Unsatisfied Conditions:")
        for failure in failures[:3]:  # Show first 3
            print(f"    - {failure}")
    
    # Mark some conditions as satisfied
    print("\nMarking Conditions as Satisfied:")
    arch_gate = manager.phase_gates[Phase.ARCHITECTURE]
    for condition in arch_gate.exit_conditions[:2]:
        success = manager.mark_gate_condition_satisfied(
            Phase.ARCHITECTURE,
            condition.condition_id,
            "Demo User"
        )
        if success:
            print(f"  ✓ {condition.condition_id}")
    
    # Show updated status
    can_exit, failures = manager.check_phase_exit_ready(current_phase)
    print(f"\nUpdated Exit Status:")
    print(f"  Remaining Unsatisfied: {len(failures)}")


def demo_integration_management(manager):
    """Demonstrate integration step management."""
    print_section("INTEGRATION STEP MANAGEMENT")
    
    # Prepare modules for integration
    print("\nPreparing Modules for Integration Step 1:")
    manager.update_module_status("01", ModuleStatus.UNIT_TESTED)
    manager.update_module_status("09", ModuleStatus.UNIT_TESTED)
    print("  ✓ Module 01 unit tested")
    print("  ✓ Module 09 unit tested")
    
    # Check integration readiness
    print("\nChecking Integration Step 1 Readiness:")
    ready, blockers = manager.get_integration_step_readiness(1)
    print(f"  Ready: {ready}")
    if blockers:
        print(f"  Blockers:")
        for blocker in blockers:
            print(f"    - {blocker}")
    
    # Approve test plan
    step = manager.integration_steps[1]
    step.test_plan_approved = True
    print("\n  ✓ Test plan approved")
    
    # Recheck readiness
    ready, blockers = manager.get_integration_step_readiness(1)
    print(f"\nUpdated Readiness: {ready}")
    
    # Start integration
    if ready:
        step.status = IntegrationStatus.READY
        step.start_integration()
        print(f"\n  Integration Step 1 started")
        print(f"  Status: {step.status.value}")
        print(f"  Start Date: {step.start_date}")
        
        # Simulate test execution
        step.update_test_results(passing=8, total=10)
        print(f"\n  Test Results: {step.tests_passing}/{step.tests_total} passing")
        
        # Complete remaining tests
        step.update_test_results(passing=10, total=10)
        step.complete_integration()
        print(f"  Integration completed: {step.completion_date}")


def demo_risk_management(manager):
    """Demonstrate risk tracking."""
    print_section("RISK MANAGEMENT")
    
    # Add risks
    risks = [
        RiskInfo(
            risk_id="RISK-001",
            description="Foundation modules may take longer than estimated",
            category="schedule",
            level=RiskLevel.MODERATE,
            probability=0.6,
            impact=0.7,
            mitigation_strategy="Buffer time allocated; daily progress tracking",
            owner="Project Manager"
        ),
        RiskInfo(
            risk_id="RISK-002",
            description="Integration complexity with physiological models",
            category="technical",
            level=RiskLevel.HIGH,
            probability=0.7,
            impact=0.8,
            mitigation_strategy="Early prototyping; expert consultation",
            owner="Integration Lead"
        ),
        RiskInfo(
            risk_id="RISK-003",
            description="Key developer may become unavailable",
            category="resource",
            level=RiskLevel.CRITICAL,
            probability=0.3,
            impact=0.95,
            mitigation_strategy="Cross-training; documentation",
            owner="HR Lead"
        ),
    ]
    
    print("\nAdding Project Risks:")
    for risk in risks:
        manager.add_risk(risk)
        print(f"  {risk.risk_id}: {risk.description}")
        print(f"    Level: {risk.level.value}, Owner: {risk.owner}")
    
    # Show high-priority risks
    print("\nHigh-Priority Risks:")
    high_risks = manager.project_state.get_high_priority_risks()
    for risk in high_risks:
        print(f"  ⚠ {risk.risk_id}: {risk.description}")
        print(f"    Probability: {risk.probability:.1%}, Impact: {risk.impact:.1%}")
        print(f"    Mitigation: {risk.mitigation_strategy}")
    
    # Update risk status
    print("\nMitigating RISK-001:")
    manager.update_risk(
        "RISK-001",
        status="mitigated",
        level=RiskLevel.LOW,
        notes="Buffer proved adequate; on schedule"
    )
    print("  ✓ Risk reduced to LOW")


def demo_milestone_tracking(manager):
    """Demonstrate milestone management."""
    print_section("MILESTONE TRACKING")
    
    # Add milestones
    milestones = [
        MilestoneInfo(
            milestone_id="M1",
            name="Architecture Baseline",
            description="Complete architectural specification approved",
            phase=Phase.ARCHITECTURE,
            planned_date=datetime.now() - timedelta(days=30),
            deliverables=[
                "All 50 architectural documents",
                "Interface verification report",
                "ARB approval"
            ]
        ),
        MilestoneInfo(
            milestone_id="M2",
            name="Foundation Alpha",
            description="Foundation modules operational",
            phase=Phase.FOUNDATION,
            planned_date=datetime.now() + timedelta(days=60),
            deliverables=[
                "Modules 01, 09, 03 implemented",
                "Foundation integration complete",
                "Alpha baseline tagged"
            ]
        ),
    ]
    
    print("\nProject Milestones:")
    for milestone in milestones:
        manager.add_milestone(milestone)
        status = "✓ Achieved" if milestone.achieved else "○ Pending"
        print(f"  {status} {milestone.milestone_id}: {milestone.name}")
        print(f"    Phase: {milestone.phase.value}")
        print(f"    Planned: {milestone.planned_date.strftime('%Y-%m-%d')}")
    
    # Achieve first milestone
    print("\nAchieving Milestone M1:")
    manager.achieve_milestone("M1")
    m1 = manager.project_state.milestones["M1"]
    print(f"  ✓ Achieved on {m1.actual_date.strftime('%Y-%m-%d')}")


def demo_status_reporting(manager):
    """Demonstrate status tracking and reporting."""
    print_section("STATUS REPORTING")
    
    # Set project start date
    manager.project_state.project_start_date = datetime.now() - timedelta(days=45)
    
    # Make some progress
    manager.update_module_status("01", ModuleStatus.INTEGRATED)
    manager.update_module_status("09", ModuleStatus.INTEGRATED)
    manager.update_module_status("03", ModuleStatus.IN_DEVELOPMENT)
    
    # Generate tracker
    tracker = StatusTracker(manager.project_state)
    
    # Calculate metrics
    print("\nProject Metrics:")
    metrics = tracker.calculate_metrics()
    print(f"  Overall Completion: {metrics.completion_percentage:.1f}%")
    print(f"  Modules Completed: {metrics.modules_completed}/{metrics.modules_total}")
    print(f"  Current Phase: {metrics.current_phase.value}")
    print(f"  Phase Progress: {metrics.current_phase_completion:.1f}%")
    print(f"  Days Elapsed: {metrics.days_elapsed}")
    print(f"  Active Risks: {metrics.active_risks_count}")
    print(f"  Maturity Level: {metrics.current_maturity.value}")
    
    # Show critical path
    print("\nCritical Path Modules:")
    critical = tracker.get_critical_path_modules()
    for module_id in critical[:5]:  # Show first 5
        module = manager.project_state.modules[module_id]
        print(f"  {module_id} ({module.module_name}): {module.status.value}")
    
    # Generate full report
    print("\n" + "=" * 70)
    print("FULL STATUS REPORT")
    print("=" * 70)
    report = tracker.generate_status_report()
    print(report)


def demo_validation(manager):
    """Demonstrate project state validation."""
    print_section("PROJECT STATE VALIDATION")
    
    tracker = StatusTracker(manager.project_state)
    results = tracker.validate_project_state()
    
    print(f"\nValidation Results: {len(results)} checks performed")
    for result in results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status}: {result.check_name}")
        print(f"    {result.message}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" 3QP IMPLEMENTATION ROADMAP - DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstration shows the capabilities of the Implementation")
    print("Roadmap module for managing the 3QP development lifecycle.")
    
    # Initialize
    manager = demo_initialization()
    
    # Module tracking
    demo_module_tracking(manager)
    
    # Phase gates
    demo_phase_gates(manager)
    
    # Integration
    demo_integration_management(manager)
    
    # Risk management
    demo_risk_management(manager)
    
    # Milestones
    demo_milestone_tracking(manager)
    
    # Status reporting
    demo_status_reporting(manager)
    
    # Validation
    demo_validation(manager)
    
    print("\n" + "=" * 70)
    print(" DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nThe Roadmap module provides comprehensive project management")
    print("capabilities for systematic implementation of the 3QP Behavioral Twin.")
    print("\nFor more information, see README.md and the architectural")
    print("specifications in versions/")
    print()


if __name__ == "__main__":
    main()
