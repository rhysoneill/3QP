"""
Tests for encoder implementations.

These tests verify:
- Correct encoding of semantic schemas to canonical states
- Input validation
- Schema version compliance
- Narrative generation
- Error handling
"""

import unittest
from state_encoding.encoders import (
    BaselineStateEncoder, ScenarioEventEncoder,
    PatternIndicatorEncoder, ThreadIndicatorEncoder,
    BaselineProfile, ScenarioEvent, PatternIndicator, ThreadIndicator
)
from state_encoding.interfaces import EncodingStatus


class TestBaselineStateEncoder(unittest.TestCase):
    """Test cases for BaselineStateEncoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = BaselineStateEncoder(schema_version="1.0.0")
        
        self.test_profile = BaselineProfile(
            profile_id="test_profile_001",
            physiological_state={
                "sleep_quality": "restless",
                "energy_level": "low"
            },
            psychological_state={
                "mood": "anxious",
                "stress_level": "moderate"
            },
            social_state={
                "social_support": "limited",
                "cohesion": "weak"
            },
            environmental_context={
                "workload": "high",
                "resources": "constrained"
            },
            metadata={"source": "baseline_assessment"}
        )
    
    def test_successful_encoding(self):
        """Test successful encoding of baseline profile."""
        result = self.encoder.encode(self.test_profile)
        
        self.assertTrue(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.SUCCESS)
        self.assertIsNotNone(result.encoded_state)
        self.assertEqual(len(result.errors), 0)
    
    def test_encoded_state_structure(self):
        """Test structure of encoded state."""
        result = self.encoder.encode(self.test_profile)
        state = result.encoded_state
        
        # Check top-level keys
        self.assertIn("profile_id", state)
        self.assertIn("domains", state)
        self.assertIn("encoding_metadata", state)
        
        # Check profile ID
        self.assertEqual(state["profile_id"], "test_profile_001")
        
        # Check domains
        domains = state["domains"]
        self.assertIn("physiological", domains)
        self.assertIn("psychological", domains)
        self.assertIn("social", domains)
        self.assertIn("environmental", domains)
        
        # Check domain content
        self.assertEqual(domains["physiological"]["sleep_quality"], "restless")
        self.assertEqual(domains["psychological"]["mood"], "anxious")
    
    def test_encoding_metadata(self):
        """Test encoding metadata is correctly populated."""
        result = self.encoder.encode(self.test_profile)
        metadata = result.encoded_state["encoding_metadata"]
        
        self.assertEqual(metadata["encoder_version"], "1.0.0")
        self.assertEqual(metadata["encoder_type"], "baseline")
        self.assertEqual(metadata["original_metadata"]["source"], "baseline_assessment")
    
    def test_validate_input_success(self):
        """Test input validation with valid profile."""
        is_valid = self.encoder.validate_input(self.test_profile)
        self.assertTrue(is_valid)
    
    def test_validate_input_failure_wrong_type(self):
        """Test input validation with wrong type."""
        is_valid = self.encoder.validate_input({"not": "a profile"})
        self.assertFalse(is_valid)
    
    def test_encode_with_invalid_input(self):
        """Test encoding with invalid input."""
        result = self.encoder.encode({"invalid": "input"})
        
        self.assertFalse(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.INVALID_INPUT)
        self.assertIsNone(result.encoded_state)
        self.assertGreater(len(result.errors), 0)
    
    def test_get_schema_version(self):
        """Test schema version retrieval."""
        version = self.encoder.get_schema_version()
        self.assertEqual(version, "1.0.0")
    
    def test_to_narrative(self):
        """Test narrative generation."""
        result = self.encoder.encode(self.test_profile)
        narrative = self.encoder.to_narrative(result.encoded_state)
        
        self.assertIn("test_profile_001", narrative)
        self.assertIn("physiological", narrative.lower())
        self.assertIn("restless", narrative)
        self.assertIn("anxious", narrative)


class TestScenarioEventEncoder(unittest.TestCase):
    """Test cases for ScenarioEventEncoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = ScenarioEventEncoder(schema_version="1.0.0")
        
        self.test_event = ScenarioEvent(
            event_id="evt_001",
            event_type="mission_assignment",
            timestamp="2024-03-15T08:00:00Z",
            actors=["crew_member_1", "crew_member_2"],
            descriptors={
                "urgency": "high",
                "complexity": "moderate"
            },
            context={
                "location": "command_center",
                "mission_phase": "pre_deployment"
            },
            metadata={"source": "scenario_timeline"}
        )
    
    def test_successful_encoding(self):
        """Test successful encoding of scenario event."""
        result = self.encoder.encode(self.test_event)
        
        self.assertTrue(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.SUCCESS)
        self.assertIsNotNone(result.encoded_state)
    
    def test_encoded_state_structure(self):
        """Test structure of encoded event state."""
        result = self.encoder.encode(self.test_event)
        state = result.encoded_state
        
        # Check top-level keys
        self.assertIn("event_id", state)
        self.assertIn("event_type", state)
        self.assertIn("temporal_context", state)
        self.assertIn("actors", state)
        self.assertIn("descriptors", state)
        self.assertIn("context", state)
        
        # Check values
        self.assertEqual(state["event_id"], "evt_001")
        self.assertEqual(state["event_type"], "mission_assignment")
        self.assertEqual(len(state["actors"]), 2)
        self.assertEqual(state["descriptors"]["urgency"], "high")
    
    def test_temporal_context(self):
        """Test temporal context encoding."""
        result = self.encoder.encode(self.test_event)
        temporal = result.encoded_state["temporal_context"]
        
        self.assertIn("timestamp", temporal)
        self.assertEqual(temporal["timestamp"], "2024-03-15T08:00:00Z")
    
    def test_validate_input_success(self):
        """Test input validation with valid event."""
        is_valid = self.encoder.validate_input(self.test_event)
        self.assertTrue(is_valid)
    
    def test_validate_input_failure(self):
        """Test input validation with invalid event."""
        is_valid = self.encoder.validate_input({"not": "an event"})
        self.assertFalse(is_valid)
    
    def test_to_narrative(self):
        """Test narrative generation for events."""
        result = self.encoder.encode(self.test_event)
        narrative = self.encoder.to_narrative(result.encoded_state)
        
        self.assertIn("evt_001", narrative)
        self.assertIn("mission_assignment", narrative)
        self.assertIn("crew_member_1", narrative)
        self.assertIn("high", narrative)


