"""
Tests for pattern recognition interfaces.

Tests abstract base classes and contract enforcement.
"""

import pytest
from typing import Dict, List, Any

from pattern_recognition.interfaces import (
    PatternRecognizer,
    SequenceAnalyzer,
    PatternAggregationEngine,
    PatternRecognitionResult,
)
from pattern_recognition.evidence import PatternEvidenceBundle


class TestPatternRecognitionResult:
    """Test PatternRecognitionResult dataclass."""
    
    def test_creation(self):
        """Test basic result creation."""
        bundle = PatternEvidenceBundle()
        result = PatternRecognitionResult(
            recognized_patterns=["pattern1", "pattern2"],
            evidence_bundle=bundle,
            metadata={"test": "value"}
        )
        
        assert result.recognized_patterns == ["pattern1", "pattern2"]
        assert result.evidence_bundle == bundle
        assert result.metadata["test"] == "value"
        assert "schema_version" in result.metadata
        assert "recognizer_versions" in result.metadata
    
    def test_auto_metadata_fields(self):
        """Test automatic metadata field addition."""
        result = PatternRecognitionResult(
            recognized_patterns=[],
            evidence_bundle=PatternEvidenceBundle(),
        )
        
        assert "schema_version" in result.metadata
        assert "recognizer_versions" in result.metadata
        assert result.metadata["schema_version"] == "unknown"
    
    def test_narrative_summary_empty(self):
        """Test narrative generation with no patterns."""
        result = PatternRecognitionResult(
            recognized_patterns=[],
            evidence_bundle=PatternEvidenceBundle(),
        )
        
        narrative = result.narrative_summary()
        assert "No patterns recognized" in narrative
    
    def test_narrative_summary_with_patterns(self):
        """Test narrative generation with patterns."""
        result = PatternRecognitionResult(
            recognized_patterns=["stable_equilibrium", "gradual_drift"],
            evidence_bundle=PatternEvidenceBundle(),
            metadata={"schema_version": "1.0.0"}
        )
        
        narrative = result.narrative_summary()
        assert "stable_equilibrium" in narrative
        assert "gradual_drift" in narrative
        assert "1.0.0" in narrative
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        bundle = PatternEvidenceBundle()
        result = PatternRecognitionResult(
            recognized_patterns=["test_pattern"],
            evidence_bundle=bundle,
            metadata={"version": "1.0"}
        )
        
        result_dict = result.to_dict()
        assert "recognized_patterns" in result_dict
        assert "evidence_bundle" in result_dict
        assert "metadata" in result_dict
        assert "timestamp" in result_dict
    
    def test_invalid_recognized_patterns_type(self):
        """Test that non-list recognized_patterns raises error."""
        with pytest.raises(TypeError):
            PatternRecognitionResult(
                recognized_patterns="not_a_list",
                evidence_bundle=PatternEvidenceBundle(),
            )
    
    def test_invalid_metadata_type(self):
        """Test that non-dict metadata raises error."""
        with pytest.raises(TypeError):
            PatternRecognitionResult(
                recognized_patterns=[],
                evidence_bundle=PatternEvidenceBundle(),
                metadata="not_a_dict"
            )


