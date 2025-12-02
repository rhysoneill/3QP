"""
Roadmap Manager: Core implementation management logic.

This module provides the RoadmapManager class that orchestrates phase
progression, gate verification, and implementation workflow management.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from .types import (
    Phase,
    PhaseStatus,
    ModuleStatus,
    IntegrationStatus,
    MaturityLevel,
    GateCondition,
    PhaseInfo,
    ModuleInfo,
    IntegrationStepInfo,
    ProjectState,
    RiskInfo,
    MilestoneInfo,
)


class PhaseGate:
    """Manages phase gate conditions and verification."""
    
    def __init__(self, phase: Phase):
        self.phase = phase
        self.entry_conditions: List[GateCondition] = []
        self.exit_conditions: List[GateCondition] = []
    
    def add_entry_condition(self, condition: GateCondition) -> None:
        """Add an entry condition to this gate."""
        self.entry_conditions.append(condition)
    
    def add_exit_condition(self, condition: GateCondition) -> None:
        """Add an exit condition to this gate."""
        self.exit_conditions.append(condition)
    
    def verify_entry(self) -> Tuple[bool, List[str]]:
        """Verify all entry conditions are satisfied."""
        failures = []
        for condition in self.entry_conditions:
            if not condition.satisfied:
                failures.append(f"{condition.condition_id}: {condition.description}")
        
        return len(failures) == 0, failures
    
    def verify_exit(self) -> Tuple[bool, List[str]]:
        """Verify all exit conditions are satisfied."""
        failures = []
        for condition in self.exit_conditions:
            if not condition.satisfied:
                failures.append(f"{condition.condition_id}: {condition.description}")
        
        return len(failures) == 0, failures
    
    def mark_condition_satisfied(
        self,
        condition_id: str,
        verified_by: str,
        is_entry: bool = False
    ) -> bool:
        """Mark a specific condition as satisfied."""
        conditions = self.entry_conditions if is_entry else self.exit_conditions
        
        for condition in conditions:
            if condition.condition_id == condition_id:
                condition.satisfied = True
                condition.verified_by = verified_by
                condition.verified_at = datetime.now()
                return True
        
        return False


class IntegrationStep:
    """Manages an individual integration step."""
    
    def __init__(
        self,
        step_id: int,
        name: str,
        modules_to_integrate: List[str]
    ):
        self.step_id = step_id
        self.name = name
        self.modules_to_integrate = modules_to_integrate
        self.status = IntegrationStatus.PLANNING
        self.test_plan_approved = False
        self.tests_passing = 0
        self.tests_total = 0
        self.start_date: Optional[datetime] = None
        self.completion_date: Optional[datetime] = None
        self.issues: List[str] = []
    
    def check_readiness(self, module_states: Dict[str, ModuleInfo]) -> Tuple[bool, List[str]]:
        """Check if integration step is ready to proceed."""
        blockers = []
        
        # Check if all required modules are unit tested
        for module_id in self.modules_to_integrate:
            if module_id not in module_states:
                blockers.append(f"Module {module_id} not found")
            elif module_states[module_id].status not in [
                ModuleStatus.UNIT_TESTED,
                ModuleStatus.INTEGRATED,
                ModuleStatus.VALIDATED
            ]:
                blockers.append(
                    f"Module {module_id} not ready (status: {module_states[module_id].status.value})"
                )
        
        # Check if test plan is approved
        if not self.test_plan_approved:
            blockers.append("Integration test plan not approved")
        
        return len(blockers) == 0, blockers
    
    def start_integration(self) -> bool:
        """Start the integration step."""
        if self.status != IntegrationStatus.READY:
            return False
        
        self.status = IntegrationStatus.IN_PROGRESS
        self.start_date = datetime.now()
        return True
    
    def update_test_results(self, passing: int, total: int) -> None:
        """Update test results for this integration step."""
        self.tests_passing = passing
        self.tests_total = total
    
    def complete_integration(self) -> bool:
        """Mark integration step as complete if all tests pass."""
        if self.tests_total == 0:
            return False
        
        if self.tests_passing == self.tests_total:
            self.status = IntegrationStatus.COMPLETE
            self.completion_date = datetime.now()
            return True
        
        return False
    
    def add_issue(self, issue: str) -> None:
        """Add an issue encountered during integration."""
        self.issues.append(issue)
        if self.status == IntegrationStatus.IN_PROGRESS:
            self.status = IntegrationStatus.BLOCKED
    
    def to_info(self) -> IntegrationStepInfo:
        """Convert to IntegrationStepInfo dataclass."""
        return IntegrationStepInfo(
            step_id=self.step_id,
            name=self.name,
            status=self.status,
            modules_to_integrate=self.modules_to_integrate.copy(),
            test_plan_approved=self.test_plan_approved,
            tests_passing=self.tests_passing,
            tests_total=self.tests_total,
            start_date=self.start_date,
            completion_date=self.completion_date,
            issues=self.issues.copy()
        )


class RoadmapManager:
    """
    Manages the implementation roadmap, phase progression, and gating.
    
    This is the primary interface for tracking and controlling the
    3QP implementation lifecycle.
    """
    
    def __init__(self):
        self.project_state = ProjectState(
            current_phase=Phase.ARCHITECTURE,
            current_maturity=MaturityLevel.NONE
        )
        self.phase_gates: Dict[Phase, PhaseGate] = {}
        self.integration_steps: Dict[int, IntegrationStep] = {}
        
        # Initialize phase gates with standard conditions
        self._initialize_phase_gates()
        self._initialize_modules()
        self._initialize_integration_steps()
    
    def _initialize_phase_gates(self) -> None:
        """Initialize standard phase gates with required conditions."""
        
        # Phase 1: Architecture → Foundation
        arch_gate = PhaseGate(Phase.ARCHITECTURE)
        arch_gate.add_exit_condition(GateCondition(
            "ARCH_COMPLETE",
            "All 10 architectural modules complete",
            "Document review and checklist"
        ))
        arch_gate.add_exit_condition(GateCondition(
            "INTERFACES_VERIFIED",
            "All inter-module interfaces verified",
            "Interface compatibility matrix review"
        ))
        arch_gate.add_exit_condition(GateCondition(
            "SCIENTIFIC_FOUNDATION_VALIDATED",
            "Scientific foundations reviewed and validated",
            "Domain expert review"
        ))
        arch_gate.add_exit_condition(GateCondition(
            "ARCHITECTURE_BASELINE_APPROVED",
            "Architecture Review Board approval obtained",
            "Formal ARB approval meeting"
        ))
        self.phase_gates[Phase.ARCHITECTURE] = arch_gate
        
        # Phase 2: Foundation → Model
        foundation_gate = PhaseGate(Phase.FOUNDATION)
        foundation_gate.add_entry_condition(GateCondition(
            "PHASE1_COMPLETE",
            "Phase 1 exit criteria satisfied",
            "Gate review"
        ))
        foundation_gate.add_exit_condition(GateCondition(
            "FOUNDATION_MODULES_IMPLEMENTED",
            "Modules 01, 09, 03 implemented and tested",
            "Module completion verification"
        ))
        foundation_gate.add_exit_condition(GateCondition(
            "FOUNDATION_INTEGRATED",
            "Foundation modules successfully integrated",
            "Integration test results"
        ))
        foundation_gate.add_exit_condition(GateCondition(
            "LOGGING_OPERATIONAL",
            "Logging system operational",
            "Logging functionality test"
        ))
        self.phase_gates[Phase.FOUNDATION] = foundation_gate
        
        # Phase 3: Model → Integration Module
        model_gate = PhaseGate(Phase.MODEL)
        model_gate.add_entry_condition(GateCondition(
            "PHASE2_COMPLETE",
            "Phase 2 exit criteria satisfied",
            "Gate review"
        ))
        model_gate.add_exit_condition(GateCondition(
            "MODEL_MODULES_IMPLEMENTED",
            "All model modules implemented and tested",
            "Module completion verification"
        ))
        model_gate.add_exit_condition(GateCondition(
            "MODEL_INTEGRATED",
            "Model modules successfully integrated",
            "Integration test results"
        ))
        model_gate.add_exit_condition(GateCondition(
            "DATA_CONTRACTS_SATISFIED",
            "All data contracts verified",
            "Interface verification testing"
        ))
        self.phase_gates[Phase.MODEL] = model_gate
        
        # Continue for remaining phases...
        # (Implementation continues for Integration Module, System Integration, Validation, Delivery)
        
        # Store phase info in project state
        for phase in Phase:
            gate = self.phase_gates.get(phase, PhaseGate(phase))
            self.project_state.phases[phase] = PhaseInfo(
                phase=phase,
                status=PhaseStatus.NOT_STARTED if phase != Phase.ARCHITECTURE else PhaseStatus.IN_PROGRESS,
                entry_conditions=gate.entry_conditions.copy(),
                exit_conditions=gate.exit_conditions.copy()
            )
    
    def _initialize_modules(self) -> None:
        """Initialize module tracking."""
        module_definitions = {
            "01": ("TQP_Core", []),
            "02": ("Breakthrough_Impact", ["01", "03", "04", "05", "06"]),
            "03": ("Architecture", ["01", "09"]),
            "04": ("SlowFast_Physiology", ["01", "03"]),
            "05": ("Social_Network", ["01", "03"]),
            "06": ("BDI_Cycle", ["01", "03"]),
            "07": ("Stressor_Model", ["01", "03"]),
            "08": ("Intervention_Engine", ["01", "03"]),
            "09": ("Logging_System", []),
            "10": ("Validation", ["01", "02", "03", "04", "05", "06", "07", "08", "09"]),
        }
        
        for module_id, (name, deps) in module_definitions.items():
            self.project_state.modules[module_id] = ModuleInfo(
                module_id=module_id,
                module_name=name,
                status=ModuleStatus.NOT_STARTED,
                dependencies=deps
            )
    
    def _initialize_integration_steps(self) -> None:
        """Initialize the 8 integration steps."""
        steps = [
            (1, "Foundation Layer", ["01", "09"]),
            (2, "Architecture Framework", ["03"]),
            (3, "Physiology Integration", ["04"]),
            (4, "Social-Cognitive Integration", ["05", "06"]),
            (5, "Environment-Response Integration", ["07", "08"]),
            (6, "Breakthrough Detection Integration", ["02"]),
            (7, "Validation Integration", ["10"]),
            (8, "Full System Verification", []),
        ]
        
        for step_id, name, modules in steps:
            step = IntegrationStep(step_id, name, modules)
            self.integration_steps[step_id] = step
            self.project_state.integration_steps[step_id] = step.to_info()
    
    def get_current_phase(self) -> Phase:
        """Get the current project phase."""
        return self.project_state.current_phase
    
    def get_current_maturity(self) -> MaturityLevel:
        """Get the current system maturity level."""
        return self.project_state.current_maturity
    
    def update_module_status(
        self,
        module_id: str,
        status: ModuleStatus,
        notes: str = ""
    ) -> bool:
        """Update the status of a module."""
        if module_id not in self.project_state.modules:
            return False
        
        module = self.project_state.modules[module_id]
        module.status = status
        if notes:
            module.notes = notes
        
        if status == ModuleStatus.UNIT_TESTED and not module.completion_date:
            module.completion_date = datetime.now()
        
        return True
    
    def check_phase_entry_ready(self, phase: Phase) -> Tuple[bool, List[str]]:
        """Check if a phase is ready to enter."""
        if phase not in self.phase_gates:
            return False, ["Phase gate not defined"]
        
        return self.phase_gates[phase].verify_entry()
    
    def check_phase_exit_ready(self, phase: Phase) -> Tuple[bool, List[str]]:
        """Check if a phase is ready to exit."""
        if phase not in self.phase_gates:
            return False, ["Phase gate not defined"]
        
        return self.phase_gates[phase].verify_exit()
    
    def mark_gate_condition_satisfied(
        self,
        phase: Phase,
        condition_id: str,
        verified_by: str,
        is_entry: bool = False
    ) -> bool:
        """Mark a specific gate condition as satisfied."""
        if phase not in self.phase_gates:
            return False
        
        success = self.phase_gates[phase].mark_condition_satisfied(
            condition_id, verified_by, is_entry
        )
        
        # Update project state
        if success:
            phase_info = self.project_state.phases[phase]
            conditions = phase_info.entry_conditions if is_entry else phase_info.exit_conditions
            for cond in conditions:
                if cond.condition_id == condition_id:
                    cond.satisfied = True
                    cond.verified_by = verified_by
                    cond.verified_at = datetime.now()
        
        return success
    
    def transition_to_phase(self, next_phase: Phase) -> Tuple[bool, str]:
        """Attempt to transition to the next phase."""
        current_phase = self.project_state.current_phase
        
        # Verify current phase exit conditions
        can_exit, exit_failures = self.check_phase_exit_ready(current_phase)
        if not can_exit:
            return False, f"Cannot exit {current_phase.value}: " + "; ".join(exit_failures)
        
        # Verify next phase entry conditions
        can_enter, entry_failures = self.check_phase_entry_ready(next_phase)
        if not can_enter:
            return False, f"Cannot enter {next_phase.value}: " + "; ".join(entry_failures)
        
        # Perform transition
        self.project_state.phases[current_phase].status = PhaseStatus.COMPLETE
        self.project_state.phases[current_phase].actual_end_date = datetime.now()
        
        self.project_state.current_phase = next_phase
        self.project_state.phases[next_phase].status = PhaseStatus.IN_PROGRESS
        self.project_state.phases[next_phase].start_date = datetime.now()
        
        # Update maturity level based on phase
        self._update_maturity_level(next_phase)
        
        return True, f"Successfully transitioned to {next_phase.value}"
    
    def _update_maturity_level(self, phase: Phase) -> None:
        """Update system maturity level based on phase completion."""
        maturity_map = {
            Phase.ARCHITECTURE: MaturityLevel.NONE,
            Phase.FOUNDATION: MaturityLevel.ALPHA,
            Phase.MODEL: MaturityLevel.BETA,
            Phase.INTEGRATION_MODULE: MaturityLevel.RELEASE_CANDIDATE,
            Phase.SYSTEM_INTEGRATION: MaturityLevel.RELEASE,
            Phase.VALIDATION: MaturityLevel.VALIDATED,
            Phase.DELIVERY: MaturityLevel.FINAL,
        }
        self.project_state.current_maturity = maturity_map.get(phase, MaturityLevel.NONE)
    
    def get_module_readiness(self, module_id: str) -> Tuple[bool, List[str]]:
        """Check if a module is ready for implementation."""
        if module_id not in self.project_state.modules:
            return False, ["Module not found"]
        
        module = self.project_state.modules[module_id]
        blockers = []
        
        # Check dependencies
        for dep_id in module.dependencies:
            if dep_id not in self.project_state.modules:
                blockers.append(f"Dependency {dep_id} not found")
            else:
                dep = self.project_state.modules[dep_id]
                if dep.status not in [ModuleStatus.INTEGRATED, ModuleStatus.VALIDATED]:
                    blockers.append(
                        f"Dependency {dep_id} not ready (status: {dep.status.value})"
                    )
        
        return len(blockers) == 0, blockers
    
    def get_integration_step_readiness(self, step_id: int) -> Tuple[bool, List[str]]:
        """Check if an integration step is ready to proceed."""
        if step_id not in self.integration_steps:
            return False, ["Integration step not found"]
        
        return self.integration_steps[step_id].check_readiness(
            self.project_state.modules
        )
    
    def get_project_state(self) -> ProjectState:
        """Get the complete project state."""
        # Update integration step info
        for step_id, step in self.integration_steps.items():
            self.project_state.integration_steps[step_id] = step.to_info()
        
        return self.project_state
    
    def add_risk(self, risk: RiskInfo) -> None:
        """Add a new risk to the project."""
        self.project_state.risks[risk.risk_id] = risk
    
    def update_risk(self, risk_id: str, **kwargs: Any) -> bool:
        """Update an existing risk."""
        if risk_id not in self.project_state.risks:
            return False
        
        risk = self.project_state.risks[risk_id]
        for key, value in kwargs.items():
            if hasattr(risk, key):
                setattr(risk, key, value)
        
        risk.updated_at = datetime.now()
        return True
    
    def add_milestone(self, milestone: MilestoneInfo) -> None:
        """Add a project milestone."""
        self.project_state.milestones[milestone.milestone_id] = milestone
    
    def achieve_milestone(self, milestone_id: str) -> bool:
        """Mark a milestone as achieved."""
        if milestone_id not in self.project_state.milestones:
            return False
        
        milestone = self.project_state.milestones[milestone_id]
        milestone.achieved = True
        milestone.actual_date = datetime.now()
        return True
