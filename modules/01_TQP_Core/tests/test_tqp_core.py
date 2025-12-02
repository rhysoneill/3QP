"""
Test suite for TQP Core module.

Tests cover:
- State management and validation
- Module registration and execution
- Time-step execution loop
- Memory buffer, event scheduler, message bus
- Error handling and rollback
"""

import unittest
from datetime import datetime, timedelta

from tqp_core import (
    TQPCore, SimulationConfig, AgentState, ModuleRegistration,
    ProcessType, MemoryRecord, GoalObject
)
from examples.example_modules import (
    NullModule, CounterModule, MemoryLoggerModule,
    StochasticModule, GoalManagerModule, ResourceModule,
    MessageSenderModule, MessageReceiverModule
)


class TestAgentState(unittest.TestCase):
    """Test AgentState data structure and validation."""
    
    def test_state_creation(self):
        """Test creating a valid agent state."""
        state = AgentState(
            agent_id="test_agent",
            simulation_time=0,
            calendar_time=datetime.now(),
            state_version=0
        )
        
        errors = state.validate()
        self.assertEqual(errors, [])
    
    def test_state_validation_negative_time(self):
        """Test validation catches negative simulation time."""
        state = AgentState(
            agent_id="test_agent",
            simulation_time=-1,
            calendar_time=datetime.now(),
            state_version=0
        )
        
        errors = state.validate()
        self.assertTrue(any("simulation_time" in e for e in errors))
    
    def test_state_validation_negative_resources(self):
        """Test validation catches negative resource values."""
        state = AgentState(
            agent_id="test_agent",
            simulation_time=0,
            calendar_time=datetime.now(),
            state_version=0,
            resource_state={"energy": -10.0}
        )
        
        errors = state.validate()
        self.assertTrue(any("energy" in e for e in errors))


class TestSimulationConfig(unittest.TestCase):
    """Test simulation configuration validation."""
    
    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = SimulationConfig(
            mission_start_datetime=datetime(2025, 1, 1),
            timestep_duration_minutes=60,
            total_timesteps=1000
        )
        self.assertEqual(config.timestep_duration_minutes, 60)
    
    def test_invalid_timestep_duration(self):
        """Test validation rejects invalid timestep duration."""
        with self.assertRaises(ValueError):
            SimulationConfig(
                mission_start_datetime=datetime(2025, 1, 1),
                timestep_duration_minutes=0,  # Invalid
                total_timesteps=1000
            )


class TestModuleRegistry(unittest.TestCase):
    """Test module registration and ordering."""
    
    def setUp(self):
        """Create a core instance for testing."""
        config = SimulationConfig(
            mission_start_datetime=datetime(2025, 1, 1),
            timestep_duration_minutes=60,
            total_timesteps=100
        )
        self.core = TQPCore(config)
    
    def test_register_module(self):
        """Test registering a module."""
        registration = ModuleRegistration(
            module_id="test_module",
            module_name="Test Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=NullModule()
        )
        
        self.core.register_module(registration)
        self.assertIn("test_module", self.core.module_registry.modules)
    
    def test_duplicate_registration(self):
        """Test that duplicate module IDs are rejected."""
        registration = ModuleRegistration(
            module_id="test_module",
            module_name="Test Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=NullModule()
        )
        
        self.core.register_module(registration)
        
        with self.assertRaises(ValueError):
            self.core.register_module(registration)
    
    def test_priority_ordering(self):
        """Test modules are ordered by priority."""
        # Register modules with different priorities
        for i, priority in enumerate([50, 200, 100]):
            registration = ModuleRegistration(
                module_id=f"module_{i}",
                module_name=f"Module {i}",
                module_version="1.0.0",
                process_type=ProcessType.FAST,
                execution_priority=priority,
                module=NullModule()
            )
            self.core.register_module(registration)
        
        fast_modules = self.core.module_registry.get_fast_modules()
        priorities = [m.execution_priority for m in fast_modules]
        
        # Should be sorted descending
        self.assertEqual(priorities, [200, 100, 50])


