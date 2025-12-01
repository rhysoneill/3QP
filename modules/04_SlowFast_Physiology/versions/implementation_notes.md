# Module 04: Slow–Fast Physiology Model — Implementation Notes

**Version**: 1.0  
**Date**: December 2025

---

## 1. Purpose and Audience

This document provides guidance for engineers implementing the Slow–Fast Physiology Model specified in `spec.md`. It addresses design choices, data structure recommendations, numerical considerations, and architectural constraints. This is **not executable code**, but rather architectural guidance to support consistent, maintainable, and correct implementations.

---

## 2. Overall Architecture

### 2.1 Module Structure

Recommended modular decomposition:

```
PhysiologyModule
│
├── Initialization
│   ├── ConfigValidator
│   ├── StateInitializer
│   └── ParameterLoader
│
├── SlowTimeEngine
│   ├── SlowStateUpdater
│   ├── DriftComputer
│   └── LoadAccumulator
│
├── FastTimeEngine
│   ├── FastStateUpdater
│   ├── AcuteResponder
│   └── RelaxationComputer
│
├── CouplingManager
│   ├── SlowToFastCoupler
│   └── FastToSlowCoupler
│
├── OutputManager
│   ├── StateEmitter
│   ├── DerivedQuantityComputer
│   └── StatusReporter
│
├── QueryInterface
│   └── StateQueryHandler
│
└── Logger (optional)
    └── HistoricalRecorder
```

### 2.2 Data Flow

1. **Initialization Phase**:
   - Validate configuration
   - Initialize state vectors
   - Set up parameters

2. **Runtime Phase** (per epoch):
   - Loop over `N_fast` fast-time steps:
     - Receive `FastTimeInput`
     - Update fast-time state
     - Emit `FastTimeOutput`
   - Receive `SlowTimeInput`
   - Update slow-time state
   - Emit `SlowTimeOutput`
   - Synchronize coupling for next epoch

3. **Query Phase** (on-demand):
   - Respond to state or parameter queries
   - Return historical data if logging enabled

---

## 3. Data Structures

### 3.1 State Representation

Recommended internal representation:

```
struct PhysiologyState {
    // Slow-time state
    float C_base;
    float L_cum;
    float R_cap;
    float gamma_drift;  // Cached drift rate
    
    // Fast-time state
    float A_resp;
    float L_trans;
    float xi;
    
    // Derived quantities (cached)
    float L_total;
    float C_eff;
    
    // Metadata
    float t_slow;
    float t_fast;
    int epoch_number;
}
```

**Design Rationale**:
- Single unified state struct simplifies state management
- Cached derived quantities avoid recomputation
- Metadata fields support logging and debugging

### 3.2 Parameter Storage

```
struct PhysiologyParameters {
    // Slow-time
    float alpha_deg;
    float beta_rec;
    float omega_in;
    float omega_out;
    float kappa_rec;
    float kappa_fatigue;
    float R_cap_max;
    
    // Fast-time
    float Delta_A_0;
    float lambda_A;
    float lambda_L;
    float lambda_xi;
    float mu;
    float A_max;
    
    // Coupling
    float sigma;
}
```

**Immutability**: Parameters should be immutable after initialization in baseline version. If runtime parameter updates are needed (future extension), implement via configuration update interface with validation.

### 3.3 Timescale Configuration

```
struct TimescaleConfig {
    float dt_slow;
    float dt_fast;
    int N_fast;  // Computed: dt_slow / dt_fast
}
```

**Validation**: Constructor must verify `N_fast` is an integer and `dt_fast < dt_slow`.

---

## 4. Numerical Integration

### 4.1 Integration Method Selection

**Slow-Time Updates**:
- **Recommended**: Forward Euler for simplicity, or RK4 for accuracy
- **Justification**: Slow-time dynamics are not stiff; explicit methods acceptable
- **Time Step**: `dt_slow` typically 1 day; sufficiently small for stable integration

**Fast-Time Updates**:
- **Recommended**: Forward Euler with adaptive step control, or exponential integrators for relaxation terms
- **Justification**: Fast-time relaxation has exponential form; can exploit analytic solution
- **Time Step**: `dt_fast` typically 1 hour; verify stability via relaxation rate analysis

