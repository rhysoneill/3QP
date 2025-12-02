"""
Tests for pattern evidence structures.

Tests evidence creation, validation, and bundling.
"""

import pytest
from datetime import datetime

from pattern_recognition.evidence import (
    PatternEvidence,
    PatternEvidenceBundle,
    QualitativeStrength,
)


class TestQualitativeStrength:
    """Test QualitativeStrength enum."""
    
    def test_valid_values(self):
        """Test all valid qualitative strength values."""
        assert QualitativeStrength.SUGGESTIVE.value == "suggestive"
        assert QualitativeStrength.WEAK.value == "weak"
        assert QualitativeStrength.STRONG.value == "strong"
        assert QualitativeStrength.CONTEXTUAL.value == "contextual"
    
    def test_is_valid(self):
        """Test validation method."""
        assert QualitativeStrength.is_valid("suggestive")
        assert QualitativeStrength.is_valid("weak")
        assert QualitativeStrength.is_valid("strong")
        assert QualitativeStrength.is_valid("contextual")
        assert not QualitativeStrength.is_valid("invalid")
        assert not QualitativeStrength.is_valid("numeric_score")


class TestPatternEvidence:
    """Test PatternEvidence dataclass."""
    
    def test_basic_creation(self):
        """Test creating evidence with required fields."""
        evidence = PatternEvidence(
            pattern_type="stable_equilibrium",
            indicator_label="Test indicator",
            qualitative_strength="strong",
            narrative="Test narrative"
        )
        
        assert evidence.pattern_type == "stable_equilibrium"
        assert evidence.indicator_label == "Test indicator"
        assert evidence.qualitative_strength == "strong"
        assert evidence.narrative == "Test narrative"
        assert evidence.source_event is None
        assert evidence.source_state is None
    
    def test_creation_with_all_fields(self):
        """Test creating evidence with all fields."""
        evidence = PatternEvidence(
            pattern_type="gradual_drift",
            indicator_label="Drift indicator",
            qualitative_strength="weak",
            narrative="Gradual drift detected",
            source_event="event_123",
            source_state="state_456",
            metadata={"custom": "data"}
        )
        
        assert evidence.source_event == "event_123"
        assert evidence.source_state == "state_456"
        assert evidence.metadata["custom"] == "data"
    
    def test_invalid_qualitative_strength(self):
        """Test that invalid strength raises error."""
        with pytest.raises(ValueError, match="qualitative_strength must be one of"):
            PatternEvidence(
                pattern_type="test",
                indicator_label="test",
                qualitative_strength="invalid_strength",
                narrative="test"
            )
    
    def test_empty_pattern_type(self):
        """Test that empty pattern_type raises error."""
        with pytest.raises(ValueError, match="pattern_type cannot be empty"):
            PatternEvidence(
                pattern_type="",
                indicator_label="test",
                qualitative_strength="strong",
                narrative="test"
            )
    
    def test_empty_indicator_label(self):
        """Test that empty indicator_label raises error."""
        with pytest.raises(ValueError, match="indicator_label cannot be empty"):
            PatternEvidence(
                pattern_type="test",
                indicator_label="",
                qualitative_strength="strong",
                narrative="test"
            )
    
    def test_empty_narrative(self):
        """Test that empty narrative raises error."""
        with pytest.raises(ValueError, match="narrative cannot be empty"):
            PatternEvidence(
                pattern_type="test",
                indicator_label="test",
                qualitative_strength="strong",
                narrative=""
            )
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        evidence = PatternEvidence(
            pattern_type="test_pattern",
            indicator_label="Test label",
            qualitative_strength="suggestive",
            narrative="Test narrative",
            source_event="event_1"
        )
        
        evidence_dict = evidence.to_dict()
        assert evidence_dict["pattern_type"] == "test_pattern"
        assert evidence_dict["indicator_label"] == "Test label"
        assert evidence_dict["qualitative_strength"] == "suggestive"
        assert evidence_dict["narrative"] == "Test narrative"
        assert evidence_dict["source_event"] == "event_1"
        assert "timestamp" in evidence_dict
    
    def test_to_narrative(self):
        """Test narrative generation."""
        evidence = PatternEvidence(
            pattern_type="disruption",
            indicator_label="Shock detected",
            qualitative_strength="strong",
            narrative="Sudden disruption in system",
            source_state="state_789"
        )
        
        narrative = evidence.to_narrative()
        assert "STRONG" in narrative
        assert "Shock detected" in narrative
        assert "disruption" in narrative
        assert "state_789" in narrative