class TestCoreExecution(unittest.TestCase):
    """Test core execution loop."""
    
    def setUp(self):
        """Create a configured core instance."""
        config = SimulationConfig(
            mission_start_datetime=datetime(2025, 1, 1),
            timestep_duration_minutes=60,
            total_timesteps=100,
            random_seed=42
        )
        self.core = TQPCore(config)
    
    def test_initialization(self):
        """Test core initialization."""
        self.core.initialize()
        self.assertTrue(self.core.is_initialized)
        self.assertIsNotNone(self.core.current_state)
        self.assertEqual(self.core.current_state.simulation_time, 0)
    
    def test_single_step(self):
        """Test executing a single time-step."""
        self.core.register_module(ModuleRegistration(
            module_id="null",
            module_name="Null Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=NullModule()
        ))
        
        self.core.initialize()
        initial_time = self.core.current_state.simulation_time
        
        success = self.core.step()
        
        self.assertTrue(success)
        self.assertEqual(self.core.current_state.simulation_time, initial_time + 1)
    
    def test_counter_module(self):
        """Test counter module increments correctly."""
        counter = CounterModule("counter")
        
        self.core.register_module(ModuleRegistration(
            module_id="counter",
            module_name="Counter Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=counter
        ))
        
        self.core.initialize()
        
        # Run 10 steps
        for _ in range(10):
            self.core.step()
        
        # Check counter value
        count = self.core.current_state.internal_vars.get("counter.count", 0)
        self.assertEqual(count, 10)
    
    def test_memory_logger_module(self):
        """Test memory logger adds records to buffer."""
        logger = MemoryLoggerModule("logger")
        
        self.core.register_module(ModuleRegistration(
            module_id="logger",
            module_name="Memory Logger",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=logger
        ))
        
        self.core.initialize()
        
        # Run 5 steps
        for _ in range(5):
            self.core.step()
        
        # Check memory buffer
        self.assertEqual(len(self.core.current_state.memory_buffer), 5)
    
    def test_stochastic_determinism(self):
        """Test that stochastic module is deterministic with same seed."""
        # Run simulation twice with same seed
        results1 = self._run_stochastic_sim(seed=42, steps=10)
        results2 = self._run_stochastic_sim(seed=42, steps=10)
        
        # Should produce identical results
        self.assertEqual(results1, results2)
    
    def _run_stochastic_sim(self, seed, steps):
        """Helper to run stochastic simulation."""
        config = SimulationConfig(
            mission_start_datetime=datetime(2025, 1, 1),
            timestep_duration_minutes=60,
            total_timesteps=100,
            random_seed=seed
        )
        core = TQPCore(config)
        
        stochastic = StochasticModule("stoch", core.get_rng())
        core.register_module(ModuleRegistration(
            module_id="stoch",
            module_name="Stochastic Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=stochastic
        ))
        
        core.initialize()
        
        results = []
        for _ in range(steps):
            core.step()
            value = core.current_state.internal_vars.get("stoch.random_value", 0)
            results.append(value)
        
        return results
    
    def test_goal_manager(self):
        """Test goal manager creates and deletes goals."""
        manager = GoalManagerModule("goal_mgr")
        
        self.core.register_module(ModuleRegistration(
            module_id="goal_mgr",
            module_name="Goal Manager",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=manager
        ))
        
        self.core.initialize()
        
        # Run 20 steps (should create 2 goals)
        for _ in range(20):
            self.core.step()
        
        self.assertEqual(len(self.core.current_state.goal_state), 2)
    
    def test_resource_module(self):
        """Test resource module updates resources."""
        resource = ResourceModule("resource")
        
        self.core.register_module(ModuleRegistration(
            module_id="resource",
            module_name="Resource Module",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=resource
        ))
        
        # Initialize with starting resources
        initial_state = AgentState(
            agent_id="test_agent",
            simulation_time=0,
            calendar_time=datetime(2025, 1, 1),
            state_version=0,
            resource_state={"energy": 100.0, "cognitive_load": 50.0}
        )
        
        self.core.initialize(initial_state)
        
        # Run a few steps
        for _ in range(5):
            self.core.step()
        
        # Energy should have decreased
        energy = self.core.current_state.resource_state.get("energy", 0)
        self.assertLess(energy, 100.0)
    
    def test_message_passing(self):
        """Test inter-module message passing."""
        sender = MessageSenderModule("sender", "receiver")
        receiver = MessageReceiverModule("receiver")
        
        self.core.register_module(ModuleRegistration(
            module_id="sender",
            module_name="Sender",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=200,  # Higher priority (executes first)
            module=sender
        ))
        
        self.core.register_module(ModuleRegistration(
            module_id="receiver",
            module_name="Receiver",
            module_version="1.0.0",
            process_type=ProcessType.FAST,
            execution_priority=100,
            module=receiver
        ))
        
        self.core.initialize()
        
        # Run 15 steps (sender sends every 5 steps)
        for _ in range(15):
            self.core.step()
        
        # Receiver should have received 3 messages
        received = self.core.current_state.internal_vars.get("receiver.messages_received", 0)
        self.assertEqual(received, 3)


class TestMemoryBuffer(unittest.TestCase):
    """Test memory buffer operations."""
    
    def test_fifo_eviction(self):
        """Test that old memories are evicted when buffer is full."""
        from tqp_core.support_systems import MemoryBuffer
        
        buffer = MemoryBuffer(max_size=5)
        
        # Add 10 records
        for i in range(10):
            record = MemoryRecord(
                timestamp=i,
                event_type="test",
                event_data={"value": i},
                source_module="test",
                salience=0.5
            )
            buffer.add(record)
        
        # Should only have last 5
        self.assertEqual(buffer.size(), 5)
        
        # First record should be from timestamp 5
        first_record = buffer.get_all()[0]
        self.assertEqual(first_record.timestamp, 5)


class TestEventScheduler(unittest.TestCase):
    """Test event scheduler."""
    
    def test_schedule_and_retrieve(self):
        """Test scheduling and retrieving events."""
        from tqp_core.support_systems import EventScheduler
        from tqp_core import ScheduledEventRequest
        
        scheduler = EventScheduler()
        
        # Schedule events for different times
        req1 = ScheduledEventRequest(
            trigger_time=10,
            event_type="test",
            event_payload={},
            target_module="module1"
        )
        req2 = ScheduledEventRequest(
            trigger_time=5,
            event_type="test",
            event_payload={},
            target_module="module2"
        )
        
        scheduler.schedule(req1)
        scheduler.schedule(req2)
        
        # Retrieve events for time 5
        events_5 = scheduler.get_events_for_time(5)
        self.assertEqual(len(events_5), 1)
        
        # Retrieve events for time 10
        events_10 = scheduler.get_events_for_time(10)
        self.assertEqual(len(events_10), 1)


if __name__ == '__main__':
    unittest.main()
