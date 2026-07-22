"""
Agentic Core Model - Phase B + Phase C

Wraps the Ruthless Core Model with the agent action/intent layer
and optional narrative rendering.

This module coordinates:
1. Reading state from core dynamics
2. Agent action selection via IntentPolicy
3. Applying action effects to inputs
4. Logging all agent behaviors
5. (Optional) Narrative rendering (Phase C)
6. Running core dynamics step-by-step

CRITICAL: This does NOT modify the core model. It wraps it.
"""

import sys
from pathlib import Path
from typing import Optional

# Import Ruthless Core Model
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase4" / "06_Ruthless_Core_Model"))
from ruthless_core import (
    RuthlessCoreConfig,
    RuthlessCoreOutput,
)

from .actions import AgentState
from .intent_policy import IntentPolicy
from .action_effects import ActionEffects
from .action_logger import ActionLogger
from .narrative_renderer import NarrativeRenderer
from .narrative_logger import NarrativeLogger


class AgenticCoreModel:
    """
    Agentic wrapper around RuthlessCoreModel.
    
    Runs the simulation step-by-step, inserting agent action selection
    and action effects at each timestep.
    
    The core dynamics remain unchanged - we only modulate the inputs
    (workload, recovery, etc.) based on agent actions.
    """
    
    def __init__(
        self,
        core_config: RuthlessCoreConfig,
        intent_policy: Optional[IntentPolicy] = None,
        action_effects: Optional[ActionEffects] = None,
        enable_actions: bool = True,
        agent_id: str = "crew",
        enable_narrative: bool = False,
        narrative_renderer: Optional[NarrativeRenderer] = None,
    ):
        """
        Initialize agentic core model.
        
        Args:
            core_config: Configuration for the underlying Ruthless Core Model
            intent_policy: Policy for action selection (uses default if None)
            action_effects: Action effects handler (uses default if None)
            enable_actions: If False, run without agentic layer (baseline mode)
            agent_id: Identifier for the agent (default: "crew" for single-agent mode)
            enable_narrative: If True, enable Phase C narrative rendering (default: False)
            narrative_renderer: Narrative renderer instance (uses default if None)
        """
        self.core_config = core_config
        self.intent_policy = intent_policy or IntentPolicy()
        self.action_effects = action_effects or ActionEffects()
        self.enable_actions = enable_actions
        self.agent_id = agent_id
        self.enable_narrative = enable_narrative
        self.narrative_renderer = narrative_renderer or NarrativeRenderer()
        
        self.T = core_config.mission_length_days
        self.action_logger = None
        self.narrative_logger = None
    
    def run(self, mission_name: str = "mission") -> tuple[RuthlessCoreOutput, Optional[ActionLogger], Optional[NarrativeLogger]]:
        """
        Run the agentic simulation.
        
        Executes the core model step-by-step with agent intervention at each step.
        
        Args:
            mission_name: Name of the mission (for logging)
            
        Returns:
            Tuple of (RuthlessCoreOutput, ActionLogger or None, NarrativeLogger or None)
        """
        # Initialize action logger if actions enabled
        if self.enable_actions:
            self.action_logger = ActionLogger(
                mission_name=mission_name,
                metadata={
                    "enable_actions": True,
                    "agent_id": self.agent_id,
                }
            )
        
        # Initialize narrative logger if narrative enabled
        if self.enable_narrative:
            self.narrative_logger = NarrativeLogger(
                mission_name=mission_name,
                metadata={
                    "enable_narrative": True,
                    "agent_id": self.agent_id,
                }
            )
        
        # Initialize state variables
        M = [0.0] * self.T  # Monotony
        S = [0.0] * self.T  # Strain
        C = [0.0] * self.T  # Cohesion
        Q = [0.0] * self.T  # TQ pressure
        days = list(range(self.T))
        
        # Set initial conditions
        M[0] = self.core_config.initial_monotony
        S[0] = self.core_config.initial_strain
        C[0] = self.core_config.initial_cohesion
        Q[0] = self._compute_tq_pressure(0)
        
        # Run simulation day by day
        for t in range(self.T - 1):
            # Agent action selection and effects
            if self.enable_actions:
                # Create agent state snapshot
                agent_state = AgentState(
                    agent_id=self.agent_id,
                    day=t,
                    strain=S[t],
                    cohesion=C[t],
                    monotony=M[t],
                    tq_pressure=Q[t],
                    mission_progress=t / self.T,
                )
                
                # Select action
                action = self.intent_policy.select_action(agent_state)
                
                # Log action
                self.action_logger.log_action(action)
                
                # Render narrative (Phase C - non-causal, read-only)
                if self.enable_narrative:
                    narrative = self.narrative_renderer.render(action, agent_state)
                    self.narrative_logger.log_narrative(narrative)
                
                # Get base inputs for this day
                base_workload = self.core_config.workload_schedule[t]
                base_recovery = self.core_config.recovery_schedule[t]
                
                # Apply action effects to inputs
                workload, recovery = self.action_effects.apply_modifiers(
                    action.action_type,
                    base_workload,
                    base_recovery
                )
            else:
                # No agentic intervention - use base inputs
                workload = self.core_config.workload_schedule[t]
                recovery = self.core_config.recovery_schedule[t]
            
            # Get event inputs
            novelty = self.core_config.novelty_events[t]
            success = self.core_config.success_events[t]
            
            # Update monotony (using core physics)
            M[t + 1] = M[t] + self.core_config.m_base - self.core_config.m_novelty * novelty
            M[t + 1] = max(0.0, M[t + 1])
            
            # Update strain (using core physics)
            strain_increase = (
                self.core_config.s_workload * workload +
                self.core_config.s_mono * M[t]
            )
            strain_decrease = self.core_config.s_recovery * recovery
            strain_leak = self.core_config.s_leak * S[t]
            S[t + 1] = S[t] + strain_increase - strain_decrease - strain_leak
            S[t + 1] = max(0.0, S[t + 1])
            
            # Compute TQ pressure
            Q[t + 1] = self._compute_tq_pressure(t + 1)
            
            # Update cohesion (using core physics)
            cohesion_decrease = (
                self.core_config.c_strain * S[t] +
                self.core_config.c_q * Q[t]
            )
            cohesion_increase = self.core_config.c_shared_success * success
            
            # Cohesion rebound after TQ peak passes
            r = (t + 1) / self.T
            if r > self.core_config.q_center:
                cohesion_rebound = self.core_config.c_rebound * (1.0 - C[t])
            else:
                cohesion_rebound = 0.0
            
            C[t + 1] = C[t] - cohesion_decrease + cohesion_increase + cohesion_rebound
            C[t + 1] = max(0.05, min(1.2, C[t + 1]))
        
        # Package output
        output = RuthlessCoreOutput(
            days=days,
            strain=S,
            cohesion=C,
            monotony=M,
            tq_pressure=Q,
            metadata={
                "version": "agentic_core_v0.1",
                "enable_actions": self.enable_actions,
                "enable_narrative": self.enable_narrative,
                "agent_id": self.agent_id,
            }
        )
        
        return output, self.action_logger, self.narrative_logger
    
    def _compute_tq_pressure(self, t: int) -> float:
        """
        Compute third quarter pressure at time t.
        
        Uses the same Gaussian function as RuthlessCoreModel.
        
        Args:
            t: Current day index
            
        Returns:
            Third quarter pressure value
        """
        r = t / self.T
        exponent = -((r - self.core_config.q_center) ** 2) / (2 * self.core_config.q_width ** 2)
        return self.core_config.q_peak * (2.718281828459045 ** exponent)  # e^x
