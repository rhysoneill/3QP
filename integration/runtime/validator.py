"""
Validator for Phase 5 Integration Harness

Validates that the Ruthless Core Model produces expected third quarter
patterns and writes validation results to output.

Uses Phase 4 trajectory classification to ensure TQP dip is detected correctly.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class TrajectoryValidator:
    """
    Validator for third quarter trajectory patterns.
    
    Checks that the simulation produces the expected TQP dynamics:
    - Cohesion minimum in third quarter range (50-90% mission progress)
    - TQ pressure peak aligned with cohesion minimum
    - Proper trajectory archetype classification
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize validator.
        
        Args:
            verbose: Whether to print validation details
        """
        self.verbose = verbose
    
    def validate(self, result) -> Dict[str, Any]:
        """
        Validate mission result for expected TQP patterns.
        
        Args:
            result: MissionResult object from mission_runner
            
        Returns:
            Validation result dictionary with checks and status
        """
        if self.verbose:
            print("[Validator] Running trajectory validation...")
        
        # Extract data
        cohesion = result.core_output.cohesion
        tq_pressure = result.core_output.tq_pressure
        days = result.core_output.days
        trajectory = result.trajectory_result
        
        mission_length = len(days)
        
        # Find cohesion minimum
        min_cohesion = min(cohesion)
        min_cohesion_idx = cohesion.index(min_cohesion)
        min_cohesion_day = days[min_cohesion_idx]
        min_cohesion_progress = min_cohesion_day / mission_length
        
        # Find TQ pressure peak
        max_tq = max(tq_pressure)
        max_tq_idx = tq_pressure.index(max_tq)
        max_tq_day = days[max_tq_idx]
        max_tq_progress = max_tq_day / mission_length
        
        # Run validation checks
        checks = []
        
        # Check 1: Cohesion minimum in third quarter range
        tq_range_check = self._check_tq_range(
            min_cohesion_progress,
            expected_min=0.50,
            expected_max=0.90
        )
        checks.append(tq_range_check)
        
        # Check 2: TQ pressure peak aligned with cohesion minimum
        alignment_check = self._check_peak_alignment(
            min_cohesion_day,
            max_tq_day,
            tolerance_days=40
        )
        checks.append(alignment_check)
        
        # Check 3: Trajectory archetype correct
        archetype_check = self._check_archetype(
            trajectory["archetype_id"],
            expected="third_quarter"
        )
        checks.append(archetype_check)
        
        # Check 4: Cohesion dip magnitude
        dip_check = self._check_cohesion_dip(
            initial=cohesion[0],
            minimum=min_cohesion,
            expected_dip_min=0.15
        )
        checks.append(dip_check)
        
        # Overall validation status
        all_passed = all(check["passed"] for check in checks)
        
        validation_result = {
            "mission_name": result.config.mission_name,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": "PASS" if all_passed else "FAIL",
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "passed": sum(1 for c in checks if c["passed"]),
                "failed": sum(1 for c in checks if not c["passed"]),
            },
            "metrics": {
                "cohesion_minimum": min_cohesion,
                "cohesion_minimum_day": min_cohesion_day,
                "cohesion_minimum_progress": min_cohesion_progress,
                "tq_pressure_peak": max_tq,
                "tq_pressure_peak_day": max_tq_day,
                "tq_pressure_peak_progress": max_tq_progress,
                "trajectory_archetype": trajectory["archetype_id"],
            }
        }
        
        if self.verbose:
            self._print_validation_summary(validation_result)
        
        return validation_result
    
    def _check_tq_range(self, progress: float, expected_min: float, expected_max: float) -> Dict[str, Any]:
        """Check if cohesion minimum is in expected third quarter range."""
        passed = expected_min <= progress <= expected_max
        return {
            "check_id": "tq_range",
            "description": "Cohesion minimum in third quarter range",
            "passed": passed,
            "expected": f"{expected_min:.0%} - {expected_max:.0%}",
            "actual": f"{progress:.1%}",
            "severity": "critical" if not passed else None,
        }
    
    def _check_peak_alignment(self, cohesion_day: int, tq_day: int, tolerance_days: int) -> Dict[str, Any]:
        """Check if TQ pressure peak is aligned with cohesion minimum."""
        difference = abs(cohesion_day - tq_day)
        passed = difference <= tolerance_days
        return {
            "check_id": "peak_alignment",
            "description": "TQ pressure peak aligned with cohesion minimum",
            "passed": passed,
            "expected": f"Within {tolerance_days} days",
            "actual": f"{difference} days difference",
            "severity": "warning" if not passed else None,
        }
    
    def _check_archetype(self, archetype: str, expected: str) -> Dict[str, Any]:
        """Check if trajectory archetype matches expected."""
        passed = archetype == expected
        return {
            "check_id": "archetype",
            "description": "Trajectory archetype classification",
            "passed": passed,
            "expected": expected,
            "actual": archetype,
            "severity": "critical" if not passed else None,
        }
    
    def _check_cohesion_dip(self, initial: float, minimum: float, expected_dip_min: float) -> Dict[str, Any]:
        """Check if cohesion dip is significant enough."""
        dip_magnitude = initial - minimum
        passed = dip_magnitude >= expected_dip_min
        return {
            "check_id": "cohesion_dip",
            "description": "Cohesion dip magnitude sufficient",
            "passed": passed,
            "expected": f"At least {expected_dip_min:.2f}",
            "actual": f"{dip_magnitude:.3f}",
            "severity": "warning" if not passed else None,
        }
    
    def _print_validation_summary(self, result: Dict[str, Any]):
        """Print validation summary to console."""
        print(f"[Validator] Overall status: {result['overall_status']}")
        print(f"[Validator] Checks: {result['summary']['passed']}/{result['summary']['total_checks']} passed")
        
        for check in result["checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"[Validator]   {status} {check['description']}: {check['actual']}")
    
    def write_validation_report(self, result: Dict[str, Any], output_path: Path):
        """
        Write validation result to JSON file.
        
        Args:
            result: Validation result dictionary
            output_path: Path to write validation report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        if self.verbose:
            print(f"[Validator] Validation report written to {output_path}")


def validate_mission_result(result, output_dir: str = "output", verbose: bool = True) -> Dict[str, Any]:
    """
    Convenience function to validate mission result and write report.
    
    Args:
        result: MissionResult object
        output_dir: Directory for validation report
        verbose: Whether to print progress
        
    Returns:
        Validation result dictionary
    """
    validator = TrajectoryValidator(verbose=verbose)
    validation_result = validator.validate(result)
    
    # Write report
    output_path = Path(output_dir) / f"{result.config.mission_name}_validation.json"
    validator.write_validation_report(validation_result, output_path)
    
    return validation_result
