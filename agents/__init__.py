"""
Phase B & C: Agent Action, Intent, and Narrative Layer

This module provides:
- Phase B: Minimal agentic behavior without modifying core physics
- Phase C: Human-legible narrative rendering (non-causal)

Components:
- actions: Action types and state container
- intent_policy: Deterministic state-to-action mapping
- action_effects: How actions influence interactions (not psychology)
- action_logger: Logging and tracking of agent behaviors
- agentic_core: Wrapper integrating agents with RuthlessCoreModel
- narrative_renderer: LLM-based expression engine (Phase C)
- narrative_logger: Narrative output tracking (Phase C)
- narrative_prompts: Constrained prompt templates (Phase C)
- llm_backend: OpenAI backend for LLM narrative calls (Phase C)
"""

from .actions import AgentAction, AgentState, ActionType
from .intent_policy import IntentPolicy, IntentPolicyConfig
from .action_effects import ActionEffects, InteractionModifiers
from .action_logger import ActionLogger, ActionLog
from .agentic_core import AgenticCoreModel
from .narrative_renderer import NarrativeRenderer, NarrativeOutput
from .narrative_logger import NarrativeLogger, NarrativeLog
from .narrative_prompts import NarrativePrompts, create_state_summary
from .llm_backend import OpenAIBackend
from .per_agent_selector import PerAgentSelector, COOPERATION_BLOCK_THRESHOLD

__all__ = [
    # Phase B
    "AgentAction",
    "AgentState",
    "ActionType",
    "IntentPolicy",
    "IntentPolicyConfig",
    "ActionEffects",
    "InteractionModifiers",
    "ActionLogger",
    "ActionLog",
    "AgenticCoreModel",
    # Phase C
    "NarrativeRenderer",
    "NarrativeOutput",
    "NarrativeLogger",
    "NarrativeLog",
    "NarrativePrompts",
    "create_state_summary",
    "OpenAIBackend",
    # Phase 5 (twin engine)
    "PerAgentSelector",
    "COOPERATION_BLOCK_THRESHOLD",
]
