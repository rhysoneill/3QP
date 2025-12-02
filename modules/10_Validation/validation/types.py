"""
Validation framework type definitions.

Defines all data structures for the validation subsystem according
to the data contract specification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# Enumerations

class ValidationCategory(Enum):
    """Validation category enumeration."""
    STRUCTURAL = "STRUCTURAL"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    DETERMINISM = "DETERMINISM"
    INTEGRATION = "INTEGRATION"
    TEMPORAL = "TEMPORAL"
    METRIC = "METRIC"


class ValidationResult(Enum):
    """Validation result enumeration."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class InitializationResult(Enum):
    """Module initialization result."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class ValidationIntensity(Enum):
    """Validation intensity level."""
    FULL = "FULL"
    STANDARD = "STANDARD"
    LIGHTWEIGHT = "LIGHTWEIGHT"


class LogLevel(Enum):
    """Validation logging level."""
    VERBOSE = "VERBOSE"
    STANDARD = "STANDARD"
    MINIMAL = "MINIMAL"


class Severity(Enum):
    """Log entry severity."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Value types

Value = Union[int, float, str, bool]


# Configuration structures

@dataclass
class Threshold:
    """Validation threshold specification."""
    critical_failure_limit: int = 0
    warning_limit: int = 10
    precision_tolerance: float = 1e-6


