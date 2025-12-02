"""
Reporting utilities for validation results.

Provides functions to render validation results as human-readable
text and machine-readable dictionaries.
"""

from .checks import ValidationRunResult, CheckResult


def render_text_report(result: ValidationRunResult) -> str:
    """
    Render a human-readable text report from validation results.
    
    Args:
        result: ValidationRunResult to render
    
    Returns:
        Multi-line text report
    """
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append("VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Run and scenario information
    lines.append(f"Run ID: {result.run_id}")
    lines.append(f"Scenario ID: {result.scenario_id}")
    
    if "scenario_label" in result.metadata:
        lines.append(f"Scenario Label: {result.metadata['scenario_label']}")
    
    if result.metadata.get("notes"):
        lines.append(f"Notes: {result.metadata['notes']}")
    
    lines.append("")
    
    # Overall status
    status_marker = "✓ PASSED" if result.passed else "✗ FAILED"
    lines.append(f"Overall Status: {status_marker}")
    lines.append("")
    
    # Summary statistics
    total_checks = len(result.check_results)
    passed_checks = sum(1 for c in result.check_results if c.passed)
    failed_checks = total_checks - passed_checks
    
    lines.append(f"Total Checks: {total_checks}")
    lines.append(f"Passed: {passed_checks}")
    lines.append(f"Failed: {failed_checks}")
    lines.append("")
    
    # Check results by severity
    lines.append("-" * 70)
    lines.append("CHECK RESULTS")
    lines.append("-" * 70)
    lines.append("")
    
    # Group by severity
    errors = [c for c in result.check_results if c.severity == "ERROR"]
    warnings = [c for c in result.check_results if c.severity == "WARNING"]
    info = [c for c in result.check_results if c.severity == "INFO"]
    
    # Show errors first
    if errors:
        lines.append("ERRORS:")
        lines.append("")
        for check in errors:
            marker = "✗" if not check.passed else "✓"
            lines.append(f"  {marker} [{check.severity}] {check.check_id}")
            lines.append(f"     {check.message}")
            
            if check.details:
                details_str = ", ".join(f"{k}={v}" for k, v in check.details.items())
                lines.append(f"     Details: {details_str}")
            
            lines.append("")
    
    # Show warnings
    if warnings:
        lines.append("WARNINGS:")
        lines.append("")
        for check in warnings:
            marker = "✗" if not check.passed else "!"
            lines.append(f"  {marker} [{check.severity}] {check.check_id}")
            lines.append(f"     {check.message}")
            
            if check.details:
                details_str = ", ".join(f"{k}={v}" for k, v in check.details.items())
                lines.append(f"     Details: {details_str}")
            
            lines.append("")
    
    # Show info (only failures or if no errors/warnings)
    if info:
        if not errors and not warnings:
            lines.append("INFO:")
            lines.append("")
            for check in info:
                marker = "✓"
                lines.append(f"  {marker} [{check.severity}] {check.check_id}")
                lines.append(f"     {check.message}")
                lines.append("")
        else:
            # Just count info checks
            info_passed = sum(1 for c in info if c.passed)
            lines.append(f"INFO: {info_passed}/{len(info)} informational checks passed")
            lines.append("")
    
    # Footer
    lines.append("=" * 70)
    lines.append(f"END OF REPORT - {status_marker}")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def render_dict_report(result: ValidationRunResult) -> dict:
    """
    Render a machine-readable dictionary from validation results.
    
    This produces a stable structure suitable for JSON serialization
    and programmatic consumption.
    
    Args:
        result: ValidationRunResult to render
    
    Returns:
        Dictionary representation of validation results
    """
    # Calculate statistics
    total_checks = len(result.check_results)
    passed_checks = sum(1 for c in result.check_results if c.passed)
    failed_checks = total_checks - passed_checks
    
    # Group by severity
    by_severity = {
        "ERROR": [c.to_dict() for c in result.check_results if c.severity == "ERROR"],
        "WARNING": [c.to_dict() for c in result.check_results if c.severity == "WARNING"],
        "INFO": [c.to_dict() for c in result.check_results if c.severity == "INFO"],
    }
    
    return {
        "run_id": result.run_id,
        "scenario_id": result.scenario_id,
        "overall_status": "PASSED" if result.passed else "FAILED",
        "passed": result.passed,
        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
        },
        "checks_by_severity": {
            "errors": len(by_severity["ERROR"]),
            "warnings": len(by_severity["WARNING"]),
            "info": len(by_severity["INFO"]),
        },
        "check_results": [c.to_dict() for c in result.check_results],
        "check_results_by_severity": by_severity,
        "metadata": result.metadata,
    }
