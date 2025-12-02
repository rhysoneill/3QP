"""
Synthetic fixtures for validation testing.

Provides pre-built test scenarios with corresponding encoded states,
pattern recognition results, and trajectory analysis results.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add phase4 workstream paths for imports
phase4_base = Path(__file__).parent.parent.parent
pattern_recognition_path = phase4_base / "03_Pattern_Recognition"
trajectory_analysis_path = phase4_base / "04_Trajectory_Analysis"

if str(pattern_recognition_path) not in sys.path:
    sys.path.insert(0, str(pattern_recognition_path))
if str(trajectory_analysis_path) not in sys.path:
    sys.path.insert(0, str(trajectory_analysis_path))

from pattern_recognition.interfaces import PatternRecognitionResult
from pattern_recognition.evidence import PatternEvidence, PatternEvidenceBundle

from trajectory_analysis.models import (
    TrajectoryHypothesis,
    TrajectoryAnalysisResult,
    TrajectoryClassificationResult,
)
from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle,
)

from .config import (
    ExpectedPattern,
    ExpectedTrajectory,
    ValidationScenarioConfig,
)


# ============================================================================
# Fixture Scenarios
# ============================================================================

def _create_stable_adaptation_scenario() -> ValidationScenarioConfig:
    """Create the stable_adaptation_case validation scenario."""
    return ValidationScenarioConfig(
        scenario_id="stable_adaptation_case",
        label="Stable Adaptation Case",
        description=(
            "A scenario demonstrating stable adaptation patterns with minimal drift. "
            "Expects stable_pattern recognition and stable_adaptation trajectory."
        ),
        expected_patterns=[
            ExpectedPattern(
                pattern_type="stable_pattern",
                required=True,
                description="Stable state with consistent parameters",
            ),
            ExpectedPattern(
                pattern_type="recovery_pattern",
                required=False,
                description="Optional recovery from minor perturbations",
            ),
        ],
        expected_trajectories=[
            ExpectedTrajectory(
                archetype_id="stable_adaptation",
                required=True,
                description="Stable adaptation trajectory archetype",
            ),
        ],
        metadata={
            "phase3_reference": "baseline_state_01",
            "scenario_type": "positive_case",
        },
    )


def _create_gradual_drift_scenario() -> ValidationScenarioConfig:
    """Create the gradual_drift_case validation scenario."""
    return ValidationScenarioConfig(
        scenario_id="gradual_drift_case",
        label="Gradual Drift Case",
        description=(
            "A scenario showing gradual drift away from baseline. "
            "Expects drift_pattern recognition and potentially intervention triggers."
        ),
        expected_patterns=[
            ExpectedPattern(
                pattern_type="drift_pattern",
                required=True,
                description="Gradual parameter drift over time",
            ),
            ExpectedPattern(
                pattern_type="stable_pattern",
                required=False,
                description="May have initial stability before drift",
            ),
        ],
        expected_trajectories=[
            ExpectedTrajectory(
                archetype_id="gradual_drift",
                required=True,
                description="Gradual drift trajectory archetype",
            ),
        ],
        metadata={
            "phase3_reference": "scenario_02_drift",
            "scenario_type": "warning_case",
        },
    )


def _create_third_quarter_signature_scenario() -> ValidationScenarioConfig:
    """Create the third_quarter_signature_case validation scenario."""
    return ValidationScenarioConfig(
        scenario_id="third_quarter_signature_case",
        label="Third Quarter Signature Case",
        description=(
            "A scenario exhibiting the characteristic third-quarter performance pattern. "
            "Expects disruption followed by recovery or resilience patterns."
        ),
        expected_patterns=[
            ExpectedPattern(
                pattern_type="disruption_pattern",
                required=True,
                description="Disruption event in temporal sequence",
            ),
            ExpectedPattern(
                pattern_type="recovery_pattern",
                required=True,
                description="Recovery from disruption",
            ),
        ],
        expected_trajectories=[
            ExpectedTrajectory(
                archetype_id="third_quarter_signature",
                required=True,
                description="Third quarter signature trajectory",
            ),
        ],
        metadata={
            "phase3_reference": "cross_module_thread_3Q",
            "scenario_type": "signature_pattern",
        },
    )


# ============================================================================
# Fixture Data Builders
# ============================================================================

def _build_stable_adaptation_fixture() -> tuple[
    list[dict],
    list[PatternRecognitionResult],
    TrajectoryClassificationResult,
]:
    """
    Build fixture data for stable_adaptation_case.
    
    Returns:
        Tuple of (encoded_states, pattern_results, trajectory_classification)
    """
    # Encoded states (placeholder structures from WS2)
    encoded_states = [
        {
            "state_id": "state_stable_001",
            "timestamp": "2024-01-01T10:00:00",
            "categorical_features": {
                "mission_phase": "execution",
                "stress_level": "low",
                "team_cohesion": "high",
            },
            "structural_features": {
                "active_goals": ["maintain_course", "monitor_systems"],
                "network_topology": "fully_connected",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
        {
            "state_id": "state_stable_002",
            "timestamp": "2024-01-01T11:00:00",
            "categorical_features": {
                "mission_phase": "execution",
                "stress_level": "low",
                "team_cohesion": "high",
            },
            "structural_features": {
                "active_goals": ["maintain_course", "monitor_systems"],
                "network_topology": "fully_connected",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
    ]
    
    # Pattern recognition results
    pattern_evidence = PatternEvidenceBundle(
        evidence_items=[
            PatternEvidence(
                pattern_type="stable_pattern",
                indicator_label="consistent_state_features",
                qualitative_strength="strong",
                narrative="Consistent categorical features across states",
                metadata={"temporal_span": "2_states"},
            ),
        ],
        metadata={"analysis_timestamp": datetime.now().isoformat()},
    )
    
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["stable_pattern"],
            evidence_bundle=pattern_evidence,
            metadata={
                "schema_version": "0.1.0",
                "recognizer_versions": {"StablePatternRecognizer": "0.1.0"},
            },
        ),
    ]
    
    # Trajectory analysis/classification
    hypothesis = TrajectoryHypothesis(
        archetype_id="stable_adaptation",
        label="Stable Adaptation",
        support_strength=TrajectorySupportStrength.STRONG,
        rationale="Sustained stable patterns with no drift or disruption",
        source_patterns=["stable_pattern"],
        metadata={"analyzer_id": "StableAdaptationAnalyzer"},
    )
    
    trajectory_evidence = TrajectoryEvidenceBundle(
        items=[
            TrajectoryEvidence(
                archetype_id="stable_adaptation",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Continuous stable state indicators",
                source_pattern_type="stable_pattern",
                metadata={"temporal_consistency": "high"},
            ),
        ],
    )
    
    trajectory_classification = TrajectoryClassificationResult(
        candidate_hypotheses=[hypothesis],
        supporting_evidence=trajectory_evidence,
        selected_archetype_id="stable_adaptation",
        trajectory_id="traj_stable_001",
        metadata={
            "classifier_id": "TrajectoryHeuristicClassifier",
            "classifier_version": "0.1.0",
        },
    )
    
    return encoded_states, pattern_results, trajectory_classification


def _build_gradual_drift_fixture() -> tuple[
    list[dict],
    list[PatternRecognitionResult],
    TrajectoryClassificationResult,
]:
    """
    Build fixture data for gradual_drift_case.
    
    Returns:
        Tuple of (encoded_states, pattern_results, trajectory_classification)
    """
    # Encoded states showing gradual drift
    encoded_states = [
        {
            "state_id": "state_drift_001",
            "timestamp": "2024-01-01T10:00:00",
            "categorical_features": {
                "mission_phase": "execution",
                "stress_level": "low",
                "team_cohesion": "high",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
        {
            "state_id": "state_drift_002",
            "timestamp": "2024-01-01T11:00:00",
            "categorical_features": {
                "mission_phase": "execution",
                "stress_level": "medium",
                "team_cohesion": "medium",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
        {
            "state_id": "state_drift_003",
            "timestamp": "2024-01-01T12:00:00",
            "categorical_features": {
                "mission_phase": "execution",
                "stress_level": "medium",
                "team_cohesion": "low",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
    ]
    
    # Pattern recognition results
    pattern_evidence = PatternEvidenceBundle(
        evidence_items=[
            PatternEvidence(
                pattern_type="drift_pattern",
                indicator_label="progressive_state_changes",
                qualitative_strength="strong",
                narrative="Progressive change in stress_level and team_cohesion",
                metadata={"drift_direction": "negative"},
            ),
        ],
        metadata={"analysis_timestamp": datetime.now().isoformat()},
    )
    
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["drift_pattern"],
            evidence_bundle=pattern_evidence,
            metadata={
                "schema_version": "0.1.0",
                "recognizer_versions": {"DriftPatternRecognizer": "0.1.0"},
            },
        ),
    ]
    
    # Trajectory analysis
    hypothesis = TrajectoryHypothesis(
        archetype_id="gradual_drift",
        label="Gradual Drift",
        support_strength=TrajectorySupportStrength.MODERATE,
        rationale="Gradual deterioration in key state features",
        source_patterns=["drift_pattern"],
        metadata={"drift_type": "negative"},
    )
    
    trajectory_evidence = TrajectoryEvidenceBundle(
        items=[
            TrajectoryEvidence(
                archetype_id="gradual_drift",
                support_strength=TrajectorySupportStrength.MODERATE,
                narrative="Progressive state changes over sequence",
                source_pattern_type="drift_pattern",
                metadata={"temporal_span": "3_states"},
            ),
        ],
    )
    
    trajectory_classification = TrajectoryClassificationResult(
        candidate_hypotheses=[hypothesis],
        supporting_evidence=trajectory_evidence,
        selected_archetype_id="gradual_drift",
        trajectory_id="traj_drift_001",
        metadata={
            "classifier_id": "TrajectoryHeuristicClassifier",
            "classifier_version": "0.1.0",
        },
    )
    
    return encoded_states, pattern_results, trajectory_classification


def _build_third_quarter_signature_fixture() -> tuple[
    list[dict],
    list[PatternRecognitionResult],
    TrajectoryClassificationResult,
]:
    """
    Build fixture data for third_quarter_signature_case.
    
    Returns:
        Tuple of (encoded_states, pattern_results, trajectory_classification)
    """
    # Encoded states showing disruption and recovery
    encoded_states = [
        {
            "state_id": "state_3q_001",
            "timestamp": "2024-01-01T10:00:00",
            "categorical_features": {
                "mission_phase": "mid_mission",
                "stress_level": "low",
                "team_cohesion": "high",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
        {
            "state_id": "state_3q_002",
            "timestamp": "2024-01-01T11:00:00",
            "categorical_features": {
                "mission_phase": "mid_mission",
                "stress_level": "high",
                "team_cohesion": "low",
            },
            "metadata": {"encoder_version": "0.1.0", "disruption_marker": "true"},
        },
        {
            "state_id": "state_3q_003",
            "timestamp": "2024-01-01T12:00:00",
            "categorical_features": {
                "mission_phase": "mid_mission",
                "stress_level": "medium",
                "team_cohesion": "medium",
            },
            "metadata": {"encoder_version": "0.1.0"},
        },
        {
            "state_id": "state_3q_004",
            "timestamp": "2024-01-01T13:00:00",
            "categorical_features": {
                "mission_phase": "mid_mission",
                "stress_level": "low",
                "team_cohesion": "high",
            },
            "metadata": {"encoder_version": "0.1.0", "recovery_marker": "true"},
        },
    ]
    
    # Pattern recognition results
    pattern_evidence = PatternEvidenceBundle(
        evidence_items=[
            PatternEvidence(
                pattern_type="disruption_pattern",
                indicator_label="sharp_stress_increase",
                qualitative_strength="strong",
                narrative="Sharp increase in stress with cohesion drop",
                metadata={"disruption_state": "state_3q_002"},
            ),
            PatternEvidence(
                pattern_type="recovery_pattern",
                indicator_label="return_to_baseline",
                qualitative_strength="strong",
                narrative="Return to baseline after disruption",
                metadata={"recovery_states": "state_3q_003,state_3q_004"},
            ),
        ],
        metadata={"analysis_timestamp": datetime.now().isoformat()},
    )
    
    pattern_results = [
        PatternRecognitionResult(
            recognized_patterns=["disruption_pattern", "recovery_pattern"],
            evidence_bundle=pattern_evidence,
            metadata={
                "schema_version": "0.1.0",
                "recognizer_versions": {
                    "DisruptionPatternRecognizer": "0.1.0",
                    "RecoveryPatternRecognizer": "0.1.0",
                },
            },
        ),
    ]
    
    # Trajectory analysis
    hypothesis = TrajectoryHypothesis(
        archetype_id="third_quarter_signature",
        label="Third Quarter Signature",
        support_strength=TrajectorySupportStrength.STRONG,
        rationale="Classic disruption-recovery pattern in mission midpoint",
        source_patterns=["disruption_pattern", "recovery_pattern"],
        metadata={"signature_type": "resilience_pattern"},
    )
    
    trajectory_evidence = TrajectoryEvidenceBundle(
        items=[
            TrajectoryEvidence(
                archetype_id="third_quarter_signature",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Disruption followed by successful recovery",
                source_pattern_type="disruption_pattern",
                metadata={"temporal_structure": "disruption_recovery_sequence"},
            ),
        ],
    )
    
    trajectory_classification = TrajectoryClassificationResult(
        candidate_hypotheses=[hypothesis],
        supporting_evidence=trajectory_evidence,
        selected_archetype_id="third_quarter_signature",
        trajectory_id="traj_3q_001",
        metadata={
            "classifier_id": "TrajectoryHeuristicClassifier",
            "classifier_version": "0.1.0",
        },
    )
    
    return encoded_states, pattern_results, trajectory_classification


# ============================================================================
# Public API
# ============================================================================

def get_fixture_scenarios() -> list[ValidationScenarioConfig]:
    """
    Get all available fixture scenarios.
    
    Returns:
        List of ValidationScenarioConfig objects
    """
    return [
        _create_stable_adaptation_scenario(),
        _create_gradual_drift_scenario(),
        _create_third_quarter_signature_scenario(),
    ]


def get_fixture_for_scenario(
    scenario_id: str,
) -> tuple[list[dict], list[PatternRecognitionResult], TrajectoryClassificationResult]:
    """
    Get fixture data for a specific scenario.
    
    Args:
        scenario_id: ID of the scenario to retrieve
    
    Returns:
        Tuple of (encoded_states, pattern_results, trajectory_classification)
    
    Raises:
        ValueError: If scenario_id is not recognized
    """
    fixture_builders = {
        "stable_adaptation_case": _build_stable_adaptation_fixture,
        "gradual_drift_case": _build_gradual_drift_fixture,
        "third_quarter_signature_case": _build_third_quarter_signature_fixture,
    }
    
    if scenario_id not in fixture_builders:
        available = ", ".join(fixture_builders.keys())
        raise ValueError(
            f"Unknown scenario_id: {scenario_id}. "
            f"Available scenarios: {available}"
        )
    
    return fixture_builders[scenario_id]()
