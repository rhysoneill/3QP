# State Encoding Layer

**Phase 4 / Workstream 2 — Three-Question Protocol (3QP)**

## Purpose

The State Encoding Layer is the canonical bridge between qualitative semantic representations and computational processing in the 3QP architecture. It transforms semantic schemas, observations, and qualitative descriptors into structured encoded states that downstream Phase 4 components can consume.

This layer operates on a fundamental principle: **representation, not computation**.

## What This Layer Does

The State Encoding Layer performs three core functions:

1. **Encoding**: Transforms semantic schemas (from Workstream 1) into canonical encoded state representations
2. **Validation**: Ensures encoded states are structurally consistent and semantically aligned
3. **Mapping**: Bridges raw/unstructured observations to semantic schema objects

## What This Layer Does NOT Do

This layer strictly avoids all computational logic:

- ❌ No simulation or transition modeling
- ❌ No numeric scoring or probabilistic inference
- ❌ No pattern recognition or classification
- ❌ No heuristics or algorithmic decision-making
- ❌ No time-based logic or trajectory computation
- ❌ No NLP or machine learning

The State Encoding Layer is purely a **structuring and validation** layer.

## Architecture

### Core Components

```
state_encoding/
├── interfaces.py       # Abstract base classes and contracts
├── encoders.py        # Semantic schema → encoded state transformers
├── validators.py      # Consistency and alignment validators
└── mappers.py         # Observation → semantic schema bridges
```

### Component Responsibilities

#### `interfaces.py`

Defines the core abstractions used throughout the encoding layer:

- **`StateEncoder`**: Abstract base for all state encoders
- **`ObservationMapper`**: Abstract base for observation-to-schema mapping
- **`SchemaBinder`**: Abstract base for schema binding and provenance
- **`EncodingResult`**: Standard container for encoding operation results

All interfaces include comprehensive docstrings explaining their conceptual role in the 3QP architecture.

#### `encoders.py`

Implements concrete encoders that transform semantic schemas into encoded states:

- **`BaselineStateEncoder`**: Transforms baseline profiles → encoded baseline state
- **`ScenarioEventEncoder`**: Transforms scenario events → encoded event fragments
- **`PatternIndicatorEncoder`**: Transforms pattern indicators → encoded pattern hints
- **`ThreadIndicatorEncoder`**: Transforms thread indicators → encoded relational hints

Each encoder:
- Accepts semantic schema objects from Workstream 1
- Outputs canonical dictionaries representing encoded states
- Includes light validation (structure, not logic)
- Provides `.to_narrative()` for debugging and Phase 3 alignment

#### `validators.py`

Implements validators for consistency and alignment checking:

- **`EncodedStateValidator`**: Checks structural consistency within encoded states
- **`SchemaAlignmentValidator`**: Verifies alignment with semantic schemas
- **`DomainConsistencyValidator`**: Applies domain-specific consistency rules

Validators return structured `ValidationResult` objects with:
- Overall validity status
- Detailed issue lists (errors, warnings, info)
- Validated field tracking
- Human-readable summaries

#### `mappers.py`

Implements bridges from unstructured observations to semantic schemas:

- **`ObservationToSchemaMapper`**: Maps observations → `BaselineProfile` objects
- **`NarrativeToEventMapper`**: Maps event descriptions → `ScenarioEvent` objects
- **`QualitativeDescriptorMapper`**: Maps descriptors → pattern/thread indicators
- **`SemanticTagMapper`**: Helper for converting descriptors → semantic tags

Mappers perform **direct, rule-based translation only**. They do not perform:
- NLP or text analysis
- Inference or classification
- Pattern recognition
- Probabilistic decisions

## Connection to Broader 3QP Architecture

### Input: Semantic Schemas (Workstream 1)

The State Encoding Layer consumes semantic schemas defined in Workstream 1. These schemas represent the qualitative, domain-rich descriptions that preserve Phase 3's human-centered nature.

**Example semantic schema objects:**
- `BaselineProfile`: Captures baseline state across physiological, psychological, social, and environmental domains
- `ScenarioEvent`: Represents discrete events in scenario timelines
- `PatternIndicator`: Hints at potential patterns (not computed, just structured)
- `ThreadIndicator`: Hints at cross-module relationships

### Output: Encoded States

Encoded states are canonical dictionary representations that downstream components can consume:

```python
{
    "profile_id": "baseline_001",
    "domains": {
        "physiological": {"sleep_quality": "restless", "energy_level": "low"},
        "psychological": {"mood": "anxious", "stress_level": "moderate"},
        "social": {"social_support": "limited", "cohesion": "weak"},
        "environmental": {"workload": "high", "resources": "constrained"}
    },
    "encoding_metadata": {
        "encoder_version": "1.0.0",
        "encoder_type": "baseline",
        "original_metadata": {...}
    }
}
```

### Downstream Consumers (Future Workstreams)

Encoded states will be consumed by:

1. **Pattern Recognition Engine (Workstream 3)**: Identifies patterns in encoded state sequences
2. **Trajectory Classifier (Workstream 4)**: Classifies state trajectories
3. **Intervention Reasoning Kernel (Workstream 5)**: Reasons about interventions based on states
4. **Simulation Harness (Workstream 6)**: Runs simulations using encoded state representations

## Design Principles

### 1. Preserve Phase 3 Qualitative Integrity

All encoded states maintain traceability to their qualitative origins. Semantic tags, domain labels, and descriptors are preserved throughout encoding.

### 2. Strict Separation of Concerns

The encoding layer **only** structures and validates. It does not compute, infer, or decide. This separation ensures:
- Clean architectural boundaries
- Testability without computational dependencies
- Independent evolution of representation vs. computation

