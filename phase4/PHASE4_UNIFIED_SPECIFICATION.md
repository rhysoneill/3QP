# Phase 4 Unified Specification (WS1–WS5)

**3QP Repository — Phase 4 Architecture Reference**

---

## 1. Purpose

This document is the **frozen architectural reference** for the five Phase 4 workstreams that comprise the computational architecture layer of the Three-Question Protocol (3QP) system:

- **WS1: Semantic Schema** — Typed representations of Phase 3 qualitative concepts
- **WS2: State Encoding** — Transformation layer from schemas to structured encodings
- **WS3: Pattern Recognition** — Qualitative pattern recognition framework
- **WS4: Trajectory Engine** — Trajectory archetype classification framework
- **WS5: Validation Harness** — End-to-end validation and orchestration

### Critical Design Constraint

All five workstreams are **qualitative-only, architecture-only layers**. They contain:

- ✅ Dataclasses and type definitions
- ✅ Abstract base classes (ABCs) and protocols
- ✅ Structural validators
- ✅ Placeholder implementations
- ✅ Categorical/qualitative metadata only

They explicitly **DO NOT** contain:

- ❌ Numeric scoring, probabilities, or confidence values
- ❌ Machine learning, statistical inference, or algorithms
- ❌ Computational logic or pattern detection
- ❌ Time-series analysis or trajectory computation
- ❌ External dependencies (Python stdlib only)
- ❌ Cross-workstream mutation or side effects

### Relationship to Phase 3

Phase 4 workstreams translate Phase 3's rich qualitative documentation into structured, typed representations suitable for future computational implementation. They preserve semantic intent while enabling systematic validation and testing.

---

## 2. Architectural Layering

The five workstreams form a **strict one-directional pipeline**:

```
WS1 (Semantic Schema)
  ↓
WS2 (State Encoding)
  ↓
WS3 (Pattern Recognition)
  ↓
WS4 (Trajectory Engine)
  ↓
WS5 (Validation Harness)
```

### Data Flow Guarantees

- **WS1 → WS2**: Semantic schemas are encoded into structured states
- **WS2 → WS3**: Encoded states are analyzed for pattern recognition
- **WS3 → WS4**: Pattern results inform trajectory classification
- **WS4 → WS5**: Trajectory classifications are validated against expectations
- **WS5**: Consumes outputs from WS2–WS4 for end-to-end validation

### Prohibited Connections

The following cross-workstream connections are **explicitly forbidden**:

- WS1 → WS3, WS4, or WS5 (skip encoding layer)
- WS2 → WS4 (skip pattern recognition)
- WS5 computing or generating patterns, trajectories, or encodings
- Any reverse flow (WS5 → WS4, WS4 → WS3, etc.)

### Separation of Responsibilities

Each workstream has a **single, well-defined responsibility**:

| Workstream | Responsibility | Does NOT |
|------------|----------------|----------|
| WS1 | Define typed schemas | Encode, compute, or analyze |
| WS2 | Transform schemas to encodings | Recognize patterns or classify |
| WS3 | Provide pattern recognition architecture | Detect patterns or score |
| WS4 | Provide trajectory classification architecture | Compute trajectories or analyze time series |
| WS5 | Validate architecture wiring | Implement logic or perform computation |

---

## 3. Workstream Specifications

### 3.1 WS1 — Semantic Schema

**Location**: `phase4/01_Semantic_Schema/`

#### Purpose

The Semantic Schema Layer provides typed data structures for representing Phase 3 qualitative concepts within the 3QP framework. It serves as a **clean semantic representation** of baseline states, scenarios, patterns, threads, and trajectories without implementing simulation logic.

#### Key Dataclasses

**Baseline States:**
- `BaselineProfile`: Multi-domain baseline configuration
- `DomainState`: State within a specific domain (physiological, cognitive, emotional, social, workload, operational)
- `SemanticTag`: Descriptive labels from Phase 3 (e.g., "well-rested", "cohesive", "low-strain")
- `ModuleReference`: Links to module-level configurations by reference

**Scenario Descriptors:**
- `ScenarioTemplate`: Overall scenario structure (nominal, disruption, third-quarter)
- `EventDescriptor`: Individual events with qualitative characteristics
- `EventStoryline`: Ordered sequence of events forming narrative arcs

