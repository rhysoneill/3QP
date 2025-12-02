"""
Unit tests for Module 10: Validation Framework

Tests validation types, strategies, orchestrator, and report generation.
"""

import unittest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.types import (
    ValidationConfiguration,
    ValidationIntensity,
    LogLevel,
    ValidationCategory,
    ValidationResult,
    Threshold,
    ModuleInitializationStatus,
    InitializationResult,
    ConsistencySignals,
    IntegrityIndicators,
    ModuleStateSnapshot,
)
from validation.validation_hooks import ModuleValidationAdapter
from validation.strategies import (
    StructuralValidationStrategy,
    DataIntegrityValidationStrategy,
    TemporalValidationStrategy,
)
from validation.orchestrator import ValidationOrchestrator
from validation.report_generator import ReportGenerator


class TestValidationTypes(unittest.TestCase):
    """Test validation type definitions."""
    
    def test_validation_configuration_valid(self):
        """Test creating valid validation configuration."""
        config = ValidationConfiguration(
            system_version="test-v1.0",
            validation_framework_version="0.1.0",
            random_seed=42,
            validation_intensity=ValidationIntensity.STANDARD,
            log_level=LogLevel.STANDARD
        )
        
        self.assertEqual(config.system_version, "test-v1.0")
        self.assertEqual(config.random_seed, 42)
        self.assertEqual(config.validation_intensity, ValidationIntensity.STANDARD)
    
    def test_validation_configuration_invalid_seed(self):
        """Test that negative seed raises error."""
        with self.assertRaises(ValueError):
            ValidationConfiguration(
                system_version="test",
                validation_framework_version="0.1.0",
                random_seed=-1
            )
    
    def test_integrity_indicators_valid(self):
        """Test creating valid integrity indicators."""
        indicators = IntegrityIndicators(
            data_completeness=0.95,
            corruption_detected=False,
            schema_compliance=True,
            null_field_count=0,
            out_of_range_count=0
        )
        
        self.assertEqual(indicators.data_completeness, 0.95)
        self.assertFalse(indicators.corruption_detected)
    
    def test_integrity_indicators_invalid_completeness(self):
        """Test that invalid completeness raises error."""
        with self.assertRaises(ValueError):
            IntegrityIndicators(
                data_completeness=1.5,  # Invalid
                corruption_detected=False,
                schema_compliance=True,
                null_field_count=0,
                out_of_range_count=0
            )


class MockModule:
    """Mock module for testing."""
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.value = 42
    
    def update(self):
        self.value += 1


class TestValidationHooks(unittest.TestCase):
    """Test validation hooks and adapters."""
    
    def test_module_validation_adapter(self):
        """Test adapter for modules without native validation."""
        module = MockModule("test_module")
        adapter = ModuleValidationAdapter("test_module", module)
        
        # Test initialization validation
        init_status = adapter.validate_initialization()
        self.assertEqual(init_status.module_id, "test_module")
        self.assertEqual(init_status.initialization_result, InitializationResult.SUCCESS)
    
    def test_adapter_state_snapshot(self):
        """Test state snapshot capture through adapter."""
        module = MockModule("test_module")
        adapter = ModuleValidationAdapter("test_module", module)
        
        snapshot = adapter.validate_state()
        self.assertEqual(snapshot.module_id, "test_module")
        self.assertIsNotNone(snapshot.state_hash)
        self.assertIn("value", snapshot.state_data)
    
    def test_adapter_consistency_signals(self):
        """Test consistency signals from adapter."""
        module = MockModule("test_module")
        adapter = ModuleValidationAdapter("test_module", module)
        
        signals = adapter.get_consistency_signals()
        self.assertTrue(signals.internal_consistency_valid)
        self.assertEqual(len(signals.constraint_violations), 0)