### 3. Schema Versioning and Alignment

All encoded states carry schema version metadata. Validators ensure alignment between:
- Encoder versions
- Semantic schema versions
- Domain vocabularies
- Qualitative tag sets

This enables schema evolution without breaking downstream components.

### 4. Validation as a First-Class Concern

Validation is not an afterthought — it's a core architectural feature. All encoders produce `EncodingResult` objects that can be validated before consumption.

Validation levels:
- **Structural**: Required fields, correct types, internal consistency
- **Semantic**: Alignment with schemas, valid tags, domain compliance
- **Domain**: Domain-specific consistency rules (e.g., no contradictory states)

## Usage Examples

### Example 1: Encoding a Baseline Profile

```python
from state_encoding.encoders import BaselineStateEncoder, BaselineProfile

# Create a baseline profile (from Workstream 1 semantic schema)
profile = BaselineProfile(
    profile_id="crew_member_001",
    physiological_state={"sleep_quality": "restless", "energy_level": "low"},
    psychological_state={"mood": "anxious", "stress_level": "moderate"},
    social_state={"social_support": "limited"},
    environmental_context={"workload": "high"}
)

# Encode it
encoder = BaselineStateEncoder(schema_version="1.0.0")
result = encoder.encode(profile)

# Check if encoding succeeded
if result.is_valid():
    encoded_state = result.encoded_state
    # Use encoded_state in downstream components
else:
    print(f"Encoding failed: {result.errors}")
```

### Example 2: Validating an Encoded State

```python
from state_encoding.validators import EncodedStateValidator, SchemaAlignmentValidator

# Validate structure
structure_validator = EncodedStateValidator(
    required_fields=["profile_id", "domains"]
)
structure_result = structure_validator.validate(encoded_state)

# Validate schema alignment
alignment_validator = SchemaAlignmentValidator(
    valid_domains={"physiological", "psychological", "social", "environmental"}
)
alignment_result = alignment_validator.validate(encoded_state, schema_version="1.0.0")

# Check results
if structure_result.is_valid and alignment_result.is_valid:
    print("State is valid and aligned")
else:
    print(structure_result.to_summary())
    print(alignment_result.to_summary())
```

### Example 3: Mapping an Observation to a Schema

```python
from state_encoding.mappers import ObservationToSchemaMapper

# Raw observation from assessment tool
observation = {
    "profile_id": "crew_002",
    "physiological": {"sleep_quality": "poor", "energy_level": "moderate"},
    "psychological": {"mood": "stable"}
}

# Map to semantic schema
mapper = ObservationToSchemaMapper()
profile = mapper.map(observation)

# Now encode it
encoder = BaselineStateEncoder()
result = encoder.encode(profile)
```

## Testing

The State Encoding Layer includes comprehensive tests:

```
tests/
├── test_interfaces.py    # Interface compliance, abstract method enforcement
├── test_encoders.py      # Encoder implementations, schema transformations
├── test_validators.py    # Validation logic, issue detection
└── test_mappers.py       # Observation mapping, semantic tag handling
```

### Running Tests

```bash
cd phase4/02_State_Encoding
python -m unittest discover tests
```

All tests use synthetic, structured inputs and do not depend on external libraries or Phase 1 modules.

## Integration Guidelines

### For Workstream 3 (Pattern Recognition Engine)

The Pattern Recognition Engine will consume encoded states from this layer:

```python
from state_encoding.encoders import BaselineStateEncoder

# Encode a sequence of baseline profiles
encoded_sequence = [encoder.encode(profile).encoded_state for profile in profiles]

# Pass to pattern recognition
# (Implementation in Workstream 3)
```

### For Workstream 4 (Trajectory Classifier)

The Trajectory Classifier will consume encoded event sequences:

```python
from state_encoding.encoders import ScenarioEventEncoder

# Encode event timeline
encoded_events = [encoder.encode(event).encoded_state for event in timeline]

# Pass to trajectory classifier
# (Implementation in Workstream 4)
```

### For Workstream 5 (Intervention Reasoning Kernel)

The Intervention Reasoning Kernel will use encoded states to reason about interventions:

```python
from state_encoding.encoders import BaselineStateEncoder

# Encode current state
current_state = encoder.encode(current_profile).encoded_state

# Reason about interventions based on encoded state
# (Implementation in Workstream 5)
```

## Future Extensions

While this workstream implements the core encoding infrastructure, future extensions may include:

1. **Additional Encoders**: Domain-specific encoders for specialized semantic schemas
2. **Advanced Validators**: More sophisticated domain consistency rules
3. **Schema Evolution Tools**: Utilities for migrating between schema versions
4. **Encoding Pipelines**: Composite encoders that chain multiple encoding steps
5. **Performance Optimizations**: Batch encoding for large state sequences

All extensions must preserve the core principle: **representation, not computation**.

## Philosophy

The State Encoding Layer embodies a critical architectural decision: **separate data structure from data processing**.

By maintaining this separation, we achieve:
- **Clarity**: Each layer has a single, well-defined responsibility
- **Testability**: Structure can be tested independently of computation
- **Evolvability**: Representation and computation can evolve independently
- **Integrity**: Phase 3's qualitative nature is preserved throughout Phase 4

This layer is the foundation upon which Phase 4's computational components are built — but it is not itself computational. It is a **representation layer**, pure and simple.

---

## License

Part of the Three-Question Protocol (3QP) — Phase 4 Architecture

## Contact

For questions or issues related to the State Encoding Layer, please refer to the main 3QP documentation or raise an issue in the project repository.
