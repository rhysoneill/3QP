"""
Basic example of using the validation framework.

This example shows the minimal setup needed to validate a simple module.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import (
    ValidationConfiguration,
    ValidationOrchestrator,
    ValidationIntensity,
    LogLevel,
    ReportGenerator,
)


class SimpleModule:
    """A simple example module."""
    
    def __init__(self, name):
        self.name = name
        self.counter = 0
    
    def update(self):
        """Update the module state."""
        self.counter += 1


def main():
    """Run basic validation example."""
    
    # Step 1: Create validation configuration
    config = ValidationConfiguration(
        system_version="example-v1.0",
        validation_framework_version="0.1.0",
        random_seed=42,
        validation_intensity=ValidationIntensity.STANDARD,
        log_level=LogLevel.STANDARD
    )
    
    # Step 2: Create orchestrator
    orchestrator = ValidationOrchestrator(config)
    
    # Step 3: Create and register modules
    module_a = SimpleModule("Module A")
    module_b = SimpleModule("Module B")
    
    orchestrator.register_module("module_a", module_a)
    orchestrator.register_module("module_b", module_b)
    
    # Step 4: Run full validation
    report = orchestrator.run_full_validation()
    
    # Step 5: Display results
    print(f"Validation Result: {report.overall_result.value}")
    print(f"Modules Validated: {len(report.module_results)}")
    print(f"Critical Failures: {len(report.critical_failures)}")
    print(f"Warnings: {len(report.warnings)}")
    
    # Step 6: Generate and save report
    markdown_report = ReportGenerator.generate_markdown_report(report)
    
    output_path = Path(__file__).parent / "example_report.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
