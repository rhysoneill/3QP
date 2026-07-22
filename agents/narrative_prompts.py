"""
Narrative Prompts - Phase C

Constrained prompt templates for LLM-based narrative generation.

These prompts enforce the non-causal, read-only constraints
of Phase C while enabling human-legible expression.

WARNING: Prompts are designed to PREVENT the LLM from:
- Selecting or modifying actions
- Updating state variables
- Introducing new motivations
- Making decisions

The LLM is strictly a RENDERING ENGINE.
"""

from typing import Dict, Any
from .actions import ActionType


class NarrativePrompts:
    """
    Prompt templates for narrative generation.
    
    Each prompt is carefully constrained to ensure LLM outputs
    remain non-causal and bounded.
    """
    
    @staticmethod
    def get_intent_expression_prompt(
        action: str,
        state_summary: Dict[str, Any],
    ) -> str:
        """
        Get prompt for expressing intent.
        
        Args:
            action: The action that was already selected
            state_summary: Qualitative state summary (NOT raw values)
            
        Returns:
            Constrained prompt for intent expression
        """
        return f"""You are translating a deterministically-selected action into natural language.

ACTION ALREADY SELECTED: {action}
This action was chosen by a rule-based policy. DO NOT suggest alternatives.

AGENT STATE (READ-ONLY):
{NarrativePrompts._format_state_summary(state_summary)}

YOUR TASK:
Express what this agent INTENDS to do, given the selected action and current state.

CONSTRAINTS:
- Maximum 2 sentences
- Reference state qualitatively ("feeling strained", "cohesion is low")
- DO NOT include state values (no numbers)
- DO NOT suggest different actions
- DO NOT explain why the action was chosen
- Focus on the forward-looking intent

OUTPUT FORMAT:
A single short paragraph expressing the intent.

Example: "needs space and reduced interaction to manage high psychological strain"

Now express the intent for action: {action}
"""
    
    @staticmethod
    def get_dialogue_prompt(
        action: str,
        state_summary: Dict[str, Any],
        expressed_intent: str,
        partner: str = "crewmate",
    ) -> str:
        """
        Get prompt for dialogue generation.
        
        Args:
            action: The selected action
            state_summary: Qualitative state summary
            expressed_intent: Already-generated intent expression
            partner: Who they're talking to
            
        Returns:
            Constrained prompt for dialogue
        """
        return f"""You are generating dialogue for an agent based on their state and selected action.

SELECTED ACTION: {action}
EXPRESSED INTENT: {expressed_intent}

AGENT STATE (READ-ONLY):
{NarrativePrompts._format_state_summary(state_summary)}

INTERACTION PARTNER: {partner}

YOUR TASK:
Generate ONE line of dialogue that:
- Reflects the selected action
- Matches the agent's current state
- Is directed at {partner}

CONSTRAINTS:
- Maximum 2 sentences
- First-person perspective ("I...")
- Conversational, natural tone
- NO technical jargon or state variable names
- NO exposition or explanation
- Just what the agent would SAY

OUTPUT FORMAT:
A single line of quoted dialogue.

Example: "I need to step back completely. I can't handle this right now."

Now generate dialogue for this action and state:
"""
    
    @staticmethod
    def get_narrative_summary_prompt(
        action: str,
        day: int,
        agent_id: str,
        state_summary: Dict[str, Any],
        mechanistic_conditions: list,
    ) -> str:
        """
        Get prompt for narrative summary generation.
        
        Args:
            action: Selected action
            day: Mission day
            agent_id: Agent identifier
            state_summary: Qualitative state summary
            mechanistic_conditions: List of threshold conditions
            
        Returns:
            Constrained prompt for narrative summary
        """
        return f"""You are generating a narrative summary of agent behavior.

AGENT: {agent_id}
DAY: {day}
ACTION TAKEN: {action}

AGENT STATE (READ-ONLY):
{NarrativePrompts._format_state_summary(state_summary)}

MECHANISTIC CONDITIONS (what triggered this action):
{NarrativePrompts._format_conditions(mechanistic_conditions)}

YOUR TASK:
Write a short narrative summary that describes what happened in story form.

CONSTRAINTS:
- Maximum 2 sentences
- Third-person perspective ("{agent_id} did...")
- Human-readable, journalistic style
- Reference mechanistic conditions implicitly (don't list them)
- NO state values (no numbers)
- NO predictions or speculation

OUTPUT FORMAT:
A short narrative paragraph.

Example: "{agent_id} withdrew from group activities on day {day}, unable to maintain social engagement under high psychological strain."

Now write the narrative summary:
"""
    
    @staticmethod
    def _format_state_summary(state_summary: Dict[str, Any]) -> str:
        """
        Format state summary for prompt inclusion.
        
        Args:
            state_summary: State summary dict
            
        Returns:
            Formatted string
        """
        lines = []
        for key, value in state_summary.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    @staticmethod
    def _format_conditions(conditions: list) -> str:
        """
        Format mechanistic conditions for prompt.
        
        Args:
            conditions: List of condition strings
            
        Returns:
            Formatted string
        """
        if not conditions:
            return "- baseline steady state"
        return "\n".join(f"- {cond}" for cond in conditions)


