"""
Tests for trajectory analysis interfaces.

Validates abstract base classes, interface contracts, and default
method implementations.
"""

import pytest
from abc import ABC

from trajectory_analysis.interfaces import (
    TrajectoryAnalyzer,
    TrajectoryClassifier,
    TrajectoryAggregationEngine
)
from trajectory_analysis.models import (
    TrajectoryAnalysisResult,
    TrajectoryClassificationResult
)


class TestTrajectoryAnalyzerInterface:
    """Tests for TrajectoryAnalyzer ABC."""
    
    def test_cannot_instantiate_directly(self):
        """TrajectoryAnalyzer cannot be instantiated as abstract class."""
        with pytest.raises(TypeError):
            TrajectoryAnalyzer()
    
    def test_is_abc(self):
        """TrajectoryAnalyzer is an ABC."""
        assert issubclass(TrajectoryAnalyzer, ABC)
    
    def test_minimal_concrete_implementation(self):
        """Minimal concrete implementation works."""
        
        class MinimalAnalyzer(TrajectoryAnalyzer):
            def analyze_sequence(self, encoded_states, pattern_results):
                from trajectory_analysis.evidence import (
                    TrajectoryEvidenceBundle,
                    TrajectorySupportStrength,
                    TrajectoryEvidence
                )
                from trajectory_analysis.models import (
                    TrajectoryHypothesis,
                    TrajectoryAnalysisResult
                )
                
                hyp = TrajectoryHypothesis(
                    archetype_id="test",
                    label="Test",
                    support_strength=TrajectorySupportStrength.WEAK,
                    rationale="Test rationale"
                )
                
                evidence = TrajectoryEvidence(
                    archetype_id="test",
                    support_strength=TrajectorySupportStrength.WEAK,
                    narrative="Test evidence"
                )
                
                return TrajectoryAnalysisResult(
                    hypotheses=[hyp],
                    evidence_bundle=TrajectoryEvidenceBundle(items=[evidence]),
                    analyzer_id="minimal",
                    analyzer_version="1.0"
                )
            
            def get_supported_archetypes(self):
                return ["test"]
        
        analyzer = MinimalAnalyzer()
        assert isinstance(analyzer, TrajectoryAnalyzer)
        assert analyzer.get_supported_archetypes() == ["test"]
    
    def test_default_get_version(self):
        """Default get_version returns expected value."""
        
        class TestAnalyzer(TrajectoryAnalyzer):
            def analyze_sequence(self, encoded_states, pattern_results):
                pass
            
            def get_supported_archetypes(self):
                return []
        
        analyzer = TestAnalyzer()
        assert analyzer.get_version() == "0.1.0"
    
    def test_default_get_metadata(self):
        """Default get_metadata returns expected structure."""
        
        class TestAnalyzer(TrajectoryAnalyzer):
            def analyze_sequence(self, encoded_states, pattern_results):
                pass
            
            def get_supported_archetypes(self):
                return []
        
        analyzer = TestAnalyzer()
        metadata = analyzer.get_metadata()
        
        assert isinstance(metadata, dict)
        assert "component" in metadata
        assert "version" in metadata
        assert metadata["component"] == "TrajectoryAnalyzer"
        assert metadata["version"] == "0.1.0"


class TestTrajectoryClassifierInterface:
    """Tests for TrajectoryClassifier ABC."""
    
    def test_cannot_instantiate_directly(self):
        """TrajectoryClassifier cannot be instantiated as abstract class."""
        with pytest.raises(TypeError):
            TrajectoryClassifier()
    
    def test_is_abc(self):
        """TrajectoryClassifier is an ABC."""
        assert issubclass(TrajectoryClassifier, ABC)
    
    def test_minimal_concrete_implementation(self):
        """Minimal concrete implementation works."""
        
        class MinimalClassifier(TrajectoryClassifier):
            def classify(self, analysis_result):
                from trajectory_analysis.evidence import TrajectoryEvidenceBundle
                
                return TrajectoryClassificationResult(
                    candidate_hypotheses=[],
                    supporting_evidence=TrajectoryEvidenceBundle(),
                    metadata={"test": "true"}
                )
            
            def get_supported_archetypes(self):
                return ["test"]
        
        classifier = MinimalClassifier()
        assert isinstance(classifier, TrajectoryClassifier)
        assert classifier.get_supported_archetypes() == ["test"]
    
    def test_default_get_version(self):
        """Default get_version returns expected value."""
        
        class TestClassifier(TrajectoryClassifier):
            def classify(self, analysis_result):
                pass
            
            def get_supported_archetypes(self):
                return []
        
        classifier = TestClassifier()
        assert classifier.get_version() == "0.1.0"
    
    def test_default_get_metadata(self):
        """Default get_metadata returns expected structure."""
        
        class TestClassifier(TrajectoryClassifier):
            def classify(self, analysis_result):
                pass
            
            def get_supported_archetypes(self):
                return []
        
        classifier = TestClassifier()
        metadata = classifier.get_metadata()
        
        assert isinstance(metadata, dict)
        assert "component" in metadata
        assert "version" in metadata
        assert metadata["component"] == "TrajectoryClassifier"
        assert metadata["version"] == "0.1.0"


class TestTrajectoryAggregationEngineInterface:
    """Tests for TrajectoryAggregationEngine ABC."""
    
    def test_cannot_instantiate_directly(self):
        """TrajectoryAggregationEngine cannot be instantiated as abstract class."""
        with pytest.raises(TypeError):
            TrajectoryAggregationEngine()
    
    def test_is_abc(self):
        """TrajectoryAggregationEngine is an ABC."""
        assert issubclass(TrajectoryAggregationEngine, ABC)
    
    def test_minimal_concrete_implementation(self):
        """Minimal concrete implementation works."""
        
        class MinimalEngine(TrajectoryAggregationEngine):
            def aggregate(self, analysis_results):
                from trajectory_analysis.evidence import TrajectoryEvidenceBundle
                
                return TrajectoryClassificationResult(
                    candidate_hypotheses=[],
                    supporting_evidence=TrajectoryEvidenceBundle(),
                    metadata={"aggregated": "true"}
                )
            
            def resolve_conflicts(self, classifications):
                return classifications[0] if classifications else None
        
        engine = MinimalEngine()
        assert isinstance(engine, TrajectoryAggregationEngine)
    
    def test_default_get_version(self):
        """Default get_version returns expected value."""
        
        class TestEngine(TrajectoryAggregationEngine):
            def aggregate(self, analysis_results):
                pass
            
            def resolve_conflicts(self, classifications):
                pass
        
        engine = TestEngine()
        assert engine.get_version() == "0.1.0"
    
    def test_default_get_metadata(self):
        """Default get_metadata returns expected structure."""
        
        class TestEngine(TrajectoryAggregationEngine):
            def aggregate(self, analysis_results):
                pass
            
            def resolve_conflicts(self, classifications):
                pass
        
        engine = TestEngine()
        metadata = engine.get_metadata()
        
        assert isinstance(metadata, dict)
        assert "component" in metadata
        assert "version" in metadata
        assert metadata["component"] == "TrajectoryAggregationEngine"
        assert metadata["version"] == "0.1.0"
