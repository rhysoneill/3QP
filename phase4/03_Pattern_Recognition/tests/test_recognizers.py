"""
Tests for pattern recognizers.

Tests that recognizers follow interface contracts and return properly
structured placeholder evidence (without performing actual detection).
"""

import pytest

from pattern_recognition.recognizers import (
    StablePatternRecognizer,
    DriftPatternRecognizer,
    DisruptionPatternRecognizer,
    RecoveryPatternRecognizer,
)
from pattern_recognition.interfaces import PatternRecognitionResult
from pattern_recognition.evidence import PatternEvidenceBundle


class TestStablePatternRecognizer:
    """Test StablePatternRecognizer."""
    
    def test_instantiation(self):
        """Test recognizer can be created."""
        recognizer = StablePatternRecognizer()
        assert recognizer is not None
        assert recognizer.__version__ == "0.1.0"
    
    def test_get_supported_pattern_types(self):
        """Test getting supported patterns."""
        recognizer = StablePatternRecognizer()
        patterns = recognizer.get_supported_pattern_types()
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert "stable_equilibrium" in patterns
        assert "homeostasis" in patterns
    
    def test_analyze_encoded_state(self):
        """Test analyzing single state."""
        recognizer = StablePatternRecognizer()
        
        encoded_state = {
            "state_id": "state_123",
            "schema_version": "1.0.0",
            "encoded_domains": {}
        }
        
        result = recognizer.analyze_encoded_state(encoded_state)
        
        # Check result type
        assert isinstance(result, PatternRecognitionResult)
        
        # Check recognized patterns
        assert isinstance(result.recognized_patterns, list)
        assert len(result.recognized_patterns) > 0
        
        # Check evidence bundle
        assert isinstance(result.evidence_bundle, PatternEvidenceBundle)
        assert result.evidence_bundle.get_evidence_count() > 0
        
        # Check metadata
        assert "placeholder" in result.metadata
        assert result.metadata["placeholder"] is True
        assert "recognizer_versions" in result.metadata
    
    def test_analyze_sequence(self):
        """Test analyzing sequence of states."""
        recognizer = StablePatternRecognizer()
        
        encoded_states = [
            {"state_id": f"state_{i}", "schema_version": "1.0.0"}
            for i in range(5)
        ]
        
        result = recognizer.analyze_sequence(encoded_states)
        
        # Check result type
        assert isinstance(result, PatternRecognitionResult)
        
        # Check recognized patterns
        assert isinstance(result.recognized_patterns, list)
        assert len(result.recognized_patterns) > 0
        
        # Check evidence
        assert result.evidence_bundle.get_evidence_count() > 0
        
        # Check metadata contains sequence info
        assert "sequence_length" in result.metadata
        assert result.metadata["sequence_length"] == 5
    
    def test_does_not_compute(self):
        """Verify recognizer returns placeholder evidence only."""
        recognizer = StablePatternRecognizer()
        
        state = {"state_id": "test", "schema_version": "1.0"}
        result = recognizer.analyze_encoded_state(state)
        
        # Check evidence is marked as placeholder
        evidence_items = result.evidence_bundle.evidence_items
        assert all(e.metadata.get("placeholder") is True for e in evidence_items)
        
        # Check narrative mentions placeholder
        for evidence in evidence_items:
            assert "placeholder" in evidence.narrative.lower()
    
    def test_get_version(self):
        """Test version retrieval."""
        recognizer = StablePatternRecognizer()
        assert recognizer.get_version() == "0.1.0"
    
    def test_get_metadata(self):
        """Test metadata retrieval."""
        recognizer = StablePatternRecognizer()
        metadata = recognizer.get_metadata()
        
        assert "recognizer_type" in metadata
        assert metadata["recognizer_type"] == "StablePatternRecognizer"
        assert "version" in metadata
        assert "supported_patterns" in metadata


class TestDriftPatternRecognizer:
    """Test DriftPatternRecognizer."""
    
    def test_instantiation(self):
        """Test recognizer can be created."""
        recognizer = DriftPatternRecognizer()
        assert recognizer is not None
    
    def test_get_supported_pattern_types(self):
        """Test getting supported patterns."""
        recognizer = DriftPatternRecognizer()
        patterns = recognizer.get_supported_pattern_types()
        
        assert "gradual_drift" in patterns
        assert "slow_shift" in patterns
        assert "trending_change" in patterns
    
    def test_analyze_encoded_state(self):
        """Test analyzing single state."""
        recognizer = DriftPatternRecognizer()
        
        encoded_state = {
            "state_id": "state_456",
            "schema_version": "1.0.0"
        }
        
        result = recognizer.analyze_encoded_state(encoded_state)
        
        assert isinstance(result, PatternRecognitionResult)
        assert len(result.recognized_patterns) > 0
        assert result.evidence_bundle.get_evidence_count() > 0
        assert result.metadata["placeholder"] is True
    
    def test_analyze_sequence(self):
        """Test analyzing sequence."""
        recognizer = DriftPatternRecognizer()
        
        states = [{"state_id": f"s{i}", "schema_version": "1.0"} for i in range(3)]
        result = recognizer.analyze_sequence(states)
        
        assert isinstance(result, PatternRecognitionResult)
        assert result.metadata["sequence_length"] == 3
    
    def test_placeholder_only(self):
        """Verify no actual drift detection."""
        recognizer = DriftPatternRecognizer()
        
        result = recognizer.analyze_encoded_state({"state_id": "test", "schema_version": "1.0"})
        
        # All evidence should be placeholder
        for evidence in result.evidence_bundle.evidence_items:
            assert evidence.metadata.get("placeholder") is True
            assert "placeholder" in evidence.narrative.lower()