class TestPatternEvidenceBundle:
    """Test PatternEvidenceBundle."""
    
    def test_empty_bundle_creation(self):
        """Test creating empty bundle."""
        bundle = PatternEvidenceBundle()
        assert bundle.get_evidence_count() == 0
        assert len(bundle.evidence_items) == 0
    
    def test_add_evidence(self):
        """Test adding evidence to bundle."""
        bundle = PatternEvidenceBundle()
        
        evidence = PatternEvidence(
            pattern_type="test",
            indicator_label="test",
            qualitative_strength="weak",
            narrative="test"
        )
        
        bundle.add_evidence(evidence)
        assert bundle.get_evidence_count() == 1
        assert evidence in bundle.evidence_items
    
    def test_add_invalid_evidence(self):
        """Test that adding non-evidence raises error."""
        bundle = PatternEvidenceBundle()
        
        with pytest.raises(TypeError, match="must be a PatternEvidence instance"):
            bundle.add_evidence("not_evidence")
    
    def test_merge_bundles(self):
        """Test merging two bundles."""
        bundle1 = PatternEvidenceBundle()
        bundle1.add_evidence(PatternEvidence(
            pattern_type="p1",
            indicator_label="i1",
            qualitative_strength="weak",
            narrative="n1"
        ))
        
        bundle2 = PatternEvidenceBundle()
        bundle2.add_evidence(PatternEvidence(
            pattern_type="p2",
            indicator_label="i2",
            qualitative_strength="strong",
            narrative="n2"
        ))
        
        merged = bundle1.merge(bundle2)
        assert merged.get_evidence_count() == 2
        assert bundle1.get_evidence_count() == 1  # Original unchanged
        assert bundle2.get_evidence_count() == 1  # Original unchanged
        assert "merged_from" in merged.metadata
    
    def test_merge_invalid_type(self):
        """Test that merging non-bundle raises error."""
        bundle = PatternEvidenceBundle()
        
        with pytest.raises(TypeError, match="must be a PatternEvidenceBundle instance"):
            bundle.merge("not_a_bundle")
    
    def test_filter_by_pattern_type(self):
        """Test filtering by pattern type."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="i1",
            qualitative_strength="weak",
            narrative="n1"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="drift",
            indicator_label="i2",
            qualitative_strength="weak",
            narrative="n2"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="i3",
            qualitative_strength="weak",
            narrative="n3"
        ))
        
        stable_evidence = bundle.filter_by_pattern_type("stable")
        assert len(stable_evidence) == 2
        
        drift_evidence = bundle.filter_by_pattern_type("drift")
        assert len(drift_evidence) == 1
    
    def test_filter_by_strength(self):
        """Test filtering by qualitative strength."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="p1",
            indicator_label="i1",
            qualitative_strength="weak",
            narrative="n1"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="p2",
            indicator_label="i2",
            qualitative_strength="strong",
            narrative="n2"
        ))
        
        weak_evidence = bundle.filter_by_strength("weak")
        assert len(weak_evidence) == 1
        
        strong_evidence = bundle.filter_by_strength("strong")
        assert len(strong_evidence) == 1
    
    def test_filter_by_invalid_strength(self):
        """Test that filtering by invalid strength raises error."""
        bundle = PatternEvidenceBundle()
        
        with pytest.raises(ValueError, match="Invalid qualitative strength"):
            bundle.filter_by_strength("invalid")
    
    def test_get_pattern_types(self):
        """Test getting unique pattern types."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="i1",
            qualitative_strength="weak",
            narrative="n1"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="drift",
            indicator_label="i2",
            qualitative_strength="weak",
            narrative="n2"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="i3",
            qualitative_strength="weak",
            narrative="n3"
        ))
        
        pattern_types = bundle.get_pattern_types()
        assert len(pattern_types) == 2
        assert "stable" in pattern_types
        assert "drift" in pattern_types
    
    def test_get_evidence_by_pattern(self):
        """Test grouping evidence by pattern."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="i1",
            qualitative_strength="weak",
            narrative="n1"
        ))
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="drift",
            indicator_label="i2",
            qualitative_strength="weak",
            narrative="n2"
        ))
        
        by_pattern = bundle.get_evidence_by_pattern()
        assert "stable" in by_pattern
        assert "drift" in by_pattern
        assert len(by_pattern["stable"]) == 1
        assert len(by_pattern["drift"]) == 1
    
    def test_to_narrative_empty(self):
        """Test narrative generation for empty bundle."""
        bundle = PatternEvidenceBundle()
        narrative = bundle.to_narrative()
        assert "No evidence" in narrative
    
    def test_to_narrative_with_evidence(self):
        """Test narrative generation with evidence."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="stable",
            indicator_label="Stability indicator",
            qualitative_strength="strong",
            narrative="System is stable"
        ))
        
        narrative = bundle.to_narrative()
        assert "stable" in narrative
        assert "1 items" in narrative
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        bundle = PatternEvidenceBundle()
        
        bundle.add_evidence(PatternEvidence(
            pattern_type="test",
            indicator_label="test",
            qualitative_strength="weak",
            narrative="test"
        ))
        
        bundle_dict = bundle.to_dict()
        assert "evidence_items" in bundle_dict
        assert "metadata" in bundle_dict
        assert "timestamp" in bundle_dict
        assert "evidence_count" in bundle_dict
        assert "pattern_types" in bundle_dict
        assert bundle_dict["evidence_count"] == 1
