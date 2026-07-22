"""
Action Effects - Phase B

Defines how agent actions influence interaction patterns without
directly modifying psychological state.

Actions shape inputs to the core dynamics (workload, recovery, novelty,
shared success) rather than bypassing the physics.

CRITICAL: This module does NOT modify strain, cohesion, or monotony directly.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from .actions import ActionType


@dataclass
class InteractionModifiers:
    """
    Modifiers to interaction-related inputs based on selected action.
    
    These modifiers influence the inputs to the core dynamics engine,
    not the state variables themselves.
    
    Attributes:
        workload_multiplier: Multiplier for workload input (default: 1.0)
        recovery_multiplier: Multiplier for recovery input (default: 1.0)
        success_probability_boost: Additive boost to success event probability (default: 0.0)
        novelty_probability_boost: Additive boost to novelty event probability (default: 0.0)
    """
    workload_multiplier: float = 1.0
    recovery_multiplier: float = 1.0
    success_probability_boost: float = 0.0
    novelty_probability_boost: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "workload_multiplier": self.workload_multiplier,
            "recovery_multiplier": self.recovery_multiplier,
            "success_probability_boost": self.success_probability_boost,
            "novelty_probability_boost": self.novelty_probability_boost,
        }


class ActionEffects:
    """
    Maps agent actions to effects on interaction patterns.
    
    This is the mechanism by which agent actions influence the system
    without bypassing the core physics. Actions modulate inputs, not states.
    
    Design principle: Actions are semantic intentions that translate into
    concrete changes in interaction frequency, workload distribution,
    recovery opportunities, etc.
    """
    
    def __init__(
        self,
        withdraw_workload_reduction: float = 0.85,
        withdraw_recovery_boost: float = 1.30,
        engage_workload_increase: float = 1.15,
        engage_novelty_boost: float = 0.15,
        support_success_boost: float = 0.20,
        support_workload_reduction: float = 0.95,
        escalate_workload_reduction: float = 0.90,
        escalate_recovery_boost: float = 1.20,
    ):
        """
        Initialize action effects with tunable parameters.
        
        Args:
            withdraw_workload_reduction: Workload multiplier for WITHDRAW (default: 0.85)
            withdraw_recovery_boost: Recovery multiplier for WITHDRAW (default: 1.30)
            engage_workload_increase: Workload multiplier for ENGAGE (default: 1.15)
            engage_novelty_boost: Novelty probability boost for ENGAGE (default: 0.15)
            support_success_boost: Success probability boost for SUPPORT (default: 0.20)
            support_workload_reduction: Workload multiplier for SUPPORT (default: 0.95)
            escalate_workload_reduction: Workload multiplier for ESCALATE (default: 0.90)
            escalate_recovery_boost: Recovery multiplier for ESCALATE (default: 1.20)
        """
        self.withdraw_workload_reduction = withdraw_workload_reduction
        self.withdraw_recovery_boost = withdraw_recovery_boost
        self.engage_workload_increase = engage_workload_increase
        self.engage_novelty_boost = engage_novelty_boost
        self.support_success_boost = support_success_boost
        self.support_workload_reduction = support_workload_reduction
        self.escalate_workload_reduction = escalate_workload_reduction
        self.escalate_recovery_boost = escalate_recovery_boost
    
    def get_modifiers(self, action_type: ActionType) -> InteractionModifiers:
        """
        Get interaction modifiers for a given action type.
        
        Args:
            action_type: The action selected by the agent
            
        Returns:
            InteractionModifiers specifying how to adjust inputs
        """
        if action_type == ActionType.WITHDRAW:
            return self._withdraw_modifiers()
        elif action_type == ActionType.ENGAGE:
            return self._engage_modifiers()
        elif action_type == ActionType.SUPPORT:
            return self._support_modifiers()
        elif action_type == ActionType.ESCALATE:
            return self._escalate_modifiers()
        else:  # MAINTAIN
            return self._maintain_modifiers()
    
    def _withdraw_modifiers(self) -> InteractionModifiers:
        """
        WITHDRAW: Reduce interaction frequency, increase recovery.
        
        Agent pulls back from activities to manage strain.
        Reduces workload exposure, increases recovery opportunities.
        """
        return InteractionModifiers(
            workload_multiplier=self.withdraw_workload_reduction,
            recovery_multiplier=self.withdraw_recovery_boost,
            success_probability_boost=0.0,
            novelty_probability_boost=0.0,
        )
    
    def _engage_modifiers(self) -> InteractionModifiers:
        """
        ENGAGE: Increase interaction frequency and novelty.
        
        Agent actively seeks new experiences to counter monotony.
        May increase workload slightly but brings novelty.
        """
        return InteractionModifiers(
            workload_multiplier=self.engage_workload_increase,
            recovery_multiplier=1.0,
            success_probability_boost=0.0,
            novelty_probability_boost=self.engage_novelty_boost,
        )
    
    def _support_modifiers(self) -> InteractionModifiers:
        """
        SUPPORT: Strengthen positive interactions and shared successes.
        
        Agent invests in social bonding and collaborative activities.
        Slight workload reduction as focus shifts to social maintenance.
        Increased probability of shared success events.
        """
        return InteractionModifiers(
            workload_multiplier=self.support_workload_reduction,
            recovery_multiplier=1.0,
            success_probability_boost=self.support_success_boost,
            novelty_probability_boost=0.0,
        )
    
    def _escalate_modifiers(self) -> InteractionModifiers:
        """
        ESCALATE: Raise visibility of issues, prioritize intervention.
        
        Agent signals distress and need for support.
        Workload reduced as issues take priority.
        Recovery opportunities increased through intervention.
        """
        return InteractionModifiers(
            workload_multiplier=self.escalate_workload_reduction,
            recovery_multiplier=self.escalate_recovery_boost,
            success_probability_boost=0.0,
            novelty_probability_boost=0.0,
        )
    
    def _maintain_modifiers(self) -> InteractionModifiers:
        """
        MAINTAIN: Continue current behavior pattern.
        
        No modifications to inputs.
        """
        return InteractionModifiers()
    
    def apply_modifiers(
        self,
        action_type: ActionType,
        workload: float,
        recovery: float,
    ) -> tuple[float, float]:
        """
        Apply action modifiers to workload and recovery inputs.
        
        Args:
            action_type: The action being applied
            workload: Base workload value
            recovery: Base recovery value
            
        Returns:
            Tuple of (modified_workload, modified_recovery)
        """
        modifiers = self.get_modifiers(action_type)
        
        modified_workload = workload * modifiers.workload_multiplier
        modified_recovery = recovery * modifiers.recovery_multiplier
        
        # Clamp to valid ranges
        modified_workload = max(0.0, min(1.0, modified_workload))
        modified_recovery = max(0.0, min(1.0, modified_recovery))
        
        return modified_workload, modified_recovery
