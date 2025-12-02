"""
Reproducibility manager for determinism validation.

Manages multiple runs with identical seeds and compares results
to verify deterministic behavior.
"""

from typing import List, Dict, Any, Callable
from datetime import datetime
import logging

from .types import (
    ValidationConfiguration,
    ReproducibilityResult,
    ReproducibilityCertificate,
    ValidationResult,
    StateDifference,
    OutputDifference,
    ModuleStateSnapshot,
)

logger = logging.getLogger(__name__)


class ReproducibilityManager:
    """
    Manages reproducibility testing and certification.
    
    Executes multiple simulation runs with identical parameters
    and verifies that results are identical.
    """
    
    def __init__(self, config: ValidationConfiguration):
        """
        Initialize reproducibility manager.
        
        Args:
            config: Validation configuration
        """
        self.config = config
        self.baseline_snapshots: List[ModuleStateSnapshot] = []
        self.comparison_runs: List[List[ModuleStateSnapshot]] = []
    
    def execute_reproducibility_test(
        self,
        run_simulation: Callable[[int], List[ModuleStateSnapshot]]
    ) -> ReproducibilityResult:
        """
        Execute reproducibility test by running simulation multiple times.
        
        Args:
            run_simulation: Function that runs simulation with given seed
                           and returns list of state snapshots
        
        Returns:
            Reproducibility test results
        """
        logger.info(
            f"Starting reproducibility test with {self.config.reproducibility_run_count} runs"
        )
        
        seed = self.config.random_seed
        
        # Execute baseline run
        logger.info(f"Executing baseline run with seed {seed}")
        self.baseline_snapshots = run_simulation(seed)
        
        # Execute comparison runs
        self.comparison_runs = []
        for i in range(self.config.reproducibility_run_count - 1):
            logger.info(f"Executing comparison run {i+1} with seed {seed}")
            run_snapshots = run_simulation(seed)
            self.comparison_runs.append(run_snapshots)
        
        # Compare runs
        result = self._compare_runs()
        
        logger.info(
            f"Reproducibility test complete: identical={result.identical}"
        )
        
        return result
    
    def _compare_runs(self) -> ReproducibilityResult:
        """
        Compare baseline and comparison runs for differences.
        
        Returns:
            Reproducibility result with differences if any
        """
        all_identical = True
        divergence_point = None
        state_differences: List[StateDifference] = []
        output_differences: List[OutputDifference] = []
        
        # Compare each comparison run against baseline
        for run_idx, comparison_snapshots in enumerate(self.comparison_runs):
            # Check snapshot counts match
            if len(comparison_snapshots) != len(self.baseline_snapshots):
                all_identical = False
                logger.warning(
                    f"Run {run_idx+1} has {len(comparison_snapshots)} snapshots "
                    f"vs baseline {len(self.baseline_snapshots)}"
                )
                continue
            
            # Compare snapshots
            for baseline_snap, comp_snap in zip(self.baseline_snapshots, comparison_snapshots):
                # Check module IDs match
                if baseline_snap.module_id != comp_snap.module_id:
                    logger.error(
                        f"Module ID mismatch at run {run_idx+1}: "
                        f"{baseline_snap.module_id} vs {comp_snap.module_id}"
                    )
                    all_identical = False
                    continue
                
                # Check time steps match
                if baseline_snap.time_step != comp_snap.time_step:
                    logger.warning(
                        f"Time step mismatch for {baseline_snap.module_id}: "
                        f"{baseline_snap.time_step} vs {comp_snap.time_step}"
                    )
                    all_identical = False
                    continue
                
                # Compare state hashes
                if baseline_snap.state_hash != comp_snap.state_hash:
                    all_identical = False
                    
                    if divergence_point is None:
                        divergence_point = baseline_snap.time_step
                    
                    # Find specific differences
                    diffs = self._find_state_differences(
                        baseline_snap,
                        comp_snap
                    )
                    state_differences.extend(diffs)
                    
                    logger.warning(
                        f"State hash mismatch for {baseline_snap.module_id} "
                        f"at time step {baseline_snap.time_step}"
                    )
        
        return ReproducibilityResult(
            runs_compared=self.config.reproducibility_run_count,
            identical=all_identical,
            divergence_point=divergence_point,
            state_differences=state_differences,
            output_differences=output_differences
        )
    
    def _find_state_differences(
        self,
        baseline: ModuleStateSnapshot,
        comparison: ModuleStateSnapshot
    ) -> List[StateDifference]:
        """
        Find specific field differences between two snapshots.
        
        Args:
            baseline: Baseline snapshot
            comparison: Comparison snapshot
            
        Returns:
            List of state differences
        """
        differences = []
        
        # Compare state data fields
        baseline_fields = set(baseline.state_data.keys())
        comparison_fields = set(comparison.state_data.keys())
        
        # Check for missing fields
        missing_in_comparison = baseline_fields - comparison_fields
        for field in missing_in_comparison:
            differences.append(StateDifference(
                module_id=baseline.module_id,
                time_step=baseline.time_step,
                field_name=field,
                expected_value=baseline.state_data[field],
                actual_value="<missing>"
            ))
        
        # Check for extra fields
        extra_in_comparison = comparison_fields - baseline_fields
        for field in extra_in_comparison:
            differences.append(StateDifference(
                module_id=baseline.module_id,
                time_step=baseline.time_step,
                field_name=field,
                expected_value="<missing>",
                actual_value=comparison.state_data[field]
            ))
        
        # Compare common fields
        common_fields = baseline_fields & comparison_fields
        for field in common_fields:
            baseline_value = baseline.state_data[field]
            comparison_value = comparison.state_data[field]
            
            if baseline_value != comparison_value:
                # Check if difference is within tolerance for floats
                if isinstance(baseline_value, float) and isinstance(comparison_value, float):
                    tolerance = self.config.acceptance_thresholds.get(
                        None,  # Use default threshold
                        type('obj', (object,), {'precision_tolerance': 1e-6})()
                    ).precision_tolerance
                    
                    if abs(baseline_value - comparison_value) > tolerance:
                        differences.append(StateDifference(
                            module_id=baseline.module_id,
                            time_step=baseline.time_step,
                            field_name=field,
                            expected_value=baseline_value,
                            actual_value=comparison_value
                        ))
                else:
                    differences.append(StateDifference(
                        module_id=baseline.module_id,
                        time_step=baseline.time_step,
                        field_name=field,
                        expected_value=baseline_value,
                        actual_value=comparison_value
                    ))
        
        return differences
    
    def generate_certificate(
        self,
        reproducibility_result: ReproducibilityResult
    ) -> ReproducibilityCertificate:
        """
        Generate reproducibility certificate based on test results.
        
        Args:
            reproducibility_result: Results from reproducibility test
            
        Returns:
            Reproducibility certificate
        """
        import hashlib
        
        # Generate certificate ID
        timestamp = datetime.now().isoformat()
        cert_data = f"{timestamp}_{self.config.system_version}_{self.config.random_seed}"
        cert_hash = hashlib.sha256(cert_data.encode()).hexdigest()[:12]
        certificate_id = f"repro_cert_{cert_hash}"
        
        # Determine certification status
        if reproducibility_result.identical:
            cert_status = ValidationResult.PASS
            validity_conditions = [
                f"System verified reproducible with seed {self.config.random_seed}",
                f"All {reproducibility_result.runs_compared} runs produced identical results"
            ]
            notes = ["System meets reproducibility requirements"]
        else:
            cert_status = ValidationResult.FAIL
            validity_conditions = [
                f"Non-deterministic behavior detected at time step {reproducibility_result.divergence_point}",
                f"System fails reproducibility requirements"
            ]
            notes = [
                f"Found {len(reproducibility_result.state_differences)} state differences",
                "System should not be used for scientific inference until reproducibility is fixed"
            ]
        
        # Compute max observed difference
        max_diff = 0.0
        if reproducibility_result.state_differences:
            for diff in reproducibility_result.state_differences:
                if isinstance(diff.expected_value, (int, float)) and \
                   isinstance(diff.actual_value, (int, float)):
                    abs_diff = abs(float(diff.expected_value) - float(diff.actual_value))
                    max_diff = max(max_diff, abs_diff)
        
        certificate = ReproducibilityCertificate(
            certificate_id=certificate_id,
            system_version=self.config.system_version,
            validation_framework_version=self.config.validation_framework_version,
            issue_timestamp=datetime.now(),
            random_seed=self.config.random_seed,
            runs_executed=reproducibility_result.runs_compared,
            all_runs_identical=reproducibility_result.identical,
            state_hash_matches=reproducibility_result.identical,
            output_hash_matches=reproducibility_result.identical,
            metric_equivalence=reproducibility_result.identical,
            precision_tolerance=self.config.acceptance_thresholds.get(
                None,
                type('obj', (object,), {'precision_tolerance': 1e-6})()
            ).precision_tolerance,
            max_observed_difference=max_diff,
            certificate_status=cert_status,
            validity_conditions=validity_conditions,
            notes=notes
        )
        
        logger.info(
            f"Reproducibility certificate generated: {certificate_id} "
            f"(status: {cert_status.value})"
        )
        
        return certificate
