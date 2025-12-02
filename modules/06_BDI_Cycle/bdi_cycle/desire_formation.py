"""
Desire formation engine for the BDI Cognitive Cycle.

Implements goal generation, conflict resolution, and desire set management
according to the BDI specification.
"""

from typing import List, Dict, Set, Optional
from .types import Belief, Desire, ConstraintSpec, BDIConfig, DomainOntology


class GoalGenerationRule:
    """
    A rule for generating desires from belief patterns.
    
    Attributes:
        rule_id: Unique identifier for the rule
        trigger_pattern: Pattern of beliefs that activates this rule
        goal_predicate: Goal predicate to generate
        goal_arguments_template: Template for goal arguments (can reference belief values)
        priority_function: Function to compute priority from beliefs
        utility_function: Function to compute utility from beliefs
        constraints: Constraints for the generated desire
    """
    
    def __init__(
        self,
        rule_id: str,
        trigger_pattern: Dict,
        goal_predicate: str,
        goal_arguments_template: List,
        priority_function: callable,
        utility_function: callable,
        constraints: List[ConstraintSpec] = None
    ):
        self.rule_id = rule_id
        self.trigger_pattern = trigger_pattern
        self.goal_predicate = goal_predicate
        self.goal_arguments_template = goal_arguments_template
        self.priority_function = priority_function
        self.utility_function = utility_function
        self.constraints = constraints or []
    
    def matches(self, beliefs: Dict[tuple, Belief]) -> bool:
        """Check if trigger pattern matches current beliefs."""
        # TODO: Implement pattern matching logic
        # For now, return False (no rules trigger)
        return False
    
    def generate_desire(
        self,
        beliefs: Dict[tuple, Belief],
        timestep: int
    ) -> Optional[Desire]:
        """Generate a desire from matched beliefs."""
        if not self.matches(beliefs):
            return None
        
        # Instantiate goal arguments from template
        goal_args = self._instantiate_arguments(beliefs)
        
        # Compute priority and utility
        priority = self.priority_function(beliefs)
        utility = self.utility_function(beliefs)
        
        return Desire(
            goal_predicate=self.goal_predicate,
            goal_arguments=goal_args,
            priority=priority,
            utility=utility,
            constraints=self.constraints.copy(),
            timestamp=timestep
        )
    
    def _instantiate_arguments(self, beliefs: Dict[tuple, Belief]) -> List:
        """Instantiate goal arguments from template using belief values."""
        # TODO: Implement template instantiation
        # For now, return template as-is
        return self.goal_arguments_template.copy()


