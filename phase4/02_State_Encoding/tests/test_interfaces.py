"""
Tests for core interfaces and abstract base classes.

These tests verify:
- Interface compliance
- Abstract method enforcement
- EncodingResult functionality
- Proper inheritance structure
"""

import unittest
from state_encoding.interfaces import (
    StateEncoder, ObservationMapper, SchemaBinder,
    EncodingResult, EncodingStatus
)


class TestEncodingResult(unittest.TestCase):
    """Test cases for EncodingResult dataclass."""
    
    def test_successful_encoding_result(self):
        """Test creation of successful encoding result."""
        result = EncodingResult(
            status=EncodingStatus.SUCCESS,
            encoded_state={"key": "value"},
            metadata={"encoder": "test"},
            errors=[],
            source_reference="test_source"
        )
        
        self.assertTrue(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.SUCCESS)
        self.assertIsNotNone(result.encoded_state)
        self.assertEqual(len(result.errors), 0)
    
    def test_failed_encoding_result(self):
        """Test creation of failed encoding result."""
        result = EncodingResult(
            status=EncodingStatus.FAILED,
            encoded_state=None,
            metadata={"encoder": "test"},
            errors=["Test error"],
            source_reference="test_source"
        )
        
        self.assertFalse(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.FAILED)
        self.assertIsNone(result.encoded_state)
        self.assertEqual(len(result.errors), 1)
    
    def test_partial_encoding_result(self):
        """Test creation of partial encoding result."""
        result = EncodingResult(
            status=EncodingStatus.PARTIAL,
            encoded_state={"partial": "data"},
            metadata={"encoder": "test"},
            errors=["Warning: incomplete data"],
            source_reference="test_source"
        )
        
        self.assertFalse(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.PARTIAL)
        self.assertIsNotNone(result.encoded_state)
    
    def test_invalid_input_result(self):
        """Test creation of invalid input result."""
        result = EncodingResult(
            status=EncodingStatus.INVALID_INPUT,
            encoded_state=None,
            metadata={"encoder": "test"},
            errors=["Invalid schema object"],
            source_reference=None
        )
        
        self.assertFalse(result.is_valid())
        self.assertEqual(result.status, EncodingStatus.INVALID_INPUT)


class TestStateEncoderInterface(unittest.TestCase):
    """Test cases for StateEncoder abstract interface."""
    
    def test_cannot_instantiate_directly(self):
        """Test that StateEncoder cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            StateEncoder()
    
    def test_subclass_must_implement_encode(self):
        """Test that subclass must implement encode method."""
        class IncompleteEncoder(StateEncoder):
            def validate_input(self, schema_object):
                return True
            
            def get_schema_version(self):
                return "1.0.0"
        
        encoder = IncompleteEncoder()
        
        with self.assertRaises(NotImplementedError):
            encoder.encode({})
    
    def test_subclass_must_implement_validate_input(self):
        """Test that subclass must implement validate_input method."""
        class IncompleteEncoder(StateEncoder):
            def encode(self, schema_object):
                return EncodingResult(
                    status=EncodingStatus.SUCCESS,
                    encoded_state={},
                    metadata={},
                    errors=[]
                )
            
            def get_schema_version(self):
                return "1.0.0"
        
        encoder = IncompleteEncoder()
        
        with self.assertRaises(NotImplementedError):
            encoder.validate_input({})
    
    def test_subclass_must_implement_get_schema_version(self):
        """Test that subclass must implement get_schema_version method."""
        class IncompleteEncoder(StateEncoder):
            def encode(self, schema_object):
                return EncodingResult(
                    status=EncodingStatus.SUCCESS,
                    encoded_state={},
                    metadata={},
                    errors=[]
                )
            
            def validate_input(self, schema_object):
                return True
        
        encoder = IncompleteEncoder()
        
        with self.assertRaises(NotImplementedError):
            encoder.get_schema_version()
    
    def test_complete_subclass_implementation(self):
        """Test that complete subclass can be instantiated and used."""
        class CompleteEncoder(StateEncoder):
            def encode(self, schema_object):
                return EncodingResult(
                    status=EncodingStatus.SUCCESS,
                    encoded_state={"test": "data"},
                    metadata={"encoder": "complete"},
                    errors=[]
                )
            
            def validate_input(self, schema_object):
                return isinstance(schema_object, dict)
            
            def get_schema_version(self):
                return "1.0.0"
        
        encoder = CompleteEncoder()
        
        # Verify all methods work
        self.assertTrue(encoder.validate_input({}))
        self.assertEqual(encoder.get_schema_version(), "1.0.0")
        
        result = encoder.encode({"test": "input"})
        self.assertTrue(result.is_valid())


class TestObservationMapperInterface(unittest.TestCase):
    """Test cases for ObservationMapper abstract interface."""
    
    def test_cannot_instantiate_directly(self):
        """Test that ObservationMapper cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            ObservationMapper()
    
    def test_subclass_must_implement_map(self):
        """Test that subclass must implement map method."""
        class IncompleteMapper(ObservationMapper):
            def supports_observation_type(self, observation_type):
                return True
            
            def get_required_fields(self):
                return []
        
        mapper = IncompleteMapper()
        
        with self.assertRaises(NotImplementedError):
            mapper.map({})
    
    def test_subclass_must_implement_supports_observation_type(self):
        """Test that subclass must implement supports_observation_type."""
        class IncompleteMapper(ObservationMapper):
            def map(self, observation):
                return observation
            
            def get_required_fields(self):
                return []
        
        mapper = IncompleteMapper()
        
        with self.assertRaises(NotImplementedError):
            mapper.supports_observation_type("test")
    
    def test_subclass_must_implement_get_required_fields(self):
        """Test that subclass must implement get_required_fields."""
        class IncompleteMapper(ObservationMapper):
            def map(self, observation):
                return observation
            
            def supports_observation_type(self, observation_type):
                return True
        
        mapper = IncompleteMapper()
        
        with self.assertRaises(NotImplementedError):
            mapper.get_required_fields()
    
    def test_complete_mapper_implementation(self):
        """Test that complete mapper can be instantiated and used."""
        class CompleteMapper(ObservationMapper):
            def map(self, observation):
                return {"mapped": observation}
            
            def supports_observation_type(self, observation_type):
                return observation_type == "test"
            
            def get_required_fields(self):
                return ["field1", "field2"]
        
        mapper = CompleteMapper()
        
        # Verify all methods work
        self.assertTrue(mapper.supports_observation_type("test"))
        self.assertFalse(mapper.supports_observation_type("other"))
        self.assertEqual(mapper.get_required_fields(), ["field1", "field2"])
        
        result = mapper.map({"test": "data"})
        self.assertEqual(result, {"mapped": {"test": "data"}})


