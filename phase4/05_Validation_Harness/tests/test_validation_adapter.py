"""
Tests for validation adapter.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

from validation_harness.validation_adapter import (
    ExternalValidationClient,
    NoOpExternalValidationClient,
    get_default_validation_client,
    submit_run_for_external_validation,
)
from validation_harness.checks import CheckResult, ValidationRunResult


def test_noop_validation_client_creation():
    """Test creating NoOpExternalValidationClient."""
    client = NoOpExternalValidationClient()
    assert client is not None


def test_noop_validation_client_submit_does_not_raise():
    """Test that NoOpExternalValidationClient.submit_validation_outcome does not raise."""
    client = NoOpExternalValidationClient()
    
    # Should not raise any exception
    client.submit_validation_outcome({"test": "data"})


def test_get_default_validation_client():
    """Test getting default validation client."""
    client = get_default_validation_client()
    
    assert client is not None
    assert isinstance(client, NoOpExternalValidationClient)


def test_submit_run_for_external_validation_does_not_raise():
    """Test that submit_run_for_external_validation does not raise with NoOp client."""
    client = NoOpExternalValidationClient()
    
    result = ValidationRunResult(
        run_id="test_run",
        scenario_id="test_scenario",
        passed=True,
        check_results=[],
    )
    
    # Should not raise
    submit_run_for_external_validation(client, result)


def test_submit_run_calls_client():
    """Test that submit_run_for_external_validation calls the client's method."""
    
    class MockValidationClient:
        """Mock client to verify calls."""
        
        def __init__(self):
            self.called = False
            self.payload = None
        
        def submit_validation_outcome(self, payload: dict) -> None:
            self.called = True
            self.payload = payload
    
    client = MockValidationClient()
    
    result = ValidationRunResult(
        run_id="test_run",
        scenario_id="test_scenario",
        passed=True,
        check_results=[],
    )
    
    submit_run_for_external_validation(client, result)
    
    assert client.called is True
    assert client.payload is not None
    assert "run_id" in client.payload


def test_submit_run_includes_dict_report():
    """Test that submit_run_for_external_validation passes dict report to client."""
    
    class CapturingClient:
        """Client that captures payload."""
        
        def __init__(self):
            self.payload = None
        
        def submit_validation_outcome(self, payload: dict) -> None:
            self.payload = payload
    
    client = CapturingClient()
    
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed"),
    ]
    
    result = ValidationRunResult(
        run_id="test_run_789",
        scenario_id="test_scenario_abc",
        passed=False,
        check_results=checks,
    )
    
    submit_run_for_external_validation(client, result)
    
    # Verify payload structure
    assert client.payload["run_id"] == "test_run_789"
    assert client.payload["scenario_id"] == "test_scenario_abc"
    assert client.payload["passed"] is False
    assert "summary" in client.payload
    assert "check_results" in client.payload


def test_validation_client_protocol():
    """Test that custom clients can implement ExternalValidationClient protocol."""
    
    class CustomValidationClient:
        """Custom implementation of ExternalValidationClient."""
        
        def submit_validation_outcome(self, payload: dict) -> None:
            """Custom implementation."""
            pass
    
    client = CustomValidationClient()
    
    # Should work with submit_run_for_external_validation
    result = ValidationRunResult(
        run_id="test",
        scenario_id="test",
        passed=True,
        check_results=[],
    )
    
    # Should not raise
    submit_run_for_external_validation(client, result)


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_noop_validation_client_creation,
        test_noop_validation_client_submit_does_not_raise,
        test_get_default_validation_client,
        test_submit_run_for_external_validation_does_not_raise,
        test_submit_run_calls_client,
        test_submit_run_includes_dict_report,
        test_validation_client_protocol,
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