class DesireFormationEngine:
    """
    Manages desire set updates including goal generation, conflict resolution,
    and pruning.
    """
    
    def __init__(self, config: BDIConfig, ontology: DomainOntology):
        """
        Initialize desire formation engine.
        
        Args:
            config: BDI configuration parameters
            ontology: Domain ontology for validation
        """
        self.config = config
        self.ontology = ontology
        self.goal_rules: List[GoalGenerationRule] = []
    
    def form_desires(
        self,
        current_desires: Dict[tuple, Desire],
        beliefs: Dict[tuple, Belief],
        current_timestep: int
    ) -> tuple[Dict[tuple, Desire], Dict[str, int]]:
        """
        Execute desire formation phase.
        
        Args:
            current_desires: Current desire set (keyed by desire.key())
            beliefs: Current belief set
            current_timestep: Current simulation timestep
            
        Returns:
            Tuple of (updated desire set, statistics dict)
        """
        stats = {
            'added': 0,
            'removed': 0,
            'conflicts_resolved': 0
        }
        
        # Start with retained old desires
        updated_desires = current_desires.copy()
        
        # Phase 1: Generate candidate desires from goal rules
        candidate_desires: List[Desire] = []
        for rule in self.goal_rules:
            desire = rule.generate_desire(beliefs, current_timestep)
            if desire and self._validate_desire(desire):
                candidate_desires.append(desire)
        
        # Phase 2: Merge candidates with existing desires
        for desire in candidate_desires:
            key = desire.key()
            if key not in updated_desires:
                updated_desires[key] = desire
                stats['added'] += 1
            else:
                # Update existing desire if new one has higher priority
                existing = updated_desires[key]
                if desire.priority > existing.priority:
                    updated_desires[key] = desire
                    stats['added'] += 1  # Count as updated
        
        # Phase 3: Check constraint satisfiability
        before_check = len(updated_desires)
        updated_desires = self._check_satisfiability(updated_desires, beliefs)
        stats['removed'] += before_check - len(updated_desires)
        
        # Phase 4: Resolve conflicts
        before_resolve = len(updated_desires)
        updated_desires, conflicts = self._resolve_conflicts(updated_desires)
        stats['removed'] += before_resolve - len(updated_desires)
        stats['conflicts_resolved'] = conflicts
        
        # Phase 5: Prune low-priority desires
        before_prune = len(updated_desires)
        updated_desires = self._prune_low_priority(updated_desires)
        stats['removed'] += before_prune - len(updated_desires)
        
        # Phase 6: Prune old desires (outside retention window)
        before_prune = len(updated_desires)
        updated_desires = self._prune_old_desires(
            updated_desires,
            current_timestep
        )
        stats['removed'] += before_prune - len(updated_desires)
        
        # Phase 7: Enforce maximum set size
        if len(updated_desires) > self.config.max_desire_set_size:
            before_prune = len(updated_desires)
            updated_desires = self._enforce_max_size(updated_desires)
            stats['removed'] += before_prune - len(updated_desires)
        
        return updated_desires, stats
    
    def _validate_desire(self, desire: Desire) -> bool:
        """Validate a desire against the ontology."""
        # Check if goal predicate is registered
        if not self.ontology.is_valid_predicate(desire.goal_predicate):
            return False
        
        # Check if goal arguments match expected types
        if not self.ontology.validate_arguments(
            desire.goal_predicate,
            desire.goal_arguments
        ):
            return False
        
        return True
    
    def _check_satisfiability(
        self,
        desires: Dict[tuple, Desire],
        beliefs: Dict[tuple, Belief]
    ) -> Dict[tuple, Desire]:
        """
        Remove desires with unsatisfiable constraints.
        
        A desire is satisfiable if all its constraint predicates
        can potentially be satisfied given current beliefs.
        """
        satisfiable = {}
        for key, desire in desires.items():
            if self._is_satisfiable(desire, beliefs):
                satisfiable[key] = desire
        return satisfiable
    
    def _is_satisfiable(
        self,
        desire: Desire,
        beliefs: Dict[tuple, Belief]
    ) -> bool:
        """Check if a desire's constraints are satisfiable."""
        # Simple check: all constraint predicates must exist in beliefs
        # More sophisticated check would involve logical reasoning
        
        if not desire.constraints:
            return True  # No constraints = always satisfiable
        
        for constraint in desire.constraints:
            # Check if any belief matches this constraint predicate
            # This is a simplified check; real implementation would be more sophisticated
            constraint_key = (constraint.predicate, tuple(str(arg) for arg in constraint.arguments))
            if constraint_key not in beliefs:
                # Constraint not currently satisfied
                # For now, we allow desires with unsatisfied constraints
                # (they might become satisfiable later)
                pass
        
        return True
    
    def _resolve_conflicts(
        self,
        desires: Dict[tuple, Desire]
    ) -> tuple[Dict[tuple, Desire], int]:
        """
        Resolve conflicting desires.
        
        Uses priority-based resolution by default.
        
        Returns:
            Tuple of (conflict-free desire set, number of conflicts resolved)
        """
        # TODO: Implement sophisticated conflict detection
        # For now, assume no conflicts (all desires are compatible)
        # 
        # Conflict detection would involve:
        # 1. Identifying mutually exclusive constraints
        # 2. Detecting resource conflicts
        # 3. Finding logical inconsistencies
        
        conflicts_resolved = 0
        
        return desires, conflicts_resolved
    
    def _prune_low_priority(
        self,
        desires: Dict[tuple, Desire]
    ) -> Dict[tuple, Desire]:
        """Remove desires below minimum priority threshold."""
        return {
            key: desire
            for key, desire in desires.items()
            if desire.priority >= self.config.minimum_priority_threshold
        }
    
    def _prune_old_desires(
        self,
        desires: Dict[tuple, Desire],
        current_timestep: int
    ) -> Dict[tuple, Desire]:
        """Remove desires outside retention window."""
        retention_cutoff = current_timestep - self.config.desire_retention_window
        return {
            key: desire
            for key, desire in desires.items()
            if desire.timestamp >= retention_cutoff
        }
    
    def _enforce_max_size(
        self,
        desires: Dict[tuple, Desire]
    ) -> Dict[tuple, Desire]:
        """
        Enforce maximum desire set size by pruning lowest-priority desires.
        """
        if len(desires) <= self.config.max_desire_set_size:
            return desires
        
        # Sort by priority (descending) and keep highest-priority desires
        sorted_desires = sorted(
            desires.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        return dict(sorted_desires[:self.config.max_desire_set_size])
    
    def add_goal_rule(self, rule: GoalGenerationRule) -> None:
        """Add a goal generation rule."""
        self.goal_rules.append(rule)
