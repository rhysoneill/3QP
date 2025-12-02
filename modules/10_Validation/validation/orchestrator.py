"""
Validation orchestrator.

Coordinates all validation activities, manages validation strategies,
collects results, and generates reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import hashlib
import json

from .types import (
    ValidationConfiguration,
    ValidationReport,
    ValidationResult,
    ValidationCategory,
    ValidationFailure,
    ValidationWarning,
    ModuleStateSnapshot,
    ModuleInitializationStatus,
    ExecutionSummary,
    Severity,
    CategoryResult,
    ModuleValidationResult,
)
from .strategies import (
    ValidationStrategy,
    StructuralValidationStrategy,
    DataIntegrityValidationStrategy,
    TemporalValidationStrategy,
    MetricValidationStrategy,
    IntegrationValidationStrategy,
    DeterminismValidationStrategy,
)
from .validation_hooks import ValidationHooks, ModuleValidationAdapter

logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """
    Central coordinator for all validation activities.
    
    The orchestrator manages:
    - Validation strategy execution
    - Data collection from modules
    - Result aggregation
    - Report generation
    - Failure tracking
    """
    
    def __init__(self, config: ValidationConfiguration):
        """
        Initialize validation orchestrator.
        
        Args:
            config: Validation configuration
        """
        self.config = config
        
        # Initialize strategies
        self.strategies: Dict[ValidationCategory, ValidationStrategy] = {
            ValidationCategory.STRUCTURAL: StructuralValidationStrategy(config),
            ValidationCategory.DATA_INTEGRITY: DataIntegrityValidationStrategy(config),
            ValidationCategory.TEMPORAL: TemporalValidationStrategy(config),
            ValidationCategory.METRIC: MetricValidationStrategy(config),
            ValidationCategory.INTEGRATION: IntegrationValidationStrategy(config),
            ValidationCategory.DETERMINISM: DeterminismValidationStrategy(config),
        }
        
        # Validation data storage
        self.initialization_statuses: List[ModuleInitializationStatus] = []
        self.state_snapshots: List[ModuleStateSnapshot] = []
        self.inter_module_messages: List[Any] = []
        self.time_step_metadata: List[Any] = []
        self.module_metrics: Dict[str, Any] = {}
        
        # Module registry
        self.module_adapters: Dict[str, ValidationHooks] = {}
        
        # Results
        self.critical_failures: List[ValidationFailure] = []
        self.warnings: List[ValidationWarning] = []
        
        # Timing
        self.validation_start_time: Optional[datetime] = None
        self.validation_end_time: Optional[datetime] = None
        
        logger.info(
            f"Validation orchestrator initialized with {len(self.strategies)} strategies"
        )
    
    def register_module(
        self,
        module_id: str,
        module_instance: Any,
        validation_hooks: Optional[ValidationHooks] = None
    ) -> None:
        """
        Register a module for validation.
        
        Args:
            module_id: Unique module identifier
            module_instance: The module instance
            validation_hooks: Optional validation hooks implementation;
                            if None, uses adapter
        """
        if validation_hooks is None:
            # Use adapter for modules without native validation support
            validation_hooks = ModuleValidationAdapter(module_id, module_instance)
        
        self.module_adapters[module_id] = validation_hooks
        logger.info(f"Registered module for validation: {module_id}")
    
    def validate_initialization(self) -> CategoryResult:
        """
        Validate module initialization.
        
        Collects initialization status from all registered modules
        and validates structural requirements.
        
        Returns:
            Category result for structural validation
        """
        logger.info("Validating module initialization")
        
        # Collect initialization statuses
        self.initialization_statuses = []
        for module_id, hooks in self.module_adapters.items():
            try:
                status = hooks.validate_initialization()
                self.initialization_statuses.append(status)
                
                # Check for initialization failures
                from .types import InitializationResult
                if status.initialization_result == InitializationResult.FAILURE:
                    self._record_failure(
                        ValidationCategory.STRUCTURAL,
                        module_id,
                        None,
                        "initialization_failure",
                        f"Module {module_id} failed to initialize: {'; '.join(status.error_messages)}"
                    )
            except Exception as e:
                logger.error(f"Failed to get initialization status from {module_id}: {e}")
                self._record_failure(
                    ValidationCategory.STRUCTURAL,
                    module_id,
                    None,
                    "initialization_check_error",
                    f"Exception while checking initialization: {str(e)}"
                )
        
        # Run structural validation
        context = {
            "initialization_statuses": self.initialization_statuses,
            "system_config": None,  # TODO: Add system config
            "state_snapshots": []
        }
        
        return self.strategies[ValidationCategory.STRUCTURAL].execute(context)
    
    def validate_time_step(self, time_step: int) -> Dict[ValidationCategory, CategoryResult]:
        """
        Validate a single time step.
        
        Collects state snapshots and runs applicable validation strategies.
        
        Args:
            time_step: Current time step
            
        Returns:
            Dictionary of category results
        """
        logger.info(f"Validating time step {time_step}")
        
        # Collect state snapshots
        current_snapshots = []
        for module_id, hooks in self.module_adapters.items():
            try:
                snapshot = hooks.validate_state()
                snapshot.time_step = time_step  # Update time step
                current_snapshots.append(snapshot)
                self.state_snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Failed to get state snapshot from {module_id}: {e}")
                self._record_warning(
                    ValidationCategory.DATA_INTEGRITY,
                    module_id,
                    time_step,
                    "snapshot_error",
                    f"Failed to capture state snapshot: {str(e)}"
                )
        
        # Build validation context
        context = {
            "state_snapshots": current_snapshots,
            "time_step_metadata": self.time_step_metadata,
            "inter_module_messages": self.inter_module_messages,
            "module_metrics": self.module_metrics,
        }
        
        # Run applicable strategies
        results = {}
        
        # Data integrity validation
        results[ValidationCategory.DATA_INTEGRITY] = \
            self.strategies[ValidationCategory.DATA_INTEGRITY].execute(context)
        
        # Temporal validation (if we have metadata)
        if self.time_step_metadata:
            results[ValidationCategory.TEMPORAL] = \
                self.strategies[ValidationCategory.TEMPORAL].execute(context)
        
        # Integration validation (if we have messages)
        if self.inter_module_messages:
            results[ValidationCategory.INTEGRATION] = \
                self.strategies[ValidationCategory.INTEGRATION].execute(context)
        
        return results
    
    def validate_post_execution(self) -> Dict[ValidationCategory, CategoryResult]:
        """
        Perform post-execution validation.
        
        Runs all validation strategies on complete execution data.
        
        Returns:
            Dictionary of category results
        """
        logger.info("Performing post-execution validation")
        
        # Build complete validation context
        context = {
            "initialization_statuses": self.initialization_statuses,
            "state_snapshots": self.state_snapshots,
            "time_step_metadata": self.time_step_metadata,
            "inter_module_messages": self.inter_module_messages,
            "module_metrics": self.module_metrics,
            "system_config": None,
        }
        
        # Run all strategies
        results = {}
        for category, strategy in self.strategies.items():
            try:
                results[category] = strategy.execute(context)
            except Exception as e:
                logger.error(f"Strategy {category} failed: {e}")
                self._record_failure(
                    category,
                    None,
                    None,
                    "strategy_execution_error",
                    f"Validation strategy failed: {str(e)}"
                )
        
        return results
    
    def generate_report(
        self,
        category_results: Dict[ValidationCategory, CategoryResult]
    ) -> ValidationReport:
        """
        Generate comprehensive validation report.
        
        Args:
            category_results: Results from all validation categories
            
        Returns:
            Complete validation report
        """
        logger.info("Generating validation report")
        
        # Determine overall result
        overall_result = self._determine_overall_result(category_results)
        
        # Generate module-level results
        module_results = self._generate_module_results()
        
        # Compute execution summary
        validation_end = datetime.now()
        validation_start = self.validation_start_time or validation_end
        
        execution_summary = ExecutionSummary(
            total_time_steps=max((s.time_step for s in self.state_snapshots), default=0),
            validation_start_time=validation_start,
            validation_end_time=validation_end,
            validation_duration_ms=(validation_end - validation_start).total_seconds() * 1000,
            modules_validated=len(self.module_adapters),
            messages_validated=len(self.inter_module_messages),
            snapshots_analyzed=len(self.state_snapshots)
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_results)
        
        # Create report
        report = ValidationReport(
            report_id=self._generate_report_id(),
            system_version=self.config.system_version,
            validation_framework_version=self.config.validation_framework_version,
            execution_timestamp=validation_end,
            random_seed=self.config.random_seed,
            overall_result=overall_result,
            category_results=category_results,
            module_results=module_results,
            critical_failures=self.critical_failures,
            warnings=self.warnings,
            recommendations=recommendations,
            execution_summary=execution_summary
        )
        
        logger.info(f"Validation report generated: {report.report_id}")
        return report
    
    def run_full_validation(self) -> ValidationReport:
        """
        Run complete validation workflow.
        
        Executes initialization validation and post-execution validation,
        then generates final report.
        
        Returns:
            Complete validation report
        """
        self.validation_start_time = datetime.now()
        logger.info("Starting full validation run")
        
        # Validate initialization
        init_result = self.validate_initialization()
        
        # Run post-execution validation
        post_exec_results = self.validate_post_execution()
        
        # Combine results
        all_results = {
            ValidationCategory.STRUCTURAL: init_result,
            **post_exec_results
        }
        
        # Generate report
        self.validation_end_time = datetime.now()
        report = self.generate_report(all_results)
        
        logger.info(
            f"Full validation complete: {report.overall_result.value} "
            f"({len(self.critical_failures)} failures, {len(self.warnings)} warnings)"
        )
        
        return report
    
    def _determine_overall_result(
        self,
        category_results: Dict[ValidationCategory, CategoryResult]
    ) -> ValidationResult:
        """Determine overall validation result from category results."""
        # FAIL if any critical failures or any category failed
        if self.critical_failures or any(
            r.result == ValidationResult.FAIL for r in category_results.values()
        ):
            return ValidationResult.FAIL
        
        # WARNING if any warnings or any category warned
        if self.warnings or any(
            r.result == ValidationResult.WARNING for r in category_results.values()
        ):
            return ValidationResult.WARNING
        
        # Otherwise PASS
        return ValidationResult.PASS
    
    def _generate_module_results(self) -> Dict[str, ModuleValidationResult]:
        """Generate per-module validation results."""
        module_results = {}
        
        for module_id in self.module_adapters.keys():
            # Get initialization status
            init_status = next(
                (s for s in self.initialization_statuses if s.module_id == module_id),
                None
            )
            
            # Determine module result based on failures and warnings
            module_failures = [
                f for f in self.critical_failures if f.module_id == module_id
            ]
            module_warnings = [
                w for w in self.warnings if w.module_id == module_id
            ]
            
            if module_failures:
                result = ValidationResult.FAIL
            elif module_warnings:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.PASS
            
            module_results[module_id] = ModuleValidationResult(
                module_id=module_id,
                module_name=init_status.module_name if init_status else module_id,
                result=result
            )
        
        return module_results
    
    def _generate_recommendations(
        self,
        category_results: Dict[ValidationCategory, CategoryResult]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for failures
        if self.critical_failures:
            recommendations.append(
                f"Address {len(self.critical_failures)} critical validation failures before using system"
            )
        
        # Check for warnings
        if self.warnings:
            recommendations.append(
                f"Review {len(self.warnings)} validation warnings"
            )
        
        # Category-specific recommendations
        for category, result in category_results.items():
            if result.result == ValidationResult.FAIL:
                recommendations.append(
                    f"Investigate failures in {category.value} validation"
                )
        
        # Data completeness recommendation
        if self.state_snapshots:
            avg_completeness = sum(
                s.integrity_indicators.data_completeness
                for s in self.state_snapshots
            ) / len(self.state_snapshots)
            
            if avg_completeness < 0.95:
                recommendations.append(
                    f"Improve data completeness (currently {avg_completeness:.2%})"
                )
        
        return recommendations
    
    def _record_failure(
        self,
        category: ValidationCategory,
        module_id: Optional[str],
        time_step: Optional[int],
        failure_type: str,
        description: str
    ) -> None:
        """Record a critical validation failure."""
        failure = ValidationFailure(
            severity=Severity.CRITICAL,
            category=category,
            module_id=module_id,
            time_step=time_step,
            failure_type=failure_type,
            description=description,
            affected_components=[module_id] if module_id else []
        )
        self.critical_failures.append(failure)
        logger.error(f"Validation failure: {description}")
    
    def _record_warning(
        self,
        category: ValidationCategory,
        module_id: Optional[str],
        time_step: Optional[int],
        warning_type: str,
        description: str
    ) -> None:
        """Record a validation warning."""
        warning = ValidationWarning(
            category=category,
            module_id=module_id,
            time_step=time_step,
            warning_type=warning_type,
            description=description
        )
        self.warnings.append(warning)
        logger.warning(f"Validation warning: {description}")
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID."""
        timestamp = datetime.now().isoformat()
        data = f"{timestamp}_{self.config.system_version}_{self.config.random_seed}"
        hash_obj = hashlib.sha256(data.encode())
        return f"validation_{hash_obj.hexdigest()[:12]}"
    
    def export_report_json(self, report: ValidationReport) -> str:
        """
        Export validation report as JSON.
        
        Args:
            report: Validation report to export
            
        Returns:
            JSON string representation
        """
        # Convert report to dictionary
        report_dict = self._report_to_dict(report)
        return json.dumps(report_dict, indent=2, default=str)
    
    def _report_to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert validation report to dictionary."""
        return {
            "report_id": report.report_id,
            "system_version": report.system_version,
            "validation_framework_version": report.validation_framework_version,
            "execution_timestamp": report.execution_timestamp.isoformat(),
            "random_seed": report.random_seed,
            "overall_result": report.overall_result.value,
            "category_results": {
                cat.value: self._category_result_to_dict(result)
                for cat, result in report.category_results.items()
            },
            "module_results": {
                module_id: self._module_result_to_dict(result)
                for module_id, result in report.module_results.items()
            },
            "critical_failures": [
                self._failure_to_dict(f) for f in report.critical_failures
            ],
            "warnings": [
                self._warning_to_dict(w) for w in report.warnings
            ],
            "recommendations": report.recommendations,
            "execution_summary": self._execution_summary_to_dict(report.execution_summary) if report.execution_summary else None,
        }
    
    def _category_result_to_dict(self, result: CategoryResult) -> Dict[str, Any]:
        """Convert category result to dictionary."""
        return {
            "category": result.category.value,
            "result": result.result.value,
            "tests_run": result.tests_run,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "tests_warned": result.tests_warned,
        }
    
    def _module_result_to_dict(self, result: ModuleValidationResult) -> Dict[str, Any]:
        """Convert module result to dictionary."""
        return {
            "module_id": result.module_id,
            "module_name": result.module_name,
            "result": result.result.value,
        }
    
    def _failure_to_dict(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Convert failure to dictionary."""
        return {
            "severity": failure.severity.value,
            "category": failure.category.value,
            "module_id": failure.module_id,
            "time_step": failure.time_step,
            "failure_type": failure.failure_type,
            "description": failure.description,
            "timestamp": failure.timestamp.isoformat(),
        }
    
    def _warning_to_dict(self, warning: ValidationWarning) -> Dict[str, Any]:
        """Convert warning to dictionary."""
        return {
            "category": warning.category.value,
            "module_id": warning.module_id,
            "time_step": warning.time_step,
            "warning_type": warning.warning_type,
            "description": warning.description,
            "timestamp": warning.timestamp.isoformat(),
        }
    
    def _execution_summary_to_dict(self, summary: ExecutionSummary) -> Dict[str, Any]:
        """Convert execution summary to dictionary."""
        return {
            "total_time_steps": summary.total_time_steps,
            "validation_start_time": summary.validation_start_time.isoformat(),
            "validation_end_time": summary.validation_end_time.isoformat(),
            "validation_duration_ms": summary.validation_duration_ms,
            "modules_validated": summary.modules_validated,
            "messages_validated": summary.messages_validated,
            "snapshots_analyzed": summary.snapshots_analyzed,
        }
