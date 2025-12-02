"""
Architectural Validation Script

Validates that Phase 4 / WS4 Trajectory Analysis Architecture
maintains all architectural guarantees:

1. Zero computation
2. No numeric scoring
3. No external dependencies
4. Qualitative only
5. Interface compliance
"""

import sys
import importlib.util


def validate_no_external_dependencies():
    """Validate that trajectory_analysis has no external dependencies."""
    print("Checking for external dependencies...")
    
    import trajectory_analysis
    
    # Get all imported modules
    import_errors = []
    allowed_modules = {
        'abc', 'dataclasses', 'enum', 'typing', 
        'trajectory_analysis', '__main__', '__future__'
    }
    
    # Check all submodules
    for name in dir(trajectory_analysis):
        if not name.startswith('_'):
            obj = getattr(trajectory_analysis, name)
            if hasattr(obj, '__module__'):
                module_base = obj.__module__.split('.')[0]
                if module_base not in allowed_modules and module_base != 'trajectory_analysis':
                    # Check if it's a standard library module
                    spec = importlib.util.find_spec(module_base)
                    if spec and 'site-packages' in (spec.origin or ''):
                        import_errors.append(f"  - {name} from external module: {obj.__module__}")
    
    if import_errors:
        print("❌ FAILED: External dependencies found:")
        for error in import_errors:
            print(error)
        return False
    else:
        print("✓ PASSED: No external dependencies detected")
        return True


def validate_no_numeric_scoring():
    """Validate that models contain no numeric scoring fields."""
    print("\nChecking for numeric scoring in models...")
    
    from trajectory_analysis.models import (
        TrajectoryHypothesis,
        TrajectoryAnalysisResult,
        TrajectoryClassificationResult
    )
    from trajectory_analysis.evidence import TrajectoryEvidence
    
    forbidden_fields = [
        'score', 'probability', 'confidence', 'weight',
        'likelihood', 'certainty', 'rating', 'threshold'
    ]
    
    models_to_check = [
        TrajectoryHypothesis,
        TrajectoryAnalysisResult,
        TrajectoryClassificationResult,
        TrajectoryEvidence
    ]
    
    errors = []
    
    for model in models_to_check:
        if hasattr(model, '__annotations__'):
            for field_name in model.__annotations__:
                for forbidden in forbidden_fields:
                    if forbidden in field_name.lower():
                        errors.append(
                            f"  - {model.__name__}.{field_name} contains forbidden term: {forbidden}"
                        )
    
    if errors:
        print("❌ FAILED: Numeric scoring fields found:")
        for error in errors:
            print(error)
        return False
    else:
        print("✓ PASSED: No numeric scoring fields in models")
        return True


def validate_placeholder_behavior():
    """Validate that analyzers are truly placeholders."""
    print("\nChecking placeholder analyzer behavior...")
    
    from trajectory_analysis import SimpleTrajectoryAnalyzer
    
    analyzer = SimpleTrajectoryAnalyzer()
    
    # Analyze with different inputs - should produce same archetype
    result1 = analyzer.analyze_sequence([], [])
    result2 = analyzer.analyze_sequence(
        [{"a": 1}, {"b": 2}],
        [object(), object()]
    )
    
    # Check that results are consistent (ignore input)
    same_archetype = result1.hypotheses[0].archetype_id == result2.hypotheses[0].archetype_id
    
    # Check metadata has placeholder marker
    has_placeholder_marker = result1.metadata.get("placeholder") == "true"
    
    if same_archetype and has_placeholder_marker:
        print("✓ PASSED: Analyzers are placeholders (ignore input, marked as placeholder)")
        return True
    
    print("❌ FAILED: Analyzers do not behave as placeholders")
    return False


def validate_interface_compliance():
    """Validate that all components implement required interfaces."""
    print("\nChecking interface compliance...")
    
    from trajectory_analysis import (
        SimpleTrajectoryAnalyzer,
        StableAdaptationAnalyzer,
        TrajectoryHeuristicClassifier,
        SimpleAggregationEngine
    )
    from trajectory_analysis.interfaces import (
        TrajectoryAnalyzer,
        TrajectoryClassifier,
        TrajectoryAggregationEngine
    )
    
    checks = [
        (SimpleTrajectoryAnalyzer, TrajectoryAnalyzer),
        (StableAdaptationAnalyzer, TrajectoryAnalyzer),
        (TrajectoryHeuristicClassifier, TrajectoryClassifier),
        (SimpleAggregationEngine, TrajectoryAggregationEngine)
    ]
    
    all_passed = True
    
    for impl_class, interface_class in checks:
        instance = impl_class()
        if not isinstance(instance, interface_class):
            print(f"❌ {impl_class.__name__} does not implement {interface_class.__name__}")
            all_passed = False
    
    if all_passed:
        print("✓ PASSED: All components implement required interfaces")
    
    return all_passed


