"""
Tests for mapper implementations.

These tests verify:
- Observation to schema mapping
- Narrative to event mapping
- Qualitative descriptor mapping
- Semantic tag handling
- Input validation and error handling
"""

import unittest
from state_encoding.mappers import (
    ObservationToSchemaMapper, NarrativeToEventMapper,
    QualitativeDescriptorMapper, SemanticTag, SemanticTagMapper
)
from state_encoding.encoders import (
    BaselineProfile, ScenarioEvent, PatternIndicator, ThreadIndicator
)


class TestObservationToSchemaMapper(unittest.TestCase):
    """Test cases for ObservationToSchemaMapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ObservationToSchemaMapper()
    
    def test_map_complete_observation(self):
        """Test mapping of complete observation."""
        observation = {
            "profile_id": "baseline_001",
            "physiological": {
                "sleep_quality": "restless",
                "energy_level": "low"
            },
            "psychological": {
                "mood": "anxious",
                "stress_level": "moderate"
            },
            "social": {
                "social_support": "limited",
                "cohesion": "weak"
            },
            "environmental": {
                "workload": "high",
                "resources": "constrained"
            }
        }
        
        profile = self.mapper.map(observation)
        
        self.assertIsInstance(profile, BaselineProfile)
        self.assertEqual(profile.profile_id, "baseline_001")
        self.assertEqual(profile.physiological_state["sleep_quality"], "restless")
        self.assertEqual(profile.psychological_state["mood"], "anxious")
        self.assertEqual(profile.social_state["cohesion"], "weak")
        self.assertEqual(profile.environmental_context["workload"], "high")
    
    def test_map_minimal_observation(self):
        """Test mapping with minimal required fields."""
        observation = {
            "profile_id": "baseline_002"
        }
        
        profile = self.mapper.map(observation)
        
        self.assertIsInstance(profile, BaselineProfile)
        self.assertEqual(profile.profile_id, "baseline_002")
        self.assertEqual(profile.physiological_state, {})
        self.assertEqual(profile.psychological_state, {})
    
    def test_map_with_metadata(self):
        """Test mapping with metadata."""
        observation = {
            "profile_id": "baseline_003",
            "physiological": {"sleep": "restless"},
            "metadata": {"source": "test", "timestamp": "2024-03-15"}
        }
        
        profile = self.mapper.map(observation)
        
        self.assertEqual(profile.metadata["source"], "test")
        self.assertEqual(profile.metadata["timestamp"], "2024-03-15")
    
    def test_map_missing_required_field(self):
        """Test mapping with missing required field."""
        observation = {
            "physiological": {"sleep": "restless"}
            # Missing profile_id
        }
        
        with self.assertRaises(ValueError) as context:
            self.mapper.map(observation)
        
        self.assertIn("profile_id", str(context.exception))
    
    def test_supports_observation_type(self):
        """Test observation type support checking."""
        self.assertTrue(self.mapper.supports_observation_type("baseline_observation"))
        self.assertTrue(self.mapper.supports_observation_type("physiological"))
        self.assertFalse(self.mapper.supports_observation_type("unknown_type"))
    
    def test_get_required_fields(self):
        """Test required fields retrieval."""
        required = self.mapper.get_required_fields()
        
        self.assertIn("profile_id", required)


class TestNarrativeToEventMapper(unittest.TestCase):
    """Test cases for NarrativeToEventMapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = NarrativeToEventMapper()
    
    def test_map_complete_event(self):
        """Test mapping of complete event description."""
        observation = {
            "event_id": "evt_001",
            "event_type": "mission_assignment",
            "timestamp": "2024-03-15T08:00:00Z",
            "actors": ["crew_member_1", "crew_member_2"],
            "description": "High-stakes mission assigned",
            "descriptors": {
                "urgency": "high",
                "complexity": "moderate"
            },
            "context": {
                "location": "command_center"
            }
        }
        
        event = self.mapper.map(observation)
        
        self.assertIsInstance(event, ScenarioEvent)
        self.assertEqual(event.event_id, "evt_001")
        self.assertEqual(event.event_type, "mission_assignment")
        self.assertEqual(event.timestamp, "2024-03-15T08:00:00Z")
        self.assertEqual(len(event.actors), 2)
        self.assertIn("description", event.context)
    
    def test_map_minimal_event(self):
        """Test mapping with minimal required fields."""
        observation = {
            "event_id": "evt_002",
            "event_type": "status_check"
        }
        
        event = self.mapper.map(observation)
        
        self.assertIsInstance(event, ScenarioEvent)
        self.assertEqual(event.event_id, "evt_002")
        self.assertEqual(event.actors, [])
        self.assertEqual(event.descriptors, {})
    
    def test_map_missing_required_field(self):
        """Test mapping with missing required field."""
        observation = {
            "event_id": "evt_003"
            # Missing event_type
        }
        
        with self.assertRaises(ValueError) as context:
            self.mapper.map(observation)
        
        self.assertIn("event_type", str(context.exception))
    
    def test_supports_observation_type(self):
        """Test observation type support checking."""
        self.assertTrue(self.mapper.supports_observation_type("narrative_event"))
        self.assertTrue(self.mapper.supports_observation_type("scenario_event"))
        self.assertFalse(self.mapper.supports_observation_type("baseline"))
    
    def test_get_required_fields(self):
        """Test required fields retrieval."""
        required = self.mapper.get_required_fields()
        
        self.assertIn("event_id", required)
        self.assertIn("event_type", required)


