"""
Central registry for pattern recognizers.

Manages registration, retrieval, and versioning of recognizers.
NO COMPUTATION - only storage and retrieval.
"""

from typing import Dict, List, Optional, Type
from .interfaces import PatternRecognizer
from .recognizers import (
    StablePatternRecognizer,
    DriftPatternRecognizer,
    DisruptionPatternRecognizer,
    RecoveryPatternRecognizer,
)


class PatternRecognizerRegistry:
    """
    Central registry for managing pattern recognizers.
    
    Provides registration, retrieval, and validation of recognizers.
    NO COMPUTATION - only organizational logic.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._recognizers: Dict[str, PatternRecognizer] = {}
        self._pattern_type_map: Dict[str, List[str]] = {}  # pattern_type -> [recognizer_ids]
    
    def register_recognizer(
        self,
        recognizer_id: str,
        recognizer: PatternRecognizer,
        allow_override: bool = False
    ) -> None:
        """
        Register a pattern recognizer.
        
        Args:
            recognizer_id: Unique identifier for the recognizer
            recognizer: PatternRecognizer instance
            allow_override: Whether to allow overriding existing registration
        
        Raises:
            TypeError: If recognizer is not a PatternRecognizer instance
            ValueError: If recognizer_id already registered and allow_override is False
        """
        if not isinstance(recognizer, PatternRecognizer):
            raise TypeError(
                f"recognizer must be a PatternRecognizer instance, "
                f"got {type(recognizer).__name__}"
            )
        
        if recognizer_id in self._recognizers and not allow_override:
            raise ValueError(
                f"Recognizer '{recognizer_id}' is already registered. "
                f"Set allow_override=True to override."
            )
        
        # Register the recognizer
        self._recognizers[recognizer_id] = recognizer
        
        # Update pattern type mappings
        for pattern_type in recognizer.get_supported_pattern_types():
            if pattern_type not in self._pattern_type_map:
                self._pattern_type_map[pattern_type] = []
            
            if recognizer_id not in self._pattern_type_map[pattern_type]:
                self._pattern_type_map[pattern_type].append(recognizer_id)
    
    def get_recognizer(self, recognizer_id: str) -> Optional[PatternRecognizer]:
        """
        Retrieve a registered recognizer by ID.
        
        Args:
            recognizer_id: Recognizer identifier
        
        Returns:
            PatternRecognizer instance or None if not found
        """
        return self._recognizers.get(recognizer_id)
    
    def get_recognizers_for_pattern(self, pattern_type: str) -> List[PatternRecognizer]:
        """
        Get all recognizers that support a specific pattern type.
        
        Args:
            pattern_type: Pattern type identifier
        
        Returns:
            List of PatternRecognizer instances
        """
        recognizer_ids = self._pattern_type_map.get(pattern_type, [])
        return [
            self._recognizers[rid]
            for rid in recognizer_ids
            if rid in self._recognizers
        ]
    
    def list_registered_patterns(self) -> List[str]:
        """
        Get list of all registered pattern types.
        
        Returns:
            List of pattern type identifiers
        """
        return list(self._pattern_type_map.keys())
    
    def list_registered_recognizers(self) -> List[str]:
        """
        Get list of all registered recognizer IDs.
        
        Returns:
            List of recognizer identifiers
        """
        return list(self._recognizers.keys())
    
    def get_recognizer_info(self, recognizer_id: str) -> Optional[Dict]:
        """
        Get metadata about a registered recognizer.
        
        Args:
            recognizer_id: Recognizer identifier
        
        Returns:
            Dictionary of recognizer metadata or None if not found
        """
        recognizer = self.get_recognizer(recognizer_id)
        if recognizer is None:
            return None
        
        return {
            "recognizer_id": recognizer_id,
            "recognizer_type": type(recognizer).__name__,
            "version": recognizer.get_version(),
            "supported_patterns": recognizer.get_supported_pattern_types(),
            "metadata": recognizer.get_metadata(),
        }
    
    def get_all_recognizers(self) -> Dict[str, PatternRecognizer]:
        """
        Get all registered recognizers.
        
        Returns:
            Dictionary mapping recognizer IDs to instances
        """
        return self._recognizers.copy()
    
    def unregister_recognizer(self, recognizer_id: str) -> bool:
        """
        Unregister a recognizer.
        
        Args:
            recognizer_id: Recognizer identifier
        
        Returns:
            True if recognizer was unregistered, False if not found
        """
        if recognizer_id not in self._recognizers:
            return False
        
        # Get pattern types before removing
        recognizer = self._recognizers[recognizer_id]
        pattern_types = recognizer.get_supported_pattern_types()
        
        # Remove from main registry
        del self._recognizers[recognizer_id]
        
        # Remove from pattern type mappings
        for pattern_type in pattern_types:
            if pattern_type in self._pattern_type_map:
                if recognizer_id in self._pattern_type_map[pattern_type]:
                    self._pattern_type_map[pattern_type].remove(recognizer_id)
                
                # Clean up empty pattern type entries
                if not self._pattern_type_map[pattern_type]:
                    del self._pattern_type_map[pattern_type]
        
        return True
    
    def clear(self) -> None:
        """Clear all registered recognizers."""
        self._recognizers.clear()
        self._pattern_type_map.clear()
    
    def get_registry_summary(self) -> Dict:
        """
        Get summary of registry contents.
        
        Returns:
            Dictionary summarizing registry state
        """
        return {
            "total_recognizers": len(self._recognizers),
            "total_pattern_types": len(self._pattern_type_map),
            "recognizer_ids": self.list_registered_recognizers(),
            "pattern_types": self.list_registered_patterns(),
            "recognizers": [
                self.get_recognizer_info(rid)
                for rid in self.list_registered_recognizers()
            ],
        }


def create_default_registry() -> PatternRecognizerRegistry:
    """
    Create and populate a registry with default recognizers.
    
    Returns:
        PatternRecognizerRegistry with all standard recognizers registered
    """
    registry = PatternRecognizerRegistry()
    
    # Register all default recognizers
    registry.register_recognizer(
        "stable_pattern",
        StablePatternRecognizer()
    )
    
    registry.register_recognizer(
        "drift_pattern",
        DriftPatternRecognizer()
    )
    
    registry.register_recognizer(
        "disruption_pattern",
        DisruptionPatternRecognizer()
    )
    
    registry.register_recognizer(
        "recovery_pattern",
        RecoveryPatternRecognizer()
    )
    
    return registry