class TestValidationStrategies(unittest.TestCase):
    """Test validation strategies."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = ValidationConfiguration(
            system_version="test-v1.0",
            validation_framework_version="0.1.0",
            random_seed=42
        )
    
    def test_structural_validation_strategy(self):
        """Test structural validation strategy."""
        strategy = StructuralValidationStrategy(self.config)
        
        # Create test context with initialization statuses
        init_status = ModuleInitializationStatus(
            module_id="test_module",
            module_name="Test Module",
            module_version="1.0",
            initialization_result=InitializationResult.SUCCESS,
            timestamp=datetime.now(),
            configuration_valid=True,
            dependencies_satisfied=True,
            interfaces_ready=True
        )
        
        context = {
            "initialization_statuses": [init_status],
            "system_config": None,
            "state_snapshots": []
        }
        
        result = strategy.execute(context)
        
        self.assertEqual(result.category, ValidationCategory.STRUCTURAL)
        self.assertGreater(result.tests_run, 0)
    
    def test_data_integrity_validation_strategy(self):
        """Test data integrity validation strategy."""
        strategy = DataIntegrityValidationStrategy(self.config)
        
        # Create test snapshot
        snapshot = ModuleStateSnapshot(
            module_id="test_module",
            time_step=1,
            timestamp=datetime.now(),
            state_version=1,
            state_hash="abc123",
            state_data={"value": 42},
            consistency_signals=ConsistencySignals(
                internal_consistency_valid=True,
                referential_integrity_valid=True
            ),
            integrity_indicators=IntegrityIndicators(
                data_completeness=1.0,
                corruption_detected=False,
                schema_compliance=True,
                null_field_count=0,
                out_of_range_count=0
            )
        )
        
        context = {
            "state_snapshots": [snapshot]
        }
        
        result = strategy.execute(context)
        
        self.assertEqual(result.category, ValidationCategory.DATA_INTEGRITY)
        self.assertGreater(result.tests_run, 0)


class TestValidationOrchestrator(unittest.TestCase):
    """Test validation orchestrator."""
    
    def setUp(self):
        """Set up test orchestrator."""
        self.config = ValidationConfiguration(
            system_version="test-v1.0",
            validation_framework_version="0.1.0",
            random_seed=42
        )
        self.orchestrator = ValidationOrchestrator(self.config)
    
    def test_module_registration(self):
        """Test module registration."""
        module = MockModule("test_module")
        self.orchestrator.register_module("test_module", module)
        
        self.assertIn("test_module", self.orchestrator.module_adapters)
    
    def test_initialization_validation(self):
        """Test initialization validation."""
        module = MockModule("test_module")
        self.orchestrator.register_module("test_module", module)
        
        result = self.orchestrator.validate_initialization()
        
        self.assertEqual(result.category, ValidationCategory.STRUCTURAL)
        self.assertGreaterEqual(result.tests_run, 1)
    
    def test_time_step_validation(self):
        """Test time step validation."""
        module = MockModule("test_module")
        self.orchestrator.register_module("test_module", module)
        
        results = self.orchestrator.validate_time_step(1)
        
        self.assertIn(ValidationCategory.DATA_INTEGRITY, results)
    
    def test_report_generation(self):
        """Test validation report generation."""
        module = MockModule("test_module")
        self.orchestrator.register_module("test_module", module)
        
        # Run validation
        init_result = self.orchestrator.validate_initialization()
        
        category_results = {
            ValidationCategory.STRUCTURAL: init_result
        }
        
        report = self.orchestrator.generate_report(category_results)
        
        self.assertIsNotNone(report.report_id)
        self.assertEqual(report.system_version, "test-v1.0")
        self.assertIn(ValidationCategory.STRUCTURAL, report.category_results)


class TestReportGenerator(unittest.TestCase):
    """Test report generator."""
    
    def setUp(self):
        """Set up test report."""
        from validation.types import (
            ValidationReport,
            CategoryResult,
            ExecutionSummary
        )
        
        category_result = CategoryResult(
            category=ValidationCategory.STRUCTURAL,
            result=ValidationResult.PASS,
            tests_run=3,
            tests_passed=3,
            tests_failed=0,
            tests_warned=0
        )
        
        self.report = ValidationReport(
            report_id="test_report_001",
            system_version="test-v1.0",
            validation_framework_version="0.1.0",
            execution_timestamp=datetime.now(),
            random_seed=42,
            overall_result=ValidationResult.PASS,
            category_results={
                ValidationCategory.STRUCTURAL: category_result
            },
            execution_summary=ExecutionSummary(
                total_time_steps=10,
                validation_start_time=datetime.now(),
                validation_end_time=datetime.now(),
                validation_duration_ms=100.0,
                modules_validated=1,
                messages_validated=0,
                snapshots_analyzed=5
            )
        )
    
    def test_generate_markdown_report(self):
        """Test Markdown report generation."""
        md_report = ReportGenerator.generate_markdown_report(self.report)
        
        self.assertIn("# Validation Report", md_report)
        self.assertIn("test_report_001", md_report)
        self.assertIn("PASS", md_report)
    
    def test_generate_text_report(self):
        """Test plain text report generation."""
        text_report = ReportGenerator.generate_text_report(self.report)
        
        self.assertIn("VALIDATION REPORT", text_report)
        self.assertIn("test_report_001", text_report)
        self.assertIn("PASS", text_report)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValidationTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationHooks))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationStrategies))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGenerator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
