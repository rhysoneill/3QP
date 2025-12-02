"""
Unit tests for the Implementation Roadmap module.
"""

import pytest
from datetime import datetime
from roadmap import (
    RoadmapManager,
    Phase,
    PhaseStatus,
    ModuleStatus,
    IntegrationStatus,
    MaturityLevel,
    GateCondition,
    RiskInfo,
    RiskLevel,
    MilestoneInfo,
    StatusTracker,
)


class TestRoadmapManager:
    """Test suite for RoadmapManager."""
    
    def test_initialization(self):
        """Test roadmap manager initialization."""
        manager = RoadmapManager()
        
        assert manager.get_current_phase() == Phase.ARCHITECTURE
        assert manager.get_current_maturity() == MaturityLevel.NONE
        assert len(manager.project_state.modules) == 10
        assert len(manager.project_state.integration_steps) == 8
    
    def test_module_dependencies(self):
        """Test module dependency tracking."""
        manager = RoadmapManager()
        
        # Module 01 has no dependencies
        ready, blockers = manager.get_module_readiness("01")
        assert ready
        assert len(blockers) == 0
        
        # Module 03 depends on 01 and 09
        ready, blockers = manager.get_module_readiness("03")
        assert not ready
        assert len(blockers) > 0
        
        # Mark dependencies as integrated
        manager.update_module_status("01", ModuleStatus.INTEGRATED)
        manager.update_module_status("09", ModuleStatus.INTEGRATED)
        
        # Now module 03 should be ready
        ready, blockers = manager.get_module_readiness("03")
        assert ready
        assert len(blockers) == 0
    
    def test_phase_progression(self):
        """Test phase gate progression."""
        manager = RoadmapManager()
        
        # Cannot transition without satisfying exit conditions
        success, msg = manager.transition_to_phase(Phase.FOUNDATION)
        assert not success
        
        # Mark all architecture exit conditions as satisfied
        arch_gate = manager.phase_gates[Phase.ARCHITECTURE]
        for condition in arch_gate.exit_conditions:
            manager.mark_gate_condition_satisfied(
                Phase.ARCHITECTURE,
                condition.condition_id,
                "test_user",
                is_entry=False
            )
        
        # Mark foundation entry conditions as satisfied
        foundation_gate = manager.phase_gates[Phase.FOUNDATION]
        for condition in foundation_gate.entry_conditions:
            manager.mark_gate_condition_satisfied(
                Phase.FOUNDATION,
                condition.condition_id,
                "test_user",
                is_entry=True
            )
        
        # Now transition should succeed
        success, msg = manager.transition_to_phase(Phase.FOUNDATION)
        assert success
        assert manager.get_current_phase() == Phase.FOUNDATION
        assert manager.get_current_maturity() == MaturityLevel.ALPHA
    
    def test_module_status_updates(self):
        """Test module status tracking."""
        manager = RoadmapManager()
        
        # Update module status
        success = manager.update_module_status(
            "01",
            ModuleStatus.UNIT_TESTED,
            "Core module completed"
        )
        assert success
        
        module = manager.project_state.modules["01"]
        assert module.status == ModuleStatus.UNIT_TESTED
        assert module.completion_date is not None
        assert "Core module completed" in module.notes
    
    def test_integration_step_readiness(self):
        """Test integration step readiness checks."""
        manager = RoadmapManager()
        
        # Step 1 requires modules 01 and 09
        ready, blockers = manager.get_integration_step_readiness(1)
        assert not ready
        
        # Mark required modules as unit tested
        manager.update_module_status("01", ModuleStatus.UNIT_TESTED)
        manager.update_module_status("09", ModuleStatus.UNIT_TESTED)
        
        # Still not ready without test plan approval
        ready, blockers = manager.get_integration_step_readiness(1)
        assert not ready
        
        # Approve test plan
        manager.integration_steps[1].test_plan_approved = True
        
        # Now should be ready
        ready, blockers = manager.get_integration_step_readiness(1)
        assert ready
    
    def test_risk_management(self):
        """Test risk tracking."""
        manager = RoadmapManager()
        
        risk = RiskInfo(
            risk_id="RISK-001",
            description="Integration complexity",
            category="technical",
            level=RiskLevel.HIGH,
            probability=0.7,
            impact=0.8,
            mitigation_strategy="Early integration testing",
            owner="Integration Lead"
        )
        
        manager.add_risk(risk)
        assert "RISK-001" in manager.project_state.risks
        
        # Update risk
        success = manager.update_risk("RISK-001", status="mitigated", level=RiskLevel.LOW)
        assert success
        assert manager.project_state.risks["RISK-001"].level == RiskLevel.LOW
    
    def test_milestone_tracking(self):
        """Test milestone management."""
        manager = RoadmapManager()
        
        milestone = MilestoneInfo(
            milestone_id="M1",
            name="Architecture Complete",
            description="All architectural modules finalized",
            phase=Phase.ARCHITECTURE,
            planned_date=datetime.now()
        )
        
        manager.add_milestone(milestone)
        assert "M1" in manager.project_state.milestones
        assert not milestone.achieved
        
        # Achieve milestone
        success = manager.achieve_milestone("M1")
        assert success
        assert manager.project_state.milestones["M1"].achieved
        assert manager.project_state.milestones["M1"].actual_date is not None