**Pattern Schemas:**
- `PatternDefinition`: Qualitative framework for recognizing recurring configurations
- `PatternInstance`: Recognition of a pattern in a specific context
- `PatternClass`: Pattern categories (stable, drift, disruption, recovery)

**Thread Schemas:**
- `ThreadDefinition`: Conceptual framework for domain relationships
- `ThreadInstance`: Recognition of a thread in a specific context

**Trajectory Schemas:**
- `TrajectoryArchetype`: Major qualitative trajectory pattern
- `TrajectoryInstance`: Characterization of a specific mission's trajectory

#### Architectural Rules

1. **Representation Only**: No simulation logic, state transitions, or computations
2. **Qualitative Fields**: All tags, descriptors, and characteristics are narrative/categorical
3. **Explicit Relationships**: Domain states reference domains; instances reference definitions
4. **Phase 3 Alignment**: Every schema includes narrative descriptions and Phase 3 references
5. **No Numeric Values**: No scores, probabilities, weights, or confidence metrics
6. **Module References Only**: Links to existing modules by reference; never modifies them

#### Public Interface

```python
# Baseline
BaselineProfile
DomainState
SemanticTag
ModuleReference

# Scenarios
ScenarioTemplate
EventDescriptor
EventStoryline

# Patterns
PatternDefinition
PatternInstance
PatternClass

# Threads
ThreadDefinition
ThreadInstance

# Trajectories
TrajectoryArchetype
TrajectoryInstance
```

---

### 3.2 WS2 — State Encoding

**Location**: `phase4/02_State_Encoding/`

#### Purpose

The State Encoding Layer transforms semantic schemas from WS1 into structured encoded states that downstream components can consume. It is a **pure transformation and validation layer** without computational logic.

#### Key Components

**Encoded State:**
- Canonical dictionary representation of semantic schemas
- Includes encoding metadata (version, type, provenance)
- Preserves qualitative fields and semantic tags

**Encoder Interfaces:**
- `StateEncoder`: Abstract base for all encoders
- `ObservationMapper`: Abstract base for observation-to-schema mapping
- `SchemaBinder`: Abstract base for schema binding and provenance
- `EncodingResult`: Standard container for encoding operation results

**Concrete Encoders:**
- `BaselineStateEncoder`: Transforms `BaselineProfile` → encoded baseline state
- `ScenarioEventEncoder`: Transforms `EventDescriptor` → encoded event
- `PatternIndicatorEncoder`: Transforms pattern indicators → encoded pattern hints
- `ThreadIndicatorEncoder`: Transforms thread indicators → encoded relational hints

**Validators:**
- `EncodedStateValidator`: Structural consistency checking
- `SchemaAlignmentValidator`: Alignment with semantic schemas
- `DomainConsistencyValidator`: Domain-specific consistency rules

**Mappers:**
- `ObservationToSchemaMapper`: Maps observations → `BaselineProfile`
- `NarrativeToEventMapper`: Maps event descriptions → `ScenarioEvent`
- `QualitativeDescriptorMapper`: Maps descriptors → pattern/thread indicators

#### Architectural Rules

1. **No Mutation**: Encoders do not mutate semantic schemas
2. **One-Directional Only**: WS1 → WS2; no reverse flow
3. **No Computation**: No pattern detection, trajectory analysis, or inference
4. **Structural Validation Only**: Validators check structure, not semantic correctness
5. **Qualitative Preservation**: All qualitative fields preserved in encodings
6. **Metadata Tracking**: All encoded states carry version and provenance metadata

#### Interface Contract with WS1

- **Input**: Semantic schema objects (`BaselineProfile`, `EventDescriptor`, etc.)
- **Output**: Encoded state dictionaries with metadata
- **Guarantee**: No semantic information lost or added during encoding

#### Public Interface

```python
# Interfaces
StateEncoder
ObservationMapper
SchemaBinder
EncodingResult

# Encoders
BaselineStateEncoder
ScenarioEventEncoder
PatternIndicatorEncoder
ThreadIndicatorEncoder

# Validators
EncodedStateValidator
SchemaAlignmentValidator
DomainConsistencyValidator
ValidationResult

# Mappers
ObservationToSchemaMapper
NarrativeToEventMapper
QualitativeDescriptorMapper
```

---

### 3.3 WS3 — Pattern Recognition

**Location**: `phase4/03_Pattern_Recognition/`

#### Purpose