def create_state_summary(state: Any) -> Dict[str, str]:
    """
    Create qualitative state summary (no raw values).
    
    Converts quantitative state into qualitative descriptions
    suitable for LLM prompts.
    
    Args:
        state: AgentState instance
        
    Returns:
        Dictionary of qualitative descriptions
    """
    summary = {}
    
    # Strain qualitative descriptor
    if state.strain > 0.9:
        summary["psychological_strain"] = "critical"
    elif state.strain > 0.75:
        summary["psychological_strain"] = "high"
    elif state.strain > 0.5:
        summary["psychological_strain"] = "elevated"
    elif state.strain > 0.3:
        summary["psychological_strain"] = "moderate"
    else:
        summary["psychological_strain"] = "low"
    
    # Cohesion qualitative descriptor
    if state.cohesion < 0.25:
        summary["social_cohesion"] = "critical"
    elif state.cohesion < 0.4:
        summary["social_cohesion"] = "low"
    elif state.cohesion < 0.6:
        summary["social_cohesion"] = "moderate"
    elif state.cohesion < 0.75:
        summary["social_cohesion"] = "good"
    else:
        summary["social_cohesion"] = "strong"
    
    # Monotony qualitative descriptor
    if state.monotony > 0.7:
        summary["monotony"] = "very high"
    elif state.monotony > 0.6:
        summary["monotony"] = "high"
    elif state.monotony > 0.4:
        summary["monotony"] = "moderate"
    else:
        summary["monotony"] = "low"
    
    # TQ pressure qualitative descriptor
    if state.tq_pressure > 0.35:
        summary["third_quarter_pressure"] = "high"
    elif state.tq_pressure > 0.2:
        summary["third_quarter_pressure"] = "moderate"
    else:
        summary["third_quarter_pressure"] = "low"
    
    # Mission phase
    if state.mission_progress < 0.25:
        summary["mission_phase"] = "early (first quarter)"
    elif state.mission_progress < 0.5:
        summary["mission_phase"] = "second quarter"
    elif state.mission_progress < 0.75:
        summary["mission_phase"] = "third quarter"
    else:
        summary["mission_phase"] = "late (fourth quarter)"
    
    return summary


# Action-specific prompt refinements
ACTION_CONTEXT = {
    ActionType.WITHDRAW: {
        "intent_hint": "reducing interaction to preserve resources",
        "dialogue_hint": "expressing need for space",
    },
    ActionType.ENGAGE: {
        "intent_hint": "increasing social connection",
        "dialogue_hint": "initiating interaction or suggesting change",
    },
    ActionType.SUPPORT: {
        "intent_hint": "strengthening group bonds",
        "dialogue_hint": "offering help or encouragement",
    },
    ActionType.ESCALATE: {
        "intent_hint": "raising concerns to leadership",
        "dialogue_hint": "expressing serious concerns",
    },
    ActionType.MAINTAIN: {
        "intent_hint": "continuing current pattern",
        "dialogue_hint": "routine check-in",
    },
}