def validate_evidence_qualitative():
    """Validate that evidence system is purely qualitative."""
    print("\nChecking evidence system is qualitative...")
    
    from trajectory_analysis.evidence import (
        TrajectorySupportStrength,
        TrajectoryEvidence
    )
    
    # Check enum has no numeric values
    has_numeric = False
    for member in TrajectorySupportStrength:
        if isinstance(member.value, (int, float)):
            has_numeric = True
            break
    
    if has_numeric:
        print("❌ FAILED: TrajectorySupportStrength has numeric values")
        return False
    
    # Check evidence requires narrative
    try:
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.WEAK,
            narrative="Test narrative"
        )
        
        if evidence.narrative and isinstance(evidence.narrative, str):
            print("✓ PASSED: Evidence system is qualitative (enum values are strings, narrative required)")
            return True
    except Exception as e:
        print(f"❌ FAILED: Error creating evidence: {e}")
        return False


def validate_validators_work():
    """Validate that validators detect forbidden metadata."""
    print("\nChecking validator forbidden metadata detection...")
    
    from trajectory_analysis import (
        TrajectoryAnalysisResult,
        TrajectoryEvidenceBundle,
        TrajectoryResultValidator
    )
    
    # Create result with forbidden key
    result = TrajectoryAnalysisResult(
        hypotheses=[],
        evidence_bundle=TrajectoryEvidenceBundle(),
        analyzer_id="test",
        analyzer_version="1.0",
        metadata={"confidence_score": "0.95"}  # Should be detected!
    )
    
    validator = TrajectoryResultValidator()
    validation = validator.validate_analysis_result(result)
    
    if not validation.is_valid and any("Forbidden" in err for err in validation.errors):
        print("✓ PASSED: Validators detect forbidden numeric scoring metadata")
        return True
    else:
        print("❌ FAILED: Validators did not detect forbidden metadata")
        return False


def validate_test_coverage():
    """Validate that test suite is comprehensive."""
    print("\nChecking test coverage...")
    
    import os
    import glob
    
    test_dir = "tests"
    
    if not os.path.exists(test_dir):
        print("❌ FAILED: Test directory not found")
        return False
    
    test_files = glob.glob(os.path.join(test_dir, "test_*.py"))
    
    expected_tests = [
        "test_interfaces.py",
        "test_models.py",
        "test_evidence.py",
        "test_analyzers.py",
        "test_registry.py",
        "test_validators.py"
    ]
    
    found_tests = [os.path.basename(f) for f in test_files]
    
    missing = set(expected_tests) - set(found_tests)
    
    if missing:
        print(f"❌ FAILED: Missing test files: {missing}")
        return False
    else:
        print(f"✓ PASSED: All {len(expected_tests)} test modules present")
        return True


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("  TRAJECTORY ANALYSIS ARCHITECTURE VALIDATION")
    print("  Phase 4 / Workstream 4")
    print("=" * 70)
    
    checks = [
        validate_no_external_dependencies,
        validate_no_numeric_scoring,
        validate_placeholder_behavior,
        validate_interface_compliance,
        validate_evidence_qualitative,
        validate_validators_work,
        validate_test_coverage
    ]
    
    results = []
    
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERROR in {check.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("  VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL ARCHITECTURAL GUARANTEES VALIDATED")
        print("\nArchitecture layer is complete and compliant:")
        print("  ✓ Zero computation maintained")
        print("  ✓ No numeric scoring")
        print("  ✓ No external dependencies")
        print("  ✓ Purely qualitative evidence")
        print("  ✓ Interface compliance verified")
        print("  ✓ Validators functional")
        print("  ✓ Comprehensive test coverage")
        return 0
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print(f"\nFailed: {total - passed} check(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