The Pattern Recognition Engine provides a **pure architectural framework** for qualitative pattern recognition. It defines interfaces, evidence structures, and validators without performing any actual pattern detection.

#### Key Components

**Recognition Result:**
- `PatternRecognitionResult`: Container for recognized patterns and evidence
- Includes pattern identifiers, evidence bundle, and metadata
- Provides narrative summaries

**Evidence Structures:**
- `PatternEvidence`: Single evidence item with qualitative strength
- `PatternEvidenceBundle`: Collection of evidence items
- `QualitativeStrength`: Enum (SUGGESTIVE, WEAK, STRONG, CONTEXTUAL)

**Recognizer Interfaces:**
- `PatternRecognizer`: ABC for all recognizers
  - `analyze_encoded_state()`: Analyze single state
  - `analyze_sequence()`: Analyze state sequence
  - `get_supported_pattern_types()`: Return supported patterns
- `SequenceAnalyzer`: ABC for temporal pattern context
- `PatternAggregationEngine`: ABC for evidence aggregation

**Placeholder Recognizers:**
- `StablePatternRecognizer`: Equilibrium/homeostasis patterns
- `DriftPatternRecognizer`: Gradual shift patterns
- `DisruptionPatternRecognizer`: Sudden shock patterns
- `RecoveryPatternRecognizer`: Restoration patterns

**Registry:**
- `PatternRecognizerRegistry`: Central component registry
- `create_default_registry()`: Factory for pre-populated registry

**Validators:**
- `EvidenceValidator`: Evidence structure validation
- `RecognizerOutputValidator`: Recognition result validation
- `SequenceValidator`: State sequence validation

#### Architectural Rules

1. **Pure Structural Recognition**: Interfaces define contracts only
2. **No Pattern Logic**: Recognizers are placeholders; no actual detection
3. **Qualitative Evidence Only**: All strength indicators are categorical
4. **No Numeric Scoring**: No probabilities, confidence, weights, or thresholds
5. **No Computation**: No algorithms, ML, statistics, or inference
6. **Validation is Structural**: Validators check format, not correctness

#### Interface Contract with WS2

- **Input**: Encoded states from WS2 (opaque dictionaries)
- **Output**: `PatternRecognitionResult` with evidence bundle
- **Guarantee**: No mutation of encoded states; purely additive analysis

#### Public Interface

```python
# Interfaces
PatternRecognizer
SequenceAnalyzer
PatternAggregationEngine
PatternRecognitionResult

# Evidence
PatternEvidence
PatternEvidenceBundle

# Recognizers (Placeholders)
StablePatternRecognizer
DriftPatternRecognizer
DisruptionPatternRecognizer
RecoveryPatternRecognizer

# Registry
PatternRecognizerRegistry
create_default_registry

# Validators
EvidenceValidator
RecognizerOutputValidator
SequenceValidator
```

---

### 3.4 WS4 — Trajectory Engine

**Location**: `phase4/04_Trajectory_Analysis/`

#### Purpose

The Trajectory Engine provides the **architectural framework** for trajectory-level analysis and classification. It defines interfaces and evidence models for categorizing mission arcs into Phase 3 trajectory archetypes without performing actual trajectory computation.

#### Key Components

**Classification Result:**
- `TrajectoryClassificationResult`: Final trajectory classification
- Includes selected archetype, evidence bundle, and hypotheses
- Provides narrative summaries

**Hypothesis:**
- `TrajectoryHypothesis`: Qualitative assertion about trajectory archetype
- Includes archetype ID, rationale, and supporting patterns
- No numeric scoring or confidence values

**Analysis Result:**
- `TrajectoryAnalysisResult`: Output from trajectory analyzer
- Contains candidate hypotheses and evidence
- Links to pattern recognition results

**Evidence Structures:**
- `TrajectoryEvidence`: Single evidence item
- `TrajectoryEvidenceBundle`: Collection of evidence items
- `TrajectorySupportStrength`: Qualitative categories (SUGGESTIVE, WEAK, MODERATE, STRONG, CONTEXTUAL_ONLY)

**Analyzer Interfaces:**
- `TrajectoryAnalyzer`: ABC for sequence analyzers
  - `analyze_sequence()`: Analyze state/pattern sequences
  - `get_supported_archetypes()`: Return supported archetypes
- `TrajectoryClassifier`: ABC for trajectory classifiers
- `TrajectoryAggregationEngine`: ABC for aggregating analyses

