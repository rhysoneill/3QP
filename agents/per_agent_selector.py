"""
Per-Agent Action Selector — Phase 5

Personality-aware, per-astronaut action selection for the 3QP twin engine.

This module extends the existing IntentPolicy with:
  1. Per-agent personality-adjusted decision thresholds
  2. Translation of twin internal state (AstronautInternalState) into the
     AgentState representation expected by IntentPolicy
  3. cooperation_threshold gate: agents above their cooperation threshold
     are blocked from SUPPORT and ENGAGE actions
  4. Aggregation of per-agent actions into crew-level physics inputs for
     the RuthlessCoreModel day step

Design contract:
    Reads:  AstronautInternalState, AstronautBeliefState, CrewProfile
    Writes: AgentAction per agent, physics modifier tuple
    Never modifies any state layer — pure function over inputs
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Path setup — mirrors the pattern established by agentic_core.py
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from crew.profile import CrewProfile, PersonalityScores
from internal_state.astronaut_state import AstronautInternalState
from beliefs.belief_engine import AstronautBeliefState

from .actions import AgentState, AgentAction, ActionType
from .intent_policy import IntentPolicy, IntentPolicyConfig
from .action_effects import ActionEffects


# ---------------------------------------------------------------------------
# Cooperation gate threshold
# ---------------------------------------------------------------------------

COOPERATION_BLOCK_THRESHOLD = 0.70
"""
If an agent's cooperation_threshold >= this value, they are too stressed or
exhausted to cooperate. SUPPORT and ENGAGE actions are blocked:
    SUPPORT → MAINTAIN  (willing in principle, incapacitated in practice)
    ENGAGE  → WITHDRAW  (boredom + high stress compound into retreat)
