"""
Type definitions for the Implementation Roadmap module.

This module defines enumerations, data classes, and type specifications for
project states, phases, milestones, and gating conditions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class Phase(Enum):
    """Project development phases."""
    ARCHITECTURE = "architecture"
    FOUNDATION = "foundation"
    MODEL = "model"
    INTEGRATION_MODULE = "integration_module"
    SYSTEM_INTEGRATION = "system_integration"
    VALIDATION = "validation"
    DELIVERY = "delivery"


class PhaseStatus(Enum):
    """Status of a development phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class ModuleStatus(Enum):
    """Status of individual module implementation."""
    NOT_STARTED = "not_started"
    IN_DEVELOPMENT = "in_development"
    UNIT_TESTED = "unit_tested"
    INTEGRATED = "integrated"
    VALIDATED = "validated"


class IntegrationStatus(Enum):
    """Status of integration steps."""
    PLANNING = "planning"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class MaturityLevel(Enum):
    """System maturity levels."""
    NONE = "none"
    ALPHA = "alpha"
    BETA = "beta"
    RELEASE_CANDIDATE = "rc"
    RELEASE = "release"
    VALIDATED = "validated"
    FINAL = "final"


class RiskLevel(Enum):
    """Risk severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GateCondition:
    """Represents a gating condition for phase progression."""
    condition_id: str
    description: str
    verification_method: str
    satisfied: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class ModuleInfo:
    """Information about a module's implementation status."""
    module_id: str
    module_name: str
    status: ModuleStatus
    dependencies: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    test_coverage: float = 0.0
    architecture_compliant: bool = False
    notes: str = ""


@dataclass
class IntegrationStepInfo:
    """Information about an integration step."""
    step_id: int
    name: str
    status: IntegrationStatus
    modules_to_integrate: List[str]
    test_plan_approved: bool = False
    tests_passing: int = 0
    tests_total: int = 0
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    issues: List[str] = field(default_factory=list)


@dataclass
class PhaseInfo:
    """Information about a development phase."""
    phase: Phase
    status: PhaseStatus
    start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    entry_conditions: List[GateCondition] = field(default_factory=list)
    exit_conditions: List[GateCondition] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    risks: List['RiskInfo'] = field(default_factory=list)
    notes: str = ""


@dataclass
class RiskInfo:
    """Information about a project risk."""
    risk_id: str
    description: str
    category: str
    level: RiskLevel
    probability: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    mitigation_strategy: str
    owner: Optional[str] = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MilestoneInfo:
    """Information about a project milestone."""
    milestone_id: str
    name: str
    description: str
    phase: Phase
    planned_date: datetime
    actual_date: Optional[datetime] = None
    achieved: bool = False
    deliverables: List[str] = field(default_factory=list)


@dataclass
class ProjectState:
    """Complete state of the project."""
    current_phase: Phase
    current_maturity: MaturityLevel
    phases: Dict[Phase, PhaseInfo] = field(default_factory=dict)
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    integration_steps: Dict[int, IntegrationStepInfo] = field(default_factory=dict)
    milestones: Dict[str, MilestoneInfo] = field(default_factory=dict)
    risks: Dict[str, RiskInfo] = field(default_factory=dict)
    project_start_date: Optional[datetime] = None
    architecture_baseline_date: Optional[datetime] = None
    
    def get_completion_percentage(self) -> float:
        """Calculate overall project completion percentage."""
        if not self.modules:
            return 0.0
        
        total = len(self.modules)
        completed = sum(
            1 for m in self.modules.values() 
            if m.status in [ModuleStatus.INTEGRATED, ModuleStatus.VALIDATED]
        )
        return (completed / total) * 100.0
    
    def get_phase_completion_percentage(self, phase: Phase) -> float:
        """Calculate completion percentage for a specific phase."""
        phase_info = self.phases.get(phase)
        if not phase_info or not phase_info.exit_conditions:
            return 0.0
        
        total = len(phase_info.exit_conditions)
        satisfied = sum(1 for c in phase_info.exit_conditions if c.satisfied)
        return (satisfied / total) * 100.0
    
    def get_active_risks(self) -> List[RiskInfo]:
        """Get all active risks."""
        return [r for r in self.risks.values() if r.status == "active"]
    
    def get_high_priority_risks(self) -> List[RiskInfo]:
        """Get high and critical priority active risks."""
        return [
            r for r in self.risks.values()
            if r.status == "active" and r.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
