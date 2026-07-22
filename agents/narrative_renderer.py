"""
Narrative Renderer - Phase C

LLM-based rendering engine for human-legible expression of agent behavior.

CRITICAL CONSTRAINTS:
- Read-only access to state
- Non-causal outputs only
- All outputs must be structured
- No action selection or state modification
- Strictly downstream from decision logic

This is a RENDERING ENGINE, not a cognitive engine.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import json

from .actions import AgentState, AgentAction, ActionType
from .narrative_prompts import NarrativePrompts, create_state_summary


@dataclass
class NarrativeOutput:
    """
    Structured output from narrative rendering.
    
    Attributes:
        agent_id: Agent identifier
        day: Mission day
        action: Action that was selected (deterministically)
        expressed_intent: Natural language expression of the intent
        dialogue: Conversational expression (if applicable)
        narrative_summary: Short human-readable behavior summary
        mechanistic_reference: List of threshold/state conditions that triggered this
    """
    agent_id: str
    day: int
    action: str
    expressed_intent: str
    dialogue: Optional[str]
    narrative_summary: str
    mechanistic_reference: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "day": self.day,
            "action": self.action,
            "expressed_intent": self.expressed_intent,
            "dialogue": self.dialogue,
            "narrative_summary": self.narrative_summary,
            "mechanistic_reference": self.mechanistic_reference,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class NarrativeRenderer:
    """
    LLM-based rendering engine for agent behavior expression.
    
    Takes deterministically-selected actions and state snapshots as input,
    generates human-legible narrative output.
    
    DOES NOT:
    - Select actions
    - Modify state
    - Introduce randomness into decision logic
    - Override intent policy
    
    DOES:
    - Express selected intent in natural language
    - Generate contextual dialogue
    - Create narrative summaries
    - Link narratives to mechanistic explanations
    """
    
    def __init__(
        self,
        enable_dialogue: bool = True,
        enable_narrative: bool = True,
        llm_backend: Optional[Any] = None,
    ):
        """
        Initialize narrative renderer.
        
        Args:
            enable_dialogue: Generate dialogue (default: True)
            enable_narrative: Generate narrative summaries (default: True)
            llm_backend: LLM interface (None = use mock/rule-based)
        """
        self.enable_dialogue = enable_dialogue
        self.enable_narrative = enable_narrative
        self.llm_backend = llm_backend
    
    def render(
        self,
        action: AgentAction,
        state: AgentState,
        interaction_partner: Optional[str] = None,
    ) -> NarrativeOutput:
        """
        Render narrative expression for a selected action.
        
        This is the main entry point. Takes a deterministically-selected
        action and generates human-legible expression.
        
        Args:
            action: The action that was selected (READ-ONLY)
            state: The state snapshot (READ-ONLY)
            interaction_partner: Optional partner for dialogue generation
            
        Returns:
            NarrativeOutput with structured narrative elements
        """
        # Extract mechanistic conditions that explain this action
        mechanistic_ref = self._extract_mechanistic_reference(action, state)
        
        # Generate expressed intent
        expressed_intent = self._generate_expressed_intent(action, state)
        
        # Generate dialogue (if enabled and applicable)
        dialogue = None
        if self.enable_dialogue:
            dialogue = self._generate_dialogue(
                action, state, interaction_partner, expressed_intent
            )
        
        # Generate narrative summary (if enabled)
        narrative_summary = ""
        if self.enable_narrative:
            narrative_summary = self._generate_narrative_summary(
                action, state, mechanistic_ref
            )
        
        return NarrativeOutput(
            agent_id=action.agent_id,
            day=action.day,
            action=str(action.action_type),
            expressed_intent=expressed_intent,
            dialogue=dialogue,
            narrative_summary=narrative_summary,
            mechanistic_reference=mechanistic_ref,
        )
    
    def _extract_mechanistic_reference(
        self,
        action: AgentAction,
        state: AgentState,
    ) -> List[str]:
        """
        Extract mechanistic conditions that explain the action.
        
        Maps state values to threshold conditions that would trigger
        this action according to the intent policy.
        
        Args:
            action: Selected action
            state: State snapshot
            
        Returns:
            List of mechanistic condition strings
        """
        conditions = []
        
        # Strain conditions
        if state.strain > 0.9:
            conditions.append("strain_critical")
        elif state.strain > 0.75:
            conditions.append("strain_high")
        elif state.strain > 0.5:
            conditions.append("strain_elevated")
        
        # Cohesion conditions
        if state.cohesion < 0.25:
            conditions.append("cohesion_critical")
        elif state.cohesion < 0.4:
            conditions.append("cohesion_low")
        elif state.cohesion > 0.7:
            conditions.append("cohesion_strong")
        
        # TQ pressure conditions
        if state.tq_pressure > 0.35:
            conditions.append("tq_pressure_high")
        elif state.tq_pressure > 0.2:
            conditions.append("tq_pressure_moderate")
        
        # Monotony conditions
        if state.monotony > 0.6:
            conditions.append("monotony_high")
        elif state.monotony > 0.4:
            conditions.append("monotony_moderate")
        
        # Action-specific conditions
        action_type = action.action_type
        if action_type == ActionType.WITHDRAW:
            if state.strain + state.tq_pressure > 1.2:
                conditions.append("combined_stress_threshold_exceeded")
        elif action_type == ActionType.ESCALATE:
            if state.strain > 0.9 or state.cohesion < 0.25:
                conditions.append("critical_intervention_needed")
        elif action_type == ActionType.SUPPORT:
            if state.cohesion >= 0.5:
                conditions.append("cohesion_maintenance_viable")
        elif action_type == ActionType.ENGAGE:
            if state.monotony > 0.6:
                conditions.append("monotony_counter_needed")
        
        return conditions if conditions else ["baseline_steady_state"]
    
    def _generate_expressed_intent(
        self,
        action: AgentAction,
        state: AgentState,
    ) -> str:
        """
        Generate natural language expression of intent.
        
        Converts the selected action into a short human-readable
        expression of what the agent intends to do.
        
        Args:
            action: Selected action
            state: State snapshot
            
        Returns:
            Short intent expression (1-2 sentences max)
        """
        action_type = action.action_type

        # Use LLM if backend is available
        if self.llm_backend is not None:
            try:
                state_summary = create_state_summary(state)
                prompt = NarrativePrompts.get_intent_expression_prompt(
                    action=str(action_type),
                    state_summary=state_summary,
                )
                result = self.llm_backend.complete(prompt, max_tokens=80)
                if result:
                    return result
            except Exception:
                pass  # fall through to rule-based

        # Rule-based fallback
        # Simple rule-based expressions (can be replaced with LLM)
        # These are templates that reference state qualitatively
        
        if action_type == ActionType.WITHDRAW:
            if state.strain > 0.9:
                return "needs immediate space and reduced interaction to manage critical strain"
            elif state.strain > 0.75:
                return "seeking reduced interaction to recover from high psychological strain"
            else:
                return "reducing interaction frequency to preserve personal resources"
        
        elif action_type == ActionType.ENGAGE:
            if state.monotony > 0.7:
                return "actively seeking increased interaction to break monotony"
            else:
                return "increasing engagement to enhance social connection"
        
        elif action_type == ActionType.SUPPORT:
            if state.cohesion > 0.7:
                return "reinforcing strong group cohesion through positive interaction"
            else:
                return "working to strengthen group cohesion and mutual support"
        
        elif action_type == ActionType.ESCALATE:
            if state.strain > 0.9 and state.cohesion < 0.25:
                return "raising critical concerns about team wellbeing and cohesion"
            elif state.strain > 0.9:
                return "escalating strain concerns to leadership for intervention"
            else:
                return "increasing visibility of current challenges"
        
        else:  # MAINTAIN
            return "continuing current behavioral pattern"
    
    def _generate_dialogue(
        self,
        action: AgentAction,
        state: AgentState,
        interaction_partner: Optional[str],
        expressed_intent: str,
    ) -> Optional[str]:
        """
        Generate conversational dialogue for the action.
        
        Creates natural language dialogue that:
        - Reflects the selected action
        - Matches the agent's current state
        - Fits the interaction context
        
        Args:
            action: Selected action
            state: State snapshot
            interaction_partner: Who they're talking to (if applicable)
            expressed_intent: The intent expression
            
        Returns:
            Dialogue string or None if not applicable
        """
        action_type = action.action_type

        # Only generate dialogue for interactive actions
        if action_type == ActionType.MAINTAIN:
            return None

        # Use LLM if backend is available
        if self.llm_backend is not None:
            try:
                state_summary = create_state_summary(state)
                prompt = NarrativePrompts.get_dialogue_prompt(
                    action=str(action_type),
                    state_summary=state_summary,
                    expressed_intent=expressed_intent,
                    partner=interaction_partner or "crewmate",
                )
                result = self.llm_backend.complete(prompt, max_tokens=80)
                if result:
                    return result
            except Exception:
                pass  # fall through to rule-based

        # Rule-based fallback
        # Simple rule-based dialogue (can be replaced with LLM)
        # Dialogue reflects state qualitatively without revealing exact values
        
        if action_type == ActionType.WITHDRAW:
            if state.strain > 0.9:
                return "I need to step back completely. I can't handle this right now."
            elif state.strain > 0.75:
                return "I'm going to take some space. I need to focus on getting through this."
            else:
                return "I'm going to reduce my involvement for a bit. Need to recharge."
        
        elif action_type == ActionType.ENGAGE:
            if state.monotony > 0.7:
                return "We need to change things up. Let's try something different."
            else:
                return "I think we should connect more. How are you doing?"
        
        elif action_type == ActionType.SUPPORT:
            if state.cohesion > 0.7:
                return "We're doing well as a team. Let's keep supporting each other."
            else:
                return "I want to help. What can I do to support you?"
        
        elif action_type == ActionType.ESCALATE:
            if state.strain > 0.9 and state.cohesion < 0.25:
                return "We have a serious problem. We need external help immediately."
            elif state.strain > 0.9:
                return "This is beyond what I can handle alone. We need intervention."
            else:
                return "I think we need to raise this issue with leadership."
        
        return None
    
    def _generate_narrative_summary(
        self,
        action: AgentAction,
        state: AgentState,
        mechanistic_ref: List[str],
    ) -> str:
        """
        Generate short narrative summary of behavior.
        
        Creates a human-readable summary that describes what happened
        in story form, while being grounded in mechanistic conditions.
        
        Args:
            action: Selected action
            state: State snapshot
            mechanistic_ref: Mechanistic conditions
            
        Returns:
            Narrative summary (1-2 sentences)
        """
        action_type = action.action_type
        day = action.day
        agent = action.agent_id

        # Use LLM if backend is available
        if self.llm_backend is not None:
            try:
                state_summary = create_state_summary(state)
                prompt = NarrativePrompts.get_narrative_summary_prompt(
                    action=str(action_type),
                    day=day,
                    agent_id=agent,
                    state_summary=state_summary,
                    mechanistic_conditions=mechanistic_ref,
                )
                result = self.llm_backend.complete(prompt, max_tokens=100)
                if result:
                    return result
            except Exception:
                pass  # fall through to rule-based

        # Rule-based fallback
        # Generate narrative that implicitly references mechanistic conditions
        
        if action_type == ActionType.WITHDRAW:
            if "strain_critical" in mechanistic_ref:
                return f"{agent} withdrew completely on day {day}, unable to maintain social engagement under critical psychological strain."
            elif "combined_stress_threshold_exceeded" in mechanistic_ref:
                return f"{agent} reduced interaction significantly on day {day} as combined stress exceeded sustainable levels."
            else:
                return f"{agent} stepped back from group activities on day {day} to preserve personal resources."
        
        elif action_type == ActionType.ENGAGE:
            if "monotony_high" in mechanistic_ref:
                return f"{agent} actively sought increased engagement on day {day} to counter high monotony."
            else:
                return f"{agent} increased social interaction on day {day} to strengthen connections."
        
        elif action_type == ActionType.SUPPORT:
            if "cohesion_strong" in mechanistic_ref:
                return f"{agent} reinforced group cohesion on day {day} through supportive interaction."
            else:
                return f"{agent} worked to strengthen team bonds on day {day} despite challenges."
        
        elif action_type == ActionType.ESCALATE:
            if "critical_intervention_needed" in mechanistic_ref:
                return f"{agent} escalated critical concerns on day {day}, signaling need for immediate intervention."
            else:
                return f"{agent} raised visibility of challenges on day {day} to seek support."
        
        else:  # MAINTAIN
            return f"{agent} maintained steady behavioral pattern on day {day}."
    
    def batch_render(
        self,
        actions: List[AgentAction],
        states: List[AgentState],
    ) -> List[NarrativeOutput]:
        """
        Render narrative for multiple actions.
        
        Efficiently processes multiple actions in batch.
        
        Args:
            actions: List of actions
            states: Corresponding list of states
            
        Returns:
            List of narrative outputs
        """
        if len(actions) != len(states):
            raise ValueError("Actions and states lists must have same length")
        
        return [
            self.render(action, state)
            for action, state in zip(actions, states)
        ]
