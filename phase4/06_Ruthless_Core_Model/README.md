# Ruthless Core Model

## Overview

The **Ruthless Core Model** is a minimal dynamical engine for generating third quarter trajectories in long-duration isolated confined environments. Unlike Phase 4 Workstreams 1-5 (which are pure architecture layers), this is a **computational module** that implements simple differential equations to simulate psychological and social dynamics over time.

## Purpose

This model provides:

- **Synthetic trajectory generation** for calibration and validation
- **Transparent, interpretable dynamics** with explicit parameters
- **Baseline third quarter behavior** for comparison with more complex models
- **Integration point** for Phase 4 trajectory analysis and validation

## Model Overview

### State Variables

The model tracks four state variables over discrete time steps (days):

1. **M(t)** - Monotony: Accumulates over time, reduced by novelty events
2. **S(t)** - Psychological Strain: Driven by workload and monotony, moderated by recovery
3. **Q(t)** - Third Quarter Pressure: Gaussian hump centered in third quarter of mission
4. **C(t)** - Social Cohesion: Eroded by strain and TQ pressure, boosted by shared successes

### Update Equations

**Monotony:**
```
M(t+1) = M(t) + m_base - m_novelty * novelty_event(t)
```

**Strain:**
```
S(t+1) = S(t) + s_workload * workload(t) + s_mono * M(t) - s_recovery * recovery(t)
```

**Third Quarter Pressure:**
```
Q(t) = q_peak * exp(-(r - q_center)^2 / (2 * q_width^2))
where r = t / T (mission progress fraction)
```

**Cohesion:**
```
C(t+1) = C(t) - c_strain * S(t) - c_q * Q(t) + c_shared_success * success_event(t)
```

### Input Schedules

The model accepts daily input sequences:

- **workload(t)**: Workload intensity [0, 1]
- **recovery(t)**: Recovery opportunity [0, 1]
- **novelty_event(t)**: Binary novelty indicator {0, 1}
- **success_event(t)**: Binary shared success indicator {0, 1}

If not provided, reasonable default schedules are generated automatically.

## Installation

No installation required. The module is self-contained in:

```
phase4/06_Ruthless_Core_Model/
├── __init__.py
├── ruthless_core.py       # Core model implementation
├── demo.py                # Demonstration script
├── example_config.yaml    # Example configuration
└── README.md             # This file
```

## Quick Start

### Running the Demo

```bash
cd phase4/06_Ruthless_Core_Model
python demo.py
```

This will:
- Run a 200-day simulation
- Display trajectory statistics
- Show Phase 4 integration examples
- Demonstrate parameter exploration

### Basic Usage

```python
from ruthless_core import RuthlessCoreConfig, RuthlessCoreModel

# Create configuration
config = RuthlessCoreConfig(
    mission_length_days=200,
    q_center=0.70,  # Third quarter at 70% mission progress
    q_peak=0.5,
    q_width=0.15,
)

# Run simulation
model = RuthlessCoreModel(config)
output = model.run()

# Access results
print(f"Final cohesion: {output.cohesion[-1]:.3f}")
print(f"Min cohesion day: {output.days[output.cohesion.index(min(output.cohesion))]}")
```

### Phase 4 Integration

```python
from ruthless_core import (
    RuthlessCoreConfig,
    RuthlessCoreModel,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)

# Run model
config = RuthlessCoreConfig(mission_length_days=180)
model = RuthlessCoreModel(config)
output = model.run()

# Convert to Phase 4 formats
encoded_states = to_phase4_encoded_states(output)
trajectory_result = to_phase4_trajectory_result(output)

# Use with Phase 4 trajectory analysis
# (encoded_states can be passed to WS3 pattern recognition)
# (trajectory_result can be validated with WS5 validation harness)
```

## Configuration

All parameters are configured via `RuthlessCoreConfig`. See `example_config.yaml` for documentation of each parameter.

### Key Parameters for Third Quarter Calibration

- **q_center**: Position of TQ peak (0.66-0.75 typical for third quarter)
- **q_peak**: Amplitude of TQ pressure (0.3-0.8 typical range)
- **q_width**: Spread of TQ effect (0.10-0.20 typical range)
- **c_strain**: How much strain erodes cohesion
- **c_q**: How much TQ pressure directly impacts cohesion

## Calibration

Use the calibration notebook for visual parameter tuning:

```bash
jupyter notebook ../../../notebooks/ruthless_core_calibration.ipynb
```

The notebook provides:
- Comparison against synthetic "real" cohesion data
- Interactive parameter adjustment
- Visual plots of all state variables
- Error metrics (MSE, etc.)

## Design Principles

1. **Simplicity**: No hidden states, no complex feedback loops
2. **Transparency**: All equations are explicit and documented
3. **Calibratability**: All parameters are exposed and tunable
4. **Interpretability**: State variables map to qualitative concepts
5. **Phase 4 Compatible**: Outputs integrate cleanly with existing Phase 4 pipeline

## Not Included

This is **not** a full BDI agent model. It does not include:

- Belief-desire-intention reasoning
- Social network dynamics
- Intervention engine logic
- Stressor model complexity
- Module 1-12 integration

This model is a minimal dynamical core designed to sit **underneath** the full agentic architecture, providing a simple, calibratable baseline for third quarter phenomena.

## API Reference

### Classes

**RuthlessCoreConfig**
- Configuration dataclass with all model parameters
- Auto-generates default input schedules if not provided

**RuthlessCoreModel**
- Main simulation engine
- `__init__(config)`: Initialize with configuration
- `run() -> RuthlessCoreOutput`: Run full simulation

**RuthlessCoreOutput**
- Output container with time series data
- Fields: `days`, `strain`, `cohesion`, `monotony`, `tq_pressure`, `metadata`
- `to_dict()`: Convert to dictionary for serialization

### Functions

**to_phase4_encoded_states(output) -> List[Dict]**
- Convert output to Phase 4 WS2 encoded states format
- Returns list of state dicts, one per day

**to_phase4_trajectory_result(output, archetype_id) -> Dict**
- Convert output to Phase 4 trajectory classification result
- Auto-detects third quarter archetype based on cohesion minimum

## Version

**0.1.0** - Initial implementation (December 2025)

## Author

3QP Development Team

## Related Documentation

- Phase 4 Unified Specification: `phase4/PHASE4_UNIFIED_SPECIFICATION.md`
- Calibration Notebook: `notebooks/ruthless_core_calibration.ipynb`
- Phase 3 Trajectory Analysis: `phase3/05_Trajectory_Analysis/`
