# CLAUDE.md — 3QP Project Context

## What This Project Is

**3QP (Third-Quarter Phenomenon Behavioral Twin)** is a lunar crew behavioral simulation engine built to model, reproduce, and study the Third-Quarter Phenomenon (TQP) — the well-documented psychological and social deterioration that occurs roughly 50-75% through long-duration isolated missions.

The end goal: a high-fidelity simulator usable by NASA for astronaut behavioral health training and mission planning.

**Owner/Context**: Built by Rhys O'Neill at MITRE. This is a personal passion project aimed at providing a publishable, auditable, NASA-grade behavioral health tool.

---

## Core Design Philosophy (Critical to Understand)

1. **Causal, not statistical** — Every state change has an explicit mechanical cause. No black-box ML.
2. **Transparent** — Every action, state transition, and decision is logged and inspectable.
3. **Layered** — Physics → Actions → Narrative. Each layer reads from the one below; none write back up.
4. **Deterministic causality** — Same inputs always produce the same outputs. Randomness only via seeded RNG.
5. **Narrative is decorative** — LLM rendering of outputs is non-causal; it can't influence the simulation.
6. **Modular and frozen** — 12 modules at v0.1. Avoid touching frozen code unless explicitly needed.

---

## Architecture Overview

```
Phase 3 (Qualitative Reference)
    └─ Baseline states, scenarios, patterns, trajectories

Phase 4 (Computational Architecture — 5 Workstreams)
    WS1: Semantic Schema → WS2: State Encoding → WS3: Pattern Recognition
    → WS4: Trajectory Analysis → WS5: Validation Harness

    └─ phase4/06_Ruthless_Core_Model/ruthless_core.py  ← THE PHYSICS ENGINE

Phase A: Collapse Fingerprinting
    └─ fingerprinting/  (timing, depth, fractiousness)

Phase B: Agentic Layer (Deterministic Action Selection)
    └─ agents/  (WITHDRAW, ENGAGE, SUPPORT, ESCALATE, MAINTAIN)

Phase C: Narrative Rendering (Non-causal LLM overlay)
    └─ agents/PHASE_C_*.md + test_phase_c*.py

Phase D: Counterfactual Validation
    └─ phase_d/  (11 experiments, failure taxonomy, causal analysis)

Phase 5: Runtime Integration
    └─ integration/runtime/run_simulation.py  ← CLI ENTRY POINT (batch + twin modes)
    └─ integration/runtime/twin_runner.py     ← Day-by-day twin mode orchestrator
```

---

## Twin Engine Architecture (COMPLETE)

3QP has been upgraded from a crew-unit scenario engine to a persistent behavioral mission twin.

**Core pipeline (locked)**:
```
Resource Layer (objective consumables: coffee, food, sleep, comms delay, etc.)
    ↓
Perception Model (per-agent, filtered by personality and social position)
    ↓
Belief Update (per-agent: belief_scarcity, belief_fairness, belief_mc_support, etc.)
    ↓
Internal State Drift (per-agent: stress, morale, fatigue, boredom, trust_in_crew, etc.)
    ↓
Action Selection (per-agent, personality-aware thresholds)
    ↓
Physics Inputs (aggregated → workload, recovery, novelty, success → RuthlessCoreModel)
```

**Behavioral drift invariants (locked)**:
- No internal state variable has a time-indexed drift term — all changes trace to belief inputs
- Resource scarcity never touches internal state directly — always via perception → belief
- Communication delay never directly reduces trust — must pass through interpretation
- Isolation duration alone does not bias state in any direction
- Agents can improve trust, morale, and cooperation under scarcity if beliefs support it

**Twin engine layers (all complete)**:

| Layer | File | Purpose |
|-------|------|---------|
| Resource Engine | `resources/resource_model.py` | Objective consumable tracking + depletion |
| Perception Model | `perception/perception_model.py` | Per-agent filtered view of resources |
| Belief Engine | `beliefs/belief_engine.py` | Named belief state updated from perception only |
| Internal State | `internal_state/astronaut_state.py` | 7-variable per-astronaut state + drift |
| Per-Agent Selector | `agents/per_agent_selector.py` | Personality-aware action selection |
| MC Types | `mission_control/mc_types.py` | PlannedIntervention, MCCommunication, CrewReport |
| Twin Runner | `integration/runtime/twin_runner.py` | Day-by-day orchestrator |

**HermitClaw** (`../hermitclaw/` — brendanhogan/hermitclaw, cloned to `3QP Main/hermitclaw/`):
- Entirely external to the simulation. Not imported or called by any sim code.
- Rhys's personal briefing tool: drop per-day JSON files from `output/{mission_name}/` into the HermitClaw box to get natural language readouts and record notes without launching a full interface.
- The simulation writes `day_NNNN.json` files — HermitClaw reads them. That is the entire relationship.