class TestSchemaBinderInterface(unittest.TestCase):
    """Test cases for SchemaBinder abstract interface."""
    
    def test_cannot_instantiate_directly(self):
        """Test that SchemaBinder cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SchemaBinder()
    
    def test_subclass_must_implement_bind(self):
        """Test that subclass must implement bind method."""
        class IncompleteBinder(SchemaBinder):
            def verify_binding(self, encoded_state):
                return True
            
            def get_bound_schema_id(self, encoded_state):
                return "test_schema"
        
        binder = IncompleteBinder()
        
        with self.assertRaises(NotImplementedError):
            binder.bind({}, "schema_id")
    
    def test_subclass_must_implement_verify_binding(self):
        """Test that subclass must implement verify_binding method."""
        class IncompleteBinder(SchemaBinder):
            def bind(self, encoded_state, schema_id):
                return encoded_state
            
            def get_bound_schema_id(self, encoded_state):
                return "test_schema"
        
        binder = IncompleteBinder()
        
        with self.assertRaises(NotImplementedError):
            binder.verify_binding({})
    
    def test_subclass_must_implement_get_bound_schema_id(self):
        """Test that subclass must implement get_bound_schema_id method."""
        class IncompleteBinder(SchemaBinder):
            def bind(self, encoded_state, schema_id):
                return encoded_state
            
            def verify_binding(self, encoded_state):
                return True
        
        binder = IncompleteBinder()
        
        with self.assertRaises(NotImplementedError):
            binder.get_bound_schema_id({})
    
    def test_complete_binder_implementation(self):
        """Test that complete binder can be instantiated and used."""
        class CompleteBinder(SchemaBinder):
            def bind(self, encoded_state, schema_id):
                encoded_state["_schema_id"] = schema_id
                return encoded_state
            
            def verify_binding(self, encoded_state):
                return "_schema_id" in encoded_state
            
            def get_bound_schema_id(self, encoded_state):
                return encoded_state.get("_schema_id")
        
        binder = CompleteBinder()
        
        # Test binding
        state = {"data": "test"}
        bound_state = binder.bind(state, "schema_v1")
        
        self.assertEqual(bound_state["_schema_id"], "schema_v1")
        self.assertTrue(binder.verify_binding(bound_state))
        self.assertEqual(binder.get_bound_schema_id(bound_state), "schema_v1")
        
        # Test unbound state
        unbound_state = {"data": "test"}
        self.assertFalse(binder.verify_binding(unbound_state))
        self.assertIsNone(binder.get_bound_schema_id(unbound_state))


if __name__ == '__main__':
    unittest.main()
