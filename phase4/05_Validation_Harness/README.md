# Phase 4 / Workstream 5 – Validation Harness

End-to-end validation harness for Phase 4 stack (WS1–WS4).

## Overview

The Validation Harness provides orchestration and checking capabilities to validate that the Phase 4 architecture (Semantic Schema, State Encoding, Pattern Recognition, and Trajectory Analysis) functions correctly according to expected qualitative behaviors defined in Phase 3.

**Key Principle**: This is about verification and wiring, not computation. The harness exercises contracts, validates structural correctness, and checks for expected qualitative patterns without introducing any new behavioral logic.

## Purpose

- **Exercise the Phase 4 Stack**: Run encoded states through pattern recognition and trajectory analysis
- **Validate Contracts**: Ensure WS1-WS4 components meet their structural and interface requirements
- **Check Qualitative Expectations**: Verify that expected patterns and trajectories are recognized
- **Enable Future Integration**: Provide adapter layers for Module 09 (Logging) and Module 10 (Validation)

## Features

### ✓ Configuration Management
- Define validation scenarios with expected patterns and trajectories
- Support required vs. optional expectations
- Serialize and deserialize configurations

### ✓ Synthetic Fixtures
- Three canonical test scenarios:
  - `stable_adaptation_case`: Stable patterns with minimal drift
  - `gradual_drift_case`: Progressive parameter drift
  - `third_quarter_signature_case`: Disruption-recovery pattern
- Pre-built encoded states, pattern results, and trajectory classifications
- Aligned with Phase 3 baseline states and reference patterns

### ✓ Qualitative Validation Checks
- Pattern presence verification (required and optional)
- Trajectory archetype matching
- Structural validation using WS3/WS4 validators
- Enforcement of qualitative-only constraints (no numeric scoring)

### ✓ Reporting
- Human-readable text reports
- Machine-readable dictionary/JSON reports
- Summary statistics and severity grouping

### ✓ Adapter Layers
- Protocol-based logging integration (Module 09)
- Protocol-based validation integration (Module 10)
- No-op implementations for standalone operation

## Installation

No installation required. This module uses Python standard library only.

To use in your code:

```python
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path("path/to/phase4/05_Validation_Harness")))

from validation_harness import run_validation, ValidationRunConfig
from validation_harness.fixtures import get_fixture_scenarios
```

## Usage

### Running a Validation

```python
from validation_harness import run_validation, ValidationRunConfig
from validation_harness.fixtures import get_fixture_scenarios

# Get available scenarios
scenarios = get_fixture_scenarios()
stable_scenario = scenarios[0]  # stable_adaptation_case

# Create run configuration
run_config = ValidationRunConfig(
    run_id="my_validation_run_001",
    scenario=stable_scenario,
    notes="Testing stable adaptation patterns",
)

# Run validation
result = run_validation(run_config)

# Check results
print(result.summary())
print(f"Passed: {result.passed}")
print(f"Checks run: {len(result.check_results)}")
```

### Generating Reports

```python
from validation_harness import run_validation, render_text_report, render_dict_report

# ... run validation as above ...

# Generate human-readable report
text_report = render_text_report(result)
print(text_report)

# Generate machine-readable report
dict_report = render_dict_report(result)

# Can be saved as JSON
import json
with open("validation_report.json", "w") as f:
    json.dump(dict_report, f, indent=2)
```

### Using Custom Scenarios

```python
from validation_harness import (
    ValidationRunConfig,
    ValidationScenarioConfig,
    ExpectedPattern,
    ExpectedTrajectory,
)

# Define custom scenario
custom_scenario = ValidationScenarioConfig(
    scenario_id="custom_test",
    label="Custom Test Scenario",
    description="Testing custom patterns",
    expected_patterns=[
        ExpectedPattern(
            pattern_type="my_pattern",
            required=True,
            description="Expected to see my_pattern",
        ),
    ],
    expected_trajectories=[
        ExpectedTrajectory(
            archetype_id="my_trajectory",
            required=True,
            description="Expected trajectory archetype",
        ),
    ],
)

# Note: You'll need to add corresponding fixture data
# in fixtures.py to use custom scenarios
```

