"""
Tests for the 3QP Logging System.

Tests core functionality: log types, serialization, batch management,
manifest, and integration with the logging interface.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from logging_system import (
    LoggingSystem,
    LoggingConfig,
    StateLogEntry,
    EventLogEntry,
    CycleLogEntry,
    MetricLogEntry,
)
from logging_system.serializer import Serializer
from logging_system.batch_manager import BatchManager, BatchFile
from logging_system.manifest import IndexManifest


class TestLogEntryTypes(unittest.TestCase):
    """Test log entry data types and validation."""
    
    def test_state_log_entry_valid(self):
        """Test valid state log entry."""
        entry = StateLogEntry(
            timestamp=42,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            state_snapshot={"var1": 1.0, "var2": "test"}
        )
        
        errors = entry.validate()
        self.assertEqual(len(errors), 0)
    
    def test_state_log_entry_invalid(self):
        """Test invalid state log entry."""
        entry = StateLogEntry(
            timestamp=-1,  # Invalid
            wall_time="",  # Invalid
            module_id="",  # Invalid
            state_snapshot="not_a_dict"  # Invalid
        )
        
        errors = entry.validate()
        self.assertGreater(len(errors), 0)
    
    def test_event_log_entry_valid(self):
        """Test valid event log entry."""
        entry = EventLogEntry(
            timestamp=42,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            event_category="test_event",
            event_data={"key": "value"}
        )
        
        errors = entry.validate()
        self.assertEqual(len(errors), 0)
    
    def test_metric_log_entry_valid(self):
        """Test valid metric log entry."""
        entry = MetricLogEntry(
            timestamp_start=0,
            timestamp_end=10,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            metric_name="test_metric",
            metric_value=42.5
        )
        
        errors = entry.validate()
        self.assertEqual(len(errors), 0)
    
    def test_metric_log_invalid_range(self):
        """Test metric with invalid time range."""
        entry = MetricLogEntry(
            timestamp_start=10,
            timestamp_end=5,  # Invalid: end < start
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            metric_name="test_metric",
            metric_value=42.5
        )
        
        errors = entry.validate()
        self.assertGreater(len(errors), 0)


class TestSerializer(unittest.TestCase):
    """Test log serialization."""
    
    def setUp(self):
        """Set up test serializer."""
        self.serializer = Serializer(compression="none")
    
    def test_serialize_state_entry(self):
        """Test serializing a state log entry."""
        entry = StateLogEntry(
            timestamp=42,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            state_snapshot={"var1": 1.0}
        )
        
        json_str = self.serializer.serialize_entry(entry)
        self.assertIsInstance(json_str, str)
        
        # Deserialize to verify
        entry_dict = self.serializer.deserialize_entry(json_str)
        self.assertEqual(entry_dict["log_type"], "STATE")
        self.assertEqual(entry_dict["timestamp"], 42)
        self.assertEqual(entry_dict["module_id"], "test_module")
    
    def test_serialization_deterministic(self):
        """Test that serialization is deterministic."""
        entry = StateLogEntry(
            timestamp=42,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            state_snapshot={"z": 3, "a": 1, "m": 2}  # Unordered
        )
        
        # Serialize twice
        json_str1 = self.serializer.serialize_entry(entry)
        json_str2 = self.serializer.serialize_entry(entry)
        
        # Should be identical
        self.assertEqual(json_str1, json_str2)


class TestBatchManager(unittest.TestCase):
    """Test batch file management."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = LoggingConfig(
            output_directory=self.temp_dir,
            batch_size=10,
            enable_compression=False
        )
        self.serializer = Serializer(compression="none")
        self.batch_manager = BatchManager(self.config, self.serializer)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_batch_creation(self):
        """Test creating a batch file."""
        batch = self.batch_manager.get_batch("test_module", "STATE", 0)
        
        self.assertIsNotNone(batch)
        self.assertEqual(batch.module_id, "test_module")
        self.assertEqual(batch.log_type, "STATE")
        self.assertEqual(batch.timestamp_start, 0)
        self.assertEqual(batch.timestamp_end, 9)
    
    def test_batch_rotation(self):
        """Test batch rotation at boundary."""
        # Get batch for timestep 0
        batch1 = self.batch_manager.get_batch("test_module", "STATE", 0)
        
        # Get batch for timestep 10 (should trigger rotation)
        batch2 = self.batch_manager.get_batch("test_module", "STATE", 10)
        
        # Should be different batches
        self.assertNotEqual(batch1.timestamp_start, batch2.timestamp_start)
        self.assertEqual(batch2.timestamp_start, 10)
        
        # First batch should be in completed list
        self.assertEqual(len(self.batch_manager.completed_batches), 1)
    
    def test_batch_write(self):
        """Test writing entries to batch."""
        batch = self.batch_manager.get_batch("test_module", "STATE", 0)
        
        entry = StateLogEntry(
            timestamp=0,
            wall_time="2025-01-01T12:00:00.000Z",
            module_id="test_module",
            state_snapshot={"var": 1.0}
        )
        
        success = batch.write_entry(entry)
        self.assertTrue(success)
        self.assertEqual(batch.record_count, 1)


