# Module 04: Slow–Fast Physiology Model — Data Contract

**Version**: 1.0  
**Date**: December 2025

---

## 1. Purpose

This document defines the data interfaces for Module 04: Slow–Fast Physiology Model. It specifies the structure, types, and constraints of all data exchanged between the physiology module and other components of the 3QP simulation framework.

---

## 2. Input Data Contract

### 2.1 Initialization Data

**Data Structure**: `PhysiologyInitConfig`

```
PhysiologyInitConfig {
    initial_state: PhysiologyState,
    parameters: PhysiologyParameters,
    timescale_config: TimescaleConfig
}
```

#### 2.1.1 `PhysiologyState`

```
PhysiologyState {
    C_base: float [0.0, 1.0],      // Baseline capacity
    L_cum: float [0.0, +inf),       // Cumulative load
    R_cap: float [0.0, 1.0],        // Recovery capacity
    A_resp: float [0.0, A_max],     // Acute response
    L_trans: float [0.0, +inf),     // Transient load
    xi: float [0.0, 1.0]            // Relaxation state
}
```

**Constraints**:
- All fields must be present
- All values must be finite (no NaN, no Inf except where explicitly allowed)
- Range violations trigger initialization error

#### 2.1.2 `PhysiologyParameters`

```
PhysiologyParameters {
    // Slow-time parameters
    alpha_deg: float > 0.0,         // Degradation coefficient
    beta_rec: float > 0.0,          // Recovery coefficient
    omega_in: float > 0.0,          // Load accumulation rate
    omega_out: float > 0.0,         // Load dissipation rate
    kappa_rec: float > 0.0,         // Recovery restoration rate
    kappa_fatigue: float > 0.0,     // Fatigue degradation rate
    R_cap_max: float = 1.0,         // Max recovery capacity
    
    // Fast-time parameters
    Delta_A_0: float > 0.0,         // Baseline acute response sensitivity
    lambda_A: float > 0.0,          // Acute response relaxation rate
    lambda_L: float > 0.0,          // Transient load relaxation rate
    lambda_xi: float > 0.0,         // Relaxation state rate
    mu: float >= 0.0,               // Coupling coefficient
    A_max: float > 0.0,             // Maximum acute response
    
    // Coupling parameters
    sigma: float >= 0.0             // Load-dependent modulation coefficient
}
```

**Constraints**:
- All rate constants must be positive
- Parameter values provided at initialization; runtime modification not supported in baseline version

#### 2.1.3 `TimescaleConfig`

```
TimescaleConfig {
    dt_slow: float > 0.0,           // Slow time step (e.g., 1.0 day)
    dt_fast: float > 0.0,           // Fast time step (e.g., 1.0/24 day = 1 hour)
    time_unit: string               // "days", "hours", etc. (metadata only)
}
```

**Constraints**:
- `dt_fast < dt_slow`
- `dt_slow / dt_fast` must be an integer (number of fast steps per slow step)

---

### 2.2 Runtime Input Data

#### 2.2.1 Slow-Time Input

**Data Structure**: `SlowTimeInput`

```
SlowTimeInput {
    t_slow: float >= 0.0,           // Current slow-time timestamp
    I_slow: float [0.0, +inf)       // Slow-time stressor intensity
}
```

**Timing**: Provided once per slow-time epoch (every `dt_slow`)

**Semantic Content**: `I_slow` is a dimensionless intensity value; physiology module does not interpret semantic meaning.

**Default**: If `I_slow` not provided, assume `I_slow = 0.0`

#### 2.2.2 Fast-Time Input

**Data Structure**: `FastTimeInput`

```
FastTimeInput {
    t_fast: float >= 0.0,           // Current fast-time timestamp
    I_fast: float [0.0, +inf)       // Fast-time stressor intensity
}
```

**Timing**: Provided once per fast-time step (every `dt_fast`)

**Semantic Content**: `I_fast` is a dimensionless intensity value; physiology module does not interpret semantic meaning.

**Default**: If `I_fast` not provided, assume `I_fast = 0.0`

---

## 3. Output Data Contract

### 3.1 Slow-Time Output

**Data Structure**: `SlowTimeOutput`

```
SlowTimeOutput {
    t_slow: float >= 0.0,           // Timestamp of this output
    state: SlowTimeState,           // Slow-time state variables
    status: StatusCode              // Module status indicator
}
```

