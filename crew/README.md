# Crew Profile Layer

## Purpose

The crew profile layer provides a personality-based interface for configuring the Ruthless Core Model. Instead of directly tuning low-level model parameters, you can specify crew members with Big Five personality traits (OCEAN model), and the system will automatically map these to appropriate `RuthlessCoreConfig` parameters.

This layer is designed to be:
- **Transparent**: All mappings are documented and deterministic
- **Non-invasive**: Does not modify any core dynamics code
- **Interpretable**: Personality-to-parameter mappings align with psychological research
- **Practical**: Provides preset crew profiles for quick testing

## Components

### 1. `profile.py`
Defines the core data structures:
- `PersonalityScores`: Big Five traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- `CrewMember`: Individual crew member with name, role, and personality
- `CrewProfile`: Complete crew with aggregate personality calculation

### 2. `personality_to_config.py`
Maps personality traits to Ruthless Core Model parameters:

**Mapping Logic:**
- **Neuroticism** → Higher initial strain, stronger TQ response
- **Conscientiousness** → Better workload management, faster recovery
- **Agreeableness** → More resilient cohesion under stress and TQ pressure
- **Extraversion** → More sensitive to monotony, greater benefit from novelty
- **Openness** → Enhanced novelty effects, stronger shared success impact

All mappings use linear interpolation to keep parameters within reasonable ranges.

### 3. `examples.py`
Provides three preset crew profiles:
- **`high_cohesion_team`**: Stable, agreeable, conscientious → resilient dynamics
- **`fragile_team`**: Higher neuroticism, lower agreeableness → vulnerable cohesion
- **`extroverted_explorers`**: High openness and extraversion → novelty-seeking

Use `get_crew_preset(name)` to load a preset by name.

## Usage

### Basic Usage in Runtime

The crew layer integrates with the Phase 5 runtime harness via the `crew_preset` field in `RuntimeConfig`:

```python
from integration.runtime import RuntimeConfig, run_mission

# Run simulation with a crew preset
config = RuntimeConfig(
    mission_name="test_fragile_crew",
    mission_length_days=200,
    crew_preset="fragile_team"  # Uses personality mapping
)

result = run_mission(config)
```

### Creating Custom Crews

```python
from crew.profile import PersonalityScores, CrewMember, CrewProfile
from crew.personality_to_config import PersonalityToConfigMapper

# Define custom crew
my_crew = CrewProfile(
    crew_name="My Custom Crew",
    members=[
        CrewMember(
            name="Alice",
            role="Commander",
            personality=PersonalityScores(
                openness=0.7,
                conscientiousness=0.8,
                extraversion=0.6,
                agreeableness=0.7,
                neuroticism=0.3
            )
        ),
        # Add more members...
    ]
)

# Map to configuration
mapper = PersonalityToConfigMapper()
config = mapper.map_to_ruthless_config(my_crew, mission_length_days=180)

# config is now a RuthlessCoreConfig ready for simulation
```

## Design Philosophy

The crew layer is intentionally **lightweight and interpretable**. It does not add new dynamics or modify existing behavior - it simply provides a more intuitive interface for parameter selection based on well-established personality psychology.

This approach allows mission designers to:
1. Think in terms of crew composition rather than abstract parameters
2. Explore how different personality profiles might affect mission dynamics
3. Generate hypotheses about crew selection for long-duration missions
4. Maintain full transparency into how personality maps to model behavior

## Integration with 3QP System

The crew layer sits **on top** of the Phase 5 runtime harness and does not touch:
- Any of the 12 core modules
- The Ruthless Core Model engine
- The Phase 4 adapters
- Existing validation or logging systems

It is purely additive and can be bypassed entirely by not specifying a `crew_preset` in the runtime configuration.
