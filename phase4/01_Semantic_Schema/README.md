# Semantic Schema Layer

**Phase 4 / Workstream 1: Semantic Schema Layer**  
**3QP Repository**

## Overview

The Semantic Schema Layer provides typed data structures and interfaces for representing Phase 3 concepts within the Three Question Protocol (3QP) framework. This layer sits between the raw qualitative documentation from Phase 3 and future computational implementations, serving as a clean semantic representation of baseline states, scenarios, patterns, threads, and trajectories.

**Critical Design Principle**: This layer is **representation only**—it defines schemas without implementing simulation logic or business rules. It is purely declarative.

## Purpose

The semantic schema layer serves multiple functions:

### 1. **Bridge Between Qualitative and Computational**

Phase 3 documentation is rich, narrative, and qualitative. Future Phase 4 implementations will require structured data. The semantic schema layer translates qualitative concepts into typed data structures while preserving the semantic intent of the original documentation.

### 2. **Shared Vocabulary**

By defining explicit schemas, this layer creates a shared vocabulary for:
- Researchers analyzing mission dynamics
- Developers implementing simulation systems
- Mission planners designing scenarios
- Crew psychologists interpreting patterns

### 3. **Validation and Consistency**

Typed schemas ensure that relationships are consistent (e.g., a domain state's tags must match its domain) and that required fields are present. This catches errors early and makes implicit assumptions explicit.

### 4. **Separation of Concerns**

The semantic layer is isolated from:
- **Module implementations** in `modules/`—it references them but does not modify them
- **Simulation engines**—it represents states but does not compute state transitions
- **Phase 3 documentation**—it translates concepts without replacing the narrative source material

## What This Layer Contains

The semantic schema layer defines five core concept areas, each with its own module:

### `baseline.py` — Baseline State Schemas

Defines multi-domain baseline configurations representing the stable, equilibrium state from which scenarios begin.

**Key types**:
- `BaselineProfile`: Complete baseline configuration across all domains
- `DomainState`: State within a specific domain (physiological, cognitive, emotional, social, workload, operational)
- `SemanticTag`: Descriptive labels from Phase 3 Reference States (e.g., "well-rested", "cohesive", "low-strain")
- `ModuleReference`: Links to module-level configurations by reference

**Semantic tags** map directly to Phase 3 vocabulary:
- Physiological: "well-rested", "calm-and-balanced", "full-capacity"
- Cognitive: "clear-and-focused", "confident-and-decisive"
- Emotional: "stable-and-positive", "well-regulated"
- Social: "cohesive", "open-and-constructive", "high-trust"
- Workload: "moderate-and-balanced", "adequate-resources"
- Operational: "routine-operations", "low-background-pressure"

### `scenarios.py` — Scenario Schemas

Defines scenario templates and event descriptors for mission arcs.

**Key types**:
- `ScenarioTemplate`: Overall scenario structure (nominal, disruption, third-quarter)
- `EventDescriptor`: Individual events with qualitative characteristics
- `EventStoryline`: Ordered sequence of events forming a narrative arc

**Scenario types** from Phase 3:
- Nominal Mission: Stable, well-functioning mission arc
- Stressor-Driven Disruption: Escalating pressures challenging baseline
- Third-Quarter Phenomenon: Mid-mission drift and disengagement

Events are described semantically—category (operational, social, environmental, cognitive, emotional, physiological), intensity (minimal to critical), temporal character (transient, episodic, sustained, chronic)—without numeric values.

### `patterns.py` — Pattern Schemas

Defines pattern definitions (what patterns mean) and pattern instances (when they occur).

**Key types**:
- `PatternDefinition`: Qualitative framework for recognizing recurring configurations
- `PatternInstance`: Recognition of a pattern in a specific context
- `StateCharacteristic`: Description of state characteristics that define a pattern

**Pattern classes** from Phase 3:
- Stable: Equilibrium states maintaining coherence
- Drift: Gradual, imperceptible shifts from baseline
- Disruption: Acute destabilization
- Recovery: Restabilization following disruption or drift

Patterns describe **how states evolve** through narrative descriptors and recognition indicators, not mathematical formulas.

### `threads.py` — Thread Schemas

Defines narrative threads—emergent meaning structures describing how domains influence each other.

**Key types**:
- `ThreadDefinition`: Conceptual framework for domain relationships
- `ThreadInstance`: Recognition of a thread in a specific context
- `DomainInfluence`: Qualitative description of how one domain affects another

**Thread categories** from Phase 3:
- Domain Interaction: Pairwise domain influences (physiology → cognition)
- Mission Phase: Phase-specific cross-domain patterns
- Composite: Rich multi-domain narrative threads (strain-reactivity, meaning erosion)

**Influence types**: amplifying, constraining, transforming, triggering, modulating, mutual-reinforcement

Threads capture **interplay without modeling**—they describe tendencies, not mechanisms.

### `trajectories.py` — Trajectory Schemas

Defines trajectory archetypes (whole-mission narrative arcs) and trajectory instances.

**Key types**:
- `TrajectoryDefinition`: Major qualitative trajectory pattern
- `TrajectoryInstance`: Characterization of a specific mission's trajectory
- `DomainEvolution`: How a domain evolves across a trajectory

**Trajectory archetypes** from Phase 3:
- Stable Adaptation: Smooth, well-functioning mission
- Gradual Drift: Slow erosion across domains
- Disruption-Stabilization: Acute challenge followed by recovery or new equilibrium
- Third-Quarter: Mid-mission slump with temporal disengagement
- Cumulative Strain: Progressive wear without adequate recovery
- Meaning Erosion: Loss of connection to mission purpose
- Recovery-Renewal: Movement from constraint back to coherence
- Divergent Crew: Different crew members on different trajectories

Trajectories integrate baseline states, scenarios, patterns, and threads into **coherent whole-mission narratives**.

## How It Relates to Phase 3

The semantic schema layer **translates** Phase 3 concepts:

| Phase 3 Documentation | Semantic Schema |
|---|---|
| Baseline State Specification (prose) | `BaselineProfile` (typed data structure) |
| Reference States (qualitative vocabulary) | `SemanticTag` enums |
| Scenario Templates (narrative) | `ScenarioTemplate` with `EventStoryline` |
| Pattern Library (conceptual frameworks) | `PatternDefinition` with `StateCharacteristic` |
| Narrative Threads (meaning structures) | `ThreadDefinition` with `DomainInfluence` |
| Trajectory Archetypes (whole-mission arcs) | `TrajectoryDefinition` with `DomainEvolution` |

The schema layer **does not replace** Phase 3 documentation. Phase 3 remains the authoritative source of qualitative understanding. The schemas provide structured representations for computational work while preserving references back to the original documentation.

## How It Relates to Phase 4 Implementation

The semantic schema layer is the **foundation** for Phase 4 computational work:

### For Simulation Systems

When building simulation engines, these schemas define:
- **State representations**: What data structures represent crew states
- **Event structures**: How events are described and linked to state changes
- **Pattern recognition**: What qualitative signatures to detect
- **Trajectory classification**: How to categorize whole-mission arcs

### For Analysis Tools

Tools analyzing mission data can use these schemas to:
- **Tag states** with semantic labels
- **Identify patterns** by matching state characteristics
- **Recognize threads** by observing domain influences
- **Classify trajectories** by comparing to archetypes

### For Validation

Schemas support validation by:
- **Defining expectations**: What relationships should hold
- **Providing test cases**: Factory functions create canonical examples
- **Enabling consistency checks**: Type validation ensures correctness

## Design Principles

### 1. **No Simulation Logic**

This layer contains **zero** simulation logic. It does not:
- Compute state transitions
- Calculate probabilities
- Run time-based simulations
- Generate synthetic data (beyond test examples)

It only **represents** states, events, patterns, threads, and trajectories.

### 2. **Preserve Qualitative Intent**

Every schema includes:
- Narrative descriptions in natural language
- References to Phase 3 source documentation
- Qualitative descriptors (not quantified where Phase 3 is qualitative)
- Semantic tags mapping to Phase 3 vocabulary

### 3. **Explicit Over Implicit**

Relationships are explicit:
- A `DomainState` must reference its `Domain`
- A `PatternInstance` must reference its `PatternDefinition`
- A `ThreadDefinition` explicitly lists `DomainInfluence` relationships

This makes assumptions visible and validates consistency.

### 4. **Typed and Validated**

Python dataclasses with type hints ensure:
- Required fields are present
- Types are correct
- Enums constrain values to valid options
- Validation logic catches mismatches (e.g., tag domain ≠ state domain)

### 5. **Reference, Don't Modify**

When linking to modules (e.g., `slowfast_physiology`), schemas use `ModuleReference` objects that point to configurations **by reference**, never modifying them.

### 6. **Narrative Methods**

Every major type includes a `to_narrative()` method that generates human-readable descriptions. This supports:
- Understanding what a schema represents
- Generating reports for mission planners
- Debugging schema instances

## Usage Examples

### Creating a Baseline Profile

```python
from semantic_schema.baseline import create_nominal_baseline

# Create the canonical nominal baseline
baseline = create_nominal_baseline()

# Access domain states
phys_state = baseline.get_domain_state(Domain.PHYSIOLOGICAL)
print(phys_state.primary_tag.label)  # "well-rested"

# Generate narrative summary
summary = baseline.to_narrative_summary()
print(summary)
```

### Defining a Scenario

```python
from semantic_schema.scenarios import (
    create_disruption_scenario,
    EventDescriptor,
    EventCategory,
    EventIntensity,
    TemporalCharacter
)

# Create a disruption scenario
scenario = create_disruption_scenario()

# Add custom event to storyline
custom_event = EventDescriptor(
    event_id="custom_001",
    name="Communication Delay",
    description="Extended period without ground contact",
    category=EventCategory.ENVIRONMENTAL,
    intensity=EventIntensity.MODERATE,
    temporal_character=TemporalCharacter.SUSTAINED,
    affected_domains=["cognitive", "emotional", "social"]
)

scenario.storyline.add_event(custom_event)

# Generate narrative
narrative = scenario.to_narrative()
```

### Recognizing a Pattern

```python
from semantic_schema.patterns import (
    create_drift_pattern_example,
    PatternInstance
)

# Get pattern definition
sleep_drift_pattern = create_drift_pattern_example()

# Create an instance when pattern is recognized
instance = PatternInstance(
    instance_id="instance_001",
    pattern_definition_id=sleep_drift_pattern.pattern_id,
    pattern_name=sleep_drift_pattern.name,
    scenario_id="scenario_disruption_001",
    phase_descriptor="mid-mission",
    narrative_summary=(
        "Crew members report incrementally less restorative sleep "
        "beginning around mission day 60, with subtle accumulation "
        "of daytime fatigue."
    )
)

instance.add_observation("Sleep latency increasing")
instance.add_observation("More nighttime awakenings reported")
```

### Defining a Thread

```python
from semantic_schema.threads import create_strain_reactivity_thread

# Create the strain-reactivity composite thread
thread = create_strain_reactivity_thread()

# Examine domain influences
for influence in thread.domain_influences:
    print(f"{influence.source_domain} → {influence.target_domain}")
    print(f"  Type: {influence.influence_type.value}")
    print(f"  {influence.description}\n")
```

### Characterizing a Trajectory

```python
from semantic_schema.trajectories import (
    create_gradual_drift_trajectory,
    TrajectoryInstance
)

# Get trajectory definition
drift_traj = create_gradual_drift_trajectory()

# Characterize a specific mission
mission_traj = TrajectoryInstance(
    instance_id="traj_instance_001",
    trajectory_definition_id=drift_traj.trajectory_id,
    trajectory_name=drift_traj.name,
    mission_id="mission_alpha_001",
    scenario_id="scenario_third_quarter_001",
    baseline_id="baseline_nominal_001",
    narrative_summary=(
        "Mission Alpha exhibited classic gradual drift pattern with "
        "subtle erosion of sleep quality, cognitive sharpness, and "
        "emotional engagement beginning mid-mission."
    )
)

mission_traj.add_pattern_instance("pattern_drift_sleep_001")
mission_traj.add_thread_instance("thread_meaning_erosion_001")
```

## Testing

Comprehensive test suites validate all schemas:

- `tests/test_baseline_schema.py`: Baseline profiles and domain states
- `tests/test_scenarios_schema.py`: Scenarios and events
- `tests/test_patterns_schema.py`: Pattern definitions and instances
- `tests/test_threads_schema.py`: Thread definitions and instances
- `tests/test_trajectories_schema.py`: Trajectory definitions and instances

Tests ensure:
- Schemas can be instantiated with valid values
- Validation logic catches errors (mismatched domains, missing fields)
- Factory functions produce well-formed canonical examples
- Narrative methods generate readable output
- Relationships are consistent (e.g., thread instances reference valid patterns)

## Extensibility

The semantic schema layer is designed for extension:

### Adding Custom Semantic Tags

```python
from semantic_schema.baseline import SemanticTag, Domain

# Create custom tag
custom_tag = SemanticTag(
    domain=Domain.EMOTIONAL,
    label="creative-engagement",
    description="Crew member actively engaged in creative activities"
)
```

Custom tags are allowed and automatically marked as non-standard.

### Defining New Patterns

```python
from semantic_schema.patterns import (
    PatternDefinition,
    PatternClass,
    PatternScope,
    StateCharacteristic
)

# Define custom pattern
resilience_pattern = PatternDefinition(
    pattern_id="pattern_custom_001",
    name="Resilience Rebound Pattern",
    pattern_class=PatternClass.RECOVERY,
    pattern_scope=PatternScope.WHOLE_CREW,
    description="Crew demonstrates rapid recovery after disruption",
    narrative_description="..."
)
```

### Creating Custom Scenarios

```python
from semantic_schema.scenarios import ScenarioTemplate, ScenarioType

custom_scenario = ScenarioTemplate(
    template_id="scenario_custom_001",
    name="Hybrid Scenario",
    scenario_type=ScenarioType.CUSTOM,
    description="Combines elements of nominal and disruption scenarios",
    # ... additional fields
)
```

## Integration with Modules

The semantic schema layer **does not modify** existing modules in `modules/`. Instead:

1. **Module references** point to configurations:
   ```python
   ModuleReference(
       module_name="slowfast_physiology",
       config_id="baseline_config_001"
   )
   ```

2. **Domain states** describe qualitative conditions that **could** map to module states but do not prescribe how

3. **Future integration** will translate semantic schemas into module-specific configurations, but that is Phase 4 implementation work, not semantic layer responsibility

## Relationship to Phase 3 Workstreams

| Phase 3 Workstream | Semantic Schema Module |
|---|---|
| Workstream 1: Baseline State | `baseline.py` |
| Workstream 2: Scenarios | `scenarios.py` |
| Workstream 3: Reference Patterns | `patterns.py` |
| Workstream 4: Cross-Module Threads | `threads.py` |
| Workstream 5: Trajectory Analysis | `trajectories.py` |

The semantic schema layer provides structured representations of **all** Phase 3 concepts.

## Next Steps

With the semantic schema layer complete, Phase 4 can proceed to:

1. **Implement simulation engines** that use these schemas as state representations
2. **Build pattern recognition systems** that detect patterns by comparing to `PatternDefinition` characteristics
3. **Develop trajectory classification tools** that map mission data to `TrajectoryArchetype` categories
4. **Create visualization systems** that render semantic schemas in intuitive formats
5. **Design intervention support tools** that use threads to identify leverage points

The semantic layer serves as the **foundation** for all computational work while preserving the qualitative richness of Phase 3 understanding.

## Conclusion

The Semantic Schema Layer is a **clean, typed, purely representational** foundation for Phase 4 computational work. It translates Phase 3's qualitative understanding into structured data without introducing simulation logic, preserving semantic intent while enabling future implementation.

**Key Characteristics**:
- ✅ Representation only—no simulation logic
- ✅ Typed and validated—catches errors early
- ✅ Preserves Phase 3 intent—narrative descriptions and references throughout
- ✅ Extensible—custom tags, patterns, scenarios supported
- ✅ Well-tested—comprehensive test coverage
- ✅ Documented—narrative methods and Phase 3 references embedded

This layer ensures that computational implementations honor the depth and nuance of Phase 3's qualitative framework.
