"""
Unit tests for the BDI Cognitive Cycle module.
"""

import pytest
from bdi_cycle import (
    BDIModule,
    BDIInput,
    BDIConfig,
    BeliefAssertion,
    Belief,
    Desire,
    Intention,
    DomainOntology,
    PredicateSchema,
    ControlSignal,
)


class TestBDITypes:
    """Test BDI type definitions and validation."""
    
    def test_belief_assertion_validation(self):
        """Test BeliefAssertion validation."""
        # Valid assertion
        assertion = BeliefAssertion(
            predicate="resource_level",
            arguments=["oxygen", 0.85],
            confidence=0.95,
            source="perception"
        )
        assert assertion.confidence == 0.95
        
        # Invalid confidence (should raise)
        with pytest.raises(ValueError):
            BeliefAssertion(
                predicate="test",
                arguments=[],
                confidence=1.5,
                source="perception"
            )
    
    def test_belief_key_generation(self):
        """Test Belief unique key generation."""
        belief1 = Belief(
            predicate="resource_level",
            arguments=["oxygen", 0.85],
            confidence=0.95,
            timestamp=0,
            source="perception"
        )
        belief2 = Belief(
            predicate="resource_level",
            arguments=["oxygen", 0.85],
            confidence=0.90,
            timestamp=1,
            source="perception"
        )
        
        # Same predicate and arguments should have same key
        assert belief1.key() == belief2.key()
    
    def test_desire_validation(self):
        """Test Desire validation."""
        desire = Desire(
            goal_predicate="maintain_resource",
            goal_arguments=["oxygen", 0.9],
            priority=0.8,
            utility=50.0,
            constraints=[],
            timestamp=0
        )
        assert desire.priority == 0.8
        
        # Invalid priority
        with pytest.raises(ValueError):
            Desire(
                goal_predicate="test",
                goal_arguments=[],
                priority=1.5,
                utility=0.0,
                constraints=[],
                timestamp=0
            )
    
    def test_intention_validation(self):
        """Test Intention validation."""
        intention = Intention(
            goal_predicate="maintain_resource",
            goal_arguments=["oxygen", 0.9],
            commitment_level=1.0,
            resources=["resource_manager"],
            plan_id=None,
            timestamp=0
        )
        assert intention.commitment_level == 1.0


class TestDomainOntology:
    """Test domain ontology functionality."""
    
    def test_predicate_registration(self):
        """Test registering predicates in ontology."""
        ontology = DomainOntology()
        
        schema = PredicateSchema(
            name="resource_level",
            argument_types=[str, float],
            description="Resource level predicate",
            category="state"
        )
        ontology.register_predicate(schema)
        
        assert ontology.is_valid_predicate("resource_level")
        assert not ontology.is_valid_predicate("unknown_predicate")
    
    def test_argument_validation(self):
        """Test argument validation against schema."""
        ontology = DomainOntology()
        
        schema = PredicateSchema(
            name="resource_level",
            argument_types=[str, float],
            description="Resource level predicate",
            category="state"
        )
        ontology.register_predicate(schema)
        
        # Valid arguments
        assert ontology.validate_arguments("resource_level", ["oxygen", 0.85])
        
        # Wrong number of arguments
        assert not ontology.validate_arguments("resource_level", ["oxygen"])


