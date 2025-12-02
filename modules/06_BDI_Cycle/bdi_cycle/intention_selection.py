"""
Intention selection engine for the BDI Cognitive Cycle.

Implements intention commitment, resource allocation, and reconsideration
according to the BDI specification.
"""

from typing import List, Dict, Set, Optional
from .types import Belief, Desire, Intention, BDIConfig, DomainOntology


class ResourceManager:
    """
    Manages resource allocation for intentions.
    """
    
    def __init__(self, available_resources: List[str] = None):
        """
        Initialize resource manager.
        
        Args:
            available_resources: List of available resource identifiers
        """
        self.available_resources = set(available_resources or [])
        self.allocated_resources: Dict[str, str] = {}  # resource -> intention_key
    
    def allocate(self, intention_key: tuple, resources: List[str]) -> bool:
        """
        Attempt to allocate resources to an intention.
        
        Args:
            intention_key: Key of the intention requesting resources
            resources: List of resource identifiers to allocate
            
        Returns:
            True if allocation succeeded, False if resources unavailable
        """
        # Check if all requested resources are available
        for resource in resources:
            if resource in self.allocated_resources:
                # Resource already allocated
                return False
        
        # Allocate all resources
        for resource in resources:
            self.allocated_resources[resource] = intention_key
        
        return True
    
    def deallocate(self, intention_key: tuple) -> None:
        """
        Deallocate all resources assigned to an intention.
        
        Args:
            intention_key: Key of the intention releasing resources
        """
        # Find and remove all resources allocated to this intention
        to_remove = [
            resource
            for resource, allocated_to in self.allocated_resources.items()
            if allocated_to == intention_key
        ]
        for resource in to_remove:
            del self.allocated_resources[resource]
    
    def get_allocated_resources(self, intention_key: tuple) -> List[str]:
        """Get list of resources allocated to an intention."""
        return [
            resource
            for resource, allocated_to in self.allocated_resources.items()
            if allocated_to == intention_key
        ]
    
    def is_available(self, resource: str) -> bool:
        """Check if a resource is available."""
        return resource not in self.allocated_resources


