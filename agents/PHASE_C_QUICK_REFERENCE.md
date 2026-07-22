# Phase C Quick Reference

## One-Line Summary

**Phase C adds human-legible narrative rendering to 3QP without affecting physics.**

---

## Enable Phase C

```python
from agents import AgenticCoreModel
from ruthless_core import RuthlessCoreConfig

config = RuthlessCoreConfig(mission_length_days=200)
model = AgenticCoreModel(
    core_config=config,
    enable_actions=True,      # Phase B
    enable_narrative=True,    # Phase C
)

output, action_log, narrative_log = model.run("mission_name")
```

---

## Access Narratives

```python
# Print summary
narrative_log.print_summary()

# Get recent narratives
recent = narrative_log.get_recent_narratives(n=10)
for n in recent:
    print(f"Day {n.day}: {n.narrative_summary}")

# Get critical moments
critical = narrative_log.log.get_critical_moments()

# Get all dialogue
dialogues = narrative_log.log.get_dialogue_exchanges()

# Save to JSON
from pathlib import Path
narrative_log.save(Path("output/narratives.json"))
```

---

## Output Schema

```json
{
  "agent_id": "crew",
  "day": 114,
  "action": "WITHDRAW",
  "expressed_intent": "...",
  "dialogue": "...",
  "narrative_summary": "...",
  "mechanistic_reference": ["strain_high", "..."]
}
```

---

## Key Constraints

1. **Read-Only**: Narrative never modifies state
2. **Non-Causal**: Narrative never affects physics
3. **Structured**: All outputs follow schema
4. **Auditable**: Every narrative has mechanistic reference

---

## Validation

```bash
python -m agents.demo_phase_c
```

Expected: `✅ VALIDATION PASSED - Narrative layer is confirmed non-causal`

---

## Components

| Component | Purpose |
|-----------|---------|
| `narrative_renderer.py` | LLM-based rendering engine |
| `narrative_logger.py` | Narrative output tracking |
| `narrative_prompts.py` | Constrained prompt templates |
| `demo_phase_c.py` | Demonstration & validation |

---

## DON'T

- ❌ Select actions in narrative layer
- ❌ Modify state variables
- ❌ Add randomness
- ❌ Create feedback loops
- ❌ Override intent policy

---

## DO

- ✅ Express selected intents in natural language
- ✅ Generate contextual dialogue
- ✅ Create narrative summaries
- ✅ Link narratives to mechanistic conditions
- ✅ Keep outputs structured

---

## Files Modified

- `agentic_core.py` - Added narrative integration
- `__init__.py` - Exported Phase C components

## Files Created

- `narrative_renderer.py` (416 lines)
- `narrative_logger.py` (192 lines)
- `narrative_prompts.py` (267 lines)
- `demo_phase_c.py` (271 lines)
- `PHASE_C_README.md`
- `PHASE_C_QUICK_REFERENCE.md`

**Total**: ~1,150 lines, minimal modifications to existing code.