class TestBDIConfig:
    """Test BDI configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BDIConfig()
        assert config.confidence_decay_rate == 0.0
        assert config.minimum_confidence_threshold == 0.1
        assert config.max_belief_set_size == 1000
    
    def test_config_validation(self):
        """Test configuration parameter validation."""
        # Invalid decay rate
        with pytest.raises(ValueError):
            BDIConfig(confidence_decay_rate=1.5)
        
        # Invalid policy
        with pytest.raises(ValueError):
            BDIConfig(intention_selection_policy="invalid")
    
    def test_config_update(self):
        """Test runtime configuration updates."""
        config = BDIConfig()
        config.update_parameter("max_belief_set_size", 500)
        assert config.max_belief_set_size == 500
        
        # Invalid parameter
        with pytest.raises(ValueError):
            config.update_parameter("unknown_param", 100)


class TestBDIModule:
    """Test main BDI module functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ontology = DomainOntology()
        
        # Register test predicates
        self.ontology.register_predicate(PredicateSchema(
            name="resource_level",
            argument_types=[str, float],
            description="Resource level",
            category="state"
        ))
        self.ontology.register_predicate(PredicateSchema(
            name="maintain_resource",
            argument_types=[str, float],
            description="Maintain resource goal",
            category="goal"
        ))
        
        self.config = BDIConfig()
        self.module = BDIModule(config=self.config, ontology=self.ontology)
        self.module.initialize()
    
    def test_initialization(self):
        """Test module initialization."""
        assert self.module.initialized
        assert len(self.module.beliefs) == 0
        assert len(self.module.desires) == 0
        assert len(self.module.intentions) == 0
    
    def test_belief_integration(self):
        """Test belief integration in BDI cycle."""
        # Create input with new belief
        bdi_input = BDIInput(
            timestep=0,
            new_beliefs=[
                BeliefAssertion(
                    predicate="resource_level",
                    arguments=["oxygen", 0.85],
                    confidence=0.95,
                    source="perception"
                )
            ],
            control_signal=ControlSignal.RUN
        )
        
        # Execute cycle
        output = self.module.execute_cycle(bdi_input)
        
        # Check output
        assert output.status.code == "success"
        assert len(output.beliefs) == 1
        assert output.beliefs[0].predicate == "resource_level"
        assert output.cycle_statistics.beliefs_added == 1
    
    def test_belief_update(self):
        """Test belief update with higher confidence."""
        # First cycle: add belief
        input1 = BDIInput(
            timestep=0,
            new_beliefs=[
                BeliefAssertion(
                    predicate="resource_level",
                    arguments=["oxygen", 0.85],
                    confidence=0.8,
                    source="perception"
                )
            ]
        )
        output1 = self.module.execute_cycle(input1)
        assert len(output1.beliefs) == 1
        assert output1.beliefs[0].confidence == 0.8
        
        # Second cycle: update with higher confidence
        input2 = BDIInput(
            timestep=1,
            new_beliefs=[
                BeliefAssertion(
                    predicate="resource_level",
                    arguments=["oxygen", 0.85],
                    confidence=0.95,
                    source="perception"
                )
            ]
        )
        output2 = self.module.execute_cycle(input2)
        assert len(output2.beliefs) == 1
        assert output2.beliefs[0].confidence == 0.95
        assert output2.cycle_statistics.beliefs_updated == 1
    
    def test_control_signals(self):
        """Test control signal handling."""
        # Test PAUSE
        pause_input = BDIInput(
            timestep=0,
            new_beliefs=[],
            control_signal=ControlSignal.PAUSE
        )
        output = self.module.execute_cycle(pause_input)
        assert output.status.code == "skipped"
        
        # Test RESET
        reset_input = BDIInput(
            timestep=0,
            new_beliefs=[],
            control_signal=ControlSignal.RESET
        )
        output = self.module.execute_cycle(reset_input)
        assert output.status.code == "success"
        assert len(output.beliefs) == 0
    
    def test_timestep_validation(self):
        """Test timestep sequencing validation."""
        # First timestep
        input1 = BDIInput(timestep=0, new_beliefs=[])
        output1 = self.module.execute_cycle(input1)
        assert output1.status.code == "success"
        
        # Non-sequential timestep should fail
        input2 = BDIInput(timestep=5, new_beliefs=[])
        output2 = self.module.execute_cycle(input2)
        assert output2.status.code == "error"
    
    def test_max_belief_set_size(self):
        """Test enforcement of maximum belief set size."""
        # Configure small max size
        small_config = BDIConfig(max_belief_set_size=2)
        small_module = BDIModule(config=small_config, ontology=self.ontology)
        small_module.initialize()
        
        # Add 3 beliefs
        bdi_input = BDIInput(
            timestep=0,
            new_beliefs=[
                BeliefAssertion("resource_level", ["oxygen", 0.9], 0.9, "perception"),
                BeliefAssertion("resource_level", ["water", 0.8], 0.8, "perception"),
                BeliefAssertion("resource_level", ["food", 0.7], 0.7, "perception"),
            ]
        )
        
        output = small_module.execute_cycle(bdi_input)
        
        # Should only keep 2 highest-confidence beliefs
        assert len(output.beliefs) <= 2
    
    def test_state_summary(self):
        """Test state summary generation."""
        # Add some beliefs
        bdi_input = BDIInput(
            timestep=0,
            new_beliefs=[
                BeliefAssertion("resource_level", ["oxygen", 0.85], 0.95, "perception")
            ]
        )
        self.module.execute_cycle(bdi_input)
        
        # Get summary
        summary = self.module.get_state_summary()
        assert summary['timestep'] == 0
        assert summary['belief_count'] == 1
        assert len(summary['beliefs']) == 1


class TestBeliefRevision:
    """Test belief revision engine."""
    
    def test_confidence_pruning(self):
        """Test pruning of low-confidence beliefs."""
        config = BDIConfig(minimum_confidence_threshold=0.5)
        ontology = DomainOntology()
        ontology.register_predicate(PredicateSchema(
            name="test_pred",
            argument_types=[],
            description="Test",
            category="state"
        ))
        
        module = BDIModule(config=config, ontology=ontology)
        module.initialize()
        
        # Add beliefs with different confidences
        bdi_input = BDIInput(
            timestep=0,
            new_beliefs=[
                BeliefAssertion("test_pred", [], 0.9, "perception"),
                BeliefAssertion("test_pred", ["low"], 0.3, "perception"),
            ]
        )
        
        output = module.execute_cycle(bdi_input)
        
        # Low confidence belief should be pruned
        assert all(b.confidence >= 0.5 for b in output.beliefs)


class TestDesireFormation:
    """Test desire formation engine."""
    
    def test_desire_retention_window(self):
        """Test pruning of old desires."""
        config = BDIConfig(desire_retention_window=2)
        module = BDIModule(config=config)
        module.initialize()
        
        # This would require manually adding desires to test
        # For now, this is a placeholder for future testing
        pass


class TestIntentionSelection:
    """Test intention selection engine."""
    
    def test_max_intention_set_size(self):
        """Test enforcement of maximum intention set size."""
        config = BDIConfig(max_intention_set_size=2)
        module = BDIModule(config=config)
        module.initialize()
        
        # This would require desires to select from
        # For now, this is a placeholder for future testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
