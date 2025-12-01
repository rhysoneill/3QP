# Module 04: Slow–Fast Physiology Model — Technical Specification

**Version**: 1.0  
**Date**: December 2025  
**Status**: Baseline Specification

---

## 1. Overview

The Slow–Fast Physiology Model is a hybrid dynamical system component within the 3QP simulation framework. It maintains physiological state variables evolving on two distinct timescales:

- **Slow timescale**: Days to months; represents cumulative physiological drift
- **Fast timescale**: Minutes to hours; represents acute physiological responses

The module receives abstract input signals, updates internal state according to deterministic or stochastic rules, and outputs physiological state variables for consumption by downstream modules. The model is abstract and computational, not a medical or biological simulation.

---

## 2. Physiological State Variables

### 2.1 Slow-Time Variables

| Variable | Symbol | Domain | Description |
|----------|--------|--------|-------------|
| Baseline Capacity | `C_base` | [0, 1] | Normalized physiological capacity representing long-term functional reserve |
| Cumulative Load | `L_cum` | [0, ∞) | Dimensionless accumulated physiological burden; unbounded growth possible |
| Recovery Capacity | `R_cap` | [0, 1] | Normalized capacity for physiological recovery and adaptation |
| Drift Rate | `γ_drift` | ℝ | Rate of slow-time change in baseline capacity; can be positive (recovery) or negative (degradation) |

### 2.2 Fast-Time Variables

| Variable | Symbol | Domain | Description |
|----------|--------|--------|-------------|
| Acute Response | `A_resp` | [0, A_max] | Magnitude of fast-time physiological deviation from baseline |
| Transient Load | `L_trans` | [0, ∞) | Short-term load component that decays over fast timescale |
| Relaxation State | `ξ` | [0, 1] | Indicator of position in fast-time relaxation dynamics; 0 = fully perturbed, 1 = relaxed |

### 2.3 Auxiliary Variables

| Variable | Symbol | Domain | Description |
|----------|--------|--------|-------------|
| Total Load | `L_total` | [0, ∞) | Composite load computed as `L_total = L_cum + L_trans` |
| Effective Capacity | `C_eff` | [0, 1] | Effective physiological capacity computed as `C_eff = C_base * f(L_total)` |

---

## 3. Slow-Time Processes

### 3.1 Baseline Capacity Drift

Baseline capacity evolves according to:

```
dC_base/dt_slow = γ_drift - α_deg * g(L_cum) + β_rec * R_cap * h(C_base)
```

Where:
- `t_slow`: Slow-time variable (units: days)
- `α_deg`: Degradation coefficient
- `β_rec`: Recovery coefficient
- `g(L_cum)`: Monotonic increasing function of cumulative load (e.g., linear or power-law)
- `h(C_base)`: Recovery saturation function (e.g., `1 - C_base`)

**Constraints**:
- `C_base` must remain in [0, 1]; update clamped if necessary
- `γ_drift` may be externally modulated or internally computed

### 3.2 Cumulative Load Accumulation

Cumulative load increases with sustained stressor exposure:

```
dL_cum/dt_slow = ω_in * I_slow - ω_out * R_cap * L_cum
```

Where:
- `ω_in`: Accumulation rate coefficient
- `ω_out`: Dissipation rate coefficient
- `I_slow`: Slow-time stressor intensity input (dimensionless, externally provided)
- Second term represents recovery-mediated load reduction

**Constraints**:
- `L_cum ≥ 0` enforced at all times
- If `I_slow = 0` and `R_cap > 0`, `L_cum` decays exponentially

### 3.3 Recovery Capacity Dynamics

Recovery capacity may itself evolve:

```
dR_cap/dt_slow = κ_rec * (R_cap_max - R_cap) - κ_fatigue * L_cum * R_cap
```

Where:
- `κ_rec`: Recovery restoration rate
- `κ_fatigue`: Fatigue-induced degradation rate
- `R_cap_max`: Maximum recovery capacity (typically 1.0)

**Constraints**:
- `R_cap` bounded in [0, 1]
- If `L_cum = 0`, `R_cap` approaches `R_cap_max` asymptotically

### 3.4 Slow-Time Update Cycle

Slow-time updates occur at a fixed interval `Δt_slow` (e.g., 1 day simulation time).