### Integration with Logging

```python
from validation_harness.logging_adapter import (
    get_default_logging_client,
    log_run_result,
)

# Get logging client (currently no-op)
logging_client = get_default_logging_client()

# Run validation
result = run_validation(run_config)

# Log the result
log_run_result(logging_client, result)
```

### Integration with External Validation

```python
from validation_harness.validation_adapter import (
    get_default_validation_client,
    submit_run_for_external_validation,
)

# Get validation client (currently no-op)
validation_client = get_default_validation_client()

# Run validation
result = run_validation(run_config)

# Submit to external validation system
submit_run_for_external_validation(validation_client, result)
```

## Architecture Constraints

**Hard Constraints (DO NOT VIOLATE)**:
- ✓ Python standard library only
- ✓ No ML, statistics, or numeric scoring
- ✓ No probabilities or confidence values
- ✓ Qualitative/categorical data only
- ✓ No modification of WS1-WS4 or existing modules

**Design Principles**:
- Uses existing WS3/WS4 validators for structural checks
- Fixtures use real dataclasses from pattern_recognition and trajectory_analysis
- All checks are existence-based or categorical
- Protocol-based adapters for future extensibility

## Available Scenarios

### 1. stable_adaptation_case
- **Description**: Demonstrates stable adaptation patterns with minimal drift
- **Expected Patterns**: `stable_pattern` (required)
- **Expected Trajectories**: `stable_adaptation` (required)
- **Phase 3 Reference**: baseline_state_01

### 2. gradual_drift_case
- **Description**: Shows gradual drift away from baseline
- **Expected Patterns**: `drift_pattern` (required)
- **Expected Trajectories**: `gradual_drift` (required)
- **Phase 3 Reference**: scenario_02_drift

### 3. third_quarter_signature_case
- **Description**: Exhibits characteristic third-quarter performance pattern
- **Expected Patterns**: `disruption_pattern` (required), `recovery_pattern` (required)
- **Expected Trajectories**: `third_quarter_signature` (required)
- **Phase 3 Reference**: cross_module_thread_3Q

## Testing

Run tests from the `tests/` directory:

```powershell
# Run individual test files
python tests/test_config.py
python tests/test_fixtures.py
python tests/test_checks.py
python tests/test_pipeline.py
python tests/test_reporting.py
python tests/test_logging_adapter.py
python tests/test_validation_adapter.py
```

All tests use only Python standard library and include built-in test runners.

## Extension Points

### Adding New Scenarios

1. Create scenario config in `fixtures.py` (`_create_*_scenario()`)
2. Build fixture data in `fixtures.py` (`_build_*_fixture()`)
3. Add to `get_fixture_scenarios()` and `get_fixture_for_scenario()`
4. Add corresponding tests in `tests/test_fixtures.py`

### Integrating with Module 09 (Logging)

Update `logging_adapter.py`:

```python
def get_default_logging_client() -> LoggingClient:
    try:
        from modules.09_Logging_System.logging_system import create_logger
        logger = create_logger("validation_harness")
        return RealLoggingClient(logger)
    except ImportError:
        return NoOpLoggingClient()
```

### Integrating with Module 10 (Validation)

Update `validation_adapter.py`:

```python
def get_default_validation_client() -> ExternalValidationClient:
    try:
        from modules.10_Validation.validation import ValidationEngine
        engine = ValidationEngine()
        return RealValidationClient(engine)
    except ImportError:
        return NoOpExternalValidationClient()
```

## Files and Modules

```
validation_harness/
├── __init__.py              # Public API exports
├── config.py                # Configuration dataclasses
├── fixtures.py              # Synthetic test fixtures
├── checks.py                # Validation check implementations
├── pipeline.py              # Orchestration logic
├── reporting.py             # Report generation
├── logging_adapter.py       # Module 09 integration (stub)
└── validation_adapter.py    # Module 10 integration (stub)

tests/
├── test_config.py
├── test_fixtures.py
├── test_checks.py
├── test_pipeline.py
├── test_reporting.py
├── test_logging_adapter.py
└── test_validation_adapter.py
```

## License

Part of the 3QP (Third Quarter Phenomenon) project.
