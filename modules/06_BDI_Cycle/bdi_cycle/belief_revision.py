"""
Belief revision engine for the BDI Cognitive Cycle.

Implements belief update, conflict resolution, inference, and pruning
according to the BDI specification.
"""

from typing import List, Dict, Set, Optional
import time
from .types import Belief, BeliefAssertion, BDIConfig, DomainOntology


class BeliefRevisionEngine:
    """
    Manages belief set updates including validation, conflict resolution,
    inference, decay, and pruning.
    """
    
    def __init__(self, config: BDIConfig, ontology: DomainOntology):
        """
        Initialize belief revision engine.
        
        Args:
            config: BDI configuration parameters
            ontology: Domain ontology for validation
        """
        self.config = config
        self.ontology = ontology
        self.inference_rules: List[Dict] = []  # Placeholder for inference rules
    
    def revise_beliefs(
        self,
        current_beliefs: Dict[tuple, Belief],
        new_assertions: List[BeliefAssertion],
        current_timestep: int
    ) -> tuple[Dict[tuple, Belief], Dict[str, int]]:
        """
        Execute belief revision phase.
        
        Args:
            current_beliefs: Current belief set (keyed by belief.key())
            new_assertions: New belief assertions to integrate
            current_timestep: Current simulation timestep
            
        Returns:
            Tuple of (updated belief set, statistics dict)
        """
        stats = {
            'added': 0,
            'removed': 0,
            'updated': 0,
            'inference_applications': 0
        }
        
        # Start with copy of current beliefs
        updated_beliefs = current_beliefs.copy()
        
        # Phase 1: Validate and integrate new assertions
        for assertion in new_assertions:
            if not self._validate_assertion(assertion):
                continue  # Skip invalid assertions
            
            belief = self._assertion_to_belief(assertion, current_timestep)
            key = belief.key()
            
            if key in updated_beliefs:
                # Conflict resolution: higher confidence wins
                existing = updated_beliefs[key]
                if belief.confidence > existing.confidence:
                    updated_beliefs[key] = belief
                    stats['updated'] += 1
                # else: retain existing belief
            else:
                # New belief
                updated_beliefs[key] = belief
                stats['added'] += 1
        
        # Phase 2: Apply confidence decay (if configured)
        if self.config.confidence_decay_rate > 0.0:
            updated_beliefs = self._apply_decay(
                updated_beliefs,
                current_timestep
            )
        
        # Phase 3: Prune low-confidence beliefs
        before_prune = len(updated_beliefs)
        updated_beliefs = self._prune_low_confidence(updated_beliefs)
        stats['removed'] += before_prune - len(updated_beliefs)
        
        # Phase 4: Prune old beliefs (outside retention window)
        before_prune = len(updated_beliefs)
        updated_beliefs = self._prune_old_beliefs(
            updated_beliefs,
            current_timestep
        )
        stats['removed'] += before_prune - len(updated_beliefs)
        
        # Phase 5: Apply inference rules (if configured)
        if self.config.inference_depth_limit > 0 and self.inference_rules:
            inferred_beliefs, inference_count = self._apply_inference(
                updated_beliefs,
                current_timestep
            )
            # Add inferred beliefs
            for belief in inferred_beliefs:
                key = belief.key()
                if key not in updated_beliefs:
                    updated_beliefs[key] = belief
                    stats['added'] += 1
            stats['inference_applications'] = inference_count
        
        # Phase 6: Enforce maximum set size
        if len(updated_beliefs) > self.config.max_belief_set_size:
            before_prune = len(updated_beliefs)
            updated_beliefs = self._enforce_max_size(updated_beliefs)
            stats['removed'] += before_prune - len(updated_beliefs)
        
        return updated_beliefs, stats
    
    def _validate_assertion(self, assertion: BeliefAssertion) -> bool:
        """Validate a belief assertion against the ontology."""
        # Check if predicate is registered
        if not self.ontology.is_valid_predicate(assertion.predicate):
            return False
        
        # Check if arguments match expected types
        if not self.ontology.validate_arguments(
            assertion.predicate,
            assertion.arguments
        ):
            return False
        
        return True
    
    def _assertion_to_belief(
        self,
        assertion: BeliefAssertion,
        timestep: int
    ) -> Belief:
        """Convert a belief assertion to a belief."""
        return Belief(
            predicate=assertion.predicate,
            arguments=assertion.arguments,
            confidence=assertion.confidence,
            timestamp=timestep,
            source=assertion.source
        )
    
    def _apply_decay(
        self,
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> Dict[tuple, Belief]:
        """Apply confidence decay to old beliefs."""
        decayed = {}
        for key, belief in beliefs.items():
            age = current_timestep - belief.timestamp
            if age > 0:
                # Simple exponential decay
                decay_factor = (1.0 - self.config.confidence_decay_rate) ** age
                new_confidence = belief.confidence * decay_factor
                decayed[key] = Belief(
                    predicate=belief.predicate,
                    arguments=belief.arguments,
                    confidence=new_confidence,
                    timestamp=belief.timestamp,
                    source=belief.source
                )
            else:
                decayed[key] = belief
        return decayed
    
    def _prune_low_confidence(
        self,
        beliefs: Dict[tuple, Belief]
    ) -> Dict[tuple, Belief]:
        """Remove beliefs below minimum confidence threshold."""
        return {
            key: belief
            for key, belief in beliefs.items()
            if belief.confidence >= self.config.minimum_confidence_threshold
        }
    
    def _prune_old_beliefs(
        self,
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> Dict[tuple, Belief]:
        """Remove beliefs outside retention window."""
        retention_cutoff = current_timestep - self.config.belief_retention_window
        return {
            key: belief
            for key, belief in beliefs.items()
            if belief.timestamp >= retention_cutoff
        }
    
    def _apply_inference(
        self,
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> tuple[List[Belief], int]:
        """
        Apply inference rules to derive new beliefs.
        
        Returns:
            Tuple of (inferred beliefs list, number of rule applications)
        """
        # TODO: Implement inference engine when rules are defined
        # For now, return empty list
        # 
        # Inference would involve:
        # 1. Pattern matching against belief set
        # 2. Forward chaining derivation
        # 3. Depth-bounded search
        # 4. Cycle detection
        
        inferred = []
        applications = 0
        
        return inferred, applications
    
    def _enforce_max_size(
        self,
        beliefs: Dict[tuple, Belief]
    ) -> Dict[tuple, Belief]:
        """
        Enforce maximum belief set size by pruning lowest-confidence beliefs.
        """
        if len(beliefs) <= self.config.max_belief_set_size:
            return beliefs
        
        # Sort by confidence (ascending) and keep highest-confidence beliefs
        sorted_beliefs = sorted(
            beliefs.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )
        
        # Keep only top max_belief_set_size beliefs
        return dict(sorted_beliefs[:self.config.max_belief_set_size])
    
    def add_inference_rule(self, rule: Dict) -> None:
        """
        Add an inference rule.
        
        Args:
            rule: Inference rule specification
                  (format TBD, depends on domain requirements)
        """
        self.inference_rules.append(rule)