class TestDisruptionPatternRecognizer:
    """Test DisruptionPatternRecognizer."""
    
    def test_instantiation(self):
        """Test recognizer can be created."""
        recognizer = DisruptionPatternRecognizer()
        assert recognizer is not None
    
    def test_get_supported_pattern_types(self):
        """Test getting supported patterns."""
        recognizer = DisruptionPatternRecognizer()
        patterns = recognizer.get_supported_pattern_types()
        
        assert "sudden_disruption" in patterns
        assert "shock_event" in patterns
        assert "abrupt_change" in patterns
    
    def test_analyze_encoded_state(self):
        """Test analyzing single state."""
        recognizer = DisruptionPatternRecognizer()
        
        encoded_state = {
            "state_id": "state_789",
            "schema_version": "1.0.0"
        }
        
        result = recognizer.analyze_encoded_state(encoded_state)
        
        assert isinstance(result, PatternRecognitionResult)
        assert len(result.recognized_patterns) > 0
        assert result.evidence_bundle.get_evidence_count() > 0
    
    def test_analyze_sequence(self):
        """Test analyzing sequence."""
        recognizer = DisruptionPatternRecognizer()
        
        states = [{"state_id": f"s{i}", "schema_version": "1.0"} for i in range(4)]
        result = recognizer.analyze_sequence(states)
        
        assert isinstance(result, PatternRecognitionResult)
        assert result.metadata["sequence_length"] == 4
    
    def test_no_actual_detection(self):
        """Verify no actual disruption detection."""
        recognizer = DisruptionPatternRecognizer()
        
        result = recognizer.analyze_encoded_state({"state_id": "test", "schema_version": "1.0"})
        
        # Check placeholder status
        for evidence in result.evidence_bundle.evidence_items:
            assert evidence.metadata.get("placeholder") is True


class TestRecoveryPatternRecognizer:
    """Test RecoveryPatternRecognizer."""
    
    def test_instantiation(self):
        """Test recognizer can be created."""
        recognizer = RecoveryPatternRecognizer()
        assert recognizer is not None
    
    def test_get_supported_pattern_types(self):
        """Test getting supported patterns."""
        recognizer = RecoveryPatternRecognizer()
        patterns = recognizer.get_supported_pattern_types()
        
        assert "recovery_trajectory" in patterns
        assert "restoration_process" in patterns
        assert "return_to_baseline" in patterns
        assert "adaptive_recovery" in patterns
    
    def test_analyze_encoded_state(self):
        """Test analyzing single state."""
        recognizer = RecoveryPatternRecognizer()
        
        encoded_state = {
            "state_id": "state_recovery",
            "schema_version": "1.0.0"
        }
        
        result = recognizer.analyze_encoded_state(encoded_state)
        
        assert isinstance(result, PatternRecognitionResult)
        assert len(result.recognized_patterns) > 0
        assert result.evidence_bundle.get_evidence_count() > 0
    
    def test_analyze_sequence(self):
        """Test analyzing sequence."""
        recognizer = RecoveryPatternRecognizer()
        
        states = [{"state_id": f"s{i}", "schema_version": "1.0"} for i in range(6)]
        result = recognizer.analyze_sequence(states)
        
        assert isinstance(result, PatternRecognitionResult)
        assert result.metadata["sequence_length"] == 6
    
    def test_placeholder_evidence(self):
        """Verify placeholder evidence only."""
        recognizer = RecoveryPatternRecognizer()
        
        result = recognizer.analyze_encoded_state({"state_id": "test", "schema_version": "1.0"})
        
        for evidence in result.evidence_bundle.evidence_items:
            assert evidence.metadata.get("placeholder") is True
            assert "placeholder" in evidence.narrative.lower()


class TestAllRecognizers:
    """Cross-recognizer tests."""
    
    def test_all_return_results(self):
        """Test all recognizers return PatternRecognitionResult."""
        recognizers = [
            StablePatternRecognizer(),
            DriftPatternRecognizer(),
            DisruptionPatternRecognizer(),
            RecoveryPatternRecognizer(),
        ]
        
        state = {"state_id": "test", "schema_version": "1.0"}
        
        for recognizer in recognizers:
            result = recognizer.analyze_encoded_state(state)
            assert isinstance(result, PatternRecognitionResult)
    
    def test_all_have_unique_patterns(self):
        """Test recognizers support different pattern types."""
        recognizers = [
            StablePatternRecognizer(),
            DriftPatternRecognizer(),
            DisruptionPatternRecognizer(),
            RecoveryPatternRecognizer(),
        ]
        
        all_patterns = set()
        for recognizer in recognizers:
            patterns = recognizer.get_supported_pattern_types()
            all_patterns.update(patterns)
        
        # Should have many unique patterns
        assert len(all_patterns) > 10
    
    def test_all_generate_narratives(self):
        """Test all recognizers generate narratives."""
        recognizers = [
            StablePatternRecognizer(),
            DriftPatternRecognizer(),
            DisruptionPatternRecognizer(),
            RecoveryPatternRecognizer(),
        ]
        
        state = {"state_id": "test", "schema_version": "1.0"}
        
        for recognizer in recognizers:
            result = recognizer.analyze_encoded_state(state)
            narrative = result.narrative_summary()
            assert isinstance(narrative, str)
            assert len(narrative) > 0