class TestStatusTracker:
    """Test suite for StatusTracker."""
    
    def test_metrics_calculation(self):
        """Test project metrics calculation."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        metrics = tracker.calculate_metrics()
        
        assert metrics.completion_percentage == 0.0
        assert metrics.modules_total == 10
        assert metrics.modules_completed == 0
        assert metrics.current_phase == Phase.ARCHITECTURE
        assert metrics.current_maturity == MaturityLevel.NONE
    
    def test_metrics_with_progress(self):
        """Test metrics with some progress."""
        manager = RoadmapManager()
        
        # Make some progress
        manager.update_module_status("01", ModuleStatus.INTEGRATED)
        manager.update_module_status("09", ModuleStatus.INTEGRATED)
        
        tracker = StatusTracker(manager.project_state)
        metrics = tracker.calculate_metrics()
        
        assert metrics.modules_completed == 2
        assert metrics.completion_percentage == 20.0
    
    def test_status_report_generation(self):
        """Test status report generation."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        report = tracker.generate_status_report()
        
        assert "3QP IMPLEMENTATION ROADMAP" in report
        assert "OVERALL STATUS" in report
        assert "MODULE STATUS" in report
        assert "INTEGRATION STATUS" in report
        assert "RISK STATUS" in report
    
    def test_critical_path_identification(self):
        """Test critical path module identification."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        critical = tracker.get_critical_path_modules()
        
        # Should include foundation, architecture, and key model modules
        assert "01" in critical  # TQP Core
        assert "09" in critical  # Logging
        assert "03" in critical  # Architecture
        assert "10" in critical  # Validation
    
    def test_blocking_issues(self):
        """Test blocking issue identification."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        # Add a high-priority risk
        risk = RiskInfo(
            risk_id="BLOCK-001",
            description="Resource unavailable",
            category="resource",
            level=RiskLevel.CRITICAL,
            probability=0.9,
            impact=0.9,
            mitigation_strategy="Acquire backup resource"
        )
        manager.add_risk(risk)
        
        issues = tracker.get_blocking_issues()
        assert len(issues) > 0
        assert any("BLOCK-001" in issue for issue in issues)
    
    def test_project_state_validation(self):
        """Test project state validation."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        results = tracker.validate_project_state()
        
        # Should pass validation with initial state
        assert len(results) > 0
        assert any(r.passed for r in results)
    
    def test_metrics_export(self):
        """Test metrics export to JSON."""
        manager = RoadmapManager()
        tracker = StatusTracker(manager.project_state)
        
        exported = tracker.export_metrics_json()
        
        assert "completion_percentage" in exported
        assert "modules" in exported
        assert "phases" in exported
        assert "integration" in exported
        assert "risks" in exported
        assert exported["maturity"] == "none"


class TestIntegrationStep:
    """Test suite for IntegrationStep."""
    
    def test_integration_step_lifecycle(self):
        """Test complete integration step lifecycle."""
        manager = RoadmapManager()
        
        # Get first integration step
        step = manager.integration_steps[1]
        
        # Initially in planning
        assert step.status == IntegrationStatus.PLANNING
        
        # Set up modules
        manager.update_module_status("01", ModuleStatus.UNIT_TESTED)
        manager.update_module_status("09", ModuleStatus.UNIT_TESTED)
        step.test_plan_approved = True
        
        # Check readiness
        ready, blockers = step.check_readiness(manager.project_state.modules)
        assert ready
        
        # Update status to ready
        step.status = IntegrationStatus.READY
        
        # Start integration
        success = step.start_integration()
        assert success
        assert step.status == IntegrationStatus.IN_PROGRESS
        assert step.start_date is not None
        
        # Update test results
        step.update_test_results(10, 10)
        
        # Complete integration
        success = step.complete_integration()
        assert success
        assert step.status == IntegrationStatus.COMPLETE
        assert step.completion_date is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