### 4.2 Stability Analysis

For exponential relaxation $\frac{dy}{dt} = -\lambda y$, Forward Euler is stable if:

$$
\Delta t < \frac{2}{\lambda}
$$

**Guideline**: Choose `dt_fast` such that `dt_fast * lambda_A < 1.0` for all relaxation rates.

**Example**:
- If `lambda_A = 0.5 / hour`, then `dt_fast < 2 hours` for stability
- Chosen `dt_fast = 1 hour` satisfies this with margin

### 4.3 Analytic Relaxation (Optimization)

For pure relaxation intervals (no input), use exact solution:

$$
y(t + \Delta t) = y(t) \cdot e^{-\lambda \Delta t}
$$

**Advantage**: Unconditionally stable, no numerical error accumulation

**Applicability**: Fast-time relaxation dynamics; slow-time if drift term is approximately constant

---

## 5. Constraint Enforcement

### 5.1 State Variable Clamping

After each update, enforce constraints:

```
function clamp_state(state):
    state.C_base = clamp(state.C_base, 0.0, 1.0)
    state.L_cum = max(state.L_cum, 0.0)
    state.R_cap = clamp(state.R_cap, 0.0, 1.0)
    state.A_resp = clamp(state.A_resp, 0.0, params.A_max)
    state.L_trans = max(state.L_trans, 0.0)
    state.xi = clamp(state.xi, 0.0, 1.0)
    
    if any clamping occurred:
        status = PHYS_STATE_CLAMP
    else:
        status = PHYS_OK
    
    return state, status
```

**Logging**: Record clamping events for diagnostics; frequent clamping indicates parameter tuning issues.

### 5.2 Input Validation

```
function validate_input(input, min_val, max_val):
    if input is NaN or Inf:
        return default_value, PHYS_INPUT_INVALID
    if input < min_val or input > max_val:
        return clamp(input, min_val, max_val), PHYS_INPUT_INVALID
    return input, PHYS_OK
```

**Behavior**: Invalid inputs trigger warning but allow simulation to continue with clamped values.

---

## 6. Coupling Implementation

### 6.1 Slow → Fast Coupling

At the start of each epoch, update fast-time parameters based on slow-time state:

```
function update_fast_params(slow_state, base_params):
    // Modulate acute response sensitivity by baseline capacity
    Delta_A = base_params.Delta_A_0 * slow_state.C_base
    
    // Increase relaxation time if cumulative load is high
    lambda_A = base_params.lambda_A / (1.0 + base_params.sigma * slow_state.L_cum)
    
    return {Delta_A, lambda_A}
```

**Timing**: Execute once per epoch, before first fast-time step.

### 6.2 Fast → Slow Coupling

Aggregate fast-time activity for slow-time update:

```
function aggregate_fast_activity(fast_states_in_epoch):
    // Time-averaged transient load over the epoch
    L_trans_avg = mean([state.L_trans for state in fast_states_in_epoch])
    
    return L_trans_avg
```

**Usage**: Include `L_trans_avg` in slow-time load accumulation equation.

---

## 7. Error Handling Strategy

### 7.1 Error Hierarchy

1. **Warnings** (`PHYS_STATE_CLAMP`, `PHYS_INPUT_INVALID`):
   - Log event
   - Continue simulation
   - Set status flag in output

2. **Critical Errors** (`PHYS_NUMERIC_ERROR`):
   - Halt update
   - Retain previous valid state
   - Emit error status
   - Notify upstream controller (e.g., TQP Core)

### 7.2 Numeric Error Detection

```
function detect_numeric_error(state):
    if any field in state is NaN or Inf:
        return true
    if state violates invariant (e.g., negative when must be positive):
        return true
    return false
```

**Invariants to Check**:
- `L_cum >= 0`
- `L_trans >= 0`
- All bounded variables in valid ranges after clamping

### 7.3 Graceful Degradation

If numeric error detected:
- Emit last valid state with error status
- Optionally switch to "safe mode": freeze state, stop updates, await external reset

---

## 8. Performance Considerations

### 8.1 Computational Complexity

