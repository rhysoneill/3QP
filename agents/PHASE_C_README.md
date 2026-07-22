# Phase C: Narrative Rendering Layer

**Status**: ✅ Complete  
**Date**: December 16, 2025

---

## Overview

Phase C adds **human-legible social texture** to the 3QP system without contaminating causality.

This is a **rendering engine**, not a cognitive engine. The LLM is used strictly for expression, not decision-making.

---

## Design Philosophy

### Core Constraints

1. **Read-Only**: All inputs are snapshots, never modified
2. **Non-Causal**: Outputs do not affect state or actions
3. **Structured**: All outputs follow strict schemas
4. **Auditable**: Narrative paired with mechanistic explanations
5. **Downstream**: Operates after action selection, never before

### What Phase C Does

- Express selected intents in natural language
- Generate contextual dialogue for actions
- Create narrative summaries of behavior
- Link narratives to mechanistic conditions

### What Phase C Does NOT Do

- ❌ Select or modify actions
- ❌ Update psychological state
- ❌ Introduce new motivations
- ❌ Make decisions
- ❌ Add randomness to physics
- ❌ Override intent policy

---

## Architecture

```
Phase B (Deterministic)          Phase C (Non-Causal)
─────────────────────           ─────────────────────
                                
State (S, C, M, Q)              State Snapshot
       ↓                               ↓
Intent Policy    ────────────→  Narrative Renderer
       ↓                               ↓
Selected Action  ────────────→  Narrative Output
       ↓                        {
Action Effects                    expressed_intent,
       ↓                          dialogue,
Physics Update                    narrative_summary,
       ↓                          mechanistic_reference
Next State                       }
       ↓                               ↓
Action Logger                   Narrative Logger


CAUSAL PATH: State → Action → Physics
NON-CAUSAL: State → Narrative (observation only)
```

---

## Components

### 1. Narrative Renderer (`narrative_renderer.py`)

LLM-based rendering engine for human-legible expression.

**Key Method**: `render(action, state) -> NarrativeOutput`

Takes a deterministically-selected action and generates:
- **Expressed Intent**: Natural language intent (1-2 sentences)
- **Dialogue**: Conversational expression (if applicable)
- **Narrative Summary**: Story-form behavior description
- **Mechanistic Reference**: Threshold conditions that explain the action

**Current Implementation**: Rule-based templates (LLM-ready)

The renderer is designed to accept an LLM backend but currently uses rule-based templates that reference state qualitatively:
- "feeling strained" (not S=0.85)
- "cohesion is low" (not C=0.32)
- "third quarter pressure" (not Q=0.41)

### 2. Narrative Logger (`narrative_logger.py`)

Tracking system for narrative outputs, separate from action logs.

**Capabilities**:
- Log all narrative outputs with full context
- Group by day, action type, or criticality
- Extract critical moments (strain_critical, cohesion_critical, etc.)
- Get dialogue exchanges
- Compute summary statistics
- Serialize to JSON

### 3. Narrative Prompts (`narrative_prompts.py`)

Constrained prompt templates for LLM integration.

**Design**: Prompts are structured to **prevent** the LLM from:
- Selecting actions
- Modifying state
- Introducing new motivations
- Making decisions

**Key Function**: `create_state_summary(state) -> Dict[str, str]`

Converts quantitative state to qualitative descriptions:
- `strain=0.85` → `psychological_strain: "high"`
- `cohesion=0.32` → `social_cohesion: "low"`
- `monotony=0.67` → `monotony: "high"`

This ensures LLM prompts never expose raw state values.

### 4. Integration (`agentic_core.py`)

Phase C integrates seamlessly with Phase B:

```python
# Enable narrative rendering
model = AgenticCoreModel(
    core_config=config,
    enable_actions=True,      # Phase B
    enable_narrative=True,    # Phase C
)

output, action_log, narrative_log = model.run("mission_name")
```

**Execution Flow**:
1. Select action (Phase B - deterministic)
2. Log action
3. **[Phase C]** Render narrative (read-only)
4. **[Phase C]** Log narrative
5. Apply action effects
6. Update physics

