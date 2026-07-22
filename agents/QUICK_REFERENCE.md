# Phase B Quick Reference

## Enable Agentic Mode

```python
from integration.runtime import run_mission, RuntimeConfig

config = RuntimeConfig(mission_name="test", mission_length_days=200)
result = run_mission(runtime_config=config, enable_agents=True)
```

## Action Types

| Action | When Selected | Effect |
|--------|--------------|--------|
| ESCALATE | Critical cohesion < 0.25 OR very high strain + low cohesion | 0.9× workload, 1.2× recovery |
| WITHDRAW | High strain ≥ 0.75 OR combined stress ≥ 1.2 | 0.85× workload, 1.3× recovery |
| SUPPORT | Good cohesion ≥ 0.5 + (strain ≥ 0.4 OR TQ ≥ 0.35) | 0.95× workload, +0.2 success probability |
| ENGAGE | High monotony ≥ 0.6 + strain < 0.75 | 1.15× workload, +0.15 novelty probability |
| MAINTAIN | Default | No modifications |

## Access Action Log

```python
if result.action_log:
    stats = result.action_log.get_statistics()
    print(stats['dominant_action'])
    print(stats['action_counts'])
    
    # Get pre-collapse actions
    pre = result.action_log.log.get_pre_collapse_actions(
        collapse_day=result.collapse_fingerprint.collapse_day,
        window_days=20
    )
```

## Customize Policy

```python
from agents import IntentPolicyConfig, IntentPolicy, AgenticCoreModel

policy_config = IntentPolicyConfig(
    high_strain_threshold=0.8,  # More tolerant
    low_cohesion_threshold=0.3   # Lower trigger
)

policy = IntentPolicy(config=policy_config)

model = AgenticCoreModel(
    core_config=core_config,
    intent_policy=policy
)
```

## Fingerprint Metadata

Action statistics automatically attached:

```python
result.collapse_fingerprint.metadata["action_summary"]
result.collapse_fingerprint.metadata["pre_collapse_actions"]
```

## Run Demo

```bash
python agents/demo_phase_b.py
```

## Key Principle

**Actions modulate inputs, not state**:
- ✅ Modify workload, recovery, novelty, success (inputs)
- ❌ Never directly modify strain, cohesion, monotony (state)
