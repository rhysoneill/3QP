"""
Tests for trajectory analysis evidence structures.

Validates evidence items, support strength enum, and evidence bundles.
"""

import pytest

from trajectory_analysis.evidence import (
    TrajectorySupportStrength,
    TrajectoryEvidence,
    TrajectoryEvidenceBundle
)


class TestTrajectorySupportStrength:
    """Tests for TrajectorySupportStrength enum."""
    
    def test_enum_values_exist(self):
        """All expected enum values are defined."""
        assert hasattr(TrajectorySupportStrength, 'SUGGESTIVE')
        assert hasattr(TrajectorySupportStrength, 'WEAK')
        assert hasattr(TrajectorySupportStrength, 'MODERATE')
        assert hasattr(TrajectorySupportStrength, 'STRONG')
        assert hasattr(TrajectorySupportStrength, 'CONTEXTUAL_ONLY')
    
    def test_is_valid_with_enum_member(self):
        """is_valid returns True for enum members."""
        assert TrajectorySupportStrength.is_valid(TrajectorySupportStrength.WEAK)
        assert TrajectorySupportStrength.is_valid(TrajectorySupportStrength.STRONG)
    
    def test_is_valid_with_string(self):
        """is_valid returns True for valid string values."""
        assert TrajectorySupportStrength.is_valid("weak")
        assert TrajectorySupportStrength.is_valid("moderate")
    
    def test_is_valid_with_invalid_value(self):
        """is_valid returns False for invalid values."""
        assert not TrajectorySupportStrength.is_valid("invalid")
        assert not TrajectorySupportStrength.is_valid(123)
        assert not TrajectorySupportStrength.is_valid(None)


class TestTrajectoryEvidence:
    """Tests for TrajectoryEvidence dataclass."""
    
    def test_creation_with_required_fields(self):
        """Evidence can be created with required fields."""
        evidence = TrajectoryEvidence(
            archetype_id="test_archetype",
            support_strength=TrajectorySupportStrength.MODERATE,
            narrative="Test narrative"
        )
        
        assert evidence.archetype_id == "test_archetype"
        assert evidence.support_strength == TrajectorySupportStrength.MODERATE
        assert evidence.narrative == "Test narrative"
        assert evidence.source_pattern_type is None
        assert evidence.source_event_id is None
        assert evidence.source_state_id is None
        assert evidence.metadata is None
    
    def test_creation_with_all_fields(self):
        """Evidence can be created with all fields."""
        evidence = TrajectoryEvidence(
            archetype_id="test_archetype",
            support_strength=TrajectorySupportStrength.STRONG,
            narrative="Complete narrative",
            source_pattern_type="pattern_type_1",
            source_event_id="event_123",
            source_state_id="state_456",
            metadata={"key": "value"}
        )
        
        assert evidence.source_pattern_type == "pattern_type_1"
        assert evidence.source_event_id == "event_123"
        assert evidence.source_state_id == "state_456"
        assert evidence.metadata == {"key": "value"}
    
    def test_validation_empty_archetype_id(self):
        """Empty archetype_id raises ValueError."""
        with pytest.raises(ValueError, match="archetype_id"):
            TrajectoryEvidence(
                archetype_id="",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Test"
            )
    
    def test_validation_empty_narrative(self):
        """Empty narrative raises ValueError."""
        with pytest.raises(ValueError, match="narrative"):
            TrajectoryEvidence(
                archetype_id="test",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative=""
            )
    
    def test_validation_invalid_support_strength(self):
        """Invalid support_strength raises ValueError."""
        with pytest.raises(ValueError, match="support_strength"):
            TrajectoryEvidence(
                archetype_id="test",
                support_strength="not_an_enum",
                narrative="Test"
            )
    
    def test_to_narrative(self):
        """to_narrative returns human-readable string."""
        evidence = TrajectoryEvidence(
            archetype_id="test_archetype",
            support_strength=TrajectorySupportStrength.STRONG,
            narrative="Test narrative"
        )
        
        narrative = evidence.to_narrative()
        assert isinstance(narrative, str)
        assert "test_archetype" in narrative
        assert "STRONG" in narrative
        assert "Test narrative" in narrative
    
    def test_to_narrative_with_sources(self):
        """to_narrative includes source information."""
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.MODERATE,
            narrative="Test",
            source_pattern_type="pattern_1",
            source_event_id="event_1"
        )
        
        narrative = evidence.to_narrative()
        assert "pattern: pattern_1" in narrative
        assert "event: event_1" in narrative
    
    def test_to_dict(self):
        """to_dict returns complete dictionary representation."""
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.WEAK,
            narrative="Test narrative",
            metadata={"custom": "data"}
        )
        
        result = evidence.to_dict()
        assert isinstance(result, dict)
        assert result["archetype_id"] == "test"
        assert result["support_strength"] == "weak"
        assert result["narrative"] == "Test narrative"
        assert result["metadata"] == {"custom": "data"}