**Placeholder Analyzers:**
- `SimpleTrajectoryAnalyzer`: Minimal placeholder
- `StableAdaptationAnalyzer`: Placeholder for stable_adaptation archetype
- `TrajectoryHeuristicClassifier`: Simple classifier placeholder
- `SimpleAggregationEngine`: Placeholder aggregation

**Registry:**
- `TrajectoryAnalysisRegistry`: Central component registry
- `create_default_registry()`: Factory for pre-populated registry

**Validators:**
- `TrajectoryEvidenceValidator`: Evidence validation
- `TrajectoryResultValidator`: Result validation
- `SequenceInputValidator`: Input validation

#### Trajectory Archetypes

Trajectory archetypes are **qualitative categories from Phase 3**:

- `stable_adaptation`: Consistent adaptation to challenges
- `third_quarter`: Mid-mission performance decline
- `cumulative_strain`: Progressive degradation over time
- `gradual_drift`: Slow erosion across domains
- `disruption_stabilization`: Acute challenge followed by recovery
- `meaning_erosion`: Loss of connection to mission purpose
- `recovery_renewal`: Movement from constraint to coherence
- `divergent_crew`: Different crew members on different trajectories

#### Architectural Rules

1. **Architecture Only**: Interfaces and contracts; no trajectory computation
2. **Qualitative Categories**: All archetypes are descriptive, not numeric
3. **No Scoring**: No probabilities, confidence, or weighted aggregation
4. **Structural Validation Only**: Validators check format and required fields
5. **Placeholder Analysis**: Analyzers return properly formatted placeholders
6. **No Time-Series Logic**: No temporal analysis or state transition computation

#### Interface Contract with WS3

- **Input**: Pattern recognition results from WS3
- **Output**: `TrajectoryClassificationResult` with evidence
- **Guarantee**: No access to WS1 or WS2; consumes WS3 outputs only

#### Public Interface

```python
# Interfaces
TrajectoryAnalyzer
TrajectoryClassifier
TrajectoryAggregationEngine

# Data Models
TrajectoryHypothesis
TrajectoryAnalysisResult
TrajectoryClassificationResult

# Evidence
TrajectorySupportStrength
TrajectoryEvidence
TrajectoryEvidenceBundle

# Analyzers (Placeholders)
SimpleTrajectoryAnalyzer
StableAdaptationAnalyzer
TrajectoryHeuristicClassifier
SimpleAggregationEngine

# Registry
TrajectoryAnalysisRegistry
create_default_registry

# Validators
ValidationResult
TrajectoryEvidenceValidator
TrajectoryResultValidator
SequenceInputValidator
```

---

### 3.5 WS5 — Validation Harness

**Location**: `phase4/05_Validation_Harness/`

#### Purpose

The Validation Harness provides **end-to-end orchestration and validation** for the Phase 4 stack (WS1–WS4). It exercises architectural contracts, validates structural correctness, and checks for expected qualitative behaviors **without introducing new computational logic**.

#### Key Components

**Configuration:**
- `ValidationScenarioConfig`: Defines expected patterns and trajectories
- `ValidationRunConfig`: Configuration for a validation run
- `ExpectedPattern`: Expected pattern specification (required/optional)
- `ExpectedTrajectory`: Expected trajectory specification (required/optional)

**Results:**
- `ValidationRunResult`: Aggregated validation results
- `CheckResult`: Individual check outcome
- Severity levels: ERROR, WARNING, INFO

**Fixtures:**
- Synthetic test scenarios aligned with Phase 3 reference patterns:
  - `stable_adaptation_case`: Stable patterns with minimal drift
  - `gradual_drift_case`: Progressive parameter drift
  - `third_quarter_signature_case`: Disruption-recovery pattern
- Pre-built encoded states, pattern results, trajectory classifications

**Validation Checks:**
- Pattern presence verification (required vs. optional)
- Trajectory archetype matching
- Structural validation using WS3/WS4 validators
- Enforcement of qualitative-only constraints

**Reporting:**
- `render_text_report()`: Human-readable text reports
- `render_dict_report()`: Machine-readable JSON reports
- Summary statistics and severity grouping

**Adapter Layers:**
- `LoggingClient` protocol for Module 09 (Logging System) integration
- `ExternalValidationClient` protocol for Module 10 (Validation) integration
- No-op implementations for standalone operation