"""


# ---------------------------------------------------------------------------
# Per-Agent Selector
# ---------------------------------------------------------------------------

class PerAgentSelector:
    """
    Personality-aware per-astronaut action selection.

    For each crew member, constructs a personalized IntentPolicy with thresholds
    shifted by their Big Five personality scores. On each day step, translates
    twin state (AstronautInternalState + AstronautBeliefState) into the
    AgentState that IntentPolicy expects, then applies the cooperation gate.

    Also provides aggregate_crew_inputs() to fold per-agent actions into the
    single (workload_modifier, recovery_modifier, novelty_boost, success_boost)
    tuple that TwinRunner injects into the RuthlessCoreModel day step.

    Args:
        crew:           Full crew profile (provides personality per agent)
        mission_length: Total mission days (for mission_progress calculation)
        action_effects: ActionEffects instance (uses defaults if None)
    """

    def __init__(
        self,
        crew: CrewProfile,
        mission_length: int = 365,
        action_effects: Optional[ActionEffects] = None,
    ):
        self._crew = crew
        self._mission_length = mission_length
        self._action_effects = action_effects or ActionEffects()

        # Build per-agent personality map and IntentPolicy instances
        self._personalities: Dict[str, PersonalityScores] = {}
        self._policies: Dict[str, IntentPolicy] = {}

        for member in crew.members:
            self._personalities[member.name] = member.personality
            config = self._build_personality_config(member.personality)
            self._policies[member.name] = IntentPolicy(config)

    # -------------------------------------------------------------------
    # Primary interface
    # -------------------------------------------------------------------

    def select_action(
        self,
        agent_id: str,
        internal_state: AstronautInternalState,
        belief_state: AstronautBeliefState,
        crew_states: Dict[str, AstronautInternalState],
        day: int,
    ) -> AgentAction:
        """
        Select action for one agent on one day.

        Process:
          1. Build synthetic AgentState from twin internal/belief state
          2. Delegate to personality-adjusted IntentPolicy
          3. Apply cooperation_threshold gate (blocks SUPPORT/ENGAGE if overloaded)

        Args:
            agent_id:       Agent identifier (must match crew member name)
            internal_state: This agent's AstronautInternalState
            belief_state:   This agent's AstronautBeliefState
            crew_states:    All agents' internal states (context; currently
                            unused in selection but passed for future use)
            day:            Current simulation day

        Returns:
            AgentAction for this agent on this day
        """
        synthetic = self._build_synthetic_agent_state(
            agent_id, internal_state, belief_state, day
        )

        # Use personality-adjusted policy if known, else fall back to default
        policy = self._policies.get(agent_id, IntentPolicy())
        action = policy.select_action(synthetic)

        return self._apply_cooperation_gate(action, internal_state)

    def aggregate_crew_inputs(
        self,
        actions: Dict[str, AgentAction],
        internal_states: Dict[str, AstronautInternalState],
    ) -> Tuple[float, float, float, float]:
        """
        Fold per-agent actions into crew-level physics modifier tuple.

        Returns:
            (workload_modifier, recovery_modifier, novelty_boost, success_boost)

            workload_modifier:  Mean workload multiplier across all agents
            recovery_modifier:  Mean recovery multiplier across all agents
            novelty_boost:      Fraction of ENGAGE agents × engage_novelty_boost
            success_boost:      Fraction of SUPPORT agents × support_success_boost

        TwinRunner applies these as:
            effective_workload = base_workload * workload_modifier
            effective_recovery = base_recovery * recovery_modifier
            effective_novelty  = clamp(base_novelty + novelty_boost * N)
            effective_success  = clamp(base_success + success_boost * N)
        """
        if not actions:
            return 1.0, 1.0, 0.0, 0.0

        n = len(actions)
        total_workload_mod = 0.0
        total_recovery_mod = 0.0
        engage_count = 0
        support_count = 0

        for action in actions.values():
            modifiers = self._action_effects.get_modifiers(action.action_type)
            total_workload_mod += modifiers.workload_multiplier
            total_recovery_mod += modifiers.recovery_multiplier
            if action.action_type == ActionType.ENGAGE:
                engage_count += 1
            if action.action_type == ActionType.SUPPORT:
                support_count += 1

        workload_modifier = total_workload_mod / n
        recovery_modifier = total_recovery_mod / n
        novelty_boost = (engage_count / n) * self._action_effects.engage_novelty_boost
        success_boost = (support_count / n) * self._action_effects.support_success_boost

        return workload_modifier, recovery_modifier, novelty_boost, success_boost

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _build_personality_config(
        self, personality: PersonalityScores
    ) -> IntentPolicyConfig:
        """
        Build an IntentPolicyConfig with thresholds shifted by personality.

        Shift logic — all deltas are linear in trait deviation from 0.5:

            neuroticism (n_dev = neuroticism - 0.5, range [-0.5, +0.5]):
                Reactive agents withdraw/escalate sooner.
                high_strain_threshold    -= 0.20 * n_dev
                very_high_strain_threshold -= 0.20 * n_dev
                withdraw_combined        -= 0.30 * n_dev
                → neuroticism=1.0: each threshold drops by 0.10
                → neuroticism=0.0: each threshold rises by 0.10

            agreeableness (a_dev = agreeableness - 0.5):
                Cooperative agents avoid escalation, offer support more easily.
                very_high_strain_threshold += 0.15 * a_dev
                critical_cohesion_threshold += 0.05 * a_dev
                support_cohesion_threshold  -= 0.10 * a_dev

            extraversion (e_dev = extraversion - 0.5):
                Social agents engage more readily to counter monotony.
                high_monotony_threshold -= 0.20 * e_dev

            conscientiousness (c_dev = conscientiousness - 0.5):
                Deliberate agents raise the bar before offering support.
                support_cohesion_threshold += 0.10 * c_dev
        """
        base = IntentPolicyConfig()

        n_dev = personality.neuroticism - 0.5
        a_dev = personality.agreeableness - 0.5
        e_dev = personality.extraversion - 0.5
        c_dev = personality.conscientiousness - 0.5

        high_strain = _clamp(
            base.high_strain_threshold - 0.20 * n_dev, 0.40, 0.95
        )
        very_high_strain = _clamp(
            base.very_high_strain_threshold - 0.20 * n_dev + 0.15 * a_dev, 0.55, 1.0
        )
        critical_cohesion = _clamp(
            base.critical_cohesion_threshold + 0.05 * a_dev, 0.10, 0.40
        )
        high_monotony = _clamp(
            base.high_monotony_threshold - 0.20 * e_dev, 0.35, 0.85
        )
        support_cohesion = _clamp(
            base.support_cohesion_threshold - 0.10 * a_dev + 0.10 * c_dev, 0.25, 0.70
        )
        withdraw_combined = _clamp(
            base.withdraw_combined_threshold - 0.30 * n_dev, 0.80, 1.60
        )

        return IntentPolicyConfig(
            high_strain_threshold=high_strain,
            very_high_strain_threshold=very_high_strain,
            low_cohesion_threshold=base.low_cohesion_threshold,
            critical_cohesion_threshold=critical_cohesion,
            high_tq_threshold=base.high_tq_threshold,
            high_monotony_threshold=high_monotony,
            support_cohesion_threshold=support_cohesion,
            withdraw_combined_threshold=withdraw_combined,
        )

    def _build_synthetic_agent_state(
        self,
        agent_id: str,
        internal_state: AstronautInternalState,
        belief_state: AstronautBeliefState,
        day: int,
    ) -> AgentState:
        """
        Translate twin internal state into AgentState for IntentPolicy.

        Variable mapping:
            strain           ← internal_state.stress
            cohesion         ← internal_state.trust_in_crew
            monotony         ← internal_state.boredom
            tq_pressure      ← (1.0 - internal_state.future_outlook) * 0.5
                               Scaled to 0–0.5 so that belief-derived TQ pressure
                               stays within the physiologically meaningful range
            mission_progress ← day / mission_length
        """
        tq_proxy = (1.0 - internal_state.future_outlook) * 0.5
        mission_progress = min(1.0, day / max(1, self._mission_length))

        return AgentState(
            agent_id=agent_id,
            day=day,
            strain=internal_state.stress,
            cohesion=internal_state.trust_in_crew,
            monotony=internal_state.boredom,
            tq_pressure=tq_proxy,
            mission_progress=mission_progress,
        )

    def _apply_cooperation_gate(
        self,
        action: AgentAction,
        internal_state: AstronautInternalState,
    ) -> AgentAction:
        """
        Block SUPPORT and ENGAGE when cooperation_threshold is exceeded.

        When an agent is too stressed/fatigued/frustrated to cooperate:
            SUPPORT → MAINTAIN  (willing but incapacitated)
            ENGAGE  → WITHDRAW  (boredom + stress compound into retreat)

        WITHDRAW, ESCALATE, and MAINTAIN pass through unmodified.
        """
        if internal_state.cooperation_threshold < COOPERATION_BLOCK_THRESHOLD:
            return action

        blocked = action.action_type

        if blocked == ActionType.SUPPORT:
            new_type = ActionType.MAINTAIN
            gate_reason = "cooperation_gate:SUPPORT->MAINTAIN"
        elif blocked == ActionType.ENGAGE:
            new_type = ActionType.WITHDRAW
            gate_reason = "cooperation_gate:ENGAGE->WITHDRAW"
        else:
            return action  # WITHDRAW / ESCALATE / MAINTAIN pass through

        metadata = dict(action.metadata or {})
        metadata["cooperation_gate_fired"] = True
        metadata["original_action"] = blocked.value
        metadata["gate_reason"] = gate_reason
        metadata["cooperation_threshold"] = round(internal_state.cooperation_threshold, 4)

        return AgentAction(
            agent_id=action.agent_id,
            day=action.day,
            action_type=new_type,
            state_snapshot=action.state_snapshot,
            metadata=metadata,
        )

    # -------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------

    def get_policy_config(self, agent_id: str) -> Optional[IntentPolicyConfig]:
        """Return the personality-adjusted IntentPolicyConfig for an agent, or None."""
        policy = self._policies.get(agent_id)
        return policy.config if policy else None

    def get_crew_personalities(self) -> Dict[str, PersonalityScores]:
        """Return a copy of per-agent personality scores."""
        return dict(self._personalities)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))
