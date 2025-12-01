# Module 07: Lunar Mission Stressor Model - Data Contract

**Document Version**: 1.0  
**Date**: December 1, 2025  
**Status**: Baseline

---

## 1. Introduction

This document defines the input and output data structures for the Lunar Mission Stressor Model. The data contract specifies:

- **Inputs**: External configuration and event data consumed by the module
- **Outputs**: Stressor intensity signals and metadata provided to downstream modules
- **Timing and Granularity**: Update frequencies and temporal resolution
- **Validity Constraints**: Rules for data consumers to ensure correct interpretation

All data structures are represented in abstract pseudocode notation. Implementations may use language-specific equivalents (structs, classes, JSON schemas, etc.).

---

## 2. Module Inputs

### 2.1 Mission Configuration Input

**Provided At**: Initialization (T=0)

**Data Structure**:

```
MissionConfig {
  mission_id: string
  mission_start_date: datetime
  mission_duration_days: float
  random_seed: int
  
  phase_definitions: PhaseDefinition[]
  stressor_parameters: StressorParameterSet[]
  event_schedule: ScheduledEvent[]
}

PhaseDefinition {
  phase_id: string
  start_day: float
  end_day: float
  phase_type: enum { COMMISSIONING, STEADY_STATE, CREW_ROTATION, CLOSEOUT }
}

StressorParameterSet {
  stressor_id: string
  category: enum { OPERATIONAL, ENVIRONMENTAL, TEMPORAL, MONOTONY }
  enabled: boolean
  
  baseline: float [0.0, 1.0]
  max_intensity: float [0.0, 1.0]
  decay_tau: float (days) | null
  accumulation_rate: float (per day) | null
  
  cadence_period: float (days) | null
  cadence_amplitude: float [0.0, 1.0] | null
  cadence_phase_offset: float (radians) | null
  
  spike_schedule: SpikeEvent[] | null
  noise_parameters: NoiseConfig | null
}

SpikeEvent {
  trigger_time: float (days from mission start)
  magnitude: float [0.0, 1.0]
  duration: float (days)
}

NoiseConfig {
  noise_type: enum { ORNSTEIN_UHLENBECK, WHITE, NONE }
  intensity: float [0.0, 1.0]
  correlation_time: float (days) | null
}

ScheduledEvent {
  event_id: string
  event_time: float (days from mission start)
  event_type: enum { EVA, MAINTENANCE, RESUPPLY, CREW_CHANGE, MILESTONE }
  stressor_modifiers: StressorModifier[]
}

StressorModifier {
  stressor_id: string
  intensity_delta: float [-1.0, 1.0]
  duration: float (days)
}
```

**Validity Constraints**:
- `mission_duration_days > 0`
- `phase_definitions` must cover entire mission duration without gaps or overlaps
- `baseline <= max_intensity` for all stressor parameters
- `decay_tau > 0` if specified
- `spike_schedule` times must fall within mission duration
- `random_seed` must be consistent across replicate runs for reproducibility

**Source**: TQP Core initialization subsystem

---

### 2.2 Update Cycle Input

**Provided At**: Each simulation timestep

**Data Structure**:

```
UpdateCycleInput {
  current_time: float (days from mission start)
  delta_time: float (days since last update)
  
  triggered_events: TriggeredEvent[]
}

TriggeredEvent {
  event_id: string
  event_type: enum { EVA, MAINTENANCE, RESUPPLY, CREW_CHANGE, MILESTONE, ANOMALY }
  event_time: float (days from mission start)
}
```

**Validity Constraints**:
- `current_time >= 0`
- `delta_time > 0`
- `current_time` must be monotonically increasing across updates
- `triggered_events` must reference valid event types from mission configuration

**Source**: TQP Core simulation loop

---

## 3. Module Outputs

### 3.1 Stressor Intensity Vector

**Provided At**: After each update cycle

**Data Structure**:

```
StressorIntensityVector {
  mission_time: float (days from mission start)
  timestamp: datetime
  
  operational_stressors: StressorValue[]
  environmental_stressors: StressorValue[]
  temporal_stressors: StressorValue[]
  monotony_stressors: StressorValue[]
  
  summary_metrics: SummaryMetrics
}

StressorValue {
  stressor_id: string
  current_intensity: float [0.0, 1.0]
  accumulated_exposure: float (intensity-days)
  last_spike_time: float (days from mission start) | null
  spike_count: int
  
  state_flags: StateFlags
}

StateFlags {
  is_active: boolean
  is_spiking: boolean
  is_degraded: boolean  // parameter violation or numerical issue
}

SummaryMetrics {
  total_operational_intensity: float [0.0, 1.0]
  total_environmental_intensity: float [0.0, 1.0]
  total_temporal_intensity: float [0.0, 1.0]
  total_monotony_intensity: float [0.0, 1.0]
  
  overall_stressor_load: float [0.0, 1.0]  // aggregate across all categories
}
```