class TestPatternRecognizerInterface:
    """Test PatternRecognizer abstract base class."""
    
    def test_cannot_instantiate_directly(self):
        """Test that ABC cannot be instantiated."""
        with pytest.raises(TypeError):
            PatternRecognizer()
    
    def test_subclass_must_implement_methods(self):
        """Test that incomplete subclass cannot be instantiated."""
        
        class IncompleteRecognizer(PatternRecognizer):
            """Missing required methods."""
            pass
        
        with pytest.raises(TypeError):
            IncompleteRecognizer()
    
    def test_valid_subclass(self):
        """Test that complete subclass can be instantiated."""
        
        class CompleteRecognizer(PatternRecognizer):
            def analyze_encoded_state(self, encoded_state: Dict[str, Any]) -> PatternRecognitionResult:
                return PatternRecognitionResult(
                    recognized_patterns=[],
                    evidence_bundle=PatternEvidenceBundle()
                )
            
            def analyze_sequence(self, encoded_states: List[Dict[str, Any]]) -> PatternRecognitionResult:
                return PatternRecognitionResult(
                    recognized_patterns=[],
                    evidence_bundle=PatternEvidenceBundle()
                )
            
            def get_supported_pattern_types(self) -> List[str]:
                return ["test_pattern"]
        
        # Should not raise
        recognizer = CompleteRecognizer()
        assert recognizer is not None
        assert recognizer.get_version() == "0.1.0"
        assert recognizer.get_supported_pattern_types() == ["test_pattern"]
    
    def test_get_metadata(self):
        """Test default metadata generation."""
        
        class TestRecognizer(PatternRecognizer):
            def analyze_encoded_state(self, encoded_state: Dict[str, Any]) -> PatternRecognitionResult:
                return PatternRecognitionResult(
                    recognized_patterns=[],
                    evidence_bundle=PatternEvidenceBundle()
                )
            
            def analyze_sequence(self, encoded_states: List[Dict[str, Any]]) -> PatternRecognitionResult:
                return PatternRecognitionResult(
                    recognized_patterns=[],
                    evidence_bundle=PatternEvidenceBundle()
                )
            
            def get_supported_pattern_types(self) -> List[str]:
                return ["pattern1", "pattern2"]
        
        recognizer = TestRecognizer()
        metadata = recognizer.get_metadata()
        
        assert metadata["recognizer_type"] == "TestRecognizer"
        assert metadata["version"] == "0.1.0"
        assert metadata["supported_patterns"] == ["pattern1", "pattern2"]


class TestSequenceAnalyzerInterface:
    """Test SequenceAnalyzer abstract base class."""
    
    def test_cannot_instantiate_directly(self):
        """Test that ABC cannot be instantiated."""
        with pytest.raises(TypeError):
            SequenceAnalyzer()
    
    def test_subclass_must_implement_methods(self):
        """Test that incomplete subclass cannot be instantiated."""
        
        class IncompleteAnalyzer(SequenceAnalyzer):
            pass
        
        with pytest.raises(TypeError):
            IncompleteAnalyzer()
    
    def test_valid_subclass(self):
        """Test that complete subclass can be instantiated."""
        
        class CompleteAnalyzer(SequenceAnalyzer):
            def analyze_temporal_context(
                self,
                encoded_states: List[Dict[str, Any]],
                window_size=None
            ) -> PatternEvidenceBundle:
                return PatternEvidenceBundle()
            
            def get_sequence_requirements(self) -> Dict[str, Any]:
                return {"min_length": 2}
        
        # Should not raise
        analyzer = CompleteAnalyzer()
        assert analyzer is not None
        reqs = analyzer.get_sequence_requirements()
        assert reqs["min_length"] == 2


class TestPatternAggregationEngineInterface:
    """Test PatternAggregationEngine abstract base class."""
    
    def test_cannot_instantiate_directly(self):
        """Test that ABC cannot be instantiated."""
        with pytest.raises(TypeError):
            PatternAggregationEngine()
    
    def test_subclass_must_implement_methods(self):
        """Test that incomplete subclass cannot be instantiated."""
        
        class IncompleteEngine(PatternAggregationEngine):
            pass
        
        with pytest.raises(TypeError):
            IncompleteEngine()
    
    def test_valid_subclass(self):
        """Test that complete subclass can be instantiated."""
        
        class CompleteEngine(PatternAggregationEngine):
            def aggregate_evidence(
                self,
                recognition_results: List[PatternRecognitionResult]
            ) -> PatternRecognitionResult:
                return PatternRecognitionResult(
                    recognized_patterns=[],
                    evidence_bundle=PatternEvidenceBundle()
                )
            
            def resolve_conflicts(self, conflicting_patterns: List[str]) -> List[str]:
                return conflicting_patterns[:1]  # Just return first one
        
        # Should not raise
        engine = CompleteEngine()
        assert engine is not None
        
        # Test methods
        result = engine.aggregate_evidence([])
        assert isinstance(result, PatternRecognitionResult)
        
        resolved = engine.resolve_conflicts(["p1", "p2"])
        assert resolved == ["p1"]
