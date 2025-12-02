"""
Tests for logging adapter.
"""

import sys
from pathlib import Path

# Add validation_harness to path
harness_path = Path(__file__).parent.parent
sys.path.insert(0, str(harness_path))

from validation_harness.logging_adapter import (
    LoggingClient,
    NoOpLoggingClient,
    get_default_logging_client,
    log_run_result,
)
from validation_harness.checks import CheckResult, ValidationRunResult


def test_noop_logging_client_creation():
    """Test creating NoOpLoggingClient."""
    client = NoOpLoggingClient()
    assert client is not None


def test_noop_logging_client_log_does_not_raise():
    """Test that NoOpLoggingClient.log_validation_result does not raise."""
    client = NoOpLoggingClient()
    
    # Should not raise any exception
    client.log_validation_result({"test": "data"})


def test_get_default_logging_client():
    """Test getting default logging client."""
    client = get_default_logging_client()
    
    assert client is not None
    assert isinstance(client, NoOpLoggingClient)


def test_log_run_result_does_not_raise():
    """Test that log_run_result does not raise with NoOp client."""
    client = NoOpLoggingClient()
    
    result = ValidationRunResult(
        run_id="test_run",
        scenario_id="test_scenario",
        passed=True,
        check_results=[],
    )
    
    # Should not raise
    log_run_result(client, result)


def test_log_run_result_calls_client():
    """Test that log_run_result calls the client's method."""
    
    class MockLoggingClient:
        """Mock client to verify calls."""
        
        def __init__(self):
            self.called = False
            self.payload = None
        
        def log_validation_result(self, payload: dict) -> None:
            self.called = True
            self.payload = payload
    
    client = MockLoggingClient()
    
    result = ValidationRunResult(
        run_id="test_run",
        scenario_id="test_scenario",
        passed=True,
        check_results=[],
    )
    
    log_run_result(client, result)
    
    assert client.called is True
    assert client.payload is not None
    assert "run_id" in client.payload


def test_log_run_result_includes_dict_report():
    """Test that log_run_result passes dict report to client."""
    
    class CapturingClient:
        """Client that captures payload."""
        
        def __init__(self):
            self.payload = None
        
        def log_validation_result(self, payload: dict) -> None:
            self.payload = payload
    
    client = CapturingClient()
    
    checks = [
        CheckResult("check1", True, "INFO", "Passed"),
        CheckResult("check2", False, "ERROR", "Failed"),
    ]
    
    result = ValidationRunResult(
        run_id="test_run_123",
        scenario_id="test_scenario_456",
        passed=False,
        check_results=checks,
    )
    
    log_run_result(client, result)
    
    # Verify payload structure
    assert client.payload["run_id"] == "test_run_123"
    assert client.payload["scenario_id"] == "test_scenario_456"
    assert client.payload["passed"] is False
    assert "summary" in client.payload
    assert "check_results" in client.payload


def test_logging_client_protocol():
    """Test that custom clients can implement LoggingClient protocol."""
    
    class CustomLoggingClient:
        """Custom implementation of LoggingClient."""
        
        def log_validation_result(self, payload: dict) -> None:
            """Custom implementation."""
            pass
    
    client = CustomLoggingClient()
    
    # Should work with log_run_result
    result = ValidationRunResult(
        run_id="test",
        scenario_id="test",
        passed=True,
        check_results=[],
    )
    
    # Should not raise
    log_run_result(client, result)


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_noop_logging_client_creation,
        test_noop_logging_client_log_does_not_raise,
        test_get_default_logging_client,
        test_log_run_result_does_not_raise,
        test_log_run_result_calls_client,
        test_log_run_result_includes_dict_report,
        test_logging_client_protocol,
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