#### 3.1.1 `SlowTimeState`

```
SlowTimeState {
    C_base: float [0.0, 1.0],
    L_cum: float [0.0, +inf),
    R_cap: float [0.0, 1.0],
    gamma_drift: float              // Current drift rate (derived)
}
```

**Timing**: Emitted once per slow-time epoch, after slow-time update

**Availability**: All downstream modules may read `SlowTimeState` via query interface

---

### 3.2 Fast-Time Output

**Data Structure**: `FastTimeOutput`

```
FastTimeOutput {
    t_fast: float >= 0.0,           // Timestamp of this output
    state: FastTimeState,           // Fast-time state variables
    status: StatusCode              // Module status indicator
}
```

#### 3.2.1 `FastTimeState`

```
FastTimeState {
    A_resp: float [0.0, A_max],
    L_trans: float [0.0, +inf),
    xi: float [0.0, 1.0]
}
```

**Timing**: Emitted once per fast-time step, after fast-time update

**Availability**: Downstream modules may read `FastTimeState` at fast-time resolution; if slow-time modules query, they receive most recent fast-time state

---

### 3.3 Derived Quantities Output

**Data Structure**: `PhysiologyDerivedOutput`

```
PhysiologyDerivedOutput {
    t: float >= 0.0,
    L_total: float [0.0, +inf),     // L_cum + L_trans
    C_eff: float [0.0, 1.0]         // Effective capacity (computed from C_base and L_total)
}
```

**Computation**:
```
L_total = L_cum + L_trans
C_eff = C_base * f(L_total)
```

where `f(L_total)` is a saturation function (e.g., `1 / (1 + L_total)`).

**Timing**: Computed on-demand or emitted with fast-time output

---

## 4. Status Codes

```
StatusCode {
    PHYS_OK = 0,                    // Update successful, no issues
    PHYS_INPUT_INVALID = 1,         // Input out of range or malformed
    PHYS_STATE_CLAMP = 2,           // State variable clamped (warning)
    PHYS_NUMERIC_ERROR = 3          // Numerical instability detected (critical error)
}
```

**Behavior**:
- `PHYS_OK`: Normal operation
- `PHYS_INPUT_INVALID`: Update skipped; previous state retained; error logged
- `PHYS_STATE_CLAMP`: Update completed but state constrained; warning logged
- `PHYS_NUMERIC_ERROR`: Update failed; module enters safe mode; critical error logged

---

## 5. Query Interface

### 5.1 State Query

**Request**:
```
StateQuery {
    query_type: "slow" | "fast" | "derived",
    timestamp: float (optional)     // If omitted, return current state
}
```

**Response**:
```
StateQueryResponse {
    query_type: string,
    timestamp: float,
    state: SlowTimeState | FastTimeState | PhysiologyDerivedOutput,
    status: StatusCode
}
```

**Constraints**:
- Queries are **read-only**; external modules cannot modify state via query interface
- Historical queries supported only if logging enabled (see Section 6)

---

### 5.2 Parameter Query

**Request**:
```
ParameterQuery {}
```

**Response**:
```
ParameterQueryResponse {
    parameters: PhysiologyParameters
}
```

**Use Case**: Verification, debugging, or logging parameter values

---

## 6. Logging and Historical Data

### 6.1 Historical State Storage

If logging is enabled, module stores:

```
HistoricalRecord {
    t: float,
    slow_state: SlowTimeState,
    fast_state: FastTimeState,
    inputs: {I_slow: float, I_fast: float}
}
```

**Storage Frequency**:
- Slow-time: Every epoch
- Fast-time: Configurable (every step, decimated, or off)

**Access**: Via `HistoricalQuery` interface (details implementation-specific)

---

## 7. Data Exchange Timing

### 7.1 Epoch Structure

```
Epoch n:
    for i = 1 to N_fast:
        receive FastTimeInput(t_fast)
        update fast-time state
        emit FastTimeOutput(t_fast)
    
    receive SlowTimeInput(t_slow)
    update slow-time state
    emit SlowTimeOutput(t_slow)
```

where `N_fast = dt_slow / dt_fast`.

### 7.2 Synchronization

