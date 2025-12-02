# Module 10: Validation Framework

## Overview

The Validation Framework provides comprehensive validation infrastructure for the 3QP system. It validates structural integrity, data integrity, temporal consistency, deterministic reproducibility, inter-module integration, and computed metrics.

## Key Features

- **Structural Validation**: Verifies architectural compliance, module initialization, and configuration
- **Data Integrity Validation**: Ensures data consistency, completeness, and constraint satisfaction
- **Deterministic Reproducibility**: Confirms identical outputs across runs with same seed
- **Integration Validation**: Validates inter-module communication and contracts
- **Temporal Validation**: Ensures correct time-step progression and synchronization
- **Metric Validation**: Verifies computed metrics and statistical properties
- **Comprehensive Reporting**: Generates detailed reports in multiple formats (Markdown, JSON, text)

## Architecture

The validation framework follows a modular strategy pattern architecture:

```
ValidationOrchestrator
├── ValidationStrategies (one per category)
│   ├── StructuralValidationStrategy
│   ├── DataIntegrityValidationStrategy
│   ├── TemporalValidationStrategy
│   ├── MetricValidationStrategy
│   ├── IntegrationValidationStrategy
│   └── DeterminismValidationStrategy
├── ModuleValidationAdapters (one per module)
├── ReproducibilityManager
└── ReportGenerator
```

## Usage

### Basic Validation Workflow

```python
from validation import (
    ValidationConfiguration,
    ValidationOrchestrator,
    ValidationIntensity,
    ReportGenerator,
)

# Create configuration
config = ValidationConfiguration(
    system_version="my-system-v1.0",
    validation_framework_version="0.1.0",
    random_seed=12345,
    validation_intensity=ValidationIntensity.STANDARD
)

# Initialize orchestrator
orchestrator = ValidationOrchestrator(config)

# Register modules
orchestrator.register_module("module_01", my_module_01)
orchestrator.register_module("module_02", my_module_02)

# Run initialization validation
init_result = orchestrator.validate_initialization()

# Run time-step validation
for time_step in range(num_steps):
    # ... execute time step ...
    step_results = orchestrator.validate_time_step(time_step)

# Run post-execution validation
post_exec_results = orchestrator.validate_post_execution()

# Generate comprehensive report
all_results = {
    ValidationCategory.STRUCTURAL: init_result,
    **post_exec_results
}
report = orchestrator.generate_report(all_results)

# Export report
markdown_report = ReportGenerator.generate_markdown_report(report)
json_report = orchestrator.export_report_json(report)
```

### Implementing Validation Hooks

Modules can implement the `ValidationHooks` interface for better validation support:

```python
from validation import ValidationHooks, ModuleInitializationStatus, ModuleStateSnapshot

class MyModule(ValidationHooks):
    def validate_initialization(self) -> ModuleInitializationStatus:
        # Return initialization status
        return ModuleInitializationStatus(...)
    
    def validate_state(self) -> ModuleStateSnapshot:
        # Capture and return state snapshot
        return ModuleStateSnapshot(...)
    
    def validate_output(self, time_step: int) -> Dict[str, Any]:
        # Validate outputs for time step
        return {...}
    
    def get_consistency_signals(self) -> ConsistencySignals:
        # Return consistency indicators
        return ConsistencySignals(...)
    
    def get_integrity_metrics(self) -> IntegrityIndicators:
        # Return integrity metrics
        return IntegrityIndicators(...)
```

If modules don't implement `ValidationHooks`, the framework automatically uses `ModuleValidationAdapter` for basic validation.

### Reproducibility Testing

```python
from validation import ReproducibilityManager

# Create reproducibility manager
repro_manager = ReproducibilityManager(config)

# Define simulation runner
def run_simulation(seed):
    # Run simulation and return state snapshots
    return snapshots

# Execute reproducibility test
repro_result = repro_manager.execute_reproducibility_test(run_simulation)

# Generate certificate
certificate = repro_manager.generate_certificate(repro_result)

# Export certificate
cert_markdown = ReportGenerator.generate_certificate_markdown(certificate)
```

