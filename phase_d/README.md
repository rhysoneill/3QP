# Phase D: Counterfactual Validation and Evidence Generation

## Overview

Phase D demonstrates that the 3QP system produces stable causal outcomes, supports counterfactual mission design, remains explainable, and provides decision-grade usefulness.

**This phase adds no new features.** It generates evidence through controlled experiments and systematic analysis.

## Objective

Demonstrate that the system:
1. Produces stable causal outcomes
2. Supports counterfactual mission design
3. Remains explainable even when narratives vary
4. Provides insight that LLM-first simulations cannot

## Components

### D.1 Counterfactual Experiment Harness

Three experiment families with single-variable manipulations:

**Experiment 1: Mission Duration**
- Baseline duration
- -10%, -20% duration
- +10%, +20% duration

**Experiment 2: Crew Composition**
- Same average personality traits
- Different dyadic compatibility structures
- Hold mission profile constant

**Experiment 3: Intervention Timing**
- No intervention (control)
- Early intervention (~20% through mission)
- Late intervention (~70% through mission)

### D.2 Data Collection

For each run, collects and stores:
- Collapse fingerprint
- Action frequency distributions
- Action sequences in pre-collapse window
- Narrative summaries (paired with mechanistic references)

All outputs are timestamped and reproducible.

### D.3 Analysis & Validation

Analysis routines demonstrate:
- Fingerprint stability under narrative variability
- Predictable fingerprint shifts under counterfactual changes
- Correlation between action patterns and collapse archetypes

Enables answering: **"This outcome changed because X crossed Y."**

### D.4 Failure Mode Taxonomy

Taxonomy of collapse modes derived from fingerprints + action traces:

1. **Cohesion-Led Collapse**
   - Fingerprint: TQ timing, moderate depth (0.2-0.4)
   - Actions: Increasing WITHDRAW, low diversity
   - Intervention: Most effective early (>30 days before collapse)

2. **Strain-Spike Collapse**
   - Fingerprint: Early timing, deep collapse (0.4-0.7), critical risk
   - Actions: High intensity (ASSERT, CONFRONT), high diversity
   - Intervention: Short window (<10 days once spike detected)

3. **Dyadic Fracture-Driven Collapse**
   - Fingerprint: TQ timing, high fractiousness (>0.6)
   - Actions: CONFRONT followed by WITHDRAW
   - Intervention: Target specific dyadic pairs early (>40 days)

4. **Gradual Monotony Erosion**
   - Fingerprint: Late timing, moderate depth (0.15-0.35)
   - Actions: Overwhelming ROUTINE dominance, very low diversity
   - Intervention: Long window (>50 days), gradual deterioration

Each mode has publishable artifacts:
- Fingerprint signature
- Characteristic action pattern
- Sensitivity window for intervention

## Files

```
phase_d/
├── __init__.py                          # Package exports
├── experiment_harness.py                # D.1: Experiment execution framework
├── experiment_runner.py                 # D.1: Pre-configured experiment builders
├── data_collector.py                    # D.2: Data collection and storage
├── failure_taxonomy.py                  # D.4: Collapse mode taxonomy
├── demo_phase_d.py                      # Complete demonstration
├── validate_phase_d.py                  # Quick validation
├── README.md                            # This file
├── analysis/
│   ├── __init__.py
│   └── counterfactual_analysis.py       # D.3: Analysis routines
├── outputs/
│   ├── run_data/                        # Collected run data
│   ├── analysis/                        # Analysis results
│   └── failure_taxonomy.json            # Taxonomy definition
└── experiments/                         # (Reserved for future use)
```

## Usage

### Quick Validation

Run quick validation to ensure all components work:

```bash
python -m phase_d.validate_phase_d
```

Expected output: `✅ ALL VALIDATION TESTS PASSED`

### Full Demonstration

Run complete Phase D workflow (2-5 minutes):

```bash
python -m phase_d.demo_phase_d
```

This will:
1. Run all three experiment families (~11 runs total)
2. Collect structured data
3. Perform counterfactual analysis
4. Generate failure mode taxonomy
5. Save all results to `phase_d/outputs/`

### Programmatic Usage

```python
from phase_d import (
    ExperimentHarness,
    run_mission_duration_sweep,
    DataCollector,
    CounterfactualAnalyzer,
    FailureTaxonomy,
)

# Run experiments
harness = ExperimentHarness()
results = run_mission_duration_sweep(harness=harness)

# Collect data
collector = DataCollector()
for result in results:
    run_data = collector.collect_from_result(result)
    collector.save_run(run_data)

# Analyze
analyzer = CounterfactualAnalyzer()
analyzer.load_runs(collector.load_all_runs())
analysis = analyzer.analyze_duration_effects()

# Generate taxonomy
taxonomy = FailureTaxonomy()
summary = taxonomy.analyze_runs(collector.load_all_runs())
```

## Expected Outcomes

At the end of Phase D, you will have:

1. **Clear counterfactual results**
   - Evidence that duration changes produce predictable shifts
   - Evidence that crew composition affects collapse patterns
   - Evidence that intervention timing matters

2. **Stable causal behavior**
   - Fingerprints remain consistent under narrative variation
   - Outcomes are reproducible and deterministic
   - Threshold crossings are identifiable

3. **Defensible failure mode taxonomy**
   - Four distinct collapse modes
   - Each with fingerprint signature and action pattern
   - Intervention windows quantified

4. **Publishable artifacts**
   - Figures showing duration-collapse correlations
   - Tables of action-collapse correlations
   - Taxonomy definitions suitable for paper Methods/Results sections
   - Causal explanations demonstrating explainability

## Key Constraints

**DO NOT:**
- Modify Phases A, B, or C
- Add new LLM features
- Add new narrative capabilities
- Add learning or adaptation
- Add new psychology
- Refactor architecture

**Phase D is analysis and evidence only.**

## Success Criteria

Phase D succeeds when it demonstrates:
1. ✅ Stable causal outcomes (fingerprints don't change with narrative variation)
2. ✅ Predictable counterfactual shifts (duration → timing/depth changes)
3. ✅ Action-collapse correlations (patterns predict outcomes)
4. ✅ Publishable failure taxonomy (4 modes with signatures)
5. ✅ Causal explanations ("X changed because Y crossed threshold Z")

## Integration with Existing Phases

Phase D **uses but does not modify**:
- Phase A: Behavioral physics (cohesion, strain, monotony)
- Phase B: Agentic action layer and logging
- Phase C: Narrative rendering (optional)
- Phase 4: Ruthless Core Model
- Fingerprinting: Collapse fingerprinting utilities
- Crew: Personality and dyadic fractiousness

All Phase D code is contained in the `phase_d/` directory and imports existing infrastructure.

## Next Steps

After running Phase D:

1. Review outputs in `phase_d/outputs/`
2. Examine analysis results in `phase_d/outputs/analysis/`
3. Review failure taxonomy in `phase_d/outputs/failure_taxonomy.json`
4. Use findings for mission planning and crew selection
5. Generate figures and tables for publication

## Questions?

Phase D is designed to be self-contained and unambiguous. If you encounter issues:

1. Run `validate_phase_d.py` first
2. Check that all previous phases are working
3. Verify Python environment has required dependencies
4. Review error messages for specific failures

For conceptual questions about the taxonomy or analysis methods, consult the detailed mode definitions in the demo output.
