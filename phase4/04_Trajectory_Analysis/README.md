# Phase 4 / Workstream 4: Trajectory Analysis Architecture

## Overview

This workstream provides the **Trajectory Analysis Architecture Layer** for the 3QP system. It defines interfaces, data structures, evidence models, and validators for trajectory-level analysis and classification.

**CRITICAL**: This is a **pure architecture layer with ZERO computation**. No actual trajectory detection, scoring, machine learning, or numerical analysis is performed. All components are structural placeholders designed to establish contracts for future implementation.

## Purpose

Trajectory analysis operates at the highest level of the 3QP analysis stack:

1. **WS1 (Semantic Schema)**: Defines conceptual vocabulary
2. **WS2 (State Encoding)**: Encodes mission states into structured representations
3. **WS3 (Pattern Recognition)**: Identifies patterns within states
4. **WS4 (Trajectory Analysis)**: Classifies sequences of states/patterns into trajectory archetypes

This workstream consumes:
- Encoded states from WS2 (treated as opaque dictionaries)
- Pattern recognition results from WS3 (structurally similar objects)

This workstream produces:
- Trajectory-level hypotheses referencing Phase 3 archetypes
- Qualitative evidence bundles
- Narrative summaries
- Classification results

## Architectural Guarantees

- **No numeric scoring**: No probabilities, confidence scores, weights, or thresholds
- **No real computation**: All analyzers are placeholder implementations
- **No dependencies**: Does not import WS1, WS2, or WS3 modules
- **Qualitative only**: All evidence and support strength is categorical
- **Standard library only**: No external dependencies

## Structure

```
phase4/04_Trajectory_Analysis/
├── README.md
├── IMPLEMENTATION_SUMMARY.md
├── trajectory_analysis/
│   ├── __init__.py          # Public API
│   ├── interfaces.py        # Abstract base classes
│   ├── models.py            # Data models (hypotheses, results)
│   ├── evidence.py          # Evidence structures
│   ├── analyzers.py         # Placeholder implementations
│   ├── registry.py          # Component registry
│   └── validators.py        # Structural validators
└── tests/
    ├── test_interfaces.py
    ├── test_models.py
    ├── test_evidence.py
    ├── test_analyzers.py
    ├── test_registry.py
    └── test_validators.py
```

## Core Concepts

### Trajectory Archetypes

Trajectory archetypes are qualitative pattern templates from Phase 3 that describe mission-level trajectories:

- `stable_adaptation`: Consistent adaptation to challenges
- `third_quarter`: Mid-mission performance decline
- `cumulative_strain`: Progressive degradation over time
- `breakthrough_paradox`: Success followed by decline
- And others from Phase 3 reference patterns

### Evidence and Support

All evidence is **qualitative** and uses categorical support strength:

- `SUGGESTIVE`: Minimal indication
- `WEAK`: Some support
- `MODERATE`: Reasonable support
- `STRONG`: Clear support
- `CONTEXTUAL_ONLY`: Context-dependent only

### Hypotheses and Classification

A **trajectory hypothesis** is a qualitative assertion that a particular archetype may be present, supported by narrative rationale and pattern references.

A **trajectory classification** selects a primary archetype (or none) from candidate hypotheses, supported by an evidence bundle.

## Usage Example

```python
from trajectory_analysis import (
    create_default_registry,
    SequenceInputValidator
)

# Create registry with default components
registry = create_default_registry()

# Get an analyzer
analyzer = registry.get_analyzer("stable_adaptation")

# Prepare inputs (WS2 encoded states and WS3 pattern results)
encoded_states = [
    {"state_id": "s1", "phase": "early", "context": {...}},
    {"state_id": "s2", "phase": "mid", "context": {...}},
]

# Pattern results would come from WS3 (stubbed here)
pattern_results = [...]  # WS3 PatternRecognitionResult objects

# Validate inputs
validator = SequenceInputValidator()
validation = validator.validate_inputs(encoded_states, pattern_results)

if validation.is_valid:
    # Analyze sequence
    analysis_result = analyzer.analyze_sequence(encoded_states, pattern_results)
    
    # Get narrative summary
    print(analysis_result.to_narrative())
    
    # Classify using default classifier
    classifier = registry.get_classifier("simple_classifier")
    classification = classifier.classify(analysis_result)
    
    print(f"Selected archetype: {classification.selected_archetype_id}")
    print(classification.to_narrative())
```