**Validity Constraints**:
- All `current_intensity` values in [0.0, 1.0]
- `accumulated_exposure >= 0`
- `spike_count >= 0`
- `summary_metrics` values in [0.0, 1.0]

**Consumers**: 
- Module 04 (Slow/Fast Physiology)
- Module 06 (BDI Cycle)
- Module 05 (Social Network) [optional, if environmental context needed]
- Module 09 (Logging System)

---

### 3.2 Stressor Metadata

**Provided At**: On demand (query interface)

**Data Structure**:

```
StressorMetadata {
  stressor_id: string
  category: enum { OPERATIONAL, ENVIRONMENTAL, TEMPORAL, MONOTONY }
  description: string
  
  current_parameters: StressorParameterSet
  activation_history: ActivationEvent[]
  
  statistical_summary: StatisticalSummary
}

ActivationEvent {
  event_time: float (days from mission start)
  event_type: enum { INITIALIZED, SPIKE_TRIGGERED, PARAMETER_CHANGED, DEACTIVATED }
}

StatisticalSummary {
  mean_intensity: float [0.0, 1.0]
  max_intensity: float [0.0, 1.0]
  min_intensity: float [0.0, 1.0]
  std_dev_intensity: float
  
  time_above_threshold: float (days)  // time with intensity > 0.5
}
```

**Consumers**:
- Module 09 (Logging System) for diagnostic telemetry
- Module 10 (Validation) for unit testing and scenario verification

---

## 4. Timing and Granularity

### 4.1 Update Frequencies

| Stressor Category | Typical Update Frequency | Rationale |
|-------------------|--------------------------|-----------|
| Operational       | Every timestep (hourly)  | Task schedules vary on sub-day timescales |
| Environmental     | Daily or per shift       | Habitat conditions relatively stable |
| Temporal          | Daily                    | Mission phase transitions occur on day-scale |
| Monotony          | Weekly                   | Requires extended observation window |

**Note**: Update frequencies are configurable per stressor type. High-frequency stressors may be updated more often than the minimum cadence if computational resources allow.

### 4.2 Data Freshness Guarantees

- **Stressor Intensity Vector**: Published within 10 ms of update cycle completion (real-time constraint for synchronous simulation)
- **Stressor Metadata**: Available on-demand with <100 ms latency (for logging and diagnostics)

### 4.3 Historical Data Retention

- **Full State History**: Retained for validation and debugging purposes (storage-limited)
- **Sampled History**: Downsampled to 1-hour resolution for long-term archival
- **Summary Statistics**: Computed over rolling windows (24-hour, 7-day, 30-day)

---

## 5. Validity Constraints for Consumers

Downstream modules consuming stressor data MUST adhere to the following constraints:

### 5.1 Intensity Interpretation

- **Normalized Values**: All `current_intensity` values are normalized to [0.0, 1.0]. Consumers MUST apply domain-specific scaling if physical units are required.
- **Zero Baseline**: `intensity = 0.0` does NOT imply "no stressor present." It represents the minimum expected baseline for that stressor type.
- **Saturation**: `intensity = 1.0` represents the maximum anticipated intensity. Values should NOT be extrapolated beyond this bound.

### 5.2 Temporal Alignment

- **Synchronous Updates**: Stressor data is valid for the current simulation time `mission_time`. Consumers MUST NOT use stale stressor values from previous timesteps.
- **No Temporal Interpolation**: If a consumer requires sub-timestep stressor values, it MUST query the Stressor Model explicitly (if supported) or use the most recent available value.

### 5.3 Accumulated Exposure

- **Cumulative Metric**: `accumulated_exposure` is a monotonically increasing integral of intensity over time. Consumers MUST NOT reset or modify this value.
- **Units**: Exposure is measured in intensity-days (e.g., an intensity of 0.5 sustained for 10 days = 5.0 intensity-days).

### 5.4 State Flags

- **is_active**: If `false`, the stressor is currently disabled (e.g., phase-dependent stressor outside its active phase). Consumers SHOULD ignore intensity values.
- **is_spiking**: If `true`, the stressor is undergoing a transient spike. Consumers MAY use this flag to trigger adaptive responses.
- **is_degraded**: If `true`, the stressor has encountered a parameter violation or numerical issue. Consumers SHOULD treat intensity values with caution and log diagnostic information.

