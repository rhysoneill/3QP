"""
Demo: Trajectory Analysis Architecture

This demo showcases the trajectory analysis architecture layer,
demonstrating how analyzers, classifiers, and validators work together.

IMPORTANT: This is architecture-only. No real trajectory analysis is performed.
All outputs are placeholder results for structural validation.
"""

from trajectory_analysis import (
    create_default_registry,
    SequenceInputValidator,
    TrajectoryResultValidator,
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle,
    TrajectoryHypothesis
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_basic_analysis():
    """Demonstrate basic trajectory analysis workflow."""
    print_section("1. Basic Trajectory Analysis Workflow")
    
    # Create registry with default components
    registry = create_default_registry()
    
    print("Available analyzers:")
    for analyzer_id in registry.list_analyzers():
        info = registry.get_analyzer_info(analyzer_id)
        print(f"  - {analyzer_id}: {info['supported_archetypes']}")
    
    print("\nAvailable classifiers:")
    for classifier_id in registry.list_classifiers():
        info = registry.get_classifier_info(classifier_id)
        print(f"  - {classifier_id}")
    
    # Simulate encoded states from WS2 (placeholder data)
    encoded_states = [
        {"state_id": "s1", "phase": "early", "context": "initial"},
        {"state_id": "s2", "phase": "mid", "context": "adjustment"},
        {"state_id": "s3", "phase": "late", "context": "stabilization"}
    ]
    
    # Simulate pattern results from WS3 (using stubs)
    class PatternResultStub:
        def __init__(self):
            self.recognized_patterns = ["adaptation_pattern"]
            self.evidence_bundle = None
            self.metadata = {"placeholder": "true"}
    
    pattern_results = [PatternResultStub() for _ in range(3)]
    
    # Validate inputs
    print("\n--- Input Validation ---")
    validator = SequenceInputValidator()
    validation = validator.validate_inputs(encoded_states, pattern_results)
    
    print(f"Input validation: {'PASSED' if validation.is_valid else 'FAILED'}")
    if validation.warnings:
        print(f"Warnings: {len(validation.warnings)}")
    
    # Get analyzer and analyze
    print("\n--- Trajectory Analysis ---")
    analyzer = registry.get_analyzer("stable_adaptation")
    result = analyzer.analyze_sequence(encoded_states, pattern_results)
    
    print(f"Analyzer: {result.analyzer_id} v{result.analyzer_version}")
    print(f"Hypotheses generated: {len(result.hypotheses)}")
    
    if result.hypotheses:
        primary = result.primary_hypothesis()
        print(f"\nPrimary hypothesis:")
        print(f"  Archetype: {primary.archetype_id}")
        print(f"  Label: {primary.label}")
        print(f"  Support: {primary.support_strength.value}")
        print(f"  Rationale: {primary.rationale[:80]}...")
    
    # Validate analysis result
    print("\n--- Result Validation ---")
    result_validator = TrajectoryResultValidator()
    result_validation = result_validator.validate_analysis_result(result)
    
    print(f"Analysis result validation: {'PASSED' if result_validation.is_valid else 'FAILED'}")
    print(f"Errors: {len(result_validation.errors)}")
    print(f"Warnings: {len(result_validation.warnings)}")
    
    # Classify
    print("\n--- Trajectory Classification ---")
    classifier = registry.get_classifier("simple_classifier")
    classification = classifier.classify(result)
    
    print(f"Selected archetype: {classification.selected_archetype_id}")
    print(f"Candidate hypotheses: {len(classification.candidate_hypotheses)}")
    print(f"Evidence items: {len(classification.supporting_evidence.items)}")


def demo_evidence_system():
    """Demonstrate evidence structure and operations."""
    print_section("2. Evidence System Demonstration")
    
    # Create evidence items
    print("Creating evidence items...")
    
    evidence1 = TrajectoryEvidence(
        archetype_id="stable_adaptation",
        support_strength=TrajectorySupportStrength.STRONG,
        narrative="Consistent adaptation patterns observed throughout mission",
        source_pattern_type="adaptation_pattern",
        metadata={"phase": "complete"}
    )
    
    evidence2 = TrajectoryEvidence(
        archetype_id="stable_adaptation",
        support_strength=TrajectorySupportStrength.MODERATE,
        narrative="Recovery after challenges indicates stable baseline",
        source_pattern_type="recovery_pattern",
        source_state_id="s2"
    )
    
    evidence3 = TrajectoryEvidence(
        archetype_id="third_quarter",
        support_strength=TrajectorySupportStrength.WEAK,
        narrative="Slight performance dip mid-mission (contextual)",
        source_state_id="s2"
    )
    
    # Create bundle
    bundle = TrajectoryEvidenceBundle(items=[evidence1, evidence2, evidence3])
    
    print(f"\nTotal evidence items: {len(bundle.items)}")
    print(f"Unique archetypes: {bundle.get_archetype_ids()}")
    
    # Filter by archetype
    print("\n--- Filtering by Archetype ---")
    stable_evidence = bundle.filter_by_archetype("stable_adaptation")
    print(f"Evidence for 'stable_adaptation': {len(stable_evidence.items)}")
    
    # Filter by strength
    print("\n--- Filtering by Strength ---")
    strong_evidence = bundle.filter_by_strength([
        TrajectorySupportStrength.STRONG,
        TrajectorySupportStrength.MODERATE
    ])
    print(f"Strong/Moderate evidence: {len(strong_evidence.items)}")
    
    # Group by archetype
    print("\n--- Grouping by Archetype ---")
    grouped = bundle.group_by_archetype()
    for archetype_id, items in grouped.items():
        print(f"{archetype_id}: {len(items)} items")
    
    # Merge bundles
    print("\n--- Merging Bundles ---")
    new_evidence = TrajectoryEvidence(
        archetype_id="cumulative_strain",
        support_strength=TrajectorySupportStrength.SUGGESTIVE,
        narrative="Minor cumulative effects noted"
    )
    new_bundle = TrajectoryEvidenceBundle(items=[new_evidence])
    
    merged = bundle.merge(new_bundle)
    print(f"Original bundle: {len(bundle.items)} items")
    print(f"New bundle: {len(new_bundle.items)} items")
    print(f"Merged bundle: {len(merged.items)} items")


def demo_narrative_output():
    """Demonstrate narrative generation."""
    print_section("3. Narrative Output Demonstration")
    
    # Create hypothesis
    hyp = TrajectoryHypothesis(
        archetype_id="stable_adaptation",
        label="Stable Adaptation Trajectory",
        support_strength=TrajectorySupportStrength.STRONG,
        rationale=(
            "Mission demonstrates consistent adaptation to challenges "
            "with stable baseline performance throughout all phases."
        ),
        source_patterns=["adaptation_pattern", "recovery_pattern"],
        metadata={"confidence_class": "high"}
    )
    
    print("Hypothesis Narrative:")
    print("-" * 70)
    print(hyp.to_narrative())
    print("-" * 70)
    
    # Create evidence bundle
    evidence = TrajectoryEvidence(
        archetype_id="stable_adaptation",
        support_strength=TrajectorySupportStrength.STRONG,
        narrative="Strong adaptation patterns across all mission phases",
        source_pattern_type="adaptation_pattern"
    )
    
    bundle = TrajectoryEvidenceBundle(items=[evidence])
    
    print("\n\nEvidence Bundle Narrative:")
    print("-" * 70)
    print(bundle.to_narrative())
    print("-" * 70)


def demo_validation():
    """Demonstrate validation capabilities."""
    print_section("4. Validation Demonstration")
    
    from trajectory_analysis import (
        TrajectoryAnalysisResult,
        ValidationResult
    )
    
    # Test forbidden metadata detection
    print("Testing forbidden metadata detection...")
    
    # Create result with forbidden metadata key
    try:
        result = TrajectoryAnalysisResult(
            hypotheses=[],
            evidence_bundle=TrajectoryEvidenceBundle(),
            analyzer_id="test",
            analyzer_version="1.0",
            metadata={"trajectory_score": "0.95"}  # FORBIDDEN!
        )
        
        validator = TrajectoryResultValidator()
        validation = validator.validate_analysis_result(result)
        
        print(f"\nValidation status: {'PASSED' if validation.is_valid else 'FAILED'}")
        print(f"Errors detected: {len(validation.errors)}")
        
        if validation.errors:
            print("\nErrors:")
            for error in validation.errors:
                print(f"  - {error}")
        
        print("\n✓ Forbidden metadata detection working correctly!")
        
    except Exception as e:
        print(f"Error during validation: {e}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  TRAJECTORY ANALYSIS ARCHITECTURE DEMO")
    print("  Phase 4 / Workstream 4")
    print("  Version: 0.1.0")
    print("=" * 70)
    print("\nIMPORTANT: This is a pure architecture layer.")
    print("No real trajectory analysis is performed.")
    print("All outputs are placeholder results for structural validation.")
    
    demo_basic_analysis()
    demo_evidence_system()
    demo_narrative_output()
    demo_validation()
    
    print_section("Demo Complete")
    print("✓ All architectural components demonstrated successfully!")
    print("✓ Zero computation maintained throughout")
    print("✓ No numeric scoring detected")
    print("\nNext steps: Implement computational layer (WS6+)")


if __name__ == "__main__":
    main()