## Public API

### Interfaces

- `TrajectoryAnalyzer`: ABC for sequence analyzers
- `TrajectoryClassifier`: ABC for trajectory classifiers
- `TrajectoryAggregationEngine`: ABC for aggregating multiple analyses

### Data Models

- `TrajectoryHypothesis`: Qualitative archetype hypothesis
- `TrajectoryAnalysisResult`: Output from analyzer
- `TrajectoryClassificationResult`: Final classification

### Evidence

- `TrajectorySupportStrength`: Enum for qualitative support levels
- `TrajectoryEvidence`: Single evidence item
- `TrajectoryEvidenceBundle`: Collection of evidence items

### Placeholder Implementations

- `SimpleTrajectoryAnalyzer`: Minimal placeholder
- `StableAdaptationAnalyzer`: Placeholder for stable_adaptation
- `TrajectoryHeuristicClassifier`: Simple classifier placeholder
- `SimpleAggregationEngine`: Placeholder aggregation

### Registry

- `TrajectoryAnalysisRegistry`: Central component registry
- `create_default_registry()`: Factory for pre-populated registry

### Validators

- `ValidationResult`: Validation outcome container
- `TrajectoryEvidenceValidator`: Evidence validation
- `TrajectoryResultValidator`: Result validation
- `SequenceInputValidator`: Input validation

## Testing

Comprehensive test suite validates:

- Abstract interfaces cannot be instantiated
- Concrete implementations comply with contracts
- Data models validate fields and constraints
- Evidence structures filter and group correctly
- Placeholder analyzers produce expected outputs
- Registry manages components correctly
- Validators detect forbidden numeric scoring
- Narrative methods never raise exceptions

Run tests:

```bash
cd phase4/04_Trajectory_Analysis
pytest tests/ -v
```

## Relationship to Other Workstreams

### Phase 3 Reference Patterns

Trajectory archetypes reference qualitative patterns from Phase 3:

- `01_Baseline_State`: Initial conditions
- `02_Scenarios`: Event sequences
- `03_Reference_Patterns`: Trajectory archetypes

### Phase 4 Workstreams

- **WS1 (Semantic Schema)**: Provides conceptual vocabulary
- **WS2 (State Encoding)**: Produces encoded states consumed here
- **WS3 (Pattern Recognition)**: Produces pattern results consumed here
- **WS4 (Trajectory Analysis)**: This workstream
- **WS5**: TBD (may consume trajectory classifications)
- **WS6 (Computation Layer)**: Will implement real algorithms

## Future Implementation (WS6+)

This architecture layer will be filled in by later workstreams that implement:

- Real trajectory detection algorithms
- Time series analysis
- Pattern sequence analysis
- Machine learning models
- Probabilistic reasoning (in a separate layer, not mixed with architecture)

The separation ensures clean boundaries between architectural contracts and computational implementations.

## Development Guidelines

When extending this workstream:

1. **Maintain zero computation**: Do not add real analysis logic
2. **No numeric scoring**: Keep all evidence qualitative
3. **Preserve contracts**: Maintain interface compatibility
4. **Validate structure**: Add validators for new models
5. **Document placeholders**: Clearly mark placeholder behavior
6. **Test contracts**: Validate structure, not correctness

## Version

**Version**: 0.1.0

**Status**: Architecture layer complete, awaiting computational implementation

## License

Part of the 3QP project.
