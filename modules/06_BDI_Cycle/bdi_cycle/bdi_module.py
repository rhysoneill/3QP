"""
Main BDI Cognitive Cycle module.

Orchestrates the complete BDI cycle including belief revision,
desire formation, and intention selection.
"""

from typing import Dict, List, Optional
import time
from .types import (
    Belief,
    BeliefAssertion,
    Desire,
    Intention,
    BDIInput,
    BDIOutput,
    BDIConfig,
    Status,
    CycleStatistics,
    DomainOntology,
    ControlSignal,
)
from .belief_revision import BeliefRevisionEngine
from .desire_formation import DesireFormationEngine
from .intention_selection import IntentionSelectionEngine, ResourceManager


class BDIModule:
    """
    Main BDI Cognitive Cycle module.
    
    Implements the complete BDI cycle with strict phase ordering:
    1. Belief Revision Phase
    2. Desire Formation Phase
    3. Intention Selection Phase
    4. State Commit Phase
    """
    
    def __init__(
        self,
        config: BDIConfig = None,
        ontology: DomainOntology = None
    ):
        """
        Initialize BDI module.
        
        Args:
            config: BDI configuration parameters
            ontology: Domain ontology for validation
        """
        self.config = config or BDIConfig()
        self.ontology = ontology or DomainOntology()
        
        # Initialize engines
        self.belief_engine = BeliefRevisionEngine(self.config, self.ontology)
        self.desire_engine = DesireFormationEngine(self.config, self.ontology)
        self.resource_manager = ResourceManager()
        self.intention_engine = IntentionSelectionEngine(
            self.config,
            self.ontology,
            self.resource_manager
        )
        
        # Persistent state
        self.beliefs: Dict[tuple, Belief] = {}
        self.desires: Dict[tuple, Desire] = {}
        self.intentions: Dict[tuple, Intention] = {}
        self.current_timestep: int = -1
        
        # Tracking
        self.initialized = False
    
    def initialize(self) -> None:
        """Initialize the BDI module."""
        self.beliefs = {}
        self.desires = {}
        self.intentions = {}
        self.current_timestep = -1
        self.initialized = True
    
    def execute_cycle(self, bdi_input: BDIInput) -> BDIOutput:
        """
        Execute a complete BDI cycle.
        
        Args:
            bdi_input: Input for this timestep
            
        Returns:
            BDI output containing updated state and statistics
        """
        cycle_start = time.time()
        
        # Validate input
        if not self._validate_input(bdi_input):
            return self._create_error_output(
                bdi_input.timestep,
                "Invalid input: timestep must be sequential"
            )
        
        # Handle control signals
        if bdi_input.control_signal == ControlSignal.PAUSE:
            return self._create_skipped_output(bdi_input.timestep)
        
        if bdi_input.control_signal == ControlSignal.RESET:
            self.initialize()
            return self._create_success_output(
                bdi_input.timestep,
                CycleStatistics()
            )
        
        # Update configuration if requested
        if bdi_input.configuration_update:
            try:
                self.config.update_parameter(
                    bdi_input.configuration_update.parameter_name,
                    bdi_input.configuration_update.parameter_value
                )
            except Exception as e:
                return self._create_error_output(
                    bdi_input.timestep,
                    f"Configuration update failed: {str(e)}"
                )
        
        # Execute BDI cycle phases
        try:
            statistics = CycleStatistics()
            
            # Phase 1: Belief Revision
            self.beliefs, belief_stats = self.belief_engine.revise_beliefs(
                self.beliefs,
                bdi_input.new_beliefs,
                bdi_input.timestep
            )
            statistics.beliefs_added = belief_stats['added']
            statistics.beliefs_removed = belief_stats['removed']
            statistics.beliefs_updated = belief_stats['updated']
            statistics.inference_rule_applications = belief_stats['inference_applications']
            
            # Phase 2: Desire Formation
            self.desires, desire_stats = self.desire_engine.form_desires(
                self.desires,
                self.beliefs,
                bdi_input.timestep
            )
            statistics.desires_added = desire_stats['added']
            statistics.desires_removed = desire_stats['removed']
            statistics.conflicts_resolved = desire_stats['conflicts_resolved']
            
            # Phase 3: Intention Selection
            self.intentions, intention_stats = self.intention_engine.select_intentions(
                self.intentions,
                self.desires,
                self.beliefs,
                bdi_input.timestep
            )
            statistics.intentions_added = intention_stats['added']
            statistics.intentions_removed = intention_stats['removed']
            
            # Phase 4: State Commit
            self.current_timestep = bdi_input.timestep
            
            # Calculate cycle duration
            cycle_end = time.time()
            statistics.cycle_duration_ms = (cycle_end - cycle_start) * 1000.0
            
            # Create output
            return self._create_success_output(bdi_input.timestep, statistics)
            
        except Exception as e:
            return self._create_error_output(
                bdi_input.timestep,
                f"Cycle execution failed: {str(e)}"
            )
    
    def _validate_input(self, bdi_input: BDIInput) -> bool:
        """Validate input constraints."""
        # Check timestep sequencing
        if self.current_timestep >= 0:
            if bdi_input.timestep != self.current_timestep + 1:
                return False
        
        return True
    
    def _create_success_output(
        self,
        timestep: int,
        statistics: CycleStatistics
    ) -> BDIOutput:
        """Create a successful output."""
        return BDIOutput(
            timestep=timestep,
            beliefs=list(self.beliefs.values()),
            desires=list(self.desires.values()),
            intentions=list(self.intentions.values()),
            cycle_statistics=statistics,
            status=Status(code="success", message=None)
        )
    
    def _create_error_output(
        self,
        timestep: int,
        message: str
    ) -> BDIOutput:
        """Create an error output."""
        return BDIOutput(
            timestep=timestep,
            beliefs=list(self.beliefs.values()),
            desires=list(self.desires.values()),
            intentions=list(self.intentions.values()),
            cycle_statistics=CycleStatistics(),
            status=Status(code="error", message=message)
        )
    
    def _create_skipped_output(self, timestep: int) -> BDIOutput:
        """Create a skipped output (for pause signal)."""
        return BDIOutput(
            timestep=timestep,
            beliefs=list(self.beliefs.values()),
            desires=list(self.desires.values()),
            intentions=list(self.intentions.values()),
            cycle_statistics=CycleStatistics(),
            status=Status(code="skipped", message="Cycle paused")
        )
    
    def get_state_summary(self) -> Dict:
        """Get a summary of current BDI state."""
        return {
            'timestep': self.current_timestep,
            'belief_count': len(self.beliefs),
            'desire_count': len(self.desires),
            'intention_count': len(self.intentions),
            'beliefs': [
                {
                    'predicate': b.predicate,
                    'confidence': b.confidence,
                    'source': b.source
                }
                for b in self.beliefs.values()
            ],
            'desires': [
                {
                    'goal': d.goal_predicate,
                    'priority': d.priority,
                    'utility': d.utility
                }
                for d in self.desires.values()
            ],
            'intentions': [
                {
                    'goal': i.goal_predicate,
                    'commitment': i.commitment_level,
                    'resources': i.resources
                }
                for i in self.intentions.values()
            ]
        }
    
    def add_predicate(self, predicate_name: str, argument_types: List[type], category: str = "state") -> None:
        """
        Add a predicate to the domain ontology.
        
        Args:
            predicate_name: Name of the predicate
            argument_types: Expected types for arguments
            category: Predicate category (state, goal, constraint)
        """
        from .types import PredicateSchema
        schema = PredicateSchema(
            name=predicate_name,
            argument_types=argument_types,
            description=f"User-defined predicate: {predicate_name}",
            category=category
        )
        self.ontology.register_predicate(schema)