@dataclass
class ValidationConfiguration:
    """
    Validation framework configuration.
    
    Specifies how validation should be performed including intensity,
    intervals, thresholds, and other parameters.
    """
    system_version: str
    validation_framework_version: str
    random_seed: int
    determinism_check_enabled: bool = True
    validation_intensity: ValidationIntensity = ValidationIntensity.STANDARD
    log_level: LogLevel = LogLevel.STANDARD
    time_step_validation_interval: int = 1
    snapshot_interval: int = 10
    reproducibility_run_count: int = 2
    acceptance_thresholds: Dict[ValidationCategory, Threshold] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration constraints."""
        if self.random_seed < 0:
            raise ValueError("random_seed must be non-negative")
        if self.time_step_validation_interval < 1:
            raise ValueError("time_step_validation_interval must be >= 1")
        if self.snapshot_interval < 1:
            raise ValueError("snapshot_interval must be >= 1")
        if self.reproducibility_run_count < 2:
            raise ValueError("reproducibility_run_count must be >= 2")


# Module state and validation structures

@dataclass
class ConstraintViolation:
    """Data constraint violation record."""
    field_name: str
    constraint_type: str
    expected: str
    actual: str


@dataclass
class InvariantViolation:
    """Invariant violation record."""
    invariant_name: str
    description: str


@dataclass
class ConsistencySignals:
    """Module consistency indicators."""
    internal_consistency_valid: bool
    referential_integrity_valid: bool
    constraint_violations: List[ConstraintViolation] = field(default_factory=list)
    invariant_violations: List[InvariantViolation] = field(default_factory=list)


@dataclass
class IntegrityIndicators:
    """Module data integrity metrics."""
    data_completeness: float  # [0.0, 1.0]
    corruption_detected: bool
    schema_compliance: bool
    null_field_count: int
    out_of_range_count: int
    
    def __post_init__(self):
        """Validate constraints."""
        if not 0.0 <= self.data_completeness <= 1.0:
            raise ValueError("data_completeness must be in [0.0, 1.0]")
        if self.null_field_count < 0:
            raise ValueError("null_field_count must be non-negative")
        if self.out_of_range_count < 0:
            raise ValueError("out_of_range_count must be non-negative")


@dataclass
class ModuleInitializationStatus:
    """Module initialization validation status."""
    module_id: str
    module_name: str
    module_version: str
    initialization_result: InitializationResult
    timestamp: datetime
    configuration_valid: bool
    dependencies_satisfied: bool
    interfaces_ready: bool
    error_messages: List[str] = field(default_factory=list)
    initialization_metrics: Dict[str, Value] = field(default_factory=dict)


@dataclass
class ModuleStateSnapshot:
    """
    Complete state snapshot from a module at a validation checkpoint.
    
    Captures module state, consistency signals, and integrity indicators
    for validation analysis.
    """
    module_id: str
    time_step: int
    timestamp: datetime
    state_version: int
    state_hash: str
    state_data: Dict[str, Any]
    consistency_signals: ConsistencySignals
    integrity_indicators: IntegrityIndicators


@dataclass
class InterModuleMessage:
    """Inter-module communication record for integration validation."""
    message_id: str
    sender_module_id: str
    receiver_module_id: str
    time_step: int
    timestamp: datetime
    message_type: str
    payload: Dict[str, Any]
    payload_schema: str
    schema_valid: bool
    contract_compliant: bool
    size_bytes: int
    serialization_errors: List[str] = field(default_factory=list)


@dataclass
class StateTransition:
    """State transition record for temporal validation."""
    module_id: str
    from_state_hash: str
    to_state_hash: str
    transition_type: str
    timestamp: datetime


@dataclass
class TimeStepMetadata:
    """Metadata for a single time step execution."""
    time_step: int
    start_timestamp: datetime
    end_timestamp: datetime
    execution_duration_ms: float
    modules_executed: List[str]
    execution_order: List[str]
    state_transitions: List[StateTransition] = field(default_factory=list)
    events_processed: int = 0


# Validation result structures

@dataclass
class TestResult:
    """Result of a single validation test."""
    test_name: str
    result: ValidationResult
    message: str
    metrics: Dict[str, Value] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CategoryResult:
    """Aggregated results for a validation category."""
    category: ValidationCategory
    result: ValidationResult
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_warned: int
    details: List[TestResult] = field(default_factory=list)


@dataclass
class ModuleValidationResult:
    """Complete validation results for a single module."""
    module_id: str
    module_name: str
    result: ValidationResult
    structural_validation: Optional[TestResult] = None
    data_integrity_validation: Optional[TestResult] = None
    interface_validation: Optional[TestResult] = None
    metric_validation: Optional[TestResult] = None
    consistency_validation: Optional[TestResult] = None


@dataclass
class CrossModuleValidationResult:
    """Cross-module validation results."""
    result: ValidationResult
    consistency_checks: List[TestResult] = field(default_factory=list)
    integration_tests: List[TestResult] = field(default_factory=list)
    temporal_synchronization: Optional[TestResult] = None


@dataclass
class StateDifference:
    """State difference detected in reproducibility testing."""
    module_id: str
    time_step: int
    field_name: str
    expected_value: Value
    actual_value: Value


@dataclass
class OutputDifference:
    """Output difference detected in reproducibility testing."""
    metric_name: str
    time_step: int
    expected_value: Value
    actual_value: Value
    relative_difference: float


@dataclass
class ReproducibilityResult:
    """Results of reproducibility validation."""
    runs_compared: int
    identical: bool
    divergence_point: Optional[int] = None
    state_differences: List[StateDifference] = field(default_factory=list)
    output_differences: List[OutputDifference] = field(default_factory=list)


@dataclass
class ValidationFailure:
    """Critical validation failure record."""
    severity: Severity
    category: ValidationCategory
    module_id: Optional[str]
    time_step: Optional[int]
    failure_type: str
    description: str
    affected_components: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationWarning:
    """Non-critical validation warning record."""
    category: ValidationCategory
    module_id: Optional[str]
    time_step: Optional[int]
    warning_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionSummary:
    """Summary of validation execution."""
    total_time_steps: int
    validation_start_time: datetime
    validation_end_time: datetime
    validation_duration_ms: float
    modules_validated: int
    messages_validated: int
    snapshots_analyzed: int


@dataclass
class ValidationReport:
    """
    Complete validation report.
    
    Aggregates all validation results, failures, warnings, and metrics
    into a comprehensive report structure.
    """
    report_id: str
    system_version: str
    validation_framework_version: str
    execution_timestamp: datetime
    random_seed: int
    overall_result: ValidationResult
    
    category_results: Dict[ValidationCategory, CategoryResult] = field(default_factory=dict)
    module_results: Dict[str, ModuleValidationResult] = field(default_factory=dict)
    cross_module_results: Optional[CrossModuleValidationResult] = None
    reproducibility_result: Optional[ReproducibilityResult] = None
    
    critical_failures: List[ValidationFailure] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    execution_summary: Optional[ExecutionSummary] = None
    metadata: Dict[str, Value] = field(default_factory=dict)


@dataclass
class ReproducibilityCertificate:
    """Certificate of reproducibility for a validated system."""
    certificate_id: str
    system_version: str
    validation_framework_version: str
    issue_timestamp: datetime
    
    random_seed: int
    runs_executed: int
    all_runs_identical: bool
    
    state_hash_matches: bool
    output_hash_matches: bool
    metric_equivalence: bool
    
    precision_tolerance: float
    max_observed_difference: float
    
    certificate_status: ValidationResult
    validity_conditions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class ValidationLogEntry:
    """Single entry in validation log."""
    entry_id: str
    timestamp: datetime
    time_step: Optional[int]
    validation_category: ValidationCategory
    validation_procedure: str
    target: str  # module_id or "SYSTEM"
    result: ValidationResult
    metrics: Dict[str, Value] = field(default_factory=dict)
    message: str = ""
    details: Optional[Dict[str, Any]] = None
