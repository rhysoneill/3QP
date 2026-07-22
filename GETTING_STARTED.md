# 3QP — Getting Started

**3QP (Third-Quarter Phenomenon Behavioral Twin)** is a crew behavioral simulation engine built to model psychological and social degradation in long-duration isolated missions — specifically the well-documented performance dip that occurs roughly 50–75% through a mission. The end goal is a NASA-grade tool for astronaut behavioral health training and mission planning.

---

## Prerequisites

- Python 3.8 or later
- No external libraries required for the core simulation
- Optional: `plotly` and `pandas` for the HTML sensitivity report

```bash
pip install plotly pandas   # optional, only for sensitivity.py --html
```

> **Windows users**: run all commands with `python -X utf8` to handle Unicode console output correctly.

---

## Repository Layout (What Matters First)

```
3QP/
├── GETTING_STARTED.md          ← you are here
├── MODEL_REFERENCE.md          ← technical/scientific reference
├── integration/runtime/        ← everything you run lives here
│   ├── run_simulation.py       ← main CLI entry point
│   ├── twin_runner.py          ← day-by-day simulation engine
│   ├── demo_report.py          ← three-scenario comparison report
│   ├── sensitivity.py          ← parameter robustness sweep
│   ├── replay.py               ← deterministic replay from saved manifest
│   ├── params.py               ← all model constants in one place
│   └── output/                 ← all simulation results land here
├── phase4/06_Ruthless_Core_Model/
│   └── ruthless_core.py        ← physics engine (frozen, don't edit)
├── crew/                       ← Big Five personality → simulation config
├── calibration/                ← fitting pipeline for real mission data
└── data/                       ← example cohesion CSV + fitted config
```

---

## Your First Run — Three-Scenario Demo

Run this from the `integration/runtime/` directory:

```bash
cd "integration/runtime"
python demo_report.py
```

This runs three crew scenarios for 180 days each:
- **Baseline crew** — moderate cohesion, moderate workload
- **Fragile crew** — low-cohesion OCEAN profiles, high conflict tendency
- **High-cohesion crew** — strong interpersonal compatibility

Outputs written to `output/demo_report/`:
```
output/demo_report/
├── baseline/
│   ├── summary.json            ← mission KPIs and parameters
│   ├── kpis.json               ← critical completion rate, EVA readiness, etc.
│   ├── mission_story.json      ← top failures and phase-by-phase narrative
│   ├── run_manifest.json       ← full parameter registry + git hash
│   └── day_NNNN.json           ← per-day detailed state (one file per day)
├── fragile/
└── high_cohesion/
```

---

## Running a Single Simulation (CLI)

From `integration/runtime/`:

```bash
# Batch mode — aggregate statistics, fast
python run_simulation.py --mission-name my_mission --days 200

# Twin mode — day-by-day persistent behavioral twin (recommended)
python -X utf8 run_simulation.py --mode twin --crew-preset high_cohesion_team --mission-name twin_test --days 200

# Available crew presets
python -X utf8 run_simulation.py --mode twin --crew-preset fragile_team --mission-name fragile_test --days 200
python -X utf8 run_simulation.py --mode twin --crew-preset extroverted_explorers --mission-name ee_test --days 200
```

### Injecting Mission Control Communications

```bash
# One-time direction message on day 100
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 \
  --inject-comms "direction:100"

# Recurring reassurance every 7 days starting at day 150
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 \
  --inject-comms "reassurance:150:7"

# Multiple communication interventions
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 \
  --inject-comms "reassurance:150:7,direction:100,support:50:14"
```

Available comm types: `reassurance`, `direction`, `support`, `acknowledgment`, `resupply_announcement`

---

## Understanding the Outputs

### `summary.json`
High-level mission summary. Key fields:
- `mission_name`, `mission_length_days`, `crew_size`
- `physics.final_cohesion` — cohesion at mission end (>0.70 = healthy, <0.40 = at risk)
- `physics.min_cohesion` — lowest cohesion reached during mission
- `physics.tq_onset_day` — day when Third Quarter Pressure first exceeded 0.30
- `schema_version` — output format version

### `kpis.json`
Operational performance metrics:
- `critical_task_completion_rate` — fraction of critical tasks completed without failure
- `eva_readiness_index` — readiness for extravehicular activities
- `comms_reliability_score` — mission control communication effectiveness
- `maintenance_backlog` — accumulated deferred maintenance load
- `rework_hours_proxy` — estimated rework cost from task failures

### `mission_story.json`
Human-readable causal narrative:
- `top_failures` — 5 highest-impact failures ranked by criticality × outcome severity
- `phase_stories` — representative failure chain per mission phase (early / TQ / late)
- `summary_sentences` — plain English mission summary