**Algorithm**:
1. Retrieve current slow-time state: `C_base`, `L_cum`, `R_cap`
2. Retrieve slow-time input: `I_slow`
3. Compute derivatives using equations in 3.1–3.3
4. Apply numerical integration (e.g., Euler, RK4)
5. Enforce constraints (clamping, non-negativity)
6. Update state variables
7. Emit updated slow-time state

---

## 4. Fast-Time Processes

### 4.1 Acute Response Triggering

When a fast-time input `I_fast` is received (e.g., acute stressor pulse):

```
A_resp(t_0) = A_resp(t_0^-) + Δ_A * I_fast * (1 - ξ)
```

Where:
- `t_0`: Time of input arrival
- `Δ_A`: Sensitivity coefficient
- `ξ`: Current relaxation state (reduces response if system already perturbed)

**Constraints**:
- `A_resp ≤ A_max` enforced
- If `A_resp > A_max`, clamp to `A_max`

### 4.2 Fast-Time Relaxation Dynamics

Between acute inputs, fast-time variables relax toward baseline:

```
dA_resp/dt_fast = -λ_A * A_resp
dL_trans/dt_fast = -λ_L * L_trans + μ * A_resp
dξ/dt_fast = λ_ξ * (1 - ξ)
```

Where:
- `t_fast`: Fast-time variable (units: hours or minutes)
- `λ_A`, `λ_L`, `λ_ξ`: Relaxation rate constants
- `μ`: Coupling coefficient from acute response to transient load

**Constraints**:
- All relaxation rates positive
- `ξ` bounded in [0, 1]
- Exponential decay ensures bounded evolution

### 4.3 Fast-Time Update Cycle

Fast-time updates occur at intervals `Δt_fast` (e.g., 1 hour simulation time), nested within slow-time updates.

**Algorithm**:
1. Retrieve current fast-time state: `A_resp`, `L_trans`, `ξ`
2. Check for new fast-time input `I_fast`; if present, apply acute response rule (4.1)
3. Compute relaxation derivatives (4.2)
4. Apply numerical integration
5. Enforce constraints
6. Update fast-time state variables
7. Emit updated fast-time state

---

## 5. Coupling Between Timescales

### 5.1 Slow → Fast Coupling

Slow-time variables modulate fast-time dynamics:

- **Baseline capacity** `C_base` scales fast-time response sensitivity: `Δ_A = Δ_A_0 * C_base`
- **Cumulative load** `L_cum` increases fast-time relaxation time: `λ_A = λ_A_0 / (1 + σ * L_cum)`

### 5.2 Fast → Slow Coupling

Fast-time activity influences slow-time accumulation:

- **Transient load** `L_trans` contributes to total load: `L_total = L_cum + L_trans`
- If `L_trans` remains elevated over multiple fast-time cycles, slow-time accumulation accelerates

Coupling is **unidirectional or weakly bidirectional** to maintain numerical stability.

---

## 6. Parameterization Strategy

All model parameters are configurable at initialization:

| Parameter | Default Range | Description |
|-----------|---------------|-------------|
| `α_deg` | [0.001, 0.01] | Degradation coefficient (slow) |
| `β_rec` | [0.01, 0.1] | Recovery coefficient (slow) |
| `ω_in` | [0.1, 1.0] | Cumulative load accumulation rate |
| `ω_out` | [0.05, 0.5] | Cumulative load dissipation rate |
| `Δ_A_0` | [0.5, 2.0] | Baseline acute response sensitivity |
| `λ_A` | [0.1, 1.0] | Acute response relaxation rate (per hour) |
| `λ_L` | [0.05, 0.5] | Transient load relaxation rate (per hour) |
| `A_max` | [5.0, 10.0] | Maximum acute response magnitude |

**Parameter Sources**:
- Literature-derived ranges (computational models, not clinical data)
- Calibration via simulation experiments
- Expert elicitation (engineering judgment)

**No parameter values are biologically validated**; all are abstract computational tuning constants.

---

## 7. Model Constraints and Assumptions

### 7.1 Mathematical Constraints

- All state variables have defined bounds; updates enforce constraints
- Relaxation dynamics ensure asymptotic stability in absence of inputs
- No chaotic or divergent behavior under realistic parameter ranges

### 7.2 Physical Assumptions

