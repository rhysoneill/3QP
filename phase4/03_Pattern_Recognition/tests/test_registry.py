"""
Tests for pattern recognizer registry.

Tests registration, retrieval, and management of recognizers.
"""

import pytest

from pattern_recognition.registry import (
    PatternRecognizerRegistry,
    create_default_registry,
)
from pattern_recognition.recognizers import (
    StablePatternRecognizer,
    DriftPatternRecognizer,
    DisruptionPatternRecognizer,
    RecoveryPatternRecognizer,
)
from pattern_recognition.interfaces import PatternRecognizer


class TestPatternRecognizerRegistry:
    """Test PatternRecognizerRegistry."""
    
    def test_empty_registry_creation(self):
        """Test creating empty registry."""
        registry = PatternRecognizerRegistry()
        assert registry is not None
        assert len(registry.list_registered_recognizers()) == 0
        assert len(registry.list_registered_patterns()) == 0
    
    def test_register_recognizer(self):
        """Test registering a recognizer."""
        registry = PatternRecognizerRegistry()
        recognizer = StablePatternRecognizer()
        
        registry.register_recognizer("stable", recognizer)
        
        assert "stable" in registry.list_registered_recognizers()
        retrieved = registry.get_recognizer("stable")
        assert retrieved is recognizer
    
    def test_register_duplicate_raises_error(self):
        """Test that duplicate registration raises error."""
        registry = PatternRecognizerRegistry()
        recognizer1 = StablePatternRecognizer()
        recognizer2 = StablePatternRecognizer()
        
        registry.register_recognizer("stable", recognizer1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register_recognizer("stable", recognizer2)
    
    def test_register_duplicate_with_override(self):
        """Test overriding existing registration."""
        registry = PatternRecognizerRegistry()
        recognizer1 = StablePatternRecognizer()
        recognizer2 = DriftPatternRecognizer()
        
        registry.register_recognizer("test", recognizer1)
        registry.register_recognizer("test", recognizer2, allow_override=True)
        
        retrieved = registry.get_recognizer("test")
        assert isinstance(retrieved, DriftPatternRecognizer)
    
    def test_register_invalid_type_raises_error(self):
        """Test that registering non-recognizer raises error."""
        registry = PatternRecognizerRegistry()
        
        with pytest.raises(TypeError, match="must be a PatternRecognizer instance"):
            registry.register_recognizer("invalid", "not_a_recognizer")
    
    def test_get_nonexistent_recognizer(self):
        """Test getting non-existent recognizer returns None."""
        registry = PatternRecognizerRegistry()
        result = registry.get_recognizer("nonexistent")
        assert result is None
    
    def test_list_registered_patterns(self):
        """Test listing all registered pattern types."""
        registry = PatternRecognizerRegistry()
        
        registry.register_recognizer("stable", StablePatternRecognizer())
        registry.register_recognizer("drift", DriftPatternRecognizer())
        
        patterns = registry.list_registered_patterns()
        
        # Should have patterns from both recognizers
        assert "stable_equilibrium" in patterns
        assert "gradual_drift" in patterns
    
    def test_get_recognizers_for_pattern(self):
        """Test getting recognizers by pattern type."""
        registry = PatternRecognizerRegistry()
        
        stable_rec = StablePatternRecognizer()
        registry.register_recognizer("stable", stable_rec)
        
        # Get recognizers for stable patterns
        recognizers = registry.get_recognizers_for_pattern("stable_equilibrium")
        assert len(recognizers) == 1
        assert recognizers[0] is stable_rec
    
    def test_get_recognizers_for_nonexistent_pattern(self):
        """Test getting recognizers for unknown pattern."""
        registry = PatternRecognizerRegistry()
        recognizers = registry.get_recognizers_for_pattern("unknown_pattern")
        assert recognizers == []
    
    def test_get_recognizer_info(self):
        """Test getting recognizer metadata."""
        registry = PatternRecognizerRegistry()
        registry.register_recognizer("stable", StablePatternRecognizer())
        
        info = registry.get_recognizer_info("stable")
        
        assert info is not None
        assert info["recognizer_id"] == "stable"
        assert info["recognizer_type"] == "StablePatternRecognizer"
        assert "version" in info
        assert "supported_patterns" in info
        assert "metadata" in info
    
    def test_get_recognizer_info_nonexistent(self):
        """Test getting info for non-existent recognizer."""
        registry = PatternRecognizerRegistry()
        info = registry.get_recognizer_info("nonexistent")
        assert info is None
    
    def test_get_all_recognizers(self):
        """Test getting all registered recognizers."""
        registry = PatternRecognizerRegistry()
        
        stable = StablePatternRecognizer()
        drift = DriftPatternRecognizer()
        
        registry.register_recognizer("stable", stable)
        registry.register_recognizer("drift", drift)
        
        all_recognizers = registry.get_all_recognizers()
        
        assert len(all_recognizers) == 2
        assert all_recognizers["stable"] is stable
        assert all_recognizers["drift"] is drift
        
        # Verify it's a copy
        all_recognizers["new"] = StablePatternRecognizer()
        assert "new" not in registry.list_registered_recognizers()
    
    def test_unregister_recognizer(self):
        """Test unregistering a recognizer."""
        registry = PatternRecognizerRegistry()
        registry.register_recognizer("stable", StablePatternRecognizer())
        
        assert "stable" in registry.list_registered_recognizers()
        
        result = registry.unregister_recognizer("stable")
        assert result is True
        assert "stable" not in registry.list_registered_recognizers()
    
    def test_unregister_nonexistent(self):
        """Test unregistering non-existent recognizer."""
        registry = PatternRecognizerRegistry()
        result = registry.unregister_recognizer("nonexistent")
        assert result is False
    
    def test_unregister_removes_pattern_mappings(self):
        """Test that unregistering removes pattern type mappings."""
        registry = PatternRecognizerRegistry()
        registry.register_recognizer("stable", StablePatternRecognizer())
        
        patterns_before = registry.list_registered_patterns()
        assert len(patterns_before) > 0
        
        registry.unregister_recognizer("stable")
        
        patterns_after = registry.list_registered_patterns()
        assert len(patterns_after) == 0
    
    def test_clear_registry(self):
        """Test clearing all registrations."""
        registry = PatternRecognizerRegistry()
        
        registry.register_recognizer("stable", StablePatternRecognizer())
        registry.register_recognizer("drift", DriftPatternRecognizer())
        
        assert len(registry.list_registered_recognizers()) == 2
        
        registry.clear()
        
        assert len(registry.list_registered_recognizers()) == 0
        assert len(registry.list_registered_patterns()) == 0
    
    def test_get_registry_summary(self):
        """Test getting registry summary."""
        registry = PatternRecognizerRegistry()
        
        registry.register_recognizer("stable", StablePatternRecognizer())
        registry.register_recognizer("drift", DriftPatternRecognizer())
        
        summary = registry.get_registry_summary()
        
        assert summary["total_recognizers"] == 2
        assert summary["total_pattern_types"] > 0
        assert "recognizer_ids" in summary
        assert "pattern_types" in summary
        assert "recognizers" in summary
        
        # Check recognizers list
        assert len(summary["recognizers"]) == 2


class TestCreateDefaultRegistry:
    """Test create_default_registry function."""
    
    def test_creates_registry(self):
        """Test that function creates a registry."""
        registry = create_default_registry()
        assert isinstance(registry, PatternRecognizerRegistry)
    
    def test_registers_all_default_recognizers(self):
        """Test that all default recognizers are registered."""
        registry = create_default_registry()
        
        recognizers = registry.list_registered_recognizers()
        
        assert "stable_pattern" in recognizers
        assert "drift_pattern" in recognizers
        assert "disruption_pattern" in recognizers
        assert "recovery_pattern" in recognizers
    
    def test_all_recognizers_retrievable(self):
        """Test that all registered recognizers can be retrieved."""
        registry = create_default_registry()
        
        stable = registry.get_recognizer("stable_pattern")
        assert isinstance(stable, StablePatternRecognizer)
        
        drift = registry.get_recognizer("drift_pattern")
        assert isinstance(drift, DriftPatternRecognizer)
        
        disruption = registry.get_recognizer("disruption_pattern")
        assert isinstance(disruption, DisruptionPatternRecognizer)
        
        recovery = registry.get_recognizer("recovery_pattern")
        assert isinstance(recovery, RecoveryPatternRecognizer)
    
    def test_pattern_types_registered(self):
        """Test that all pattern types are registered."""
        registry = create_default_registry()
        
        patterns = registry.list_registered_patterns()
        
        # Should have many patterns from all recognizers
        assert len(patterns) > 10
        
        # Check some expected patterns
        assert "stable_equilibrium" in patterns
        assert "gradual_drift" in patterns
        assert "sudden_disruption" in patterns
        assert "recovery_trajectory" in patterns
    
    def test_registry_summary(self):
        """Test summary of default registry."""
        registry = create_default_registry()
        summary = registry.get_registry_summary()
        
        assert summary["total_recognizers"] == 4
        assert summary["total_pattern_types"] > 10
    
    def test_can_query_by_pattern(self):
        """Test querying recognizers by pattern type."""
        registry = create_default_registry()
        
        # Get recognizers for drift patterns
        drift_recognizers = registry.get_recognizers_for_pattern("gradual_drift")
        assert len(drift_recognizers) == 1
        assert isinstance(drift_recognizers[0], DriftPatternRecognizer)
