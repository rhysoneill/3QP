"""
Report generator for validation results.

Generates human-readable validation reports in various formats.
"""

from typing import TextIO
from datetime import datetime

from .types import (
    ValidationReport,
    ValidationResult,
    ValidationCategory,
    ReproducibilityCertificate,
)


class ReportGenerator:
    """
    Generates human-readable validation reports.
    
    Supports multiple output formats including Markdown and plain text.
    """
    
    @staticmethod
    def generate_markdown_report(report: ValidationReport) -> str:
        """
        Generate validation report in Markdown format.
        
        Args:
            report: Validation report to format
            
        Returns:
            Markdown-formatted report string
        """
        lines = []
        
        # Title and metadata
        lines.append("# Validation Report")
        lines.append("")
        lines.append(f"**Report ID:** `{report.report_id}`")
        lines.append(f"**System Version:** {report.system_version}")
        lines.append(f"**Validation Framework Version:** {report.validation_framework_version}")
        lines.append(f"**Execution Timestamp:** {report.execution_timestamp.isoformat()}")
        lines.append(f"**Random Seed:** {report.random_seed}")
        lines.append("")
        
        # Overall result
        result_emoji = {
            ValidationResult.PASS: "✅",
            ValidationResult.WARNING: "⚠️",
            ValidationResult.FAIL: "❌"
        }
        
        lines.append("## Overall Result")
        lines.append("")
        lines.append(
            f"**{result_emoji.get(report.overall_result, '❓')} "
            f"{report.overall_result.value}**"
        )
        lines.append("")
        
        # Executive summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Critical Failures:** {len(report.critical_failures)}")
        lines.append(f"- **Warnings:** {len(report.warnings)}")
        lines.append(f"- **Modules Validated:** {len(report.module_results)}")
        
        if report.execution_summary:
            lines.append(f"- **Time Steps:** {report.execution_summary.total_time_steps}")
            lines.append(f"- **Snapshots Analyzed:** {report.execution_summary.snapshots_analyzed}")
            lines.append(
                f"- **Validation Duration:** "
                f"{report.execution_summary.validation_duration_ms:.2f} ms"
            )
        
        lines.append("")
        
        # Category results
        lines.append("## Validation by Category")
        lines.append("")
        
        for category in ValidationCategory:
            if category in report.category_results:
                result = report.category_results[category]
                emoji = result_emoji.get(result.result, '❓')
                
                lines.append(f"### {emoji} {category.value}")
                lines.append("")
                lines.append(f"- **Result:** {result.result.value}")
                lines.append(f"- **Tests Run:** {result.tests_run}")
                lines.append(f"- **Tests Passed:** {result.tests_passed}")
                lines.append(f"- **Tests Failed:** {result.tests_failed}")
                lines.append(f"- **Tests Warned:** {result.tests_warned}")
                
                if result.details:
                    lines.append("")
                    lines.append("**Test Details:**")
                    lines.append("")
                    for test in result.details:
                        test_emoji = result_emoji.get(test.result, '❓')
                        lines.append(f"- {test_emoji} `{test.test_name}`: {test.message}")
                
                lines.append("")
        
        # Module results
        if report.module_results:
            lines.append("## Module Results")
            lines.append("")
            
            for module_id, module_result in sorted(report.module_results.items()):
                emoji = result_emoji.get(module_result.result, '❓')
                lines.append(
                    f"- {emoji} **{module_result.module_name}** "
                    f"(`{module_id}`): {module_result.result.value}"
                )
            
            lines.append("")
        
        # Critical failures
        if report.critical_failures:
            lines.append("## ❌ Critical Failures")
            lines.append("")
            
            for i, failure in enumerate(report.critical_failures, 1):
                lines.append(f"### Failure {i}: {failure.failure_type}")
                lines.append("")
                lines.append(f"- **Category:** {failure.category.value}")
                lines.append(f"- **Module:** {failure.module_id or 'System-wide'}")
                lines.append(f"- **Time Step:** {failure.time_step or 'N/A'}")
                lines.append(f"- **Severity:** {failure.severity.value}")
                lines.append(f"- **Description:** {failure.description}")
                lines.append(f"- **Timestamp:** {failure.timestamp.isoformat()}")
                lines.append("")
        
        # Warnings
        if report.warnings:
            lines.append("## ⚠️ Warnings")
            lines.append("")
            
            for i, warning in enumerate(report.warnings, 1):
                lines.append(f"{i}. **{warning.warning_type}** ({warning.category.value})")
                lines.append(f"   - Module: {warning.module_id or 'System-wide'}")
                lines.append(f"   - {warning.description}")
            
            lines.append("")
        
        # Reproducibility
        if report.reproducibility_result:
            lines.append("## Reproducibility")
            lines.append("")
            repro = report.reproducibility_result
            
            if repro.identical:
                lines.append("✅ **System is reproducible**")
                lines.append("")
                lines.append(f"All {repro.runs_compared} runs produced identical results.")
            else:
                lines.append("❌ **System is NOT reproducible**")
                lines.append("")
                lines.append(f"- Runs compared: {repro.runs_compared}")
                lines.append(f"- Divergence point: Time step {repro.divergence_point}")
                lines.append(f"- State differences: {len(repro.state_differences)}")
                lines.append(f"- Output differences: {len(repro.output_differences)}")
            
            lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Report generated at {datetime.now().isoformat()}*")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_text_report(report: ValidationReport) -> str:
        """
        Generate validation report in plain text format.
        
        Args:
            report: Validation report to format
            
        Returns:
            Plain text-formatted report string
        """
        lines = []
        
        # Title
        lines.append("=" * 80)
        lines.append("VALIDATION REPORT".center(80))
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        lines.append(f"Report ID: {report.report_id}")
        lines.append(f"System Version: {report.system_version}")
        lines.append(f"Validation Framework: {report.validation_framework_version}")
        lines.append(f"Timestamp: {report.execution_timestamp.isoformat()}")
        lines.append(f"Random Seed: {report.random_seed}")
        lines.append("")
        
        # Overall result
        lines.append("-" * 80)
        lines.append(f"OVERALL RESULT: {report.overall_result.value}")
        lines.append("-" * 80)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append(f"  Critical Failures: {len(report.critical_failures)}")
        lines.append(f"  Warnings: {len(report.warnings)}")
        lines.append(f"  Modules Validated: {len(report.module_results)}")
        
        if report.execution_summary:
            lines.append(f"  Time Steps: {report.execution_summary.total_time_steps}")
            lines.append(f"  Snapshots Analyzed: {report.execution_summary.snapshots_analyzed}")
        
        lines.append("")
        
        # Category results
        lines.append("VALIDATION BY CATEGORY:")
        lines.append("")
        
        for category in ValidationCategory:
            if category in report.category_results:
                result = report.category_results[category]
                lines.append(f"  {category.value}: {result.result.value}")
                lines.append(f"    Tests: {result.tests_passed}/{result.tests_run} passed")
                
                if result.tests_failed > 0:
                    lines.append(f"    Failures: {result.tests_failed}")
                if result.tests_warned > 0:
                    lines.append(f"    Warnings: {result.tests_warned}")
                
                lines.append("")
        
        # Critical failures
        if report.critical_failures:
            lines.append("CRITICAL FAILURES:")
            lines.append("")
            
            for i, failure in enumerate(report.critical_failures, 1):
                lines.append(f"  {i}. {failure.failure_type}")
                lines.append(f"     Category: {failure.category.value}")
                lines.append(f"     Module: {failure.module_id or 'System'}")
                lines.append(f"     Description: {failure.description}")
                lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def write_report_to_file(report: ValidationReport, filepath: str, format: str = "markdown") -> None:
        """
        Write validation report to file.
        
        Args:
            report: Validation report
            filepath: Output file path
            format: Output format ("markdown" or "text")
        """
        if format == "markdown":
            content = ReportGenerator.generate_markdown_report(report)
        elif format == "text":
            content = ReportGenerator.generate_text_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def generate_certificate_markdown(cert: ReproducibilityCertificate) -> str:
        """
        Generate reproducibility certificate in Markdown format.
        
        Args:
            cert: Reproducibility certificate
            
        Returns:
            Markdown-formatted certificate
        """
        lines = []
        
        lines.append("# Reproducibility Certificate")
        lines.append("")
        lines.append(f"**Certificate ID:** `{cert.certificate_id}`")
        lines.append(f"**System Version:** {cert.system_version}")
        lines.append(f"**Issued:** {cert.issue_timestamp.isoformat()}")
        lines.append("")
        
        # Status
        if cert.certificate_status == ValidationResult.PASS:
            lines.append("## ✅ CERTIFIED REPRODUCIBLE")
        else:
            lines.append("## ❌ NOT CERTIFIED")
        
        lines.append("")
        
        # Details
        lines.append("## Validation Details")
        lines.append("")
        lines.append(f"- **Random Seed:** {cert.random_seed}")
        lines.append(f"- **Runs Executed:** {cert.runs_executed}")
        lines.append(f"- **All Runs Identical:** {cert.all_runs_identical}")
        lines.append(f"- **State Hash Matches:** {cert.state_hash_matches}")
        lines.append(f"- **Output Hash Matches:** {cert.output_hash_matches}")
        lines.append(f"- **Precision Tolerance:** {cert.precision_tolerance}")
        lines.append(f"- **Max Observed Difference:** {cert.max_observed_difference}")
        lines.append("")
        
        # Validity conditions
        lines.append("## Validity Conditions")
        lines.append("")
        for condition in cert.validity_conditions:
            lines.append(f"- {condition}")
        lines.append("")
        
        # Notes
        if cert.notes:
            lines.append("## Notes")
            lines.append("")
            for note in cert.notes:
                lines.append(f"- {note}")
            lines.append("")
        
        lines.append("---")
        lines.append(f"*Certificate generated by 3QP Validation Framework v{cert.validation_framework_version}*")
        
        return "\n".join(lines)
