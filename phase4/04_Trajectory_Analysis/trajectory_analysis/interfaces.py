"""
Core abstract interfaces for trajectory analysis architecture.

This module defines the contract-level ABCs that trajectory analyzers,
classifiers, and aggregation engines must implement. No computation is
performed here—only structure and method signatures are defined.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TrajectoryAnalysisResult, TrajectoryClassificationResult


class TrajectoryAnalyzer(ABC):
    """
    Abstract base class for trajectory analyzers.
    
    A trajectory analyzer processes sequences of encoded states and
    pattern recognition results to produce trajectory-level hypotheses
    and evidence bundles. This is a structural contract only.
    """
    
    @abstractmethod
    def analyze_sequence(
        self,
        encoded_states: list[dict],
        pattern_results: list[object]
    ) -> "TrajectoryAnalysisResult":
        """
        Analyze a sequence of encoded states and pattern results.
        
        Args:
            encoded_states: List of opaque state dictionaries from WS2
            pattern_results: List of pattern recognition result objects from WS3
            
        Returns:
            TrajectoryAnalysisResult containing hypotheses and evidence
        """
        pass
    
    @abstractmethod
    def get_supported_archetypes(self) -> list[str]:
        """
        Return list of supported trajectory archetype IDs.
        
        Returns:
            List of archetype identifier strings (e.g., ["stable_adaptation"])
        """
        pass
    
    def get_version(self) -> str:
        """
        Return version string for this analyzer.
        
        Returns:
            Version string (default: "0.1.0")
        """
        return "0.1.0"
    
    def get_metadata(self) -> dict:
        """
        Return metadata dictionary for this analyzer.
        
        Returns:
            Dictionary with component and version information
        """
        return {
            "component": "TrajectoryAnalyzer",
            "version": self.get_version()
        }


class TrajectoryClassifier(ABC):
    """
    Abstract base class for trajectory classifiers.
    
    A classifier takes trajectory analysis results and produces
    higher-level classifications with selected archetypes.
    """
    
    @abstractmethod
    def classify(
        self,
        analysis_result: "TrajectoryAnalysisResult"
    ) -> "TrajectoryClassificationResult":
        """
        Classify a trajectory analysis result.
        
        Args:
            analysis_result: Result from a trajectory analyzer
            
        Returns:
            TrajectoryClassificationResult with selected archetype
        """
        pass
    
    @abstractmethod
    def get_supported_archetypes(self) -> list[str]:
        """
        Return list of supported trajectory archetype IDs.
        
        Returns:
            List of archetype identifier strings
        """
        pass
    
    def get_version(self) -> str:
        """
        Return version string for this classifier.
        
        Returns:
            Version string (default: "0.1.0")
        """
        return "0.1.0"
    
    def get_metadata(self) -> dict:
        """
        Return metadata dictionary for this classifier.
        
        Returns:
            Dictionary with component and version information
        """
        return {
            "component": "TrajectoryClassifier",
            "version": self.get_version()
        }


class TrajectoryAggregationEngine(ABC):
    """
    Abstract base class for trajectory aggregation engines.
    
    Aggregates multiple analysis results into combined trajectory views
    and resolves conflicts between classifications.
    """
    
    @abstractmethod
    def aggregate(
        self,
        analysis_results: list["TrajectoryAnalysisResult"]
    ) -> "TrajectoryClassificationResult":
        """
        Aggregate multiple analysis results into a single classification.
        
        Args:
            analysis_results: List of trajectory analysis results
            
        Returns:
            Aggregated TrajectoryClassificationResult
        """
        pass
    
    @abstractmethod
    def resolve_conflicts(
        self,
        classifications: list["TrajectoryClassificationResult"]
    ) -> "TrajectoryClassificationResult":
        """
        Resolve conflicts between multiple classifications.
        
        No real conflict resolution logic. Architecture only.
        
        Args:
            classifications: List of conflicting classifications
            
        Returns:
            Resolved TrajectoryClassificationResult
        """
        pass
    
    def get_version(self) -> str:
        """
        Return version string for this aggregation engine.
        
        Returns:
            Version string (default: "0.1.0")
        """
        return "0.1.0"
    
    def get_metadata(self) -> dict:
        """
        Return metadata dictionary for this aggregation engine.
        
        Returns:
            Dictionary with component and version information
        """
        return {
            "component": "TrajectoryAggregationEngine",
            "version": self.get_version()
        }