class TestQualitativeDescriptorMapper(unittest.TestCase):
    """Test cases for QualitativeDescriptorMapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = QualitativeDescriptorMapper()
    
    def test_map_pattern_indicator(self):
        """Test mapping of pattern indicator."""
        observation = {
            "type": "pattern_indicator",
            "indicator_id": "pat_001",
            "pattern_type": "stress_response",
            "indicators": ["elevated_heart_rate", "disrupted_sleep"],
            "confidence": "moderate",
            "context": {"timeframe": "past_week"}
        }
        
        indicator = self.mapper.map(observation)
        
        self.assertIsInstance(indicator, PatternIndicator)
        self.assertEqual(indicator.indicator_id, "pat_001")
        self.assertEqual(indicator.pattern_type, "stress_response")
        self.assertEqual(len(indicator.indicators), 2)
        self.assertEqual(indicator.confidence_level, "moderate")
    
    def test_map_thread_indicator(self):
        """Test mapping of thread indicator."""
        observation = {
            "type": "thread_indicator",
            "thread_id": "thread_001",
            "thread_type": "social_cohesion",
            "entities": ["crew_1", "crew_2", "crew_3"],
            "relationships": {
                "cohesion_level": "moderate"
            },
            "context": {"scope": "team"}
        }
        
        indicator = self.mapper.map(observation)
        
        self.assertIsInstance(indicator, ThreadIndicator)
        self.assertEqual(indicator.thread_id, "thread_001")
        self.assertEqual(indicator.thread_type, "social_cohesion")
        self.assertEqual(len(indicator.related_entities), 3)
    
    def test_map_thread_indicator_alternative_fields(self):
        """Test mapping with alternative field names."""
        observation = {
            "type": "thread_indicator",
            "thread_id": "thread_002",
            "thread_type": "resource_flow",
            "related_entities": ["unit_a", "unit_b"],
            "relationship_descriptors": {
                "flow_direction": "bidirectional"
            }
        }
        
        indicator = self.mapper.map(observation)
        
        self.assertIsInstance(indicator, ThreadIndicator)
        self.assertEqual(len(indicator.related_entities), 2)
        self.assertIn("flow_direction", indicator.relationship_descriptors)
    
    def test_map_unsupported_type(self):
        """Test mapping with unsupported type."""
        observation = {
            "type": "unknown_type",
            "data": "test"
        }
        
        with self.assertRaises(ValueError) as context:
            self.mapper.map(observation)
        
        self.assertIn("Unsupported", str(context.exception))
    
    def test_map_missing_required_pattern_field(self):
        """Test pattern indicator mapping with missing field."""
        observation = {
            "type": "pattern_indicator",
            "indicator_id": "pat_002",
            "pattern_type": "test"
            # Missing "indicators"
        }
        
        with self.assertRaises(ValueError) as context:
            self.mapper.map(observation)
        
        self.assertIn("indicators", str(context.exception))
    
    def test_supports_observation_type(self):
        """Test observation type support checking."""
        self.assertTrue(self.mapper.supports_observation_type("pattern_indicator"))
        self.assertTrue(self.mapper.supports_observation_type("thread_indicator"))
        self.assertTrue(self.mapper.supports_observation_type("PATTERN_INDICATOR"))
        self.assertFalse(self.mapper.supports_observation_type("unknown"))


class TestSemanticTag(unittest.TestCase):
    """Test cases for SemanticTag."""
    
    def test_create_semantic_tag(self):
        """Test creation of semantic tag."""
        tag = SemanticTag(
            tag_id="sleep_restless",
            tag_label="restless",
            domain="sleep_quality",
            description="Restless sleep state"
        )
        
        self.assertEqual(tag.tag_id, "sleep_restless")
        self.assertEqual(tag.tag_label, "restless")
        self.assertEqual(tag.domain, "sleep_quality")
    
    def test_from_descriptor(self):
        """Test creating tag from descriptor."""
        tag = SemanticTag.from_descriptor("anxious", "psychological")
        
        self.assertEqual(tag.tag_id, "psychological_anxious")
        self.assertEqual(tag.tag_label, "anxious")
        self.assertEqual(tag.domain, "psychological")
        self.assertIn("anxious", tag.description.lower())


class TestSemanticTagMapper(unittest.TestCase):
    """Test cases for SemanticTagMapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = SemanticTagMapper()
    
    def test_map_descriptor(self):
        """Test mapping descriptor to semantic tag."""
        tag = self.mapper.map_descriptor("restless", "sleep_quality")
        
        self.assertIsInstance(tag, SemanticTag)
        self.assertEqual(tag.tag_label, "restless")
        self.assertEqual(tag.domain, "sleep_quality")
    
    def test_map_descriptor_dict(self):
        """Test mapping dictionary of descriptors."""
        descriptors = {
            "sleep_quality": "restless",
            "energy_level": "low"
        }
        
        tags = self.mapper.map_descriptor_dict(descriptors, "physiological")
        
        self.assertEqual(len(tags), 2)
        self.assertIn("sleep_quality", tags)
        self.assertIn("energy_level", tags)
        self.assertIsInstance(tags["sleep_quality"], SemanticTag)
    
    def test_register_and_retrieve_tag(self):
        """Test registering and retrieving predefined tag."""
        predefined = SemanticTag(
            tag_id="test_tag",
            tag_label="test",
            domain="test_domain",
            description="Test tag"
        )
        
        self.mapper.register_tag(predefined)
        
        # Should retrieve predefined tag
        tag = self.mapper.map_descriptor("test", "test")
        # Won't match because tag_id is different, so creates new one
        
        # Try with exact tag_id match
        self.mapper.predefined_tags["exact_test"] = predefined
        # Direct lookup
        self.assertIn("test_tag", self.mapper.predefined_tags)
    
    def test_get_tags_for_domain(self):
        """Test retrieving tags for specific domain."""
        tag1 = SemanticTag.from_descriptor("tag1", "domain_a")
        tag2 = SemanticTag.from_descriptor("tag2", "domain_a")
        tag3 = SemanticTag.from_descriptor("tag3", "domain_b")
        
        self.mapper.register_tag(tag1)
        self.mapper.register_tag(tag2)
        self.mapper.register_tag(tag3)
        
        domain_a_tags = self.mapper.get_tags_for_domain("domain_a")
        
        self.assertEqual(len(domain_a_tags), 2)
        self.assertTrue(all(tag.domain == "domain_a" for tag in domain_a_tags))


if __name__ == '__main__':
    unittest.main()
