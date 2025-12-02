# Phase 5 Implementation Notes

## 1. Scope of Phase 5

Phase 5 will implement **actual computation** inside the following workstreams:

- **WS2: State Encoding**
  - Implement real encoders that transform semantic state into encoded representations
  - Build concrete encoding logic for beliefs, desires, intentions, physiological state, social context, stressors, and interventions

- **WS3: Pattern Recognition**
  - Implement rule-based pattern recognizers
  - Build detection logic for qualitative patterns in encoded state
  - Generate evidence structures with qualitative metadata

- **WS4: Trajectory Analysis**
  - Implement rule-based trajectory classification
  - Build trajectory engines that analyze state evolution
  - Classify trajectories qualitatively (e.g., "escalating", "stabilizing", "volatile")

**Important:** WS1 (Semantic Schema) and WS5 (Validation Harness) remain **purely structural** even in Phase 5.

- WS1 defines types and schemas only
- WS5 validates outputs against contracts only
- Neither executes domain logic

---

## 2. Constraints

Phase 5 implementation **must not violate** the following constraints:

### Structural Constraints

- **Must honor all dataclass definitions** from `PHASE4_UNIFIED_SPECIFICATION.md`
  - No field additions, removals, or renames
  - No type changes
  - No structural modifications

- **Must maintain one-directional flow**: `WS1 → WS2 → WS3 → WS4 → WS5`
  - No backward dependencies
  - No circular references
  - No skipping intermediate workstreams

### Computational Constraints

- **Must not introduce numeric scoring** unless formally approved in Phase 6
  - No probability calculations
  - No confidence scores
  - No weighted aggregations

- **Must not introduce ML/inference engines** unless approved in Phase 6
  - No neural networks
  - No statistical models
  - No learning algorithms

### Qualitative Constraints

- **Must maintain qualitative metadata** in WS3 and WS4
  - Pattern evidence must be symbolic/categorical
  - Trajectory classifications must be qualitative labels
  - All reasoning must be rule-based and interpretable

- **Must not mutate upstream objects**
  - WS3 cannot modify WS2 outputs
  - WS4 cannot modify WS3 outputs
  - WS5 cannot modify WS4 outputs
  - Data flow is read-only in the forward direction

---

## 3. Allowed Extensions

Phase 5 is **allowed** to implement:

### Core Implementations

- **Real encoders** in WS2
  - Convert semantic state into structured representations
  - Apply transformation logic to beliefs, desires, intentions, etc.
  - Generate encoded state objects

- **Rule-based recognizers** in WS3
  - Detect patterns using if-then logic
  - Apply qualitative thresholds
  - Generate evidence with categorical labels

- **Rule-based trajectory classification** in WS4
  - Analyze state sequences
  - Apply trajectory rules
  - Classify evolution patterns qualitatively

### Data Extensions

- **Expand evidence structures qualitatively**
  - Add categorical metadata fields
  - Include symbolic justifications
  - Attach interpretable reasoning chains

### Helper Modules

- **Add helper modules outside WS1–WS5** if needed
  - Utilities for common operations
  - Shared constants and enums
  - Logging and debugging tools
  - These must remain outside the core WS1–WS5 pipeline

---

## 4. Prohibited Changes

The following changes are **strictly prohibited** in Phase 5:

### Interface Changes

- **No rewrites of WS1–WS5 dataclasses**
  - Dataclass structures are frozen
  - Any perceived issues must be flagged for Phase 6 review

- **No additional fields in core WS1–WS5 objects**
  - Cannot extend frozen dataclasses
  - Cannot add computed properties
  - Cannot inject new attributes

### Architectural Changes

- **No renaming or collapsing of workstreams**
  - WS1–WS5 structure is fixed
  - Cannot merge WS3 and WS4
  - Cannot split existing workstreams

- **No bypassing WS3 or WS4**
  - Cannot create WS2 → WS4 shortcuts
  - Cannot skip pattern recognition
  - Cannot skip trajectory analysis

- **No "shortcut pipelines"**
  - Every data flow must go through all five workstreams in order
  - No express lanes
  - No conditional skipping

---

## 5. Optional Enhancements

The following enhancements are **optional** for Phase 5 but **must remain separate** from WS1–WS5:

### Testing Infrastructure

- **Batch validators calling WS5**
  - Test harnesses that run multiple scenarios
  - Aggregate validation reports
  - Must not be embedded in WS5 itself

### Scenario Management

- **Scenario runners wrapping the WS1–WS4 pipeline**
  - Execute predefined test cases
  - Compare outputs across scenarios
  - Must not modify WS1–WS4 internals

### Reporting

- **Exportable reports**
  - JSON, Markdown, or text output formats
  - Visualization of validation results
  - Must not alter WS5 validation logic

### Fixtures

- **Extended fixture libraries**
  - More test scenarios
  - More baseline states
  - More reference patterns
  - Must be stored outside WS1–WS5 code

---

## Summary

Phase 5 is about **implementing computation within frozen contracts**.

- **Do:** Build encoders, recognizers, and trajectory engines
- **Don't:** Change interfaces, add scoring, introduce ML, or bypass workstreams

All Phase 5 work must respect the Phase 4 architecture as immutable law.

