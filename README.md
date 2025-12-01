# 3QP – Third-Quarter Phenomenon Behavioral Twin (Lunar Crew Simulation)
A high-fidelity, modular behavioral simulation designed to reproduce the Third-Quarter Phenomenon in 4–6-person lunar crews using causal, theory-grounded mechanisms.

3QP is built as a distributed, modular behavioral engine where each subsystem is developed and versioned independently. This architecture avoids context overload in AI-assisted development and enables controlled integration of components over time.

## Mission Statement
Create the first behavioral simulation that can:
1. Reproduce the Third-Quarter Phenomenon as an emergent psychological phase transition.
2. Identify causal mechanisms behind it.
3. Evaluate interventions that may prevent or flatten its onset in real lunar missions.
4. Provide a transparent, auditable framework suitable for NASA BHP and long-duration spaceflight behavioral health.

## Project Structure

```
3QP/
│
├── modules/
│   ├── 01_TQP_Core/
│   ├── 02_Breakutdown_Impact/
│   ├── 03_Architecture/
│   ├── 04_SlowFast_Physiology/
│   ├── 05_Social_Network/
│   ├── 06_BDI_Cycle/
│   ├── 07_Stressor_Model/
│   ├── 08_Intervention_Engine/
│   ├── 09_Logging_System/
│   ├── 10_Validation/
│   ├── 11_Roadmap/
│   └── 12_Changelog/
│
└── integration/
    ├── integration_notes.md
    ├── module_dependency_map.md
    └── integration_tests/
```

Each module is a standalone subsystem with its own specifications, data contracts, prompts, and version history. Modules are not developed simultaneously. They are built one at a time in isolated AI contexts to preserve architectural clarity and prevent model drift.

## Module Structure

Every module contains:

```
<module>/
│
├── README.md
├── spec.md
├── theory_basis.md
├── data_contract.md
├── implementation_notes.md
│
├── prompts/
│   ├── build_prompt.md
│   ├── extend_prompt.md
│   └── integration_prompt.md
│
└── versions/
```

## Build Philosophy

1. Build modules independently.
2. Freeze module versions.
3. Integrate through documented data contracts.
4. Maintain strict boundaries (microservice-like architecture).

## Development Workflow

1. Select a module.
2. Use its `build_prompt.md` in a new AI session.
3. Populate `spec.md`, `README.md`, etc.
4. Freeze a version under `/versions/`.
5. Integrate later through the `/integration/` folder.

## NASA Review Readiness Goals

- Causal chain: stressors → cognition → social drift → third-quarter transition.
- Transparent state logging.
- Clear intervention testing pathways.
- Theory-grounded behavioral modules.
- Auditable architecture.

## Current Status

Initialization complete.  
All 12 modules scaffolded.  
Ready for module development.

## How to Begin

Choose a module from `/modules/` and open its `build_prompt.md`.

