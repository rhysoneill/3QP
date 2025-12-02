"""
Registry for trajectory analyzers and classifiers.

This module provides a centralized registry for managing trajectory
analysis components, similar to the pattern recognizer registry in WS3.
"""

from typing import Optional

from .interfaces import TrajectoryAnalyzer, TrajectoryClassifier
from .analyzers import (
    SimpleTrajectoryAnalyzer,
    StableAdaptationAnalyzer,
    TrajectoryHeuristicClassifier
)


class TrajectoryAnalysisRegistry:
    """
    Central registry for trajectory analyzers and classifiers.
    
    Manages registration, retrieval, and metadata for all trajectory
    analysis components in the system.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._analyzers: dict[str, TrajectoryAnalyzer] = {}
        self._classifiers: dict[str, TrajectoryClassifier] = {}
    
    def register_analyzer(
        self,
        analyzer_id: str,
        analyzer: TrajectoryAnalyzer
    ) -> None:
        """
        Register a trajectory analyzer.
        
        If analyzer_id already exists, the new analyzer will overwrite
        the existing one.
        
        Args:
            analyzer_id: Unique identifier for the analyzer
            analyzer: TrajectoryAnalyzer instance to register
            
        Raises:
            TypeError: If analyzer is not a TrajectoryAnalyzer instance
            ValueError: If analyzer_id is empty
        """
        if not isinstance(analyzer, TrajectoryAnalyzer):
            raise TypeError(
                f"analyzer must be TrajectoryAnalyzer instance, "
                f"got {type(analyzer)}"
            )
        
        if not analyzer_id or not isinstance(analyzer_id, str):
            raise ValueError("analyzer_id must be a non-empty string")
        
        # Overwrite if duplicate (documented behavior)
        self._analyzers[analyzer_id] = analyzer
    
    def register_classifier(
        self,
        classifier_id: str,
        classifier: TrajectoryClassifier
    ) -> None:
        """
        Register a trajectory classifier.
        
        If classifier_id already exists, the new classifier will overwrite
        the existing one.
        
        Args:
            classifier_id: Unique identifier for the classifier
            classifier: TrajectoryClassifier instance to register
            
        Raises:
            TypeError: If classifier is not a TrajectoryClassifier instance
            ValueError: If classifier_id is empty
        """
        if not isinstance(classifier, TrajectoryClassifier):
            raise TypeError(
                f"classifier must be TrajectoryClassifier instance, "
                f"got {type(classifier)}"
            )
        
        if not classifier_id or not isinstance(classifier_id, str):
            raise ValueError("classifier_id must be a non-empty string")
        
        # Overwrite if duplicate (documented behavior)
        self._classifiers[classifier_id] = classifier
    
    def get_analyzer(self, analyzer_id: str) -> TrajectoryAnalyzer:
        """
        Retrieve a registered analyzer by ID.
        
        Args:
            analyzer_id: Identifier of the analyzer to retrieve
            
        Returns:
            Registered TrajectoryAnalyzer instance
            
        Raises:
            KeyError: If analyzer_id is not registered
        """
        if analyzer_id not in self._analyzers:
            raise KeyError(f"Analyzer '{analyzer_id}' not registered")
        return self._analyzers[analyzer_id]
    
    def get_classifier(self, classifier_id: str) -> TrajectoryClassifier:
        """
        Retrieve a registered classifier by ID.
        
        Args:
            classifier_id: Identifier of the classifier to retrieve
            
        Returns:
            Registered TrajectoryClassifier instance
            
        Raises:
            KeyError: If classifier_id is not registered
        """
        if classifier_id not in self._classifiers:
            raise KeyError(f"Classifier '{classifier_id}' not registered")
        return self._classifiers[classifier_id]
    
    def list_analyzers(self) -> list[str]:
        """
        List all registered analyzer IDs.
        
        Returns:
            List of analyzer identifier strings
        """
        return list(self._analyzers.keys())
    
    def list_classifiers(self) -> list[str]:
        """
        List all registered classifier IDs.
        
        Returns:
            List of classifier identifier strings
        """
        return list(self._classifiers.keys())
    
    def get_analyzer_info(self, analyzer_id: str) -> dict:
        """
        Get metadata information about a registered analyzer.
        
        Args:
            analyzer_id: Identifier of the analyzer
            
        Returns:
            Dictionary with analyzer metadata
            
        Raises:
            KeyError: If analyzer_id is not registered
        """
        analyzer = self.get_analyzer(analyzer_id)
        
        return {
            "analyzer_id": analyzer_id,
            "supported_archetypes": analyzer.get_supported_archetypes(),
            "version": analyzer.get_version(),
            "metadata": analyzer.get_metadata()
        }
    
    def get_classifier_info(self, classifier_id: str) -> dict:
        """
        Get metadata information about a registered classifier.
        
        Args:
            classifier_id: Identifier of the classifier
            
        Returns:
            Dictionary with classifier metadata
            
        Raises:
            KeyError: If classifier_id is not registered
        """
        classifier = self.get_classifier(classifier_id)
        
        return {
            "classifier_id": classifier_id,
            "supported_archetypes": classifier.get_supported_archetypes(),
            "version": classifier.get_version(),
            "metadata": classifier.get_metadata()
        }
    
    def clear(self) -> None:
        """
        Clear all registered analyzers and classifiers.
        
        Used primarily for testing and reinitialization.
        """
        self._analyzers.clear()
        self._classifiers.clear()


def create_default_registry() -> TrajectoryAnalysisRegistry:
    """
    Create a registry pre-populated with default components.
    
    Registers:
    - simple_placeholder: SimpleTrajectoryAnalyzer
    - stable_adaptation: StableAdaptationAnalyzer
    - simple_classifier: TrajectoryHeuristicClassifier
    
    Returns:
        TrajectoryAnalysisRegistry with default components registered
    """
    registry = TrajectoryAnalysisRegistry()
    
    # Register analyzers
    registry.register_analyzer(
        "simple_placeholder",
        SimpleTrajectoryAnalyzer()
    )
    
    registry.register_analyzer(
        "stable_adaptation",
        StableAdaptationAnalyzer()
    )
    
    # Register classifier
    registry.register_classifier(
        "simple_classifier",
        TrajectoryHeuristicClassifier()
    )
    
    return registry