- Slow and fast processes operate on separable timescales (timescale separation assumption)
- Coupling terms are weak and do not violate timescale separation
- Physiology represented as lumped-parameter system (no spatial heterogeneity)

### 7.3 Computational Assumptions

- Numerical integration stable for chosen `Δt_slow` and `Δt_fast`
- Stochastic elements (if present) use reproducible pseudo-random generation
- State transitions are Markovian (history-independent given current state)

---

## 8. Update Cycle Sequencing

### 8.1 Simulation Time Structure

Simulation advances in **epochs**:
- Each epoch = 1 slow-time step (`Δt_slow`)
- Each slow-time step contains `N_fast` fast-time steps: `N_fast = Δt_slow / Δt_fast`

### 8.2 Update Order Within Epoch

1. **Fast-time updates** (repeated `N_fast` times):
   - Receive fast-time input (if any)
   - Update fast-time state
   - Emit fast-time state snapshot
2. **Slow-time update** (once per epoch):
   - Aggregate fast-time activity (e.g., time-averaged `L_trans`)
   - Update slow-time state
   - Emit slow-time state snapshot
3. **State synchronization**:
   - Slow-time state propagates to fast-time parameters for next epoch

---

## 9. Interaction with TQP Core (Abstract)

### 9.1 Initialization

TQP Core provides:
- Initial state vector: `[C_base_0, L_cum_0, R_cap_0, A_resp_0, L_trans_0, ξ_0]`
- Parameter dictionary
- Timescale configuration: `Δt_slow`, `Δt_fast`

### 9.2 Runtime Interface

**Input Channels**:
- `I_slow(t)`: Slow-time stressor intensity signal
- `I_fast(t)`: Fast-time stressor intensity signal
- Time-step trigger signals

**Output Channels**:
- Slow-time state vector (updated each epoch)
- Fast-time state vector (updated each fast-time step)
- Derived quantities: `L_total`, `C_eff`

### 9.3 Query Interface

External modules may query:
- Current state variables (read-only)
- Historical state trajectories (if logging enabled)
- Derived metrics (e.g., time-averaged load)

---

## 10. Error Handling and Stability

### 10.1 Input Validation

- All inputs checked for type, range, and validity
- Out-of-range inputs clamped or rejected with error code
- Missing inputs replaced with default values (e.g., `I_slow = 0`)

### 10.2 Numerical Stability

- State variables clamped to valid ranges after each update
- Integration time steps chosen to satisfy stability criteria (e.g., Courant condition for explicit methods)
- Overflow/underflow checks on intermediate computations

### 10.3 Error Codes

| Code | Meaning |
|------|---------|
| `PHYS_OK` | Update successful |
| `PHYS_INPUT_INVALID` | Input out of range or malformed |
| `PHYS_STATE_CLAMP` | State variable clamped to enforce constraint (warning) |
| `PHYS_NUMERIC_ERROR` | Numerical instability detected (critical) |

---

## 11. Extensibility

### 11.1 Additional State Variables

Architecture supports addition of new slow or fast variables:
- Extend state vector
- Define update equations
- Specify coupling to existing variables
- Update data contract

### 11.2 Alternative Dynamics

Implementers may substitute:
- Different relaxation functions (e.g., bi-exponential decay)
- Nonlinear coupling terms
- Stochastic differential equation formulations

**Requirements**:
- Maintain timescale separation
- Preserve modularity (no cross-module dependencies)
- Document all modifications in `implementation_notes.md`

### 11.3 Integration with Stressors and Interventions

Future modules will:
- Provide `I_slow` and `I_fast` signals with specific semantic content
- Consume physiological state outputs to modulate stressor intensity or intervention efficacy

**Physiology module remains agnostic** to semantic meaning of inputs/outputs.

---

## 12. Verification Requirements

Implementers must verify:
1. State variables remain in specified bounds under all test inputs
2. Relaxation dynamics converge in absence of inputs
3. Slow-time variables exhibit expected drift direction given sustained `I_slow`
4. Fast-time variables respond to and relax from acute inputs
5. Coupling terms do not introduce instability
6. Numerical integration error within acceptable tolerance

---

## 13. Document Control

**Version**: 1.0  
**Approval**: Architecture Review Board  
**Next Review**: After Module 07 integration testing  

---

**End of Specification**