## Validation Categories

### Structural Validation
- Module initialization checks
- Configuration validation
- Schema conformance
- Interface compliance
- Dependency satisfaction

### Data Integrity Validation
- Constraint validation
- Referential integrity
- Completeness checks
- Consistency verification
- Corruption detection

### Deterministic Reproducibility
- Seed-based execution
- State snapshot comparison
- Output equivalence testing
- RNG validation

### Integration Validation
- Interface contract testing
- Message format validation
- Data flow verification
- Error propagation testing

### Temporal Validation
- Time-step sequencing
- State transition validation
- Event ordering
- Clock synchronization

### Metric Validation
- Metric definition verification
- Aggregation validation
- Statistical property checks
- Precision and accuracy testing

## Configuration Options

```python
ValidationConfiguration(
    system_version: str,                    # System version identifier
    validation_framework_version: str,      # Framework version
    random_seed: int,                       # Random seed for reproducibility
    determinism_check_enabled: bool,        # Enable determinism checks
    validation_intensity: ValidationIntensity,  # FULL, STANDARD, or LIGHTWEIGHT
    log_level: LogLevel,                    # VERBOSE, STANDARD, or MINIMAL
    time_step_validation_interval: int,     # How often to validate during execution
    snapshot_interval: int,                 # How often to capture snapshots
    reproducibility_run_count: int,         # Number of runs for reproducibility test
    acceptance_thresholds: Dict[ValidationCategory, Threshold]  # Custom thresholds
)
```

## Report Format

Validation reports include:

- **Executive Summary**: Overall result, key metrics
- **Category Results**: Detailed results for each validation category
- **Module Results**: Per-module validation status
- **Cross-Module Results**: Integration and consistency checks
- **Reproducibility Results**: Determinism verification (if applicable)
- **Critical Failures**: List of critical validation failures
- **Warnings**: Non-critical issues
- **Recommendations**: Actionable suggestions
- **Execution Summary**: Performance and timing information

## Running the Demo

```bash
cd modules/10_Validation
python demo.py
```

The demo demonstrates:
- Basic validation workflow
- Module registration
- Initialization validation
- Time-step validation
- Report generation in multiple formats
- Error detection

## Running Tests

```bash
cd modules/10_Validation
python -m pytest tests/
```

Or run tests directly:

```bash
python tests/test_validation.py
```

## Dependencies

The validation framework has **no external dependencies** and uses only Python standard library components, making it lightweight and portable.

## Integration with 3QP System

The validation framework integrates with the 3QP system through:

1. **Module Interface**: Modules can optionally implement `ValidationHooks`
2. **Event Bus**: Validation events can be published to the system event bus
3. **Logging System**: Validation logs integrate with Module 09 (Logging System)
4. **Orchestrator**: Validation can be triggered by the system orchestrator at appropriate lifecycle points

## Best Practices

1. **Run initialization validation** before starting simulation
2. **Validate at regular intervals** during execution (configure `time_step_validation_interval`)
3. **Always run post-execution validation** for comprehensive results
4. **Use reproducibility testing** for scientific applications
5. **Review validation reports** before using simulation results
6. **Address critical failures** immediately - they indicate serious issues
7. **Investigate warnings** - they may indicate potential problems
8. **Configure appropriate thresholds** for your use case

## Performance Considerations

- **Standard intensity** adds ~10% overhead to execution time
- **Lightweight intensity** adds <5% overhead (reduced checks)
- **Full intensity** adds ~25% overhead (comprehensive validation)
- Use **snapshot intervals** to control memory usage
- **Validation logs** can be large; configure log rotation for long runs

## Extensibility

The framework supports:
- Custom validation strategies (implement `ValidationStrategy`)
- Custom thresholds per category
- Module-specific validation hooks
- Custom report formats
- Plugin architecture for additional validation procedures

## Version

Current version: **0.1.0**

## License

Part of the 3QP system.