Narrative rendering happens **after** action selection but **before** physics update, ensuring complete read-only access.

---

## Output Structure

All narrative outputs follow this schema:

```json
{
  "agent_id": "crew",
  "day": 114,
  "action": "WITHDRAW",
  "expressed_intent": "seeking reduced interaction to recover from high psychological strain",
  "dialogue": "I'm going to take some space. I need to focus on getting through this.",
  "narrative_summary": "crew reduced interaction significantly on day 114 as combined stress exceeded sustainable levels.",
  "mechanistic_reference": [
    "strain_high",
    "tq_pressure_moderate",
    "combined_stress_threshold_exceeded"
  ]
}
```

### Field Descriptions

- **expressed_intent**: What the agent plans to do (forward-looking)
- **dialogue**: What the agent says (conversational)
- **narrative_summary**: What happened (retrospective, story-form)
- **mechanistic_reference**: Why it happened (causal conditions)

Every narrative has a **mechanistic twin**, maintaining auditability.

---

## Usage Examples

### Basic Usage

```python
from agents import AgenticCoreModel, NarrativeRenderer
from ruthless_core import RuthlessCoreConfig

config = RuthlessCoreConfig(mission_length_days=200)

# Create model with narrative enabled
model = AgenticCoreModel(
    core_config=config,
    enable_actions=True,
    enable_narrative=True,
)

# Run simulation
output, action_log, narrative_log = model.run("my_mission")

# Access narratives
if narrative_log:
    narrative_log.print_summary()
    
    # Get critical moments
    critical = narrative_log.log.get_critical_moments()
    for narrative in critical:
        print(f"Day {narrative.day}: {narrative.narrative_summary}")
        print(f"  Dialogue: \"{narrative.dialogue}\"")
    
    # Save to JSON
    narrative_log.save(Path("output/narratives.json"))
```

### Custom Narrative Renderer

```python
from agents import NarrativeRenderer, AgenticCoreModel

# Create custom renderer (e.g., with LLM backend)
renderer = NarrativeRenderer(
    enable_dialogue=True,
    enable_narrative=True,
    llm_backend=None,  # Placeholder for LLM integration
)

model = AgenticCoreModel(
    core_config=config,
    enable_actions=True,
    enable_narrative=True,
    narrative_renderer=renderer,
)
```

### Standalone Rendering

```python
from agents import NarrativeRenderer, AgentState, AgentAction, ActionType

renderer = NarrativeRenderer()

# Create state snapshot (read-only)
state = AgentState(
    agent_id="crew",
    day=114,
    strain=0.85,
    cohesion=0.32,
    monotony=0.67,
    tq_pressure=0.38,
    mission_progress=0.57,
)

# Create action (already selected)
action = AgentAction(
    agent_id="crew",
    day=114,
    action_type=ActionType.WITHDRAW,
    state_snapshot=state,
)

# Render narrative
narrative = renderer.render(action, state)

print(narrative.expressed_intent)
print(narrative.dialogue)
print(narrative.narrative_summary)
print(narrative.mechanistic_reference)
```

---

## Validation

Phase C includes validation to ensure non-causal property:

```bash
python agents/demo_phase_c.py
```

**Validation Test**:
1. Runs identical mission twice
2. Once with `enable_narrative=False`
3. Once with `enable_narrative=True`
4. Compares trajectories element-by-element

**Expected Result**: Trajectories are identical (within numerical precision).

If narratives affected physics, trajectories would diverge.

---

## LLM Integration (Future)

The system is designed for LLM integration but currently uses rule-based templates.

**To Add LLM Backend**:

1. Implement LLM interface:
```python
class LLMBackend:
    def generate(self, prompt: str) -> str:
        # Call LLM API
        pass
```

2. Update `NarrativeRenderer`:
```python
def _generate_expressed_intent(self, action, state):
    if self.llm_backend:
        prompt = NarrativePrompts.get_intent_expression_prompt(
            action=str(action.action_type),
            state_summary=create_state_summary(state)
        )
        return self.llm_backend.generate(prompt)
    else:
        # Fall back to rule-based
        return self._rule_based_intent(action, state)
```