**MC communications**: injected externally by a human operator via `inject_mc_communication()` on TwinRunner. HermitClaw never writes to the crew comm channel.

**OpenClaw**: removed.

---

## The Physics Engine (Core of Everything)

**File**: `phase4/06_Ruthless_Core_Model/ruthless_core.py`

**4 State Variables**:
- `M` — Monotony (builds over time, reduced by novelty events)
- `S` — Strain (workload-driven stress accumulation)
- `C` — Cohesion (social bond quality; the key TQP indicator)
- `Q` — Third Quarter Pressure (derived from M, S, C)

**Inputs per day**: workload, recovery, novelty_events, success_events

**Output**: `RuthlessCoreOutput` — full timeseries of all state variables

**Config**: `RuthlessCoreConfig` — mission length, TQ parameters, input schedules

---

## Directory Map

```
3QP/
├── CLAUDE.md                          ← YOU ARE HERE
├── README.md
├── PHASE_D.md
│
├── phase4/06_Ruthless_Core_Model/     ← Core physics engine (FROZEN)
├── integration/runtime/               ← CLI entry point + orchestration
│   ├── run_simulation.py              ← batch + twin mode entry point
│   ├── twin_runner.py                 ← day-by-day twin mode orchestrator
│   ├── mission_runner.py
│   ├── runtime_config.py
│   ├── logger.py
│   ├── validator.py
│   ├── dashboard.py                   ← Streamlit Mission Control Room (7-tab visualization)
│   ├── .streamlit/config.toml         ← dark theme config for dashboard
│   └── output/                        ← JSON result files (per-day + summary)
│
├── resources/                         ← Resource layer (complete)
│   └── resource_model.py
│
├── perception/                        ← Per-agent perception (complete)
│   └── perception_model.py
│
├── beliefs/                           ← Belief update layer (complete)
│   ├── belief_engine.py
│   └── belief_types.py
│
├── internal_state/                    ← Per-astronaut internal state (complete)
│   └── astronaut_state.py
│
├── mission_control/                   ← MC types + legacy HermitClaw advisor code
│   ├── hermitclaw.py                  ← NOT used by simulation; retained for reference
│   └── mc_types.py                    ← PlannedIntervention, MCCommunication, CrewReport
│
├── agents/                            ← Phase B (agentic) + C (narrative) + twin selector
│   ├── agentic_core.py
│   ├── intent_policy.py
│   ├── actions.py
│   ├── action_effects.py
│   ├── action_logger.py
│   ├── per_agent_selector.py          ← personality-aware per-agent action selection
│   ├── narrative_renderer.py          ← Phase C: LLM or rule-based narrative rendering
│   ├── narrative_prompts.py           ← Phase C: constrained prompt templates
│   ├── narrative_logger.py            ← Phase C: narrative output tracking
│   └── llm_backend.py                 ← OpenAI backend (reads OPENAI_API_KEY)
│
├── phase_d/                           ← Counterfactual validation
├── fingerprinting/                    ← Collapse fingerprint schema
├── crew/                              ← Big Five → RuthlessCoreConfig mapping
├── modules/                           ← 12 foundational modules (ALL FROZEN v0.1)
├── phase3/                            ← Qualitative reference
├── notebooks/                         ← Jupyter: ruthless_core_calibration.ipynb
├── calibration/                       ← Parameter fitting against real cohesion data
│   └── fit_cohesion.py                ← Nelder-Mead optimizer (scipy or pure-Python)
└── data/                              ← example_real_cohesion.csv + fitted_config.json
```

**External tool (not inside this repo)**:
```
3QP Main/
├── 3QP/          ← this simulation repo
└── hermitclaw/   ← Weke interface (brendanhogan/hermitclaw); drop 3QP output JSONs in box
```

---

## Tech Stack

- **Language**: Python 3.8+ (stdlib-first; minimal dependencies)
- **No ML libraries** — causal model, not statistical
- **Testing**: `unittest` (stdlib)
- **Serialization**: JSON / JSON Lines
- **Optional**: matplotlib (demos), jupyter (calibration notebook)
- **No numpy** in core (by design — portability + auditability)

---

## Current Status

