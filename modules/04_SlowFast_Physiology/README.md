# Module 04: Slow-Fast Physiology Model

A hybrid dynamical system component for the 3QP simulation framework that maintains physiological state variables on two distinct timescales.

## Overview

The Slow-Fast Physiology Model implements a computational abstraction of physiological dynamics operating on:
- **Slow timescale** (days to months): Cumulative physiological drift, baseline capacity changes
- **Fast timescale** (minutes to hours): Acute stress responses, transient recovery

This module is **not a medical simulation** but rather a scientifically-grounded computational component designed for mission simulation and scenario analysis.

## Installation

```bash
cd modules/04_SlowFast_Physiology
pip install -e .
```

## Quick Start

```python
from slowfast_physiology import (
    PhysiologyModule,
    PhysiologyState,
    PhysiologyParameters,
    TimescaleConfig,
    PhysiologyInitConfig,
    SlowTimeInput,
    FastTimeInput
)

# Create initial state (healthy baseline)
initial_state = PhysiologyState(
    C_base=1.0,   # Baseline capacity
    L_cum=0.0,    # Cumulative load
    R_cap=1.0,    # Recovery capacity
    A_resp=0.0,   # Acute response
    L_trans=0.0,  # Transient load
    xi=1.0        # Relaxation state
)

# Define parameters
parameters = PhysiologyParameters(
    alpha_deg=0.005,
    beta_rec=0.05,
    omega_in=0.1,
    omega_out=0.05,
    kappa_rec=0.01,
    kappa_fatigue=0.02,
    Delta_A_0=1.0,
    lambda_A=0.5,
    lambda_L=0.2,
    lambda_xi=1.0,
    mu=0.1,
    A_max=5.0,
    sigma=0.1
)

# Configure timescales
timescale = TimescaleConfig(
    dt_slow=1.0,      # 1 day
    dt_fast=1.0/24.0, # 1 hour
    time_unit="days"
)

# Initialize module
config = PhysiologyInitConfig(
    initial_state=initial_state,
    parameters=parameters,
    timescale_config=timescale
)
module = PhysiologyModule(config)

# Run one epoch (24 fast steps + 1 slow step)
slow_input = SlowTimeInput(t_slow=1.0, I_slow=0.5)
fast_inputs = [
    FastTimeInput(t_fast=i/24.0, I_fast=0.0)
    for i in range(24)
]

slow_output, fast_outputs = module.run_epoch(slow_input, fast_inputs)
```

## Key Features

### State Variables

**Slow-Time Variables:**
- `C_base`: Baseline physiological capacity [0, 1]
- `L_cum`: Cumulative physiological load [0, ∞)
- `R_cap`: Recovery capacity [0, 1]

**Fast-Time Variables:**
- `A_resp`: Acute response magnitude [0, A_max]
- `L_trans`: Transient load [0, ∞)
- `xi`: Relaxation state [0, 1]

**Derived Quantities:**
- `L_total`: Total load (L_cum + L_trans)
- `C_eff`: Effective capacity (accounts for load)

### Dynamics

**Slow-Time Processes:**
- Baseline capacity drift with recovery and degradation
- Cumulative load accumulation and dissipation
- Recovery capacity restoration and fatigue

**Fast-Time Processes:**
- Acute response to stressor inputs
- Exponential relaxation dynamics
- Transient load coupling

**Coupling:**
- Slow → Fast: Baseline capacity modulates acute response sensitivity
- Fast → Slow: Transient activity feeds into cumulative load

## Module Structure

```
slowfast_physiology/
├── __init__.py                # Package exports
├── types.py                   # Data structures and enums
├── slow_time_engine.py        # Slow-time dynamics
├── fast_time_engine.py        # Fast-time dynamics
├── coupling_manager.py        # Timescale coupling
└── physiology_module.py       # Main module class
```

## Testing

Run the test suite:

```bash
cd modules/04_SlowFast_Physiology
pytest tests/ -v
```

Test coverage includes:
- Initialization and validation
- Slow-time dynamics
- Fast-time dynamics
- Coupling mechanisms
- Constraint enforcement
- Numerical stability

## Examples

Run the demonstration script:

```bash
python demo.py
```

This generates:
- Console output showing state evolution
- Plots of sustained stressor response
- Plots of acute stressor response
- Plots of recovery dynamics

## Architecture Integration

### Module Dependencies

**Upstream (provides inputs):**
- Module 01 (TQP Core): Initialization, timing signals
- Module 07 (Stressor Model): Stressor intensity signals

**Downstream (consumes outputs):**
- Module 06 (BDI Cycle): Reads physiological state
- Module 08 (Intervention Engine): Reads state for triggers

### Data Contracts

All inputs/outputs use typed data structures:
- `SlowTimeInput` / `SlowTimeOutput`
- `FastTimeInput` / `FastTimeOutput`
- `PhysiologyDerivedOutput`

Status codes indicate operation success:
- `PHYS_OK`: Normal operation
- `PHYS_INPUT_INVALID`: Invalid input received
- `PHYS_STATE_CLAMP`: State constrained (warning)
- `PHYS_NUMERIC_ERROR`: Numerical instability (critical)

## Scientific Foundation

This implementation is based on:
- **Hybrid dynamical systems theory** (multiple timescale analysis)
- **Allostatic load concept** (cumulative physiological burden)
- **Stress-recovery models** (impulse-response dynamics)

See `versions/theory_basis.md` for detailed theoretical background.

## Limitations

This module:
- Is **not a medical model** (no clinical validation)
- Uses **dimensionless abstract parameters** (not biological measurements)
- Represents **lumped physiological state** (no organ-specific detail)
- Is intended for **engineering simulation**, not medical prediction

## Documentation

Complete specification documents:
- `versions/spec.md`: Technical specification
- `versions/theory_basis.md`: Scientific foundation
- `versions/data_contract.md`: Interface definitions
- `versions/implementation_notes.md`: Implementation guidance

## Version

Current version: **1.0.0**

## License

Part of the 3QP project.

## Contact

For questions about this module, refer to the architecture review board or systems engineering lead.