class TestIndexManifest(unittest.TestCase):
    """Test index manifest functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manifest_path = self.temp_dir / "manifest.json"
        self.manifest = IndexManifest(self.manifest_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manifest_initialization(self):
        """Test manifest initialization."""
        self.manifest.initialize(simulation_id="test_sim_001")
        
        self.assertEqual(self.manifest.simulation_id, "test_sim_001")
        self.assertTrue(self.manifest_path.exists())
    
    def test_manifest_add_batch(self):
        """Test adding batch to manifest."""
        from logging_system.types import BatchMetadata
        
        self.manifest.initialize(simulation_id="test_sim_001")
        
        metadata = BatchMetadata(
            file_path="STATE/test_module_STATE_00000000_00000009.jsonl",
            module_id="test_module",
            log_type="STATE",
            timestamp_start=0,
            timestamp_end=9,
            record_count=10,
            file_size_bytes=1024,
            checksum="abc123",
            compression="none",
            status="closed"
        )
        
        self.manifest.add_batch(metadata)
        self.assertEqual(len(self.manifest.batches), 1)
    
    def test_manifest_query(self):
        """Test querying manifest."""
        from logging_system.types import BatchMetadata
        
        self.manifest.initialize(simulation_id="test_sim_001")
        
        # Add multiple batches
        for i in range(3):
            metadata = BatchMetadata(
                file_path=f"STATE/mod{i}_STATE_00000000_00000009.jsonl",
                module_id=f"mod{i}",
                log_type="STATE",
                timestamp_start=0,
                timestamp_end=9,
                record_count=10,
                file_size_bytes=1024,
                checksum="abc123",
                compression="none",
                status="closed"
            )
            self.manifest.add_batch(metadata)
        
        # Query by module
        results = self.manifest.query_batches(module_id="mod1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].module_id, "mod1")


class TestLoggingSystemIntegration(unittest.TestCase):
    """Test complete logging system integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = LoggingConfig(
            output_directory=self.temp_dir,
            batch_size=5,
            enable_compression=False,
            streaming_mode=True
        )
        self.logging_system = LoggingSystem(self.config)
        self.logging_system.initialize(simulation_id="test_integration")
    
    def tearDown(self):
        """Clean up test environment."""
        self.logging_system.finalize()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_module_registration(self):
        """Test module registration."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["STATE", "EVENT"]
        )
        
        self.assertIsNotNone(logger)
        self.assertIn("test_module", self.logging_system.registered_modules)
    
    def test_state_logging(self):
        """Test logging state snapshots."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["STATE"]
        )
        
        success = logger.log_state(
            timestamp=0,
            state_dict={"var1": 1.0, "var2": "test"}
        )
        
        self.assertTrue(success)
    
    def test_event_logging(self):
        """Test logging events."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["EVENT"],
            event_categories=["test_event"]
        )
        
        success = logger.log_event(
            timestamp=0,
            event_category="test_event",
            event_data={"key": "value"}
        )
        
        self.assertTrue(success)
    
    def test_metric_logging(self):
        """Test logging metrics."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["METRIC"],
            metric_names=["test_metric"]
        )
        
        success = logger.log_metric(
            timestamp_start=0,
            timestamp_end=5,
            metric_name="test_metric",
            metric_value=42.5
        )
        
        self.assertTrue(success)
    
    def test_file_creation(self):
        """Test that log files are created."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["STATE"]
        )
        
        for i in range(3):
            logger.log_state(
                timestamp=i,
                state_dict={"step": i}
            )
        
        self.logging_system.finalize()
        
        # Check that STATE directory exists
        state_dir = self.temp_dir / "STATE"
        self.assertTrue(state_dir.exists())
        
        # Check that log file exists
        log_files = list(state_dir.glob("*.jsonl"))
        self.assertGreater(len(log_files), 0)
    
    def test_statistics(self):
        """Test getting statistics."""
        logger = self.logging_system.register_module(
            module_id="test_module",
            module_version="1.0.0",
            log_types=["STATE"]
        )
        
        for i in range(10):
            logger.log_state(timestamp=i, state_dict={"step": i})
        
        self.logging_system.finalize()
        
        stats = self.logging_system.get_statistics()
        
        self.assertGreater(stats["total_records"], 0)
        self.assertIn("test_module", stats["modules"])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