#### Architectural Rules

1. **Orchestration Only**: Runs validation pipeline; does not compute patterns or trajectories
2. **Consumes WS2–WS4**: Uses outputs from encoders, recognizers, and classifiers
3. **No Generation**: Never computes or generates patterns, trajectories, or encodings
4. **Fixture-Based**: Uses pre-built synthetic data aligned with Phase 3
5. **Qualitative Enforcement**: Validates absence of numeric scoring in results
6. **Protocol-Based Integration**: Adapter layers use protocols for future extensibility

#### Validation Flow

```
1. Load ValidationRunConfig with scenario
2. Retrieve fixtures (encoded states, pattern results, trajectory results)
3. Run structural validation checks
4. Run pattern presence checks
5. Run trajectory archetype checks
6. Run qualitative constraint checks
7. Aggregate results into ValidationRunResult
8. Generate reports (text and/or JSON)
```

#### Public Interface

```python
# Configuration
ExpectedPattern
ExpectedTrajectory
ValidationScenarioConfig
ValidationRunConfig

# Results
CheckResult
ValidationRunResult

# Pipeline
run_validation

# Reporting
render_text_report
render_dict_report
```

---

## 4. Cross-Workstream Integration Rules

These rules are derived from the Integration Check Specification (`phase4/INTEGRATION_CHECK_SPECIFICATION.md`).

### Allowed Flow

The **only permitted** direction of data flow is:

```
WS1 → WS2 → WS3 → WS4 → WS5
```

### Contract Specifications

#### WS1 → WS2 Contract

- **WS1 provides**: `SemanticStateSnapshot`, semantic schemas
- **WS2 accepts**: Snapshot and outputs `EncodedState`
- **WS2 must not**: Mutate semantic fields
- **Flow**: One-directional only

#### WS2 → WS3 Contract

- **WS2 provides**: Sequences of `EncodedState`
- **WS3 accepts**: Encoded states and outputs `PatternRecognitionResult`
- **WS3 must not**: Modify or reinterpret encoders
- **WS3 must**: Remain qualitative and non-numeric

#### WS3 → WS4 Contract

- **WS3 provides**: Pattern identifiers and `PatternEvidenceBundle`
- **WS4 accepts**: `PatternRecognitionResult` and outputs `TrajectoryClassificationResult`
- **WS4 cannot**: Access WS1 or WS2 directly
- **All fields**: Remain descriptive

#### WS4 → WS5 Contract

- **WS4 provides**: `TrajectoryClassificationResult`
- **WS5 consumes**: WS4 + WS3 + WS2 results
- **WS5 performs**: Validation only
- **WS5 never**: Computes patterns or trajectories

### Prohibited Connections

The following connections are **explicitly forbidden**:

- `WS1 → WS3` (skip encoding layer)
- `WS1 → WS4` (skip encoding and pattern layers)
- `WS1 → WS5` (skip all intermediate layers)
- `WS2 → WS4` (skip pattern recognition)
- `WS3 ← WS5` (reverse flow)
- `WS4 ← WS2` (reverse flow)
- `WS5` calling encoders, recognizers, or classifiers

### Qualitative Enforcement Rules

Across **all workstreams**:

- ❌ No numeric scoring or weights
- ❌ No probabilities or confidence values
- ❌ No ML, statistics, or algorithms
- ❌ No threshold-based logic
- ✅ Evidence remains descriptive
- ✅ All strength indicators are categorical
- ✅ All metadata is qualitative

---

## 5. Public Interfaces

This section lists all public exports for each workstream. Implementation logic is **not included**; these are type definitions and contracts only.

### WS1 Exports

```python
# Baseline
BaselineProfile
DomainState
SemanticTag
ModuleReference

# Scenarios
ScenarioTemplate
EventDescriptor
EventStoryline

# Patterns
PatternDefinition
PatternInstance
PatternClass

# Threads
ThreadDefinition
ThreadInstance

# Trajectories
TrajectoryArchetype
TrajectoryInstance
```

### WS2 Exports

```python
# Interfaces
StateEncoder
ObservationMapper
SchemaBinder
EncodingResult

# Encoders
BaselineStateEncoder
ScenarioEventEncoder
PatternIndicatorEncoder
ThreadIndicatorEncoder

# Validators
EncodedStateValidator
SchemaAlignmentValidator
DomainConsistencyValidator
ValidationResult

# Mappers
ObservationToSchemaMapper
NarrativeToEventMapper
QualitativeDescriptorMapper
```