### 5.5 Summary Metrics

- **Aggregation Method**: `overall_stressor_load` is computed as a weighted sum of category intensities. Weights are configurable and documented in mission configuration.
- **Non-Linear Aggregation**: Consumers MUST NOT assume linear additivity of category intensities. Use provided summary metrics rather than recomputing aggregates.

---

## 6. Error Handling and Degraded Modes

### 6.1 Missing Stressor Data

If a downstream module queries a stressor that does not exist:
- **Response**: Return `null` or equivalent (language-dependent)
- **Logging**: Log warning with stressor ID and query context

### 6.2 Invalid Intensity Values

If a stressor produces out-of-bounds intensity:
- **Response**: Clamp to [0.0, 1.0] and set `is_degraded = true`
- **Logging**: Log error with stressor ID and computed value

### 6.3 Temporal Discontinuities

If mission time regresses or exhibits discontinuities:
- **Response**: Halt stressor updates and flag critical error
- **Logging**: Log critical error with time values and stack trace

---

## 7. Versioning and Schema Evolution

### 7.1 Data Contract Version

This data contract is versioned independently from the Stressor Model implementation.

**Current Version**: `1.0.0` (Major.Minor.Patch)

- **Major**: Breaking changes to data structures (incompatible with previous consumers)
- **Minor**: Additive changes (new fields, backward-compatible)
- **Patch**: Documentation clarifications, no structural changes

### 7.2 Backward Compatibility

Consumers MUST check data contract version at initialization:

```
if stressor_model.data_contract_version.major != EXPECTED_MAJOR_VERSION:
  raise IncompatibleDataContractError()
```

### 7.3 Deprecation Policy

Deprecated fields will be:
- Marked in documentation for at least one minor version before removal
- Populated with sentinel values (`null`, `-1`, etc.) during deprecation period
- Removed in next major version

---

## 8. Example Data Flow

### 8.1 Initialization Sequence

```
1. TQP Core loads MissionConfig from file
2. TQP Core calls StressorModel.initialize(MissionConfig)
3. StressorModel validates parameters and initializes internal state
4. StressorModel returns initial StressorIntensityVector (T=0)
5. TQP Core publishes initial stressor data to shared state
```

### 8.2 Update Cycle

```
1. TQP Core advances simulation time: t -> t + Δt
2. TQP Core assembles UpdateCycleInput (current time, delta time, triggered events)
3. TQP Core calls StressorModel.update(UpdateCycleInput)
4. StressorModel updates internal state for all active stressors
5. StressorModel computes StressorIntensityVector
6. StressorModel returns StressorIntensityVector to TQP Core
7. TQP Core publishes updated stressor data to shared state
8. Downstream modules (Physiology, BDI) read stressor data
```

### 8.3 Query Interface

```
1. Consumer (e.g., Logging System) requests StressorMetadata for stressor_id="task_density"
2. StressorModel retrieves metadata from internal state
3. StressorModel computes StatisticalSummary over relevant time window
4. StressorModel returns StressorMetadata to consumer
```

---

## 9. Implementation Guidance

### 9.1 Data Serialization

Recommended formats for data interchange:
- **JSON**: Human-readable, widely supported, moderate performance
- **Protocol Buffers**: Compact binary, high performance, requires schema compilation
- **MessagePack**: Compact binary, JSON-compatible, faster than JSON

### 9.2 Memory Management

For long-duration missions:
- Use **circular buffers** for full-resolution state history (last 7 days)
- Use **downsampled archives** for older data (hourly samples)
- Compute **summary statistics** incrementally to avoid reprocessing entire history

### 9.3 Concurrency Considerations

If parallel execution is enabled:
- Stressor state updates MUST be protected with mutex or equivalent
- Consumers MUST use read-locks when accessing stressor data
- Publish/subscribe patterns preferred over direct memory access

---

## 10. Validation and Testing

### 10.1 Contract Validation Tests

Automated tests MUST verify:
- All output fields conform to specified data types and ranges
- Intensity values remain within [0.0, 1.0] across full mission duration
- Temporal consistency (monotonic time, no gaps in history)
- State flags correctly reflect stressor status

### 10.2 Interoperability Testing

Integration tests MUST verify:
- TQP Core can successfully initialize and update the Stressor Model
- Downstream modules can correctly parse and interpret stressor data
- Data contract version checking prevents incompatible module combinations

---

**End of Data Contract Document**

**Approval**: Pending  
**Review Cycle**: December 2025  
**Next Revision**: As needed for interface changes or downstream module requirements
