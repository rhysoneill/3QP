"""
Tests for reporting functionality.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

from validation_harness.reporting import render_text_report, render_dict_report
from validation_harness.checks import CheckResult, ValidationRunResult


def test_render_text_report_basic():
    """Test rendering a basic text report."""
    checks = [
        CheckResult("check1", True, "INFO", "Check 1 passed"),
        CheckResult("check2", True, "INFO", "Check 2 passed"),
    ]
    
    result = ValidationRunResult(
        run_id="run_001",
        scenario_id="test_scenario",
        passed=True,
        check_results=checks,
        metadata={"scenario_label": "Test Scenario"},
    )
    
    report = render_text_report(result)
    
    assert isinstance(report, str)
    assert "run_001" in report
    assert "test_scenario" in report
    assert "PASSED" in report


def test_render_text_report_with_failures():
    """Test rendering a text report with failures."""
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed check"),
        CheckResult("check3", False, "WARNING", "Warning"),
    ]
    
    result = ValidationRunResult(
        run_id="run_002",
        scenario_id="failing_scenario",
        passed=False,
        check_results=checks,
    )
    
    report = render_text_report(result)
    
    assert "FAILED" in report
    assert "Failed check" in report
    assert "ERROR" in report
    assert "WARNING" in report


def test_render_text_report_includes_details():
    """Test that text report includes check details."""
    checks = [
        CheckResult(
            "check1",
            False,
            "ERROR",
            "Pattern missing",
            details={"pattern_type": "stable_pattern", "required": "True"},
        ),
    ]
    
    result = ValidationRunResult(
        run_id="run_003",
        scenario_id="test",
        passed=False,
        check_results=checks,
    )
    
    report = render_text_report(result)
    
    assert "Details:" in report
    assert "pattern_type=stable_pattern" in report


def test_render_text_report_includes_notes():
    """Test that text report includes notes."""
    result = ValidationRunResult(
        run_id="run_004",
        scenario_id="test",
        passed=True,
        check_results=[],
        metadata={"notes": "Important test run"},
    )
    
    report = render_text_report(result)
    
    assert "Important test run" in report


def test_render_dict_report_structure():
    """Test that dict report has expected structure."""
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed"),
    ]
    
    result = ValidationRunResult(
        run_id="run_005",
        scenario_id="test_scenario",
        passed=False,
        check_results=checks,
    )
    
    report = render_dict_report(result)
    
    assert isinstance(report, dict)
    assert report["run_id"] == "run_005"
    assert report["scenario_id"] == "test_scenario"
    assert report["passed"] is False
    assert "summary" in report
    assert "check_results" in report


def test_render_dict_report_summary():
    """Test that dict report includes correct summary."""
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed"),
        CheckResult("check3", True, "INFO", "Passed"),
    ]
    
    result = ValidationRunResult(
        run_id="run_006",
        scenario_id="test",
        passed=False,
        check_results=checks,
    )
    
    report = render_dict_report(result)
    
    assert report["summary"]["total_checks"] == 3
    assert report["summary"]["passed_checks"] == 2
    assert report["summary"]["failed_checks"] == 1


def test_render_dict_report_by_severity():
    """Test that dict report groups checks by severity."""
    checks = [
        CheckResult("check1", True, "INFO", "Info check"),
        CheckResult("check2", False, "ERROR", "Error check"),
        CheckResult("check3", False, "WARNING", "Warning check"),
        CheckResult("check4", True, "INFO", "Another info"),
    ]
    
    result = ValidationRunResult(
        run_id="run_007",
        scenario_id="test",
        passed=False,
        check_results=checks,
    )
    
    report = render_dict_report(result)
    
    assert "checks_by_severity" in report
    assert report["checks_by_severity"]["errors"] == 1
    assert report["checks_by_severity"]["warnings"] == 1
    assert report["checks_by_severity"]["info"] == 2
    
    assert "check_results_by_severity" in report
    assert len(report["check_results_by_severity"]["ERROR"]) == 1
    assert len(report["check_results_by_severity"]["WARNING"]) == 1
    assert len(report["check_results_by_severity"]["INFO"]) == 2


def test_render_dict_report_includes_metadata():
    """Test that dict report includes metadata."""
    result = ValidationRunResult(
        run_id="run_008",
        scenario_id="test",
        passed=True,
        check_results=[],
        metadata={"key": "value", "scenario_label": "Test"},
    )
    
    report = render_dict_report(result)
    
    assert "metadata" in report
    assert report["metadata"]["key"] == "value"
    assert report["metadata"]["scenario_label"] == "Test"


def test_render_dict_report_overall_status():
    """Test that dict report includes overall status."""
    result_passed = ValidationRunResult(
        run_id="run_009",
        scenario_id="test",
        passed=True,
        check_results=[],
    )
    
    result_failed = ValidationRunResult(
        run_id="run_010",
        scenario_id="test",
        passed=False,
        check_results=[],
    )
    
    report_passed = render_dict_report(result_passed)
    report_failed = render_dict_report(result_failed)
    
    assert report_passed["overall_status"] == "PASSED"
    assert report_failed["overall_status"] == "FAILED"


def test_render_dict_report_serializable():
    """Test that dict report can be converted to JSON-like structures."""
    import json
    
    checks = [
        CheckResult("check1", True, "INFO", "Passed", {"detail": "value"}),
    ]
    
    result = ValidationRunResult(
        run_id="run_011",
        scenario_id="test",
        passed=True,
        check_results=checks,
        metadata={"key": "value"},
    )
    
    report = render_dict_report(result)
    
    # Should be JSON-serializable
    json_str = json.dumps(report)
    assert isinstance(json_str, str)
    
    # Should round-trip
    restored = json.loads(json_str)
    assert restored["run_id"] == "run_011"


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_render_text_report_basic,
        test_render_text_report_with_failures,
        test_render_text_report_includes_details,
        test_render_text_report_includes_notes,
        test_render_dict_report_structure,
        test_render_dict_report_summary,
        test_render_dict_report_by_severity,
        test_render_dict_report_includes_metadata,
        test_render_dict_report_overall_status,
        test_render_dict_report_serializable,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
