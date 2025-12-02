"""
Status Tracker: Project metrics and reporting.

This module provides project status tracking, metrics calculation,
and reporting capabilities for monitoring implementation progress.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from .types import (
    Phase,
    PhaseStatus,
    ModuleStatus,
    IntegrationStatus,
    MaturityLevel,
    ProjectState,
    RiskLevel,
    ValidationResult,
)


@dataclass
class ProjectMetrics:
    """Project health and progress metrics."""
    
    # Overall progress
    completion_percentage: float
    modules_completed: int
    modules_total: int
    
    # Phase metrics
    current_phase: Phase
    current_phase_completion: float
    phases_completed: int
    phases_total: int
    
    # Schedule metrics
    project_start_date: Optional[datetime]
    days_elapsed: Optional[int]
    current_phase_duration_days: Optional[int]
    
    # Quality metrics
    modules_architecture_compliant: int
    average_test_coverage: float
    
    # Integration metrics
    integration_steps_complete: int
    integration_steps_total: int
    integration_tests_passing: int
    integration_tests_total: int
    
    # Risk metrics
    active_risks_count: int
    high_priority_risks_count: int
    
    # Maturity
    current_maturity: MaturityLevel
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.now)


class StatusTracker:
    """
    Tracks and reports on project status and health metrics.
    """
    
    def __init__(self, project_state: ProjectState):
        self.project_state = project_state
    
    def calculate_metrics(self) -> ProjectMetrics:
        """Calculate comprehensive project metrics."""
        
        # Overall progress
        completion_pct = self.project_state.get_completion_percentage()
        modules_completed = sum(
            1 for m in self.project_state.modules.values()
            if m.status in [ModuleStatus.INTEGRATED, ModuleStatus.VALIDATED]
        )
        modules_total = len(self.project_state.modules)
        
        # Phase metrics
        current_phase = self.project_state.current_phase
        current_phase_completion = self.project_state.get_phase_completion_percentage(current_phase)
        phases_completed = sum(
            1 for p in self.project_state.phases.values()
            if p.status == PhaseStatus.COMPLETE
        )
        phases_total = len(Phase)
        
        # Schedule metrics
        days_elapsed = None
        current_phase_duration = None
        if self.project_state.project_start_date:
            days_elapsed = (datetime.now() - self.project_state.project_start_date).days
        
        current_phase_info = self.project_state.phases.get(current_phase)
        if current_phase_info and current_phase_info.start_date:
            current_phase_duration = (datetime.now() - current_phase_info.start_date).days
        
        # Quality metrics
        compliant_modules = sum(
            1 for m in self.project_state.modules.values()
            if m.architecture_compliant
        )
        
        total_coverage = sum(
            m.test_coverage for m in self.project_state.modules.values()
        )
        avg_coverage = total_coverage / modules_total if modules_total > 0 else 0.0
        
        # Integration metrics
        integration_complete = sum(
            1 for s in self.project_state.integration_steps.values()
            if s.status == IntegrationStatus.COMPLETE
        )
        integration_total = len(self.project_state.integration_steps)
        
        total_passing = sum(
            s.tests_passing for s in self.project_state.integration_steps.values()
        )
        total_tests = sum(
            s.tests_total for s in self.project_state.integration_steps.values()
        )
        
        # Risk metrics
        active_risks = len(self.project_state.get_active_risks())
        high_risks = len(self.project_state.get_high_priority_risks())
        
        return ProjectMetrics(
            completion_percentage=completion_pct,
            modules_completed=modules_completed,
            modules_total=modules_total,
            current_phase=current_phase,
            current_phase_completion=current_phase_completion,
            phases_completed=phases_completed,
            phases_total=phases_total,
            project_start_date=self.project_state.project_start_date,
            days_elapsed=days_elapsed,
            current_phase_duration_days=current_phase_duration,
            modules_architecture_compliant=compliant_modules,
            average_test_coverage=avg_coverage,
            integration_steps_complete=integration_complete,
            integration_steps_total=integration_total,
            integration_tests_passing=total_passing,
            integration_tests_total=total_tests,
            active_risks_count=active_risks,
            high_priority_risks_count=high_risks,
            current_maturity=self.project_state.current_maturity
        )
    
    def generate_status_report(self) -> str:
        """Generate a human-readable status report."""
        metrics = self.calculate_metrics()
        
        report = []
        report.append("=" * 70)
        report.append("3QP IMPLEMENTATION ROADMAP - STATUS REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {metrics.calculated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall status
        report.append("OVERALL STATUS")
        report.append("-" * 70)
        report.append(f"Project Completion: {metrics.completion_percentage:.1f}%")
        report.append(f"Current Phase: {metrics.current_phase.value.upper()}")
        report.append(f"Phase Progress: {metrics.current_phase_completion:.1f}%")
        report.append(f"System Maturity: {metrics.current_maturity.value.upper()}")
        if metrics.days_elapsed is not None:
            report.append(f"Days Elapsed: {metrics.days_elapsed}")
        if metrics.current_phase_duration_days is not None:
            report.append(f"Current Phase Duration: {metrics.current_phase_duration_days} days")
        report.append("")
        
        # Module status
        report.append("MODULE STATUS")
        report.append("-" * 70)
        report.append(f"Modules Completed: {metrics.modules_completed}/{metrics.modules_total}")
        report.append(f"Architecture Compliant: {metrics.modules_architecture_compliant}/{metrics.modules_total}")
        report.append(f"Average Test Coverage: {metrics.average_test_coverage:.1f}%")
        report.append("")
        
        # Module breakdown
        for module_id, module in sorted(self.project_state.modules.items()):
            status_symbol = self._get_status_symbol(module.status)
            report.append(
                f"  {status_symbol} Module {module_id} ({module.module_name}): "
                f"{module.status.value}"
            )
        report.append("")
        
        # Integration status
        report.append("INTEGRATION STATUS")
        report.append("-" * 70)
        report.append(
            f"Integration Steps: {metrics.integration_steps_complete}/"
            f"{metrics.integration_steps_total} complete"
        )
        if metrics.integration_tests_total > 0:
            pass_rate = (metrics.integration_tests_passing / metrics.integration_tests_total) * 100
            report.append(
                f"Integration Tests: {metrics.integration_tests_passing}/"
                f"{metrics.integration_tests_total} passing ({pass_rate:.1f}%)"
            )
        report.append("")
        
        # Risk status
        report.append("RISK STATUS")
        report.append("-" * 70)
        report.append(f"Active Risks: {metrics.active_risks_count}")
        report.append(f"High/Critical Risks: {metrics.high_priority_risks_count}")
        
        if metrics.high_priority_risks_count > 0:
            report.append("")
            report.append("High Priority Risks:")
            for risk in self.project_state.get_high_priority_risks():
                report.append(f"  ⚠ {risk.risk_id}: {risk.description}")
                report.append(f"    Level: {risk.level.value}, Owner: {risk.owner or 'Unassigned'}")
        report.append("")
        
        # Phase gate status
        report.append("CURRENT PHASE GATE STATUS")
        report.append("-" * 70)
        current_phase_info = self.project_state.phases[metrics.current_phase]
        
        if current_phase_info.exit_conditions:
            satisfied = sum(1 for c in current_phase_info.exit_conditions if c.satisfied)
            total = len(current_phase_info.exit_conditions)
            report.append(f"Exit Conditions: {satisfied}/{total} satisfied")
            report.append("")
            
            for condition in current_phase_info.exit_conditions:
                symbol = "✓" if condition.satisfied else "○"
                report.append(f"  {symbol} {condition.condition_id}: {condition.description}")
                if condition.satisfied and condition.verified_by:
                    report.append(f"    Verified by: {condition.verified_by}")
        else:
            report.append("No exit conditions defined for current phase")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def _get_status_symbol(self, status: ModuleStatus) -> str:
        """Get a symbol representing module status."""
        symbols = {
            ModuleStatus.NOT_STARTED: "○",
            ModuleStatus.IN_DEVELOPMENT: "◐",
            ModuleStatus.UNIT_TESTED: "◑",
            ModuleStatus.INTEGRATED: "◕",
            ModuleStatus.VALIDATED: "✓",
        }
        return symbols.get(status, "?")
    
    def get_critical_path_modules(self) -> List[str]:
        """
        Identify modules on the critical path.
        
        Critical path modules are those whose delay would directly
        impact project completion.
        """
        critical = []
        
        # Foundation modules (no dependencies)
        critical.extend(["01", "09"])
        
        # Architecture framework (depends on foundation)
        critical.append("03")
        
        # First model module (establishes pattern)
        critical.append("04")
        
        # Breakthrough detection (depends on many modules)
        critical.append("02")
        
        # Validation (depends on all modules)
        critical.append("10")
        
        return critical
    
    def get_blocking_issues(self) -> List[str]:
        """Identify issues blocking progress."""
        issues = []
        
        # Check for modules blocked by dependencies
        for module_id, module in self.project_state.modules.items():
            if module.status == ModuleStatus.NOT_STARTED:
                for dep_id in module.dependencies:
                    dep = self.project_state.modules.get(dep_id)
                    if dep and dep.status not in [
                        ModuleStatus.INTEGRATED,
                        ModuleStatus.VALIDATED
                    ]:
                        issues.append(
                            f"Module {module_id} blocked by dependency {dep_id} "
                            f"(status: {dep.status.value})"
                        )
        
        # Check for blocked integration steps
        for step_id, step_info in self.project_state.integration_steps.items():
            if step_info.status == IntegrationStatus.BLOCKED:
                issues.append(
                    f"Integration step {step_id} ({step_info.name}) blocked: "
                    f"{', '.join(step_info.issues)}"
                )
        
        # Check for high-priority risks
        for risk in self.project_state.get_high_priority_risks():
            issues.append(f"High-priority risk: {risk.risk_id} - {risk.description}")
        
        return issues
    
    def validate_project_state(self) -> List[ValidationResult]:
        """Validate project state for consistency and completeness."""
        results = []
        
        # Verify module dependencies are satisfied
        for module_id, module in self.project_state.modules.items():
            for dep_id in module.dependencies:
                if dep_id not in self.project_state.modules:
                    results.append(ValidationResult(
                        check_name="module_dependencies",
                        passed=False,
                        message=f"Module {module_id} has undefined dependency {dep_id}"
                    ))
        
        # Verify phase progression is logical
        current_phase = self.project_state.current_phase
        for phase in Phase:
            phase_info = self.project_state.phases.get(phase)
            if not phase_info:
                results.append(ValidationResult(
                    check_name="phase_definitions",
                    passed=False,
                    message=f"Phase {phase.value} not defined in project state"
                ))
            elif phase.value < current_phase.value and phase_info.status != PhaseStatus.COMPLETE:
                results.append(ValidationResult(
                    check_name="phase_progression",
                    passed=False,
                    message=f"Previous phase {phase.value} not marked complete"
                ))
        
        # Verify integration step dependencies
        for step_id, step_info in self.project_state.integration_steps.items():
            for module_id in step_info.modules_to_integrate:
                if module_id not in self.project_state.modules:
                    results.append(ValidationResult(
                        check_name="integration_dependencies",
                        passed=False,
                        message=f"Integration step {step_id} references undefined module {module_id}"
                    ))
        
        # If no issues found, add success result
        if not results:
            results.append(ValidationResult(
                check_name="overall_validation",
                passed=True,
                message="Project state is valid and consistent"
            ))
        
        return results
    
    def export_metrics_json(self) -> Dict:
        """Export metrics as JSON-serializable dictionary."""
        metrics = self.calculate_metrics()
        
        return {
            "completion_percentage": metrics.completion_percentage,
            "modules": {
                "completed": metrics.modules_completed,
                "total": metrics.modules_total,
                "architecture_compliant": metrics.modules_architecture_compliant,
                "average_test_coverage": metrics.average_test_coverage,
            },
            "phases": {
                "current": metrics.current_phase.value,
                "current_completion": metrics.current_phase_completion,
                "completed": metrics.phases_completed,
                "total": metrics.phases_total,
            },
            "schedule": {
                "days_elapsed": metrics.days_elapsed,
                "current_phase_duration_days": metrics.current_phase_duration_days,
            },
            "integration": {
                "steps_complete": metrics.integration_steps_complete,
                "steps_total": metrics.integration_steps_total,
                "tests_passing": metrics.integration_tests_passing,
                "tests_total": metrics.integration_tests_total,
            },
            "risks": {
                "active": metrics.active_risks_count,
                "high_priority": metrics.high_priority_risks_count,
            },
            "maturity": metrics.current_maturity.value,
            "calculated_at": metrics.calculated_at.isoformat(),
        }
