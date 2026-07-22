# Phase 5 Runtime Integration Harness

## Overview

The Phase 5 runtime harness provides a clean, minimal wrapper around the **Ruthless Core Model** (Phase 4) that enables end-to-end mission simulation with integrated logging, validation, and interactive visualization.

**Critical Design Principle:** Phase 5 does NOT replace or modify the Ruthless Core engine. It wraps it. The core engine remains frozen and unchanged in `/phase4/06_Ruthless_Core_Model/`.

## Architecture

```
Phase 5 Runtime Layer (this directory)
    ↓ orchestrates ↓
Ruthless Core Model (phase4/06_Ruthless_Core_Model/ruthless_core.py)
    ↓ produces ↓
RuthlessCoreOutput
    ↓ wrapped by ↓
Phase 4 Adapters (to_phase4_encoded_states, to_phase4_trajectory_result)
    ↓ consumed by ↓
Logger & Validator
    ↓ writes ↓
Output Files (JSON, summary, validation)
    ↓ read by ↓
dashboard.py (Streamlit Mission Control Room)
```

## Files

| File | Purpose |
|------|---------|
| `run_simulation.py` | CLI entry point — batch + twin mode |
| `twin_runner.py` | Day-by-day twin mode orchestrator |
| `mission_runner.py` | Wraps `RuthlessCoreModel.run()`, returns `MissionResult` |
| `runtime_config.py` | `RuntimeConfig` dataclass, JSON serialization |
| `logger.py` | Writes output JSON files to `output/` |
| `validator.py` | Checks trajectory against expected TQP patterns |
| `dashboard.py` | Streamlit Mission Control Room — 7-tab interactive visualization |
| `.streamlit/config.toml` | Dark theme config for dashboard |

## Components

### 1. `runtime_config.py`
Configuration management for the runtime layer.

- **RuntimeConfig**: Dataclass for mission parameters and runtime options
- Supports JSON serialization/deserialization
- Controls logging, validation, verbosity
- Allows optional override of RuthlessCoreConfig parameters

**Example:**
```python
from runtime_config import RuntimeConfig

config = RuntimeConfig(
    mission_name="mars_analog_mission",
    mission_length_days=180,
    output_dir="output",
    enable_validation=True,
    verbose=True
)
```

### 2. `mission_runner.py`
Core orchestrator that runs the Ruthless Core Model.

- **MissionRunner**: Wraps RuthlessCoreModel execution
- Creates RuthlessCoreConfig from RuntimeConfig
- Calls `model.run()` to generate trajectory
- Applies Phase 4 adapters (encoded states, trajectory classification)
- Returns **MissionResult** with all outputs

**Key Principle:** This module **imports** and **calls** the existing Ruthless Core Model. It does NOT reimplement or modify it.

**Example:**
```python
from runtime_config import RuntimeConfig
from mission_runner import run_mission

config = RuntimeConfig(mission_length_days=200)
result = run_mission(config)

print(f"Trajectory: {result.trajectory_result['label']}")
print(f"Min cohesion: {min(result.core_output.cohesion):.3f}")
```

### 3. `logger.py`
Output management for simulation results.

- **SimulationLogger**: Writes outputs to `/output/` directory
- Generates multiple output formats:
  - `{mission_name}_timeseries.json`: Full time series data
  - `{mission_name}_summary.json`: Key metrics and findings
  - `{mission_name}_encoded_states.json`: Phase 4 WS2 format
  - `{mission_name}_trajectory.json`: Trajectory classification
- Prints console summary with key metrics

**Example:**
```python
from logger import write_mission_outputs

write_mission_outputs(result, output_dir="output", verbose=True)
```

### 4. `validator.py`
Trajectory validation against expected TQP patterns.

- **TrajectoryValidator**: Checks for third quarter dynamics
- Validation checks:
  - ✓ Cohesion minimum in third quarter range (50-90% mission progress)
  - ✓ TQ pressure peak aligned with cohesion minimum
  - ✓ Trajectory archetype correctly classified as "third_quarter"
  - ✓ Cohesion dip magnitude sufficient (>0.15)
- Writes validation report: `{mission_name}_validation.json`

**Example:**
```python
from validator import validate_mission_result

validation = validate_mission_result(result, output_dir="output")
print(f"Status: {validation['overall_status']}")  # PASS or FAIL
```

### 5. `run_simulation.py`
Command-line entrypoint for end-to-end simulation.

Complete workflow:
1. Load runtime configuration (from file or CLI args)
2. Run mission via `mission_runner`
3. Log outputs via `logger`
4. Validate trajectory via `validator`
5. Print summary and exit

**Usage:**
```bash
# Run with defaults
python run_simulation.py

# Run with custom config
python run_simulation.py --config mission_config.json

# Run with CLI overrides
python run_simulation.py --mission-name test --days 150

# Run quietly
python run_simulation.py --quiet

# Skip validation
python run_simulation.py --no-validation
```

