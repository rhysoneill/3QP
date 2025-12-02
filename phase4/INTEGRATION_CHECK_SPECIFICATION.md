# Integration Check Specification (Phase 4)

## Purpose

This document defines the required wiring relationships between WS1 (Semantic Schema), WS2 (State Encoding), WS3 (Pattern Recognition), WS4 (Trajectory Analysis), and WS5 (Validation Harness). It establishes the only permitted flow direction and prevents illegal cross-workstream dependencies. This is an architecture-only reference with zero computation, zero new design, and no changes to existing workstreams.

## Allowed Flow

The only permitted direction of data flow is:

```
WS1 → WS2 → WS3 → WS4 → WS5
```

**No reverse imports. No shortcuts.**

## WS1 → WS2 Contract

- WS1 provides `SemanticStateSnapshot`
- WS2 accepts snapshot and outputs `EncodedState`
- WS2 must not mutate semantic fields
- One-directional only

## WS2 → WS3 Contract

- WS2 provides sequences of `EncodedState`
- WS3 accepts these and outputs `PatternRecognitionResult`
- WS3 must not modify or reinterpret encoders
- WS3 must remain qualitative and non-numeric

## WS3 → WS4 Contract

- WS3 provides pattern identifiers and evidence bundles
- WS4 accepts `PatternRecognitionResult` and outputs `TrajectoryClassificationResult`
- WS4 cannot access WS1 or WS2
- All fields remain descriptive

## WS4 → WS5 Contract

- WS4 provides `TrajectoryClassificationResult`
- WS5 consumes WS4 + WS3 + WS2 results
- WS5 performs validation only
- WS5 never computes patterns or trajectories

## Prohibited Connections

The following connections are explicitly **forbidden**:

- `WS1 → WS3`
- `WS1 → WS4`
- `WS1 → WS5`
- `WS2 → WS4`
- `WS3 ← WS5`
- `WS4 ← WS2`
- `WS5` calling encoders, recognizers, or classifiers

## Qualitative Enforcement Rules

- No numeric scoring
- No probabilities
- No weights or confidence
- No ML/statistics
- Evidence remains descriptive

---

**This file is a frozen reference layer required before generating the Phase 4 Unified Specification Export.**
