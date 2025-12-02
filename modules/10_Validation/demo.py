"""
Demo script for Module 10: Validation Framework

Demonstrates the validation framework capabilities including:
- Module registration and validation
- Initialization validation
- State snapshot validation
- Report generation
"""

import sys
from pathlib import Path

# Add parent directory to path to import validation module
module_path = Path(__file__).parent
sys.path.insert(0, str(module_path))

from datetime import datetime
from validation import (
    ValidationConfiguration,
    ValidationOrchestrator,
    ValidationIntensity,
    LogLevel,
    ModuleValidationAdapter,
    ReportGenerator,
    ValidationCategory,
    Threshold,
)


# Mock module for demonstration
class MockModule:
    """Simple mock module for demonstration purposes."""
    
    def __init__(self, module_id: str, has_errors: bool = False):
        self.module_id = module_id
        self.has_errors = has_errors
        self.state = {
            "value_a": 42,
            "value_b": 3.14,
            "timestamp": datetime.now().isoformat(),
        }
    
    def update(self, *args, **kwargs):
        """Mock update method."""
        if self.has_errors:
            raise ValueError("Simulated error")
        self.state["value_a"] += 1
        return {}


def create_validation_config() -> ValidationConfiguration:
    """Create validation configuration for demo."""
    print("Creating validation configuration...")
    
    config = ValidationConfiguration(
        system_version="3QP-demo-v0.1.0",
        validation_framework_version="0.1.0",
        random_seed=12345,
        determinism_check_enabled=True,
        validation_intensity=ValidationIntensity.STANDARD,
        log_level=LogLevel.STANDARD,
        time_step_validation_interval=1,
        snapshot_interval=5,
        reproducibility_run_count=2,
        acceptance_thresholds={
            ValidationCategory.STRUCTURAL: Threshold(
                critical_failure_limit=0,
                warning_limit=5,
                precision_tolerance=1e-6
            ),
            ValidationCategory.DATA_INTEGRITY: Threshold(
                critical_failure_limit=0,
                warning_limit=10,
                precision_tolerance=1e-6
            ),
        }
    )
    
    print(f"  System version: {config.system_version}")
    print(f"  Random seed: {config.random_seed}")
    print(f"  Validation intensity: {config.validation_intensity.value}")
    print()
    
    return config


def demo_basic_validation():
    """Demonstrate basic validation workflow."""
    print("=" * 80)
    print("DEMO: Basic Validation Workflow")
    print("=" * 80)
    print()
    
    # Create configuration
    config = create_validation_config()
    
    # Create orchestrator
    print("Initializing validation orchestrator...")
    orchestrator = ValidationOrchestrator(config)
    print()
    
    # Create and register mock modules
    print("Registering modules...")
    modules = {
        "module_01": MockModule("module_01", has_errors=False),
        "module_02": MockModule("module_02", has_errors=False),
        "module_03": MockModule("module_03", has_errors=False),
    }
    
    for module_id, module_instance in modules.items():
        orchestrator.register_module(module_id, module_instance)
        print(f"  Registered: {module_id}")
    
    print()
    
    # Run initialization validation
    print("Running initialization validation...")
    init_result = orchestrator.validate_initialization()
    print(f"  Result: {init_result.result.value}")
    print(f"  Tests run: {init_result.tests_run}")
    print(f"  Tests passed: {init_result.tests_passed}")
    print()
    
    # Simulate time steps with state snapshots
    print("Simulating time steps...")
    for time_step in range(1, 11):
        print(f"  Time step {time_step}")
        
        # Update module states
        for module in modules.values():
            module.update()
        
        # Validate time step (only at intervals)
        if time_step % config.time_step_validation_interval == 0:
            step_results = orchestrator.validate_time_step(time_step)
            for category, result in step_results.items():
                print(f"    {category.value}: {result.result.value}")
    
    print()
    
    # Run post-execution validation
    print("Running post-execution validation...")
    post_exec_results = orchestrator.validate_post_execution()
    print("  Category results:")
    for category, result in post_exec_results.items():
        print(f"    {category.value}: {result.result.value} "
              f"({result.tests_passed}/{result.tests_run} tests passed)")
    print()
    
    # Generate report
    print("Generating validation report...")
    all_results = {
        ValidationCategory.STRUCTURAL: init_result,
        **post_exec_results
    }
    
    report = orchestrator.generate_report(all_results)
    
    print(f"  Report ID: {report.report_id}")
    print(f"  Overall result: {report.overall_result.value}")
    print(f"  Critical failures: {len(report.critical_failures)}")
    print(f"  Warnings: {len(report.warnings)}")
    print()
    
    # Generate formatted reports
    print("Generating formatted reports...")
    
    # Markdown report
    md_report = ReportGenerator.generate_markdown_report(report)
    md_path = module_path / "demo_validation_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"  Markdown report saved to: {md_path}")
    
    # Text report
    text_report = ReportGenerator.generate_text_report(report)
    text_path = module_path / "demo_validation_report.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"  Text report saved to: {text_path}")
    
    # JSON export
    json_report = orchestrator.export_report_json(report)
    json_path = module_path / "demo_validation_report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_report)
    print(f"  JSON report saved to: {json_path}")
    
    print()
    
    return report