- **Per fast-time step**: O(1) (fixed number of state variables and operations)
- **Per epoch**: O(N_fast) = O(24) for typical configuration
- **Per simulation day**: O(1) slow-time update + O(24) fast-time updates ≈ O(1)

**Scalability**: Module scales linearly with simulation duration; no memory growth if logging disabled.

### 8.2 Memory Footprint

- **State**: ~10 floats × 4 bytes = 40 bytes
- **Parameters**: ~13 floats × 4 bytes = 52 bytes
- **Logging** (if enabled): ~50 bytes per record × N_records

**Recommendation**: Implement circular buffer for logging to cap memory usage.

### 8.3 Optimization Opportunities

- **Vectorization**: If simulating multiple agents, vectorize state updates across agents
- **Analytic solutions**: Use closed-form exponential relaxation to skip numerical integration
- **Lazy computation**: Compute derived quantities (`L_total`, `C_eff`) only on query, not every step

---

## 9. Testing and Validation

### 9.1 Unit Tests

**Required Tests**:

1. **Initialization**:
   - Valid configuration → successful initialization
   - Invalid configuration → error code, no crash

2. **State Update**:
   - Zero input → state converges to equilibrium
   - Constant input → state reaches steady state
   - Impulse input → fast-time relaxation observed

3. **Constraint Enforcement**:
   - State exceeding bounds → clamping applied
   - Negative loads → reset to zero

4. **Coupling**:
   - Slow-time drift affects fast-time parameters
   - Fast-time activity feeds back to slow-time load

### 9.2 Integration Tests

**Scenarios**:

1. **Long-term drift**: Sustained `I_slow` > 0 → `L_cum` increases, `C_base` decreases
2. **Acute response and recovery**: `I_fast` pulse → `A_resp` spikes, then relaxes
3. **Multi-epoch stability**: Run 100 epochs with moderate inputs → no divergence

### 9.3 Verification Metrics

- **Stability**: No unbounded growth in any state variable
- **Monotonicity**: Relaxation dynamics decrease monotonically
- **Conservation**: If no inputs, total load dissipates over time
- **Coupling consistency**: Fast-time parameters updated exactly once per epoch

---

## 10. Versioning and Evolution

### 10.1 Version Numbering

- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Incompatible changes to data contract or dynamics
- **Minor**: Backward-compatible additions (e.g., new optional parameters)
- **Patch**: Bug fixes, no interface changes

### 10.2 Deprecation Policy

- Deprecated features supported for at least 2 minor versions
- Warning issued when deprecated interface used
- Documentation updated to note deprecation and migration path

### 10.3 Extension Points

Future extensions may add:

- **Additional state variables**: Extend state struct, update update rules
- **Nonlinear dynamics**: Replace linear ODEs with nonlinear functions
- **Stochastic terms**: Add noise to drift or relaxation equations
- **Multi-agent support**: Vectorize state arrays, parallelize updates

**Constraint**: All extensions must preserve modularity and avoid introducing behavioral or cognitive content.

---

## 11. Architectural Constraints

### 11.1 Module Isolation

The physiology module **MUST NOT**:

- Call functions from behavior, cognition, or social modules
- Access global state outside its own state struct
- Make assumptions about stressor semantics (e.g., "workload", "isolation")
- Implement intervention logic (e.g., when to apply countermeasures)

**Enforcement**: Static analysis or manual code review to verify no cross-module dependencies.

### 11.2 Interface Discipline

- All inputs via defined input structs (`SlowTimeInput`, `FastTimeInput`)
- All outputs via defined output structs (`SlowTimeOutput`, `FastTimeOutput`)
- No side channels (e.g., global variables, file I/O for data exchange)

**Rationale**: Maintains testability, modularity, and replaceability.

### 11.3 No Behavioral Content

The physiology module represents **physiological state**, not:

- Performance (e.g., task success rate)
- Mood or emotion
- Cognitive capacity (that is a behavioral module's responsibility)
- Social relationships

**Downstream modules** may interpret physiological state as inputs to behavioral models, but the physiology module itself remains semantically neutral.

---

## 12. Documentation Requirements

### 12.1 Inline Code Documentation

Implementers should document:

- State variable meanings and units
- Parameter definitions and expected ranges
- Update equation derivations (reference to `spec.md`)
- Clamping and constraint enforcement logic

### 12.2 API Documentation

Generate API docs from code:

- Function signatures
- Input/output types
- Error codes
- Example usage

### 12.3 Change Log

Maintain a change log documenting:

- Version number
- Date
- Changes made (features added, bugs fixed, API changes)
- Migration notes for breaking changes

---

## 13. Known Risks and Mitigations

### 13.1 Risk: Parameter Sensitivity

**Issue**: Small changes in parameters may cause large changes in long-term behavior.

**Mitigation**:
- Sensitivity analysis during calibration
- Document expected state ranges for nominal parameters
- Implement parameter bounds checking

### 13.2 Risk: Timescale Separation Violation

**Issue**: If `dt_fast` and `dt_slow` are too close, hybrid model assumptions break down.

**Mitigation**:
- Enforce `dt_slow / dt_fast >= 10` in validation
- Document timescale separation requirements in `spec.md`

### 13.3 Risk: Numeric Instability

**Issue**: Explicit integration may become unstable for stiff equations or large time steps.

**Mitigation**:
- Use stability-aware time step selection
- Implement adaptive step control (future enhancement)
- Switch to implicit methods if stiffness detected

### 13.4 Risk: Misinterpretation of Outputs

**Issue**: Downstream modules may treat abstract physiological state as medical data.

**Mitigation**:
- Clearly document abstract nature in all interfaces
- Use dimensionless units and avoid medical terminology in variable names
- Include disclaimers in output documentation

---

## 14. Collaboration with Other Modules

### 14.1 Integration with Module 01 (TQP Core)

- **Core provides**: Initialization, timing signals, orchestration
- **Physiology provides**: State updates on schedule
- **Interface**: Clean data contracts, no shared state

### 14.2 Integration with Module 07 (Stressor Model)

- **Stressor provides**: `I_slow` and `I_fast` signals
- **Physiology provides**: State for stressor modulation (future)
- **Constraint**: Physiology never computes stressor intensity; only receives it

### 14.3 Integration with Module 08 (Intervention Engine)

- **Intervention provides**: Parameter modulation requests (future)
- **Physiology provides**: State for intervention triggering
- **Constraint**: Physiology does not decide when interventions occur

---

## 15. Future Work and Extensibility

### 15.1 Planned Enhancements

- **Circadian rhythm modeling**: Add 24-hour periodic forcing term
- **Stochastic dynamics**: Add Wiener process noise to drift equations
- **Multi-compartment models**: Extend to multiple interacting physiological subsystems (e.g., metabolic, neuromuscular)

### 15.2 Research Questions

- Optimal parameter calibration strategy given sparse data
- Impact of timescale ratio on model fidelity
- Sensitivity of long-term predictions to initial conditions

### 15.3 Integration Roadmap

- **Phase 1**: Standalone physiology module with mock inputs (complete)
- **Phase 2**: Integration with stressor model (Module 07)
- **Phase 3**: Integration with intervention engine (Module 08)
- **Phase 4**: Full 3QP system integration and validation

---

## 16. References for Implementers

### 16.1 Numerical Methods

- Press et al., "Numerical Recipes" (integration methods, stability)
- Hairer & Wanner, "Solving Ordinary Differential Equations" (stiff equations, adaptive methods)

### 16.2 Hybrid Dynamical Systems

- Kuehn, "Multiple Time Scale Dynamics" (timescale separation theory)
- Goebel et al., "Hybrid Dynamical Systems" (formal treatment)

### 16.3 Software Engineering

- Martin, "Clean Architecture" (modularity, dependency inversion)
- Gamma et al., "Design Patterns" (strategy, observer patterns for module communication)

---

## 17. Contact and Support

For implementation questions or clarification:

- Refer first to `spec.md` and `data_contract.md`
- Consult `theory_basis.md` for conceptual foundation
- Escalate ambiguities to architecture review board

---

## 18. Document Control

**Version**: 1.0  
**Status**: Baseline Implementation Guidance  
**Next Review**: After first implementation complete  
**Approval**: Systems Engineering Lead

---

**End of Implementation Notes**