class TestTrajectoryEvidenceBundle:
    """Tests for TrajectoryEvidenceBundle dataclass."""
    
    def test_creation_empty(self):
        """Bundle can be created empty."""
        bundle = TrajectoryEvidenceBundle()
        assert bundle.items == []
    
    def test_creation_with_items(self):
        """Bundle can be created with items."""
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.WEAK,
            narrative="Test"
        )
        
        bundle = TrajectoryEvidenceBundle(items=[evidence])
        assert len(bundle.items) == 1
        assert bundle.items[0] == evidence
    
    def test_add_evidence(self):
        """add() adds evidence to bundle."""
        bundle = TrajectoryEvidenceBundle()
        
        evidence = TrajectoryEvidence(
            archetype_id="test",
            support_strength=TrajectorySupportStrength.MODERATE,
            narrative="Test"
        )
        
        bundle.add(evidence)
        assert len(bundle.items) == 1
        assert bundle.items[0] == evidence
    
    def test_add_invalid_type(self):
        """add() raises TypeError for invalid input."""
        bundle = TrajectoryEvidenceBundle()
        
        with pytest.raises(TypeError):
            bundle.add("not_evidence")
    
    def test_merge(self):
        """merge() creates new bundle with combined items."""
        bundle1 = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="First"
            )
        ])
        
        bundle2 = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch2",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Second"
            )
        ])
        
        merged = bundle1.merge(bundle2)
        
        assert len(merged.items) == 2
        assert len(bundle1.items) == 1  # Original unchanged
        assert len(bundle2.items) == 1  # Original unchanged
    
    def test_filter_by_archetype(self):
        """filter_by_archetype returns matching evidence."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="First"
            ),
            TrajectoryEvidence(
                archetype_id="arch2",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Second"
            ),
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Third"
            )
        ])
        
        filtered = bundle.filter_by_archetype("arch1")
        assert len(filtered.items) == 2
        assert all(e.archetype_id == "arch1" for e in filtered.items)
    
    def test_filter_by_strength(self):
        """filter_by_strength returns matching evidence."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="test",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Weak"
            ),
            TrajectoryEvidence(
                archetype_id="test",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Strong"
            ),
            TrajectoryEvidence(
                archetype_id="test",
                support_strength=TrajectorySupportStrength.MODERATE,
                narrative="Moderate"
            )
        ])
        
        filtered = bundle.filter_by_strength([
            TrajectorySupportStrength.STRONG,
            TrajectorySupportStrength.MODERATE
        ])
        
        assert len(filtered.items) == 2
        assert all(
            e.support_strength in [TrajectorySupportStrength.STRONG, TrajectorySupportStrength.MODERATE]
            for e in filtered.items
        )
    
    def test_get_archetype_ids(self):
        """get_archetype_ids returns unique IDs."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="First"
            ),
            TrajectoryEvidence(
                archetype_id="arch2",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Second"
            ),
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Third"
            )
        ])
        
        ids = bundle.get_archetype_ids()
        assert set(ids) == {"arch1", "arch2"}
    
    def test_group_by_archetype(self):
        """group_by_archetype returns dictionary of grouped evidence."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="First"
            ),
            TrajectoryEvidence(
                archetype_id="arch2",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Second"
            ),
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Third"
            )
        ])
        
        groups = bundle.group_by_archetype()
        assert isinstance(groups, dict)
        assert len(groups["arch1"]) == 2
        assert len(groups["arch2"]) == 1
    
    def test_to_narrative_empty(self):
        """to_narrative handles empty bundle."""
        bundle = TrajectoryEvidenceBundle()
        narrative = bundle.to_narrative()
        
        assert isinstance(narrative, str)
        assert "No trajectory evidence" in narrative
    
    def test_to_narrative_with_items(self):
        """to_narrative returns readable summary."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="test",
                support_strength=TrajectorySupportStrength.MODERATE,
                narrative="Test evidence"
            )
        ])
        
        narrative = bundle.to_narrative()
        assert isinstance(narrative, str)
        assert "Trajectory Evidence Bundle" in narrative
        assert "1 items" in narrative
    
    def test_to_dict(self):
        """to_dict returns structured representation."""
        bundle = TrajectoryEvidenceBundle(items=[
            TrajectoryEvidence(
                archetype_id="arch1",
                support_strength=TrajectorySupportStrength.WEAK,
                narrative="Test"
            ),
            TrajectoryEvidence(
                archetype_id="arch2",
                support_strength=TrajectorySupportStrength.STRONG,
                narrative="Test 2"
            )
        ])
        
        result = bundle.to_dict()
        assert isinstance(result, dict)
        assert result["item_count"] == 2
        assert "arch1" in result["archetype_ids"]
        assert "arch2" in result["archetype_ids"]
        assert len(result["items"]) == 2