def demo_error_detection():
    """Demonstrate error detection capabilities."""
    print("=" * 80)
    print("DEMO: Error Detection")
    print("=" * 80)
    print()
    
    # Create configuration
    config = create_validation_config()
    
    # Create orchestrator
    orchestrator = ValidationOrchestrator(config)
    
    # Register modules with one having errors
    print("Registering modules (one with simulated errors)...")
    modules = {
        "good_module": MockModule("good_module", has_errors=False),
        "error_module": MockModule("error_module", has_errors=False),  # Will fail later
    }
    
    for module_id, module_instance in modules.items():
        orchestrator.register_module(module_id, module_instance)
        print(f"  Registered: {module_id}")
    
    print()
    
    # Run initialization validation
    print("Running initialization validation...")
    init_result = orchestrator.validate_initialization()
    print(f"  Result: {init_result.result.value}")
    print()
    
    # Simulate error by corrupting module state
    print("Simulating data corruption in error_module...")
    modules["error_module"].state["value_a"] = None  # Invalid state
    print()
    
    # Run validation
    print("Running validation with corrupted data...")
    step_results = orchestrator.validate_time_step(1)
    
    for category, result in step_results.items():
        print(f"  {category.value}: {result.result.value}")
        if result.result.value != "PASS":
            for test in result.details:
                if test.result.value != "PASS":
                    print(f"    - {test.test_name}: {test.message}")
    
    print()
    
    # Generate report
    print("Generating error report...")
    all_results = {
        ValidationCategory.STRUCTURAL: init_result,
        **step_results
    }
    
    report = orchestrator.generate_report(all_results)
    
    print(f"  Overall result: {report.overall_result.value}")
    print(f"  Critical failures: {len(report.critical_failures)}")
    print(f"  Warnings: {len(report.warnings)}")
    
    if report.warnings:
        print("\n  Warnings:")
        for warning in report.warnings[:3]:  # Show first 3
            print(f"    - {warning.warning_type}: {warning.description}")
    
    print()


def demo_summary():
    """Display demo summary."""
    print("=" * 80)
    print("VALIDATION FRAMEWORK DEMO COMPLETE")
    print("=" * 80)
    print()
    print("This demonstration showed:")
    print("  ✓ Configuration and initialization")
    print("  ✓ Module registration with validation hooks")
    print("  ✓ Initialization validation")
    print("  ✓ Time-step validation")
    print("  ✓ Post-execution validation")
    print("  ✓ Report generation in multiple formats")
    print("  ✓ Error and warning detection")
    print()
    print("The validation framework provides comprehensive validation")
    print("of structural integrity, data integrity, temporal consistency,")
    print("and other critical aspects of the 3QP system.")
    print()
    print("Review the generated reports for detailed validation results.")
    print("=" * 80)


def main():
    """Main demo function."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "3QP VALIDATION FRAMEWORK DEMONSTRATION".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    try:
        # Run basic validation demo
        report = demo_basic_validation()
        
        # Run error detection demo
        demo_error_detection()
        
        # Show summary
        demo_summary()
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