### `day_NNNN.json`
Full per-day state (twin mode only). Contains:
- Per-agent internal state (fatigue, stress, morale, burnout, frustration)
- Per-agent beliefs (scarcity, fairness, MC support)
- Physics state (M, S, C, Q)
- Task outcomes with causal traces
- Social network metrics

### `run_manifest.json`
Reproducibility record. Contains:
- Complete parameter registry with values, units, descriptions
- Random seed used
- Git commit hash (if in a git repo)
- `hash_summary` for replay verification

---

## Replaying a Previous Run

To exactly reproduce a run from its manifest:

```bash
python replay.py --manifest output/demo_report/baseline/run_manifest.json \
                 --output output/demo_report/baseline_replay/

# Compare outputs — verifies bit-exact reproduction
python replay.py --manifest output/demo_report/baseline/run_manifest.json \
                 --compare output/demo_report/baseline/summary.json \
                 --output output/demo_report/baseline_replay/
```

Exit code `0` = success, `2` = hash mismatch (non-deterministic output detected).

---

## Sensitivity Sweep

Tests how robust TQ emergence is to ±20% changes in model parameters:

```bash
# Fast sweep (task failure coefficients only, ~2 min)
python sensitivity.py --n-seeds 5 --verbose

# Full sweep including backlog and phase multipliers (~15 min)
python sensitivity.py --n-seeds 10 --full-sweeps --verbose

# Generate HTML heatmap report
python sensitivity.py --n-seeds 10 --html --output-dir output/sensitivity/
```

Outputs:
- `output/sensitivity/robustness.csv` — gradient per parameter per metric
- `output/sensitivity/robustness.html` — 4-panel heatmap (requires plotly)
- Console acceptance check: PASS/FAIL per criterion

---

## Calibrating to Real Data

If you have cohesion time-series data from an analog mission (e.g., MARS-500, HI-SEAS, HERA):

```bash
cd calibration

# Fit to your data
python fit_cohesion.py --data ../data/your_mission_cohesion.csv \
                       --days 520 \
                       --output ../data/your_mission_fitted.json

# The fitted config is then usable in twin_runner.py
```

Expected CSV format: two columns, `day` and `cohesion` (normalized 0–1).

The synthetic placeholder `data/example_real_cohesion.csv` demonstrates the expected format.

---

## Running the Full Validation Suite (Phase D)

Phase D runs 11 controlled experiments that validate causal mechanisms:

```bash
cd phase_d
python -X utf8 demo_phase_d.py      # full 11-experiment suite
python -X utf8 validate_phase_d.py  # quick pass/fail check
```

These experiments verify:
- TQP timing emerges in the correct mission window
- Intervention timing matters (early vs. late)
- Crew composition affects trajectory
- The 4 collapse modes (Cohesion-Led, Strain-Spike, Dyadic Fracture, Monotony Erosion) are reproducible

---

## Crew Presets and Custom Crews

Crew presets are defined in `crew/examples.py`. Each preset maps Big Five (OCEAN) personality profiles to simulation parameters.

To see available presets:

```bash
python list_crews.py
```

To define a custom crew, pass OCEAN scores directly:

```python
from crew.personality_to_config import personality_to_config
from crew.profile import CrewProfile

crew = [
    CrewProfile(name="Alice", openness=0.8, conscientiousness=0.9,
                extraversion=0.6, agreeableness=0.7, neuroticism=0.2),
    CrewProfile(name="Bob",   openness=0.5, conscientiousness=0.7,
                extraversion=0.4, agreeableness=0.5, neuroticism=0.5),
]
config = personality_to_config(crew)
```

---

## Changing Model Parameters

All model constants live in `integration/runtime/params.py`. This is the single source of truth — no constants are hardcoded anywhere else in the runtime layer.

```python
# params.py — example entries
COORD_STRAIN_WEIGHT        = 1.20   # coordination task failure sensitivity to strain
PERSIST_MONOTONY_WEIGHT    = 0.25   # persistence task failure sensitivity to monotony
BACKLOG_WORKLOAD_PER_SKIP  = 0.008  # workload added per skipped maintenance task
DYAD_CONFLICT_INCREMENT    = 0.12   # trust penalty per conflict event (shared across pairs)
```

Every parameter change is automatically recorded in `run_manifest.json` on the next run.

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Unicode errors on Windows | Run with `python -X utf8` |
| `ModuleNotFoundError` for `params` | Run from `integration/runtime/` directory |
| `plotly` not found | `pip install plotly pandas` (only needed for `--html` flag) |
| Hash mismatch on replay | Check that `params.py` has not changed since the original run |

---

## Next Steps

Once you're comfortable running simulations:

1. Read `MODEL_REFERENCE.md` for the theoretical basis and parameter justifications
2. Try calibrating to a real dataset using `calibration/fit_cohesion.py`
3. Use `sensitivity.py` to understand which parameters most affect your scenario
4. Inject interventions using `--inject-comms` and compare outcomes across timing strategies