| Layer | Status |
|-------|--------|
| 12 Core Modules | Frozen at v0.1, all tests passing |
| Ruthless Core Model (Physics) | Complete, production-ready |
| Phase B (Agentic Layer) | Complete |
| Phase C (Narrative Layer) | Architecture complete; LLM not yet integrated |
| Phase D (Counterfactual Validation) | Complete — 11 experiments, failure taxonomy |
| Phase 5 (Runtime — batch mode) | Complete — CLI entry point works |
| Crew Layer (Personality→Config) | Complete |
| Fingerprinting | Complete |
| Resource Layer | Complete |
| Perception Layer | Complete |
| Belief Engine | Complete |
| Per-Agent Internal State | Complete |
| Per-Agent Selector | Complete |
| HermitClaw | External tool only — not part of simulation |
| Twin Runner (day-by-day) | Complete — `--mode twin` wired into CLI |
| Calibration Pipeline | Complete — automated Nelder-Mead fitting; outputs `data/fitted_config.json` |
| LLM Integration | Complete — `agents/llm_backend.py`; set `OPENAI_API_KEY` env var |
| Behavioral Realism Fixes | Complete — phase-aware events, circadian drift, exec impairment, compliance scaling, structural competence |
| Streamlit Dashboard | Complete — 7-tab Mission Control Room (`dashboard.py`); ~65% of backend fields visualized |

---

## Completed Work (Recent Sessions)

### 1. Social Network Integration — COMPLETE
`SocialNetworkModule` (Module 05) wired into the twin runner pipeline.
- `SocialNetworkModule` instantiated at init with full crew graph (init weight 0.70)
- Action selection moved before social update — actions generate interaction signals
- `DayState` now includes `social_network` field with: `global_cohesion`, `fragmentation_index`, `normalized_density`, `clique_count`, `clique_coverage`, `component_count`
- `inject_mc_communication()` and `schedule_mc_communication()` methods added to `TwinRunner`

### 2. Counterfactual Intervention CLI — COMPLETE
`--inject-comms` flag added to `run_simulation.py`.

**Usage:**
```bash
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 --inject-comms "direction:100"
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 --inject-comms "reassurance:150:7"
python run_simulation.py --mode twin --crew-preset fragile_team --days 200 --inject-comms "reassurance:150:7,direction:100"
```

**Comm types and belief deltas:**
| Type | mc_support_delta | resupply_reliability_delta |
|------|-----------------|---------------------------|
| reassurance | +0.08 | 0 |
| direction | +0.05 | 0 |
| support | +0.10 | 0 |
| acknowledgment | +0.06 | 0 |
| resupply_announcement | +0.04 | +0.10 |

### 3. Behavioral Realism Fixes — COMPLETE
Five physiological/social realism limitations addressed in `integration/runtime/twin_runner.py`.

- **Fix #1 — Circadian Drift**: `_circadian_drift` accumulator. Grows when sleep debt > 0.04, recovers slowly. Applied to `sleep_today` on top of acute sleep debt.
- **Fix #2 — Phase-Aware Events**: TQ window (50–74%): conflict ×1.8, schedule slips ×1.3, novel tasks ×0.5. Late phase: slips ×1.5, failures ×1.4, novelty ×0.3.
- **Fix #3 — Executive Function Degradation**: `exec_impairment = mean_fatigue×0.55 + mean_stress×0.45 − 0.35`. At full: +25% workload, −20% recovery.
- **Fix #4 — Intervention Compliance Scaling**: `compliance = max(0.35, 1 − strain_reactance − frustration_reactance)`. High-strain agents discount MC messages.
- **Fix #6 — Structural Competence Degradation**: `effort_quality` scales `novelty_boost` and `success_boost` — agents with high fatigue+boredom go through motions without full collective benefit.
- **Fix #5 (Reputation Memory) — Deferred**: Requires per-dyad conflict history fed back into `belief_crew_cohesion`.

### 4. Streamlit Mission Control Room Dashboard — COMPLETE
`integration/runtime/dashboard.py` — full 7-tab dark-theme visualization of all simulation outputs.

**Stack**: Streamlit 1.41.1 + Plotly 6.5.2. Dark mission-control theme via `.streamlit/config.toml`.

**Tabs and what they show:**

| Tab | Key Contents |
|-----|-------------|
| Mission Overview | Physics 2×2 (strain/cohesion/monotony/TQ), workload vs recovery area fill, novelty+success impulse bars, phase KPI breakdown, TQP emergence score |
| Agent Deep-Dive | Big Five radar, internal state (8 metrics, selectable), belief state (4 keys), perception layer (7 fields, selectable), cross-agent perception divergence, action timeline + pie, impairment index |
| Causal Forensics | Failure attribution by channel (stacked bar, phase-grouped), causal trace explorer (sleep→drift→channel→fail_prob, weakest-link agent, dependency cascade) |
| Social Network | Network metrics 2×2 (cohesion/fragmentation/clustering/clique), interactive graph (nodes=morale, edges=trust), per-agent trust trajectories |
| Tasks | Task outcome heatmap (tasks×days), rolling 7-day failure rates (all + high-criticality) |
| Resources | 6-panel resource grid (sleep/load/coffee/food/comms/hygiene), per-agent fatigue accumulation, perceived sleep quality divergence, micro-event timeline |
| Comparison | Delta KPIs, physics overlay (baseline vs intervention), TQ window strain delta, intervention catalogue, per-agent MC belief + morale penetration |