class TestPatternIndicatorEncoder(unittest.TestCase):
    """Test cases for PatternIndicatorEncoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = PatternIndicatorEncoder(schema_version="1.0.0")
        
        self.test_indicator = PatternIndicator(
            indicator_id="pat_001",
            pattern_type="stress_response",
            indicators=["elevated_heart_rate", "disrupted_sleep", "irritability"],
            confidence_level="moderate",
            context={
                "timeframe": "past_week",
                "domain": "physiological"
            },
            metadata={"source": "pattern_analysis"}
        )
    
    def test_successful_encoding(self):
        """Test successful encoding of pattern indicator."""
        result = self.encoder.encode(self.test_indicator)
        
        self.assertTrue(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.SUCCESS)
        self.assertIsNotNone(result.encoded_state)
    
    def test_encoded_state_structure(self):
        """Test structure of encoded pattern indicator."""
        result = self.encoder.encode(self.test_indicator)
        state = result.encoded_state
        
        # Check required fields
        self.assertIn("indicator_id", state)
        self.assertIn("pattern_type", state)
        self.assertIn("indicators", state)
        self.assertIn("confidence_level", state)
        
        # Check values
        self.assertEqual(state["indicator_id"], "pat_001")
        self.assertEqual(state["pattern_type"], "stress_response")
        self.assertEqual(len(state["indicators"]), 3)
        self.assertEqual(state["confidence_level"], "moderate")
    
    def test_validate_input_success(self):
        """Test input validation with valid indicator."""
        is_valid = self.encoder.validate_input(self.test_indicator)
        self.assertTrue(is_valid)
    
    def test_validate_input_failure(self):
        """Test input validation with invalid indicator."""
        is_valid = self.encoder.validate_input({"not": "an indicator"})
        self.assertFalse(is_valid)
    
    def test_to_narrative(self):
        """Test narrative generation for pattern indicators."""
        result = self.encoder.encode(self.test_indicator)
        narrative = self.encoder.to_narrative(result.encoded_state)
        
        self.assertIn("pat_001", narrative)
        self.assertIn("stress_response", narrative)
        self.assertIn("moderate", narrative)


class TestThreadIndicatorEncoder(unittest.TestCase):
    """Test cases for ThreadIndicatorEncoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.encoder = ThreadIndicatorEncoder(schema_version="1.0.0")
        
        self.test_thread = ThreadIndicator(
            thread_id="thread_001",
            thread_type="social_cohesion",
            related_entities=["crew_member_1", "crew_member_2", "crew_member_3"],
            relationship_descriptors={
                "cohesion_level": "moderate",
                "trust_level": "building"
            },
            context={
                "timeframe": "current",
                "scope": "team"
            },
            metadata={"source": "social_network_analysis"}
        )
    
    def test_successful_encoding(self):
        """Test successful encoding of thread indicator."""
        result = self.encoder.encode(self.test_thread)
        
        self.assertTrue(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.SUCCESS)
        self.assertIsNotNone(result.encoded_state)
    
    def test_encoded_state_structure(self):
        """Test structure of encoded thread indicator."""
        result = self.encoder.encode(self.test_thread)
        state = result.encoded_state
        
        # Check required fields
        self.assertIn("thread_id", state)
        self.assertIn("thread_type", state)
        self.assertIn("related_entities", state)
        self.assertIn("relationship_descriptors", state)
        
        # Check values
        self.assertEqual(state["thread_id"], "thread_001")
        self.assertEqual(state["thread_type"], "social_cohesion")
        self.assertEqual(len(state["related_entities"]), 3)
        self.assertEqual(state["relationship_descriptors"]["cohesion_level"], "moderate")
    
    def test_validate_input_success(self):
        """Test input validation with valid thread indicator."""
        is_valid = self.encoder.validate_input(self.test_thread)
        self.assertTrue(is_valid)
    
    def test_validate_input_failure(self):
        """Test input validation with invalid thread indicator."""
        is_valid = self.encoder.validate_input({"not": "a thread"})
        self.assertFalse(is_valid)
    
    def test_to_narrative(self):
        """Test narrative generation for thread indicators."""
        result = self.encoder.encode(self.test_thread)
        narrative = self.encoder.to_narrative(result.encoded_state)
        
        self.assertIn("thread_001", narrative)
        self.assertIn("social_cohesion", narrative)
        self.assertIn("crew_member_1", narrative)


if __name__ == '__main__':
    unittest.main()