## How It Works

### Data Flow

1. **RuntimeConfig** specifies mission parameters
2. **MissionRunner** converts RuntimeConfig → RuthlessCoreConfig
3. **RuthlessCoreModel.run()** generates RuthlessCoreOutput
4. **Phase 4 adapters** transform output to Phase 4 formats
5. **MissionResult** packages everything together
6. **Logger** writes outputs to files
7. **Validator** checks trajectory patterns
8. Console prints summary

### Integration with Ruthless Core

The runtime harness **imports** the Ruthless Core Model as a frozen dependency:

```python
# mission_runner.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase4" / "06_Ruthless_Core_Model"))
from ruthless_core import (
    RuthlessCoreModel,
    RuthlessCoreConfig,
    RuthlessCoreOutput,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)
```

**No modifications** are made to the core engine. The runtime layer only:
- Configures it
- Runs it
- Wraps its outputs

### Phase 4 Integration

The runtime harness uses the **existing Phase 4 adapters** built into `ruthless_core.py`:

- `to_phase4_encoded_states()`: Converts to WS2 encoded state format
- `to_phase4_trajectory_result()`: Creates trajectory classification result

These adapters are **already implemented** in the Ruthless Core module and remain unchanged.

## Quick Start

### Basic Usage

```bash
cd integration/runtime
python run_simulation.py
```

This will:
- Run a 200-day baseline mission
- Write outputs to `output/`
- Validate third quarter trajectory
- Print summary to console

### Custom Configuration

Create a JSON config file:

```json
{
  "mission_name": "my_mission",
  "mission_length_days": 180,
  "output_dir": "my_output",
  "enable_validation": true,
  "verbose": true,
  "core_config_override": {
    "q_center": 0.65,
    "q_peak": 0.6
  }
}
```

Run with config:

```bash
python run_simulation.py --config my_mission.json
```

### Programmatic Usage

```python
from runtime_config import RuntimeConfig
from mission_runner import run_mission
from logger import write_mission_outputs
from validator import validate_mission_result

# Setup
config = RuntimeConfig(
    mission_name="test_mission",
    mission_length_days=200,
    output_dir="output"
)

# Run
result = run_mission(config)

# Log
write_mission_outputs(result)

# Validate
validation = validate_mission_result(result)

# Check
assert validation["overall_status"] == "PASS"
```

## Output Files

After running a simulation, the `output/` directory contains:

```
output/
  ├── {mission_name}_timeseries.json       # Full time series (days, strain, cohesion, etc.)
  ├── {mission_name}_summary.json          # Key metrics and findings
  ├── {mission_name}_encoded_states.json   # Phase 4 WS2 encoded states
  ├── {mission_name}_trajectory.json       # Trajectory classification
  └── {mission_name}_validation.json       # Validation report
```

### Example Summary

```json
{
  "mission_name": "baseline_tqp_mission",
  "mission_length_days": 200,
  "trajectory_archetype": "third_quarter",
  "trajectory_label": "Third Quarter Trajectory",
  "metrics": {
    "cohesion": {
      "initial": 1.0,
      "final": 0.823,
      "minimum": 0.547,
      "minimum_day": 124,
      "minimum_progress": 0.62
    },
    "tq_pressure": {
      "peak": 0.55,
      "peak_day": 124,
      "peak_progress": 0.62
    }
  }
}
```

### Example Validation Report

```json
{
  "overall_status": "PASS",
  "checks": [
    {
      "check_id": "tq_range",
      "description": "Cohesion minimum in third quarter range",
      "passed": true,
      "expected": "50% - 90%",
      "actual": "62.0%"
    },
    {
      "check_id": "archetype",
      "description": "Trajectory archetype classification",
      "passed": true,
      "expected": "third_quarter",
      "actual": "third_quarter"
    }
  ]
}
```

## Design Principles

### 1. Wrapper, Not Replacement
Phase 5 wraps the existing Ruthless Core Model. It does NOT:
- Reimplement the dynamics equations
- Modify the core engine code
- Create new behavioral models

### 2. Minimal and Transparent
The runtime layer adds only what's necessary:
- Configuration loading
- Execution orchestration
- Output formatting
- Validation checking

### 3. Clean Separation
- `/modules`: Frozen, complete modules (untouched)
- `/phase4/06_Ruthless_Core_Model`: Core dynamics engine (frozen)
- `/integration/runtime`: Phase 5 runtime wrapper (this directory)

### 4. Integration First
Uses existing Phase 4 adapters and validation harness components. No reinvention.

## Relationship to 3QP Modules

The runtime harness integrates with the 3QP ecosystem:

- **Module 01 (TQP Core)**: Uses TQP concepts (third quarter, monotony)
- **Module 03 (Architecture)**: Follows domain-based state representation
- **Module 09 (Logging System)**: Could be extended to use formal logging module
- **Module 10 (Validation)**: Uses validation concepts and trajectory classification