**Backend field coverage**: ~65% of the ~150+ unique daily fields are now visualized. Key gaps remaining:
- Sleep debt and circadian drift as independent time-series (available in causal traces only)
- Dyadic conflict heatmap (per-agent-pair trust erosion tracked but not shown)
- Reputation memory (Fix #5 deferred in engine too)

**Known pitfalls (dashboard)**:
- Streamlit file watcher unreliable on Windows/OneDrive — always restart with `--server.fileWatcherType none`
- `_dl(**overrides)` helper must be used for all `update_layout()` calls — never use raw `**{k: v for k, v in _DARK_LAYOUT.items() ...}` pattern (causes duplicate keyword errors)
- Plotly 6: colorbar `title` must be `dict(text=..., font=dict(...))` — `titlefont=` removed

---

## Known Gaps (As of Last Review)

1. **No real data yet** — Calibration pipeline is complete (`calibration/fit_cohesion.py`). Still needs real analog mission data (MARS-500, HI-SEAS, Concordia). Synthetic placeholder in `data/example_real_cohesion.csv`.
2. **Module 02** is documentation only (no executable code).
3. **Narrative rendering** — `agents/narrative_renderer.py` exists but is not called by TwinRunner. Output is raw JSON, not natural language prose.
4. **Continuous time** — All dynamics are discrete (daily steps). No continuous-time formulation.
5. **Actual NASA validation** — System is designed to be validated but has not been tested against real lunar/analog crew data.
6. **Windows console encoding** — Run with `python -X utf8` on Windows to handle Unicode characters in validation output.
7. **Reputation memory (Fix #5 deferred)** — Dyadic trust does not carry conflict narrative memory. Repeated disagreements between the same agent pair do not escalate. Requires per-dyad conflict history fed back into `belief_crew_cohesion`.
8. **Dashboard visualization coverage ~65%** — Fields not yet shown: sleep debt + circadian drift as independent time-series, dyadic conflict heatmap, per-agent cooperation threshold history, clique membership stability over time.

---

## The 4 Collapse Modes (Failure Taxonomy)

From Phase D counterfactual analysis:
1. **Cohesion-Led** — Gradual erosion; TQP-aligned timing
2. **Strain-Spike** — Acute overwhelm; early onset
3. **Dyadic Fracture** — Relationship-specific breakdown
4. **Monotony Erosion** — Disengagement drift; late onset

---

## Key Execution Commands

```bash
# Run a simulation (batch mode)
cd integration/runtime
python run_simulation.py --mission-name baseline --days 200

# Run a simulation (twin mode — requires --crew-preset)
cd integration/runtime
python -X utf8 run_simulation.py --mode twin --crew-preset high_cohesion_team --mission-name twin_test --days 200

# Available crew presets: high_cohesion_team, fragile_team, extroverted_explorers

# Launch the Streamlit Mission Control Room dashboard
cd integration/runtime
streamlit run dashboard.py --server.fileWatcherType none
# → opens at http://localhost:8501
# Run a simulation first; the dashboard auto-detects output/ JSON files and populates all tabs

# Calibrate RuthlessCoreModel to a real cohesion CSV
cd calibration
python fit_cohesion.py --data ../data/example_real_cohesion.csv --days 200 --output ../data/fitted_config.json

# Calibrate against a real dataset (e.g. MARS-500, 520 days)
python fit_cohesion.py --data ../data/mars500_cohesion.csv --days 520 --output ../data/mars500_fitted.json

# Phase B demo (agentic layer)
cd agents
python demo_phase_b.py

# Phase D full validation (11 experiments)
cd phase_d
python -X utf8 demo_phase_d.py

# Quick validation check
cd phase_d
python -X utf8 validate_phase_d.py
```

Note: `-X utf8` is required on Windows to handle Unicode characters (checkmarks, arrows) in console output.

---

## What Rhys Wants This To Become

A lunar simulation tool for astronaut training — high enough fidelity that NASA could use it to:
- Train crew for psychological resilience during TQP
- Test intervention strategies before real missions
- Provide behavioral health researchers with a transparent, auditable causal model
- Eventually: a publishable contribution to the space medicine literature

---

## Working With This Codebase

- **Read before modifying** — Always read the relevant file(s) before making changes
- **Don't touch frozen modules** unless explicitly asked — modules/ are at v0.1 by design
- **Respect the layering** — never let narrative affect physics; never let action selection affect the causal model non-deterministically
- **JSON everywhere** — outputs are always JSON; don't introduce binary formats
- **Tests are important** — all modules have test suites; run affected tests after changes
- **Documentation is first-class** — each module has spec, theory, data_contract docs; keep them in sync
