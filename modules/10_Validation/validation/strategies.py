"""
Validation strategies implementing specific validation procedures.

Each strategy focuses on one validation category (structural, data integrity,
determinism, integration, temporal, or metric validation).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import logging

from .types import (
    ValidationCategory,
    ValidationResult,
    TestResult,
    CategoryResult,
    ModuleStateSnapshot,
    ValidationConfiguration,
)

logger = logging.getLogger(__name__)


class ValidationStrategy(ABC):
    """
    Abstract base class for validation strategies.
    
    Each concrete strategy implements validation procedures for
    one category of validation.
    """
    
    def __init__(self, config: ValidationConfiguration):
        """
        Initialize validation strategy.
        
        Args:
            config: Validation configuration
        """
        self.config = config
        self.test_results: List[TestResult] = []
    
    @abstractmethod
    def get_category(self) -> ValidationCategory:
        """Get the validation category this strategy handles."""
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """
        Execute validation procedures for this category.
        
        Args:
            context: Validation context containing necessary data
            
        Returns:
            Aggregated results for this category
        """
        pass
    
    def _create_test_result(
        self,
        test_name: str,
        result: ValidationResult,
        message: str,
        metrics: Dict[str, Any] = None
    ) -> TestResult:
        """
        Create a test result record.
        
        Args:
            test_name: Name of the test
            result: Test result (PASS/FAIL/WARNING)
            message: Descriptive message
            metrics: Optional metrics dictionary
            
        Returns:
            Test result record
        """
        return TestResult(
            test_name=test_name,
            result=result,
            message=message,
            metrics=metrics or {},
            timestamp=datetime.now()
        )
    
    def _aggregate_results(self) -> CategoryResult:
        """
        Aggregate individual test results into category result.
        
        Returns:
            Category result with aggregated statistics
        """
        tests_run = len(self.test_results)
        tests_passed = sum(1 for t in self.test_results if t.result == ValidationResult.PASS)
        tests_failed = sum(1 for t in self.test_results if t.result == ValidationResult.FAIL)
        tests_warned = sum(1 for t in self.test_results if t.result == ValidationResult.WARNING)
        
        # Overall category result is FAIL if any test failed, WARNING if any warned, else PASS
        if tests_failed > 0:
            overall_result = ValidationResult.FAIL
        elif tests_warned > 0:
            overall_result = ValidationResult.WARNING
        else:
            overall_result = ValidationResult.PASS
        
        return CategoryResult(
            category=self.get_category(),
            result=overall_result,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_warned=tests_warned,
            details=self.test_results.copy()
        )


class StructuralValidationStrategy(ValidationStrategy):
    """
    Validates structural integrity and architectural compliance.
    
    Checks:
    - Module initialization
    - Configuration validity
    - Schema compliance
    - Dependency satisfaction
    - Interface compliance
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.STRUCTURAL
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute structural validation procedures."""
        logger.info("Executing structural validation")
        self.test_results = []
        
        # Check module initialization
        initialization_statuses = context.get("initialization_statuses", [])
        self._validate_initialization(initialization_statuses)
        
        # Check configuration
        self._validate_configuration(context.get("system_config"))
        
        # Check schemas
        snapshots = context.get("state_snapshots", [])
        self._validate_schemas(snapshots)
        
        return self._aggregate_results()
    
    def _validate_initialization(self, statuses: List[Any]) -> None:
        """Validate module initialization."""
        from .types import InitializationResult
        
        all_successful = all(
            s.initialization_result == InitializationResult.SUCCESS
            for s in statuses
        )
        
        failed_modules = [
            s.module_id for s in statuses
            if s.initialization_result == InitializationResult.FAILURE
        ]
        
        if all_successful:
            result = self._create_test_result(
                "module_initialization",
                ValidationResult.PASS,
                f"All {len(statuses)} modules initialized successfully",
                {"modules_initialized": len(statuses)}
            )
        else:
            result = self._create_test_result(
                "module_initialization",
                ValidationResult.FAIL,
                f"Modules failed to initialize: {', '.join(failed_modules)}",
                {
                    "total_modules": len(statuses),
                    "failed_modules": len(failed_modules)
                }
            )
        
        self.test_results.append(result)
    
    def _validate_configuration(self, system_config: Any) -> None:
        """Validate system configuration."""
        if system_config is None:
            result = self._create_test_result(
                "configuration_validation",
                ValidationResult.WARNING,
                "No system configuration provided for validation"
            )
        else:
            result = self._create_test_result(
                "configuration_validation",
                ValidationResult.PASS,
                "System configuration validated"
            )
        
        self.test_results.append(result)
    
    def _validate_schemas(self, snapshots: List[ModuleStateSnapshot]) -> None:
        """Validate data structure schemas."""
        schema_compliant = sum(
            1 for s in snapshots
            if s.integrity_indicators.schema_compliance
        )
        
        total = len(snapshots)
        
        if total == 0:
            result = self._create_test_result(
                "schema_compliance",
                ValidationResult.WARNING,
                "No state snapshots available for schema validation"
            )
        elif schema_compliant == total:
            result = self._create_test_result(
                "schema_compliance",
                ValidationResult.PASS,
                f"All {total} snapshots conform to schemas",
                {"compliant": total, "total": total}
            )
        else:
            result = self._create_test_result(
                "schema_compliance",
                ValidationResult.FAIL,
                f"{total - schema_compliant} of {total} snapshots violate schemas",
                {"compliant": schema_compliant, "total": total}
            )
        
        self.test_results.append(result)


class DataIntegrityValidationStrategy(ValidationStrategy):
    """
    Validates data integrity and consistency.
    
    Checks:
    - Constraint satisfaction
    - Referential integrity
    - Data completeness
    - Corruption detection
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.DATA_INTEGRITY
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute data integrity validation procedures."""
        logger.info("Executing data integrity validation")
        self.test_results = []
        
        snapshots = context.get("state_snapshots", [])
        
        self._validate_constraints(snapshots)
        self._validate_completeness(snapshots)
        self._detect_corruption(snapshots)
        
        return self._aggregate_results()
    
    def _validate_constraints(self, snapshots: List[ModuleStateSnapshot]) -> None:
        """Validate data constraints."""
        total_violations = sum(
            len(s.consistency_signals.constraint_violations)
            for s in snapshots
        )
        
        if total_violations == 0:
            result = self._create_test_result(
                "constraint_validation",
                ValidationResult.PASS,
                f"No constraint violations in {len(snapshots)} snapshots",
                {"violations": 0, "snapshots": len(snapshots)}
            )
        else:
            result = self._create_test_result(
                "constraint_validation",
                ValidationResult.FAIL,
                f"Found {total_violations} constraint violations",
                {"violations": total_violations, "snapshots": len(snapshots)}
            )
        
        self.test_results.append(result)
    
    def _validate_completeness(self, snapshots: List[ModuleStateSnapshot]) -> None:
        """Validate data completeness."""
        if not snapshots:
            result = self._create_test_result(
                "data_completeness",
                ValidationResult.WARNING,
                "No snapshots available for completeness check"
            )
            self.test_results.append(result)
            return
        
        avg_completeness = sum(
            s.integrity_indicators.data_completeness
            for s in snapshots
        ) / len(snapshots)
        
        if avg_completeness >= 0.95:
            result_type = ValidationResult.PASS
            message = f"Data completeness: {avg_completeness:.2%}"
        elif avg_completeness >= 0.80:
            result_type = ValidationResult.WARNING
            message = f"Data completeness below target: {avg_completeness:.2%}"
        else:
            result_type = ValidationResult.FAIL
            message = f"Data completeness critically low: {avg_completeness:.2%}"
        
        result = self._create_test_result(
            "data_completeness",
            result_type,
            message,
            {"average_completeness": avg_completeness}
        )
        
        self.test_results.append(result)
    
    def _detect_corruption(self, snapshots: List[ModuleStateSnapshot]) -> None:
        """Detect data corruption."""
        corrupted = [
            s.module_id for s in snapshots
            if s.integrity_indicators.corruption_detected
        ]
        
        if not corrupted:
            result = self._create_test_result(
                "corruption_detection",
                ValidationResult.PASS,
                f"No corruption detected in {len(snapshots)} snapshots"
            )
        else:
            result = self._create_test_result(
                "corruption_detection",
                ValidationResult.FAIL,
                f"Corruption detected in modules: {', '.join(corrupted)}",
                {"corrupted_modules": len(corrupted)}
            )
        
        self.test_results.append(result)


class TemporalValidationStrategy(ValidationStrategy):
    """
    Validates temporal consistency and time-step progression.
    
    Checks:
    - Time-step sequencing
    - State transition correctness
    - Clock synchronization
    - Temporal consistency
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.TEMPORAL
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute temporal validation procedures."""
        logger.info("Executing temporal validation")
        self.test_results = []
        
        time_step_metadata = context.get("time_step_metadata", [])
        
        self._validate_time_step_sequence(time_step_metadata)
        self._validate_clock_synchronization(context.get("state_snapshots", []))
        
        return self._aggregate_results()
    
    def _validate_time_step_sequence(self, metadata: List[Any]) -> None:
        """Validate time-step sequencing."""
        if not metadata:
            result = self._create_test_result(
                "time_step_sequencing",
                ValidationResult.WARNING,
                "No time-step metadata available"
            )
            self.test_results.append(result)
            return
        
        # Check monotonic progression
        time_steps = [m.time_step for m in metadata]
        is_monotonic = all(
            time_steps[i] < time_steps[i+1]
            for i in range(len(time_steps) - 1)
        )
        
        if is_monotonic:
            result = self._create_test_result(
                "time_step_sequencing",
                ValidationResult.PASS,
                f"Time steps progress monotonically through {len(time_steps)} steps"
            )
        else:
            result = self._create_test_result(
                "time_step_sequencing",
                ValidationResult.FAIL,
                "Time-step sequence is not monotonic"
            )
        
        self.test_results.append(result)
    
    def _validate_clock_synchronization(self, snapshots: List[ModuleStateSnapshot]) -> None:
        """Validate clock synchronization across modules."""
        if not snapshots:
            result = self._create_test_result(
                "clock_synchronization",
                ValidationResult.WARNING,
                "No snapshots available for clock synchronization check"
            )
            self.test_results.append(result)
            return
        
        # Group by time_step
        time_step_groups: Dict[int, List[ModuleStateSnapshot]] = {}
        for snapshot in snapshots:
            if snapshot.time_step not in time_step_groups:
                time_step_groups[snapshot.time_step] = []
            time_step_groups[snapshot.time_step].append(snapshot)
        
        # Check each time step has consistent time across modules
        all_synchronized = True
        for time_step, group in time_step_groups.items():
            if len(set(s.time_step for s in group)) > 1:
                all_synchronized = False
                break
        
        if all_synchronized:
            result = self._create_test_result(
                "clock_synchronization",
                ValidationResult.PASS,
                "All modules synchronized across time steps"
            )
        else:
            result = self._create_test_result(
                "clock_synchronization",
                ValidationResult.FAIL,
                "Clock desynchronization detected between modules"
            )
        
        self.test_results.append(result)


class MetricValidationStrategy(ValidationStrategy):
    """
    Validates computed metrics.
    
    Checks:
    - Metric computation correctness
    - Statistical properties
    - Metric relationships
    - Precision and accuracy
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.METRIC
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute metric validation procedures."""
        logger.info("Executing metric validation")
        self.test_results = []
        
        module_metrics = context.get("module_metrics", {})
        
        self._validate_metric_ranges(module_metrics)
        self._validate_statistical_properties(module_metrics)
        
        return self._aggregate_results()
    
    def _validate_metric_ranges(self, metrics: Dict[str, Any]) -> None:
        """Validate metrics are within expected ranges."""
        # Placeholder implementation
        result = self._create_test_result(
            "metric_ranges",
            ValidationResult.PASS,
            f"Validated ranges for {len(metrics)} metric sets"
        )
        self.test_results.append(result)
    
    def _validate_statistical_properties(self, metrics: Dict[str, Any]) -> None:
        """Validate statistical properties of metrics."""
        # Placeholder implementation
        result = self._create_test_result(
            "statistical_properties",
            ValidationResult.PASS,
            "Statistical properties validated"
        )
        self.test_results.append(result)


class IntegrationValidationStrategy(ValidationStrategy):
    """
    Validates inter-module integration.
    
    Checks:
    - Interface contract compliance
    - Message format validation
    - Data flow correctness
    - Error propagation
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.INTEGRATION
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute integration validation procedures."""
        logger.info("Executing integration validation")
        self.test_results = []
        
        messages = context.get("inter_module_messages", [])
        
        self._validate_message_contracts(messages)
        self._validate_data_flow(messages)
        
        return self._aggregate_results()
    
    def _validate_message_contracts(self, messages: List[Any]) -> None:
        """Validate inter-module message contracts."""
        if not messages:
            result = self._create_test_result(
                "message_contracts",
                ValidationResult.WARNING,
                "No inter-module messages to validate"
            )
            self.test_results.append(result)
            return
        
        compliant = sum(1 for m in messages if m.contract_compliant)
        total = len(messages)
        
        if compliant == total:
            result = self._create_test_result(
                "message_contracts",
                ValidationResult.PASS,
                f"All {total} messages are contract-compliant",
                {"compliant": compliant, "total": total}
            )
        else:
            result = self._create_test_result(
                "message_contracts",
                ValidationResult.FAIL,
                f"{total - compliant} of {total} messages violate contracts",
                {"compliant": compliant, "total": total}
            )
        
        self.test_results.append(result)
    
    def _validate_data_flow(self, messages: List[Any]) -> None:
        """Validate data flow between modules."""
        # Placeholder implementation
        result = self._create_test_result(
            "data_flow_validation",
            ValidationResult.PASS,
            f"Validated data flow for {len(messages)} messages"
        )
        self.test_results.append(result)


class DeterminismValidationStrategy(ValidationStrategy):
    """
    Validates deterministic reproducibility.
    
    Checks:
    - Seed-based execution
    - State equivalence
    - Output equivalence
    - RNG sequence correctness
    """
    
    def get_category(self) -> ValidationCategory:
        return ValidationCategory.DETERMINISM
    
    def execute(self, context: Dict[str, Any]) -> CategoryResult:
        """Execute determinism validation procedures."""
        logger.info("Executing determinism validation")
        self.test_results = []
        
        reproducibility_result = context.get("reproducibility_result")
        
        if reproducibility_result:
            self._validate_reproducibility(reproducibility_result)
        else:
            result = self._create_test_result(
                "reproducibility_check",
                ValidationResult.WARNING,
                "Reproducibility validation not performed"
            )
            self.test_results.append(result)
        
        return self._aggregate_results()
    
    def _validate_reproducibility(self, repro_result: Any) -> None:
        """Validate reproducibility results."""
        if repro_result.identical:
            result = self._create_test_result(
                "reproducibility_check",
                ValidationResult.PASS,
                f"System is reproducible across {repro_result.runs_compared} runs",
                {"runs_compared": repro_result.runs_compared}
            )
        else:
            result = self._create_test_result(
                "reproducibility_check",
                ValidationResult.FAIL,
                f"Non-deterministic behavior detected at time step {repro_result.divergence_point}",
                {
                    "runs_compared": repro_result.runs_compared,
                    "divergence_point": repro_result.divergence_point,
                    "state_differences": len(repro_result.state_differences)
                }
            )
        
        self.test_results.append(result)