class IntentionSelectionEngine:
    """
    Manages intention set updates including candidate filtering, selection,
    resource allocation, and reconsideration.
    """
    
    def __init__(
        self,
        config: BDIConfig,
        ontology: DomainOntology,
        resource_manager: ResourceManager = None
    ):
        """
        Initialize intention selection engine.
        
        Args:
            config: BDI configuration parameters
            ontology: Domain ontology for validation
            resource_manager: Resource manager for allocation tracking
        """
        self.config = config
        self.ontology = ontology
        self.resource_manager = resource_manager or ResourceManager()
    
    def select_intentions(
        self,
        current_intentions: Dict[tuple, Intention],
        desires: Dict[tuple, Desire],
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> tuple[Dict[tuple, Intention], Dict[str, int]]:
        """
        Execute intention selection phase.
        
        Args:
            current_intentions: Current intention set (keyed by intention.key())
            desires: Current desire set
            beliefs: Current belief set
            current_timestep: Current simulation timestep
            
        Returns:
            Tuple of (updated intention set, statistics dict)
        """
        stats = {
            'added': 0,
            'removed': 0
        }
        
        # Phase 1: Reconsider existing intentions
        retained_intentions, reconsidered = self._reconsider_intentions(
            current_intentions,
            beliefs,
            current_timestep
        )
        stats['removed'] += reconsidered
        
        # Phase 2: Identify candidate desires for commitment
        candidates = self._identify_candidates(
            desires,
            retained_intentions,
            beliefs
        )
        
        # Phase 3: Filter candidates
        filtered_candidates = self._filter_candidates(
            candidates,
            retained_intentions,
            beliefs
        )
        
        # Phase 4: Select intentions from candidates
        selected_intentions = self._apply_selection_policy(
            filtered_candidates,
            retained_intentions
        )
        
        # Phase 5: Allocate resources and commit
        final_intentions = retained_intentions.copy()
        for desire in selected_intentions:
            intention = self._commit_to_desire(desire, current_timestep)
            if intention:
                key = intention.key()
                final_intentions[key] = intention
                stats['added'] += 1
        
        # Phase 6: Enforce maximum set size
        if len(final_intentions) > self.config.max_intention_set_size:
            before_prune = len(final_intentions)
            final_intentions = self._enforce_max_size(final_intentions)
            stats['removed'] += before_prune - len(final_intentions)
        
        return final_intentions, stats
    
    def _reconsider_intentions(
        self,
        intentions: Dict[tuple, Intention],
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> tuple[Dict[tuple, Intention], int]:
        """
        Reconsider existing intentions based on belief state changes.
        
        Returns:
            Tuple of (retained intentions, number dropped)
        """
        retained = {}
        dropped = 0
        
        for key, intention in intentions.items():
            # Check if intention should be retained
            if self._should_retain(intention, beliefs):
                retained[key] = intention
            else:
                # Drop intention and deallocate resources
                self.resource_manager.deallocate(key)
                dropped += 1
        
        return retained, dropped
    
    def _should_retain(
        self,
        intention: Intention,
        beliefs: Dict[tuple, Belief]
    ) -> bool:
        """
        Determine if an intention should be retained.
        
        Retention criteria:
        - Commitment level > 0
        - Preconditions still hold (if applicable)
        """
        # Drop if commitment has decayed to zero
        if intention.commitment_level <= 0.0:
            return False
        
        # TODO: Check preconditions against beliefs
        # For now, always retain if commitment > 0
        
        return True
    
    def _identify_candidates(
        self,
        desires: Dict[tuple, Desire],
        intentions: Dict[tuple, Intention],
        beliefs: Dict[tuple, Belief]
    ) -> List[Desire]:
        """
        Identify desires that are candidates for commitment.
        
        A desire is a candidate if it's not already committed.
        """
        intention_keys = set(intentions.keys())
        candidates = []
        
        for key, desire in desires.items():
            # Check if already committed
            # (desire and intention have same key structure)
            if key not in intention_keys:
                candidates.append(desire)
        
        return candidates
    
    def _filter_candidates(
        self,
        candidates: List[Desire],
        intentions: Dict[tuple, Intention],
        beliefs: Dict[tuple, Belief]
    ) -> List[Desire]:
        """
        Filter candidates based on:
        - Conflicts with existing intentions
        - Resource constraints
        - Priority threshold
        """
        filtered = []
        
        for desire in candidates:
            # Check priority threshold
            if desire.priority < self.config.commitment_threshold:
                continue
            
            # TODO: Check for conflicts with existing intentions
            # For now, assume no conflicts
            
            # TODO: Check resource availability
            # For now, assume resources are available
            
            filtered.append(desire)
        
        return filtered
    
    def _apply_selection_policy(
        self,
        candidates: List[Desire],
        current_intentions: Dict[tuple, Intention]
    ) -> List[Desire]:
        """
        Apply selection policy to choose intentions from candidates.
        
        Uses configured policy: priority, utility, or constraint satisfaction.
        """
        policy = self.config.intention_selection_policy
        
        # Calculate available slots
        available_slots = (
            self.config.max_intention_set_size - len(current_intentions)
        )
        
        if available_slots <= 0:
            return []
        
        if policy == "priority":
            # Sort by priority descending, select top N
            sorted_candidates = sorted(
                candidates,
                key=lambda d: d.priority,
                reverse=True
            )
            return sorted_candidates[:available_slots]
        
        elif policy == "utility":
            # Sort by utility descending, select top N
            sorted_candidates = sorted(
                candidates,
                key=lambda d: d.utility,
                reverse=True
            )
            return sorted_candidates[:available_slots]
        
        elif policy == "constraint_sat":
            # TODO: Implement constraint satisfaction approach
            # For now, fall back to priority-based
            sorted_candidates = sorted(
                candidates,
                key=lambda d: d.priority,
                reverse=True
            )
            return sorted_candidates[:available_slots]
        
        else:
            # Unknown policy, return empty
            return []
    
    def _commit_to_desire(
        self,
        desire: Desire,
        timestep: int
    ) -> Optional[Intention]:
        """
        Commit to a desire, creating an intention.
        
        Args:
            desire: Desire to commit to
            timestep: Current timestep
            
        Returns:
            Intention if commitment succeeds, None if resource allocation fails
        """
        # Create intention from desire
        intention = Intention(
            goal_predicate=desire.goal_predicate,
            goal_arguments=desire.goal_arguments,
            commitment_level=1.0,  # Start with full commitment
            resources=[],  # Will be populated by resource allocation
            plan_id=None,  # No planning in this version
            timestamp=timestep
        )
        
        # Attempt resource allocation
        # For now, we don't explicitly allocate resources
        # (resource allocation would be domain-specific)
        
        return intention
    
    def _enforce_max_size(
        self,
        intentions: Dict[tuple, Intention]
    ) -> Dict[tuple, Intention]:
        """
        Enforce maximum intention set size by dropping lowest-commitment intentions.
        """
        if len(intentions) <= self.config.max_intention_set_size:
            return intentions
        
        # Sort by commitment level (descending)
        sorted_intentions = sorted(
            intentions.items(),
            key=lambda x: x[1].commitment_level,
            reverse=True
        )
        
        # Deallocate resources for dropped intentions
        for key, intention in sorted_intentions[self.config.max_intention_set_size:]:
            self.resource_manager.deallocate(key)
        
        return dict(sorted_intentions[:self.config.max_intention_set_size])