### WS3 Exports

```python
# Interfaces
PatternRecognizer
SequenceAnalyzer
PatternAggregationEngine
PatternRecognitionResult

# Evidence
PatternEvidence
PatternEvidenceBundle

# Recognizers
StablePatternRecognizer
DriftPatternRecognizer
DisruptionPatternRecognizer
RecoveryPatternRecognizer

# Registry
PatternRecognizerRegistry
create_default_registry

# Validators
EvidenceValidator
RecognizerOutputValidator
SequenceValidator
```

### WS4 Exports

```python
# Interfaces
TrajectoryAnalyzer
TrajectoryClassifier
TrajectoryAggregationEngine

# Data Models
TrajectoryHypothesis
TrajectoryAnalysisResult
TrajectoryClassificationResult

# Evidence
TrajectorySupportStrength
TrajectoryEvidence
TrajectoryEvidenceBundle

# Analyzers
SimpleTrajectoryAnalyzer
StableAdaptationAnalyzer
TrajectoryHeuristicClassifier
SimpleAggregationEngine

# Registry
TrajectoryAnalysisRegistry
create_default_registry

# Validators
ValidationResult
TrajectoryEvidenceValidator
TrajectoryResultValidator
SequenceInputValidator
```

### WS5 Exports

```python
# Configuration
ExpectedPattern
ExpectedTrajectory
ValidationScenarioConfig
ValidationRunConfig

# Results
CheckResult
ValidationRunResult

# Pipeline
run_validation

# Reporting
render_text_report
render_dict_report
```

---

## 6. Appendix — Phase 4 Constraints

### Global Architectural Constraints

These constraints apply to **all five workstreams** and are **non-negotiable**:

#### 1. Python Standard Library Only

- **Allowed**: `dataclasses`, `abc`, `typing`, `enum`, `datetime`, `collections`, `json`, `pathlib`
- **Prohibited**: `numpy`, `scipy`, `sklearn`, `tensorflow`, `pytorch`, `pandas`, or any external package

#### 2. Dataclasses + ABCs Only

- **Data structures**: Use `@dataclass` for all data models
- **Interfaces**: Use `abc.ABC` and `@abstractmethod` for all interfaces
- **Type hints**: Mandatory for all public APIs

#### 3. Strict Qualitative Metadata

- **Allowed**: Categorical labels, enums, narrative strings, semantic tags
- **Prohibited**: Numeric scores, probabilities, weights, confidence intervals, thresholds

#### 4. No Numeric, Probabilistic, or Statistical Fields

- **No floats/ints used for scoring**: All numeric fields must be IDs, counts, or timestamps only
- **No confidence values**: No `confidence: float` fields
- **No probabilities**: No `p_value`, `likelihood`, `probability` fields
- **No weights**: No `weight`, `importance`, `priority` numeric fields

#### 5. No ML or Inference Systems

- **No machine learning**: No training, prediction, or model inference
- **No statistical inference**: No hypothesis testing, regression, or correlation
- **No optimization**: No gradient descent, search algorithms, or optimization

#### 6. No External Dependencies

- **No database connections**: No SQL, NoSQL, or network I/O
- **No file I/O** (except for logging/reporting in WS5)
- **No environment variables** for configuration (use explicit parameters)

#### 7. No Cross-Workstream Mutation

- **Immutable inputs**: Workstreams do not modify inputs from upstream layers
- **No shared state**: No global variables or shared mutable state
- **No reverse flow**: WS5 cannot call WS1–WS4 encoders/analyzers

#### 8. No Side Effects

- **Pure functions**: All transformations are deterministic and side-effect-free
- **No logging in core logic**: Logging only in WS5 adapters
- **No randomness**: No `random` module usage in core logic

### Purpose of These Constraints

These constraints ensure:

1. **Clean Architecture**: Separation of representation from computation
2. **Testability**: All components can be tested independently
3. **Evolvability**: Computational logic can be added later without refactoring architecture
4. **Integrity**: Phase 3's qualitative nature is preserved throughout
5. **Simplicity**: No hidden complexity or external dependencies

---

## Version

**Phase 4 Unified Specification v1.0.0**

**Status**: Frozen architectural reference for WS1–WS5

**Last Updated**: December 2, 2025

---

**End of Specification**