- **Fast-time updates** complete before slow-time update within each epoch
- **Slow-time state** propagates to fast-time parameters at start of next epoch
- **No mid-epoch parameter updates** allowed

---

## 8. Validity Rules

### 8.1 Input Validity

- **Range compliance**: All inputs within specified ranges
- **Temporal ordering**: `t_slow` and `t_fast` monotonically increasing
- **Type correctness**: All fields present and correctly typed

**Violation Handling**:
- Out-of-range: Clamp to valid range, emit warning, set status to `PHYS_INPUT_INVALID`
- Type error: Reject input, retain previous state, emit error
- Temporal violation: Reject input, log critical error

### 8.2 Output Validity

- **Consistency**: Output state variables satisfy all range constraints
- **Finite values**: No NaN or Inf in output
- **Monotonic time**: Output timestamps match input timestamps

**Guarantees**:
- If module status is `PHYS_OK` or `PHYS_STATE_CLAMP`, output is valid
- If status is `PHYS_NUMERIC_ERROR`, output should not be used

---

## 9. Upstream and Downstream Module Requirements

### 9.1 Upstream Requirements (Modules Providing Inputs)

- **Module 07 (Stressor Model)**: Provide `I_slow` and `I_fast` signals
- **Module 01 (TQP Core)**: Provide timing signals, initialization configuration

**Interface Contract**:
- Timing signals must respect `dt_slow` and `dt_fast`
- Stressor intensity values must be non-negative and finite

---

### 9.2 Downstream Requirements (Modules Consuming Outputs)

- **Module 06 (BDI Cycle)**: May query `C_eff` or `L_total` to modulate belief updates
- **Module 08 (Intervention Engine)**: May query physiological state to determine intervention triggers
- **Module 03 (Architecture)**: May query for visualization or state aggregation

**Interface Contract**:
- Downstream modules must use **read-only queries**; no direct state modification
- Downstream modules must handle `PHYS_NUMERIC_ERROR` gracefully (e.g., halt simulation or use fallback)

---

## 10. Versioning and Compatibility

### 10.1 Data Contract Version

Current version: **1.0**

**Compatibility Policy**:
- **Minor version changes** (1.0 → 1.1): Add optional fields; existing interfaces unchanged
- **Major version changes** (1.0 → 2.0): May change field names, types, or remove fields; requires downstream updates

### 10.2 Schema Evolution

- New state variables: Extend `PhysiologyState` struct, update documentation
- New parameters: Extend `PhysiologyParameters` struct, provide defaults
- New output fields: Add to output structs; downstream modules ignore unknown fields

---

## 11. Example Data Flow

### 11.1 Initialization

```
TQP_Core → PhysiologyModule:
    PhysiologyInitConfig {
        initial_state: {C_base: 1.0, L_cum: 0.0, R_cap: 1.0, A_resp: 0.0, L_trans: 0.0, xi: 1.0},
        parameters: {alpha_deg: 0.005, beta_rec: 0.05, ...},
        timescale_config: {dt_slow: 1.0, dt_fast: 0.04167}
    }

PhysiologyModule → TQP_Core:
    InitResponse {status: PHYS_OK}
```

### 11.2 Epoch Execution (n=1)

```
StressorModule → PhysiologyModule:
    FastTimeInput {t_fast: 0.0, I_fast: 2.5}

PhysiologyModule → (all subscribers):
    FastTimeOutput {t_fast: 0.0, state: {A_resp: 1.2, L_trans: 0.1, xi: 0.8}, status: PHYS_OK}

... (23 more fast-time steps) ...

StressorModule → PhysiologyModule:
    SlowTimeInput {t_slow: 1.0, I_slow: 0.3}

PhysiologyModule → (all subscribers):
    SlowTimeOutput {t_slow: 1.0, state: {C_base: 0.995, L_cum: 0.02, R_cap: 0.998}, status: PHYS_OK}
```

---

## 12. Data Contract Validation

Implementers must provide:

1. **Schema validators** for all input and output structs
2. **Range checkers** for all numeric fields
3. **Unit tests** exercising boundary conditions and invalid inputs
4. **Integration tests** verifying correct data flow with mock upstream/downstream modules

---

## 13. Document Control

**Version**: 1.0  
**Approval**: Data Architecture Review  
**Next Review**: After integration with Module 07 and Module 08

---

**End of Data Contract**
