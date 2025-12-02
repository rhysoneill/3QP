"""
Tests for trajectory analysis registry.

Validates component registration, retrieval, and metadata operations.
"""

import pytest

from trajectory_analysis.registry import (
    TrajectoryAnalysisRegistry,
    create_default_registry
)
from trajectory_analysis.analyzers import (
    SimpleTrajectoryAnalyzer,
    StableAdaptationAnalyzer,
    TrajectoryHeuristicClassifier
)
from trajectory_analysis.interfaces import (
    TrajectoryAnalyzer,
    TrajectoryClassifier
)
from trajectory_analysis.models import TrajectoryAnalysisResult
from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidenceBundle
)


class TestTrajectoryAnalysisRegistry:
    """Tests for TrajectoryAnalysisRegistry."""
    
    def test_creation_empty(self):
        """Registry can be created empty."""
        registry = TrajectoryAnalysisRegistry()
        
        assert registry.list_analyzers() == []
        assert registry.list_classifiers() == []
    
    def test_register_analyzer(self):
        """Analyzer can be registered."""
        registry = TrajectoryAnalysisRegistry()
        analyzer = SimpleTrajectoryAnalyzer()
        
        registry.register_analyzer("test_analyzer", analyzer)
        
        assert "test_analyzer" in registry.list_analyzers()
    
    def test_register_analyzer_type_check(self):
        """register_analyzer validates type."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(TypeError, match="TrajectoryAnalyzer"):
            registry.register_analyzer("invalid", "not_an_analyzer")
    
    def test_register_analyzer_empty_id(self):
        """register_analyzer validates ID."""
        registry = TrajectoryAnalysisRegistry()
        analyzer = SimpleTrajectoryAnalyzer()
        
        with pytest.raises(ValueError, match="analyzer_id"):
            registry.register_analyzer("", analyzer)
    
    def test_register_analyzer_overwrite(self):
        """Registering duplicate ID overwrites existing."""
        registry = TrajectoryAnalysisRegistry()
        
        analyzer1 = SimpleTrajectoryAnalyzer()
        analyzer2 = StableAdaptationAnalyzer()
        
        registry.register_analyzer("test", analyzer1)
        registry.register_analyzer("test", analyzer2)
        
        # Should get the second one
        retrieved = registry.get_analyzer("test")
        assert isinstance(retrieved, StableAdaptationAnalyzer)
    
    def test_register_classifier(self):
        """Classifier can be registered."""
        registry = TrajectoryAnalysisRegistry()
        classifier = TrajectoryHeuristicClassifier()
        
        registry.register_classifier("test_classifier", classifier)
        
        assert "test_classifier" in registry.list_classifiers()
    
    def test_register_classifier_type_check(self):
        """register_classifier validates type."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(TypeError, match="TrajectoryClassifier"):
            registry.register_classifier("invalid", "not_a_classifier")
    
    def test_register_classifier_empty_id(self):
        """register_classifier validates ID."""
        registry = TrajectoryAnalysisRegistry()
        classifier = TrajectoryHeuristicClassifier()
        
        with pytest.raises(ValueError, match="classifier_id"):
            registry.register_classifier("", classifier)
    
    def test_get_analyzer(self):
        """get_analyzer retrieves registered analyzer."""
        registry = TrajectoryAnalysisRegistry()
        analyzer = SimpleTrajectoryAnalyzer()
        
        registry.register_analyzer("test", analyzer)
        retrieved = registry.get_analyzer("test")
        
        assert retrieved == analyzer
    
    def test_get_analyzer_not_found(self):
        """get_analyzer raises KeyError for unknown ID."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(KeyError, match="not_registered"):
            registry.get_analyzer("not_registered")
    
    def test_get_classifier(self):
        """get_classifier retrieves registered classifier."""
        registry = TrajectoryAnalysisRegistry()
        classifier = TrajectoryHeuristicClassifier()
        
        registry.register_classifier("test", classifier)
        retrieved = registry.get_classifier("test")
        
        assert retrieved == classifier
    
    def test_get_classifier_not_found(self):
        """get_classifier raises KeyError for unknown ID."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(KeyError, match="not_found"):
            registry.get_classifier("not_found")
    
    def test_list_analyzers(self):
        """list_analyzers returns all registered IDs."""
        registry = TrajectoryAnalysisRegistry()
        
        registry.register_analyzer("analyzer1", SimpleTrajectoryAnalyzer())
        registry.register_analyzer("analyzer2", StableAdaptationAnalyzer())
        
        ids = registry.list_analyzers()
        
        assert len(ids) == 2
        assert "analyzer1" in ids
        assert "analyzer2" in ids
    
    def test_list_classifiers(self):
        """list_classifiers returns all registered IDs."""
        registry = TrajectoryAnalysisRegistry()
        
        registry.register_classifier("classifier1", TrajectoryHeuristicClassifier())
        
        ids = registry.list_classifiers()
        
        assert len(ids) == 1
        assert "classifier1" in ids
    
    def test_get_analyzer_info(self):
        """get_analyzer_info returns metadata."""
        registry = TrajectoryAnalysisRegistry()
        analyzer = SimpleTrajectoryAnalyzer()
        
        registry.register_analyzer("test", analyzer)
        info = registry.get_analyzer_info("test")
        
        assert isinstance(info, dict)
        assert info["analyzer_id"] == "test"
        assert "supported_archetypes" in info
        assert "version" in info
        assert "metadata" in info
    
    def test_get_analyzer_info_not_found(self):
        """get_analyzer_info raises KeyError for unknown ID."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(KeyError):
            registry.get_analyzer_info("unknown")
    
    def test_get_classifier_info(self):
        """get_classifier_info returns metadata."""
        registry = TrajectoryAnalysisRegistry()
        classifier = TrajectoryHeuristicClassifier()
        
        registry.register_classifier("test", classifier)
        info = registry.get_classifier_info("test")
        
        assert isinstance(info, dict)
        assert info["classifier_id"] == "test"
        assert "supported_archetypes" in info
        assert "version" in info
        assert "metadata" in info
    
    def test_get_classifier_info_not_found(self):
        """get_classifier_info raises KeyError for unknown ID."""
        registry = TrajectoryAnalysisRegistry()
        
        with pytest.raises(KeyError):
            registry.get_classifier_info("unknown")
    
    def test_clear(self):
        """clear removes all registered components."""
        registry = TrajectoryAnalysisRegistry()
        
        registry.register_analyzer("analyzer", SimpleTrajectoryAnalyzer())
        registry.register_classifier("classifier", TrajectoryHeuristicClassifier())
        
        assert len(registry.list_analyzers()) > 0
        assert len(registry.list_classifiers()) > 0
        
        registry.clear()
        
        assert registry.list_analyzers() == []
        assert registry.list_classifiers() == []


class TestCreateDefaultRegistry:
    """Tests for create_default_registry factory function."""
    
    def test_creates_registry(self):
        """create_default_registry returns TrajectoryAnalysisRegistry."""
        registry = create_default_registry()
        
        assert isinstance(registry, TrajectoryAnalysisRegistry)
    
    def test_registers_simple_placeholder_analyzer(self):
        """Default registry includes simple_placeholder analyzer."""
        registry = create_default_registry()
        
        assert "simple_placeholder" in registry.list_analyzers()
        analyzer = registry.get_analyzer("simple_placeholder")
        assert isinstance(analyzer, SimpleTrajectoryAnalyzer)
    
    def test_registers_stable_adaptation_analyzer(self):
        """Default registry includes stable_adaptation analyzer."""
        registry = create_default_registry()
        
        assert "stable_adaptation" in registry.list_analyzers()
        analyzer = registry.get_analyzer("stable_adaptation")
        assert isinstance(analyzer, StableAdaptationAnalyzer)
    
    def test_registers_simple_classifier(self):
        """Default registry includes simple_classifier."""
        registry = create_default_registry()
        
        assert "simple_classifier" in registry.list_classifiers()
        classifier = registry.get_classifier("simple_classifier")
        assert isinstance(classifier, TrajectoryHeuristicClassifier)
    
    def test_all_components_functional(self):
        """All default components are functional."""
        registry = create_default_registry()
        
        # Test analyzer
        analyzer = registry.get_analyzer("simple_placeholder")
        result = analyzer.analyze_sequence([], [])
        assert isinstance(result, TrajectoryAnalysisResult)
        
        # Test classifier
        classifier = registry.get_classifier("simple_classifier")
        classification = classifier.classify(result)
        assert classification is not None