But it does **NOT** require or import these modules. It only depends on:
- Phase 4 Ruthless Core Model
- Standard library (json, pathlib, datetime)

## Dashboard: Mission Control Room

`dashboard.py` is a 7-tab Streamlit application that reads simulation output JSON files and provides an interactive mission-control-style analysis interface.

**Stack**: Streamlit 1.41.1 + Plotly 6.5.2. Dark theme via `.streamlit/config.toml`.

### Quick Start

```bash
# 1. Run a simulation first
python run_simulation.py --mode twin --crew-preset high_cohesion_team --days 200

# 2. Launch the dashboard
streamlit run dashboard.py --server.fileWatcherType none
# Opens at http://localhost:8501
```

The dashboard auto-detects simulation output files in `output/` and populates a mission selector in the sidebar.

### Tabs

| Tab | Contents |
|-----|----------|
| **Mission Overview** | Physics 2×2 (strain/cohesion/monotony/TQ pressure), workload vs recovery area fill, novelty + success impulse bars, phase KPI breakdown, TQP emergence score |
| **Agent Deep-Dive** | Big Five radar, 8-metric internal state (selectable), 4-key belief state, perception layer (7 fields, selectable), cross-agent perception divergence, action pie + timeline, impairment index |
| **Causal Forensics** | Failure attribution by channel (stacked bar), phase-grouped rates, causal trace explorer (sleep → circadian drift → impairment channel → fail_prob, weakest-link agent, dependency cascade) |
| **Social Network** | Network metrics 2×2 (cohesion/fragmentation/clustering/cliques), interactive agent graph (nodes=morale + cooperation threshold, edges=trust weights), per-agent trust trajectories |
| **Tasks** | Task outcome heatmap (tasks × days, color by outcome), rolling 7-day failure rates (all tasks + high-criticality) |
| **Resources** | 6-panel resource grid with threshold shading (sleep quality, task load, coffee, food variety, comms delay, hygiene supplies), per-agent fatigue accumulation, perceived sleep quality divergence, micro-event timeline |
| **Comparison** | Requires `--inject-comms`. Shows delta KPIs, physics overlay (baseline vs intervention with fill), TQ window strain delta bars, intervention catalogue, per-agent MC belief + morale penetration (reveals if high-strain agents discounted the message) |

### Comparison Mode

Comparison tab requires running a simulation with at least one MC intervention:

```bash
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 \
    --inject-comms "reassurance:100:14,direction:150"
```

The dashboard automatically runs a matched baseline (identical seed, no comms) and computes counterfactual deltas.

### Design Notes

- `_DARK_LAYOUT` is the base Plotly layout dict. All `update_layout()` calls must use `**_dl(**overrides)` — never unpack `_DARK_LAYOUT` directly (causes duplicate keyword errors in Python's `**` expansion)
- `_dl()` uses `copy.deepcopy(_DARK_LAYOUT)` + `base.update(overrides)` — handles key conflicts correctly
- Plotly 6+: colorbar `title` must be `dict(text=..., font=dict(...))` — `titlefont=` keyword was removed
- Streamlit's file watcher is unreliable on Windows/OneDrive paths — always use `--server.fileWatcherType none`

---

## Future Extensions

Possible enhancements (NOT implemented yet):

1. **Multi-scenario runner**: Run multiple configurations in batch
2. **Parameter sweep**: Systematic exploration of TQP parameter space
3. ~~**Visualization**: Plot generation from outputs~~ — **Complete** (`dashboard.py`)
4. **Calibration**: Fit parameters to empirical data (pipeline exists in `calibration/`; needs real analog data)
5. **Module integration**: Import and use formal Module 09 logging, Module 10 validation
6. **Dashboard: dyadic conflict heatmap** — per-agent-pair trust erosion tracked in engine but not yet shown
7. **Dashboard: sleep debt + circadian drift time-series** — computed per-agent but stored only in failure traces, not in `DayState`

## Testing

To verify the runtime harness works:

```bash
cd integration/runtime
python run_simulation.py --mission-name test --days 100
```

Expected output:
- Console summary showing TQP trajectory
- Validation PASS
- Output files in `output/`

Check validation:
```bash
cat output/test_validation.json
```

Should show `"overall_status": "PASS"`.

## Summary

Phase 5 runtime harness = **lightweight wrapper** around the Ruthless Core Model.

- ✓ Orchestrates simulation execution
- ✓ Provides clean configuration interface
- ✓ Writes structured outputs
- ✓ Validates trajectory patterns
- ✓ Offers CLI entrypoint
- ✗ Does NOT modify core engine
- ✗ Does NOT reimplement dynamics
- ✗ Does NOT touch `/modules`

**Result:** Clean, maintainable integration layer that keeps the core engine frozen while enabling full mission simulations.
