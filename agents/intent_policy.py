"""
Intent Policy - Phase B

Deterministic rule-based mapping from agent state to actions.

This is the "brain" of the agent - a transparent, inspectable
decision policy that selects actions based on thresholds and
state conditions.

Requirements:
- Deterministic
- Explicit thresholds
- No randomness
- No LLM usage
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .actions import AgentState, AgentAction, ActionType


@dataclass
class IntentPolicyConfig:
    """
    Configuration for intent policy thresholds.
    
    All thresholds are tunable parameters that define the decision boundaries.
    
    Attributes:
        # Strain thresholds
        high_strain_threshold: Strain level triggering withdrawal (default: 0.75)
        very_high_strain_threshold: Strain level triggering escalation (default: 0.9)
        
        # Cohesion thresholds
        low_cohesion_threshold: Cohesion level indicating social fragility (default: 0.4)
        critical_cohesion_threshold: Cohesion level triggering escalation (default: 0.25)
        
        # TQ pressure thresholds
        high_tq_threshold: TQ pressure level indicating third quarter zone (default: 0.35)
        
        # Monotony thresholds
        high_monotony_threshold: Monotony level triggering engagement (default: 0.6)
        
        # Composite thresholds
        support_cohesion_threshold: Min cohesion for support actions (default: 0.5)
        withdraw_combined_threshold: Combined strain+TQ for withdrawal (default: 1.2)
    """
    high_strain_threshold: float = 0.75
    very_high_strain_threshold: float = 0.9
    low_cohesion_threshold: float = 0.4
    critical_cohesion_threshold: float = 0.25
    high_tq_threshold: float = 0.35
    high_monotony_threshold: float = 0.6
    support_cohesion_threshold: float = 0.5
    withdraw_combined_threshold: float = 1.2


class IntentPolicy:
    """
    Deterministic action selection policy.
    
    Maps agent state to actions using explicit threshold-based rules.
    Priority cascade ensures clear decision-making hierarchy.
    
    Decision priority (highest to lowest):
    1. ESCALATE - Critical conditions requiring attention
    2. WITHDRAW - Self-protective response to high stress
    3. SUPPORT - Proactive cohesion maintenance
    4. ENGAGE - Counter monotony and stagnation
    5. MAINTAIN - Default steady-state behavior
    """
    
    def __init__(self, config: Optional[IntentPolicyConfig] = None):
        """
        Initialize intent policy with configuration.
        
        Args:
            config: Policy configuration (uses defaults if None)
        """
        self.config = config or IntentPolicyConfig()
    
    def select_action(self, state: AgentState) -> AgentAction:
        """
        Select action based on current agent state.
        
        Uses a deterministic cascade of threshold checks to select
        the most appropriate action. All logic is transparent and traceable.
        
        Args:
            state: Current agent state
            
        Returns:
            AgentAction with selected action type and metadata
        """
        metadata = {}
        
        # Priority 1: ESCALATE - Critical conditions
        if self._should_escalate(state, metadata):
            action_type = ActionType.ESCALATE
        
        # Priority 2: WITHDRAW - High stress response
        elif self._should_withdraw(state, metadata):
            action_type = ActionType.WITHDRAW
        
        # Priority 3: SUPPORT - Proactive cohesion maintenance
        elif self._should_support(state, metadata):
            action_type = ActionType.SUPPORT
        
        # Priority 4: ENGAGE - Counter monotony
        elif self._should_engage(state, metadata):
            action_type = ActionType.ENGAGE
        
        # Priority 5: MAINTAIN - Default
        else:
            action_type = ActionType.MAINTAIN
            metadata["reason"] = "no threshold exceeded"
        
        return AgentAction(
            agent_id=state.agent_id,
            day=state.day,
            action_type=action_type,
            state_snapshot=state,
            metadata=metadata,
        )
    
    def _should_escalate(self, state: AgentState, metadata: Dict[str, Any]) -> bool:
        """
        Check if ESCALATE action should be selected.
        
        Conditions:
        - Very high strain (>= 0.9) AND low cohesion (< 0.4), OR
        - Critical cohesion (< 0.25)
        
        Args:
            state: Current state
            metadata: Dictionary to populate with decision rationale
            
        Returns:
            True if should escalate
        """
        very_high_strain = state.strain >= self.config.very_high_strain_threshold
        low_cohesion = state.cohesion < self.config.low_cohesion_threshold
        critical_cohesion = state.cohesion < self.config.critical_cohesion_threshold
        
        if critical_cohesion:
            metadata["reason"] = "critical_cohesion"
            metadata["cohesion"] = state.cohesion
            return True
        
        if very_high_strain and low_cohesion:
            metadata["reason"] = "very_high_strain_with_low_cohesion"
            metadata["strain"] = state.strain
            metadata["cohesion"] = state.cohesion
            return True
        
        return False
    
    def _should_withdraw(self, state: AgentState, metadata: Dict[str, Any]) -> bool:
        """
        Check if WITHDRAW action should be selected.
        
        Conditions:
        - High strain (>= 0.75), OR
        - Combined strain + TQ pressure exceeds threshold (>= 1.2)
        
        Args:
            state: Current state
            metadata: Dictionary to populate with decision rationale
            
        Returns:
            True if should withdraw
        """
        high_strain = state.strain >= self.config.high_strain_threshold
        combined_stress = state.strain + state.tq_pressure
        high_combined = combined_stress >= self.config.withdraw_combined_threshold
        
        if high_strain:
            metadata["reason"] = "high_strain"
            metadata["strain"] = state.strain
            return True
        
        if high_combined:
            metadata["reason"] = "high_combined_stress"
            metadata["strain"] = state.strain
            metadata["tq_pressure"] = state.tq_pressure
            metadata["combined"] = combined_stress
            return True
        
        return False
    
    def _should_support(self, state: AgentState, metadata: Dict[str, Any]) -> bool:
        """
        Check if SUPPORT action should be selected.
        
        Conditions:
        - Cohesion is moderate-to-good (>= 0.5) AND
        - Either strain is rising (>= 0.4) OR in third quarter (TQ >= 0.35)
        
        This represents proactive cohesion maintenance when conditions
        are still manageable.
        
        Args:
            state: Current state
            metadata: Dictionary to populate with decision rationale
            
        Returns:
            True if should support
        """
        good_cohesion = state.cohesion >= self.config.support_cohesion_threshold
        moderate_strain = state.strain >= 0.4
        in_tq = state.tq_pressure >= self.config.high_tq_threshold
        
        if good_cohesion and (moderate_strain or in_tq):
            if moderate_strain and in_tq:
                metadata["reason"] = "proactive_support_tq_and_strain"
            elif in_tq:
                metadata["reason"] = "proactive_support_tq"
            else:
                metadata["reason"] = "proactive_support_strain"
            
            metadata["cohesion"] = state.cohesion
            metadata["strain"] = state.strain
            metadata["tq_pressure"] = state.tq_pressure
            return True
        
        return False
    
    def _should_engage(self, state: AgentState, metadata: Dict[str, Any]) -> bool:
        """
        Check if ENGAGE action should be selected.
        
        Conditions:
        - High monotony (>= 0.6) AND
        - Low-to-moderate strain (< 0.75)
        
        This counters stagnation when psychological resources permit.
        
        Args:
            state: Current state
            metadata: Dictionary to populate with decision rationale
            
        Returns:
            True if should engage
        """
        high_monotony = state.monotony >= self.config.high_monotony_threshold
        strain_allows = state.strain < self.config.high_strain_threshold
        
        if high_monotony and strain_allows:
            metadata["reason"] = "counter_monotony"
            metadata["monotony"] = state.monotony
            metadata["strain"] = state.strain
            return True
        
        return False