3. Use constrained prompts from `narrative_prompts.py`

**Critical**: Prompts are designed to prevent the LLM from contaminating causality.

---

## File Reference

### New Files

- [`narrative_renderer.py`](narrative_renderer.py) - Core rendering engine (416 lines)
- [`narrative_logger.py`](narrative_logger.py) - Narrative logging (192 lines)
- [`narrative_prompts.py`](narrative_prompts.py) - Constrained prompts (267 lines)
- [`demo_phase_c.py`](demo_phase_c.py) - Demonstration and validation (271 lines)
- `PHASE_C_README.md` - This documentation

### Modified Files

- [`agentic_core.py`](agentic_core.py) - Added narrative integration
- [`__init__.py`](__init__.py) - Exported Phase C components

**Total Impact**: ~1,150 lines of new code, minimal modifications to Phase B.

---

## Testing

Run the demonstration:

```bash
cd c:/Users/rhysoneill/3QP
python -m agents.demo_phase_c
```

**Expected Output**:
1. Baseline mode (no agents, no narrative)
2. Agentic mode (Phase B only)
3. Full mode (Phase B + Phase C)
4. Non-causal validation (✅ PASSED)

---

## Design Decisions

### Why Separate Loggers?

Action logs are **causal** (part of the physics chain).  
Narrative logs are **non-causal** (observation only).

Keeping them separate makes the distinction explicit and prevents accidental contamination.

### Why Mechanistic Reference?

Every narrative includes the threshold conditions that triggered the action:
- `strain_high`
- `cohesion_low`
- `combined_stress_threshold_exceeded`

This ensures narratives are **grounded in physics**, not invented.

### Why No LLM Yet?

The current implementation uses rule-based templates to:
1. Demonstrate the architecture works
2. Provide deterministic baseline
3. Enable validation without API dependencies

LLM integration is straightforward - the prompts and interfaces are ready.

### Why Qualitative State Summaries?

Raw state values (`S=0.8532`) are:
- Not human-legible
- Create prompt variability
- Leak implementation details

Qualitative summaries (`psychological_strain: "high"`) are:
- Human-interpretable
- Stable across small variations
- Abstract implementation

---

## Success Criteria

Phase C succeeds if:

- ✅ System produces human-readable behavior
- ✅ Every narrative has a causal twin (mechanistic reference)
- ✅ Fingerprints remain unchanged
- ✅ System is still fully auditable
- ✅ Social realism increases without loss of control
- ✅ Non-causal property validated

**Status**: All criteria met.

---

## Future Extensions

### Optional Enhancements

1. **LLM Backend Integration**
   - OpenAI, Anthropic, or local models
   - Use `narrative_prompts.py` templates
   - Add temperature control for expression variety

2. **Multi-Agent Dialogue**
   - Agent-to-agent conversations
   - Dialogue threading over multiple days
   - Interaction partner tracking

3. **Temporal Narrative Arcs**
   - Multi-day story construction
   - Pattern detection in narratives
   - Automatic episode identification

4. **Narrative-to-Fingerprint Attachment**
   - Include narrative summaries in collapse fingerprints
   - Enable narrative-based fingerprint comparison
   - "Find missions where agents escalated concerns"

---

## Constraints Checklist

Before modifying Phase C, verify:

- [ ] No writes to state variables (S, C, M, Q)
- [ ] No action selection or override
- [ ] No randomness introduced
- [ ] All outputs are structured (no free-form strings)
- [ ] Mechanistic reference always included
- [ ] No feedback loops (narrative → state)

**Violation of these constraints = Phase C failure**

---

## Contact

For questions about Phase C implementation, see:
- Source code documentation in `narrative_renderer.py`
- Demonstration in `demo_phase_c.py`
- Prompt templates in `narrative_prompts.py`

---

**Phase C is complete and validated.**  
**The system now produces human-legible behavior while maintaining full causal control.**
