# Phase D Quick Reference

## One-Line Summary

**Phase D generates evidence of counterfactual validity, causal stability, and decision-grade usefulness through controlled experiments.**

---

## Quick Start

### Validation (30 seconds)

```bash
python -m phase_d.validate_phase_d
```

Expected: `✅ ALL VALIDATION TESTS PASSED`

### Full Demo (2-5 minutes)

```bash
python -m phase_d.demo_phase_d
```

Runs 11 experiments, generates analysis, and produces failure taxonomy.

---

## Three Experiment Families

### 1. Mission Duration

```python
from phase_d import run_mission_duration_sweep

results = run_mission_duration_sweep(baseline_duration=200)
```

Tests: -20%, -10%, baseline, +10%, +20% duration

### 2. Crew Composition

```python
from phase_d import run_crew_composition_sweep

results = run_crew_composition_sweep(baseline_duration=200)
```

Tests: Homogeneous, Polarized, Balanced crews (same avg traits, different dyadic compatibility)

### 3. Intervention Timing

```python
from phase_d import run_intervention_timing_sweep

results = run_intervention_timing_sweep(baseline_duration=200)
```

Tests: No intervention, Early (day 40), Late (day 140)

---

## Data Collection

```python
from phase_d import DataCollector

collector = DataCollector()

# Collect from experiment result
run_data = collector.collect_from_result(result)
collector.save_run(run_data)

# Load all runs
all_runs = collector.load_all_runs()

# Get summary table
summary = collector.get_summary_table(all_runs)
```

Each run captures:
- Collapse fingerprint
- Action frequencies
- Pre-collapse action sequences
- Narrative summaries (if enabled)

---

## Analysis

```python
from phase_d.analysis import CounterfactualAnalyzer

analyzer = CounterfactualAnalyzer()
analyzer.load_runs(all_runs)

# Duration effects
duration_analysis = analyzer.analyze_duration_effects()

# Action-collapse correlation
action_analysis = analyzer.analyze_action_collapse_correlation()

# Causal explanation
explanation = analyzer.generate_causal_explanation(
    run_id_baseline="duration_baseline",
    run_id_variant="duration_minus_20pct"
)
```

Demonstrates:
- Fingerprint stability
- Predictable shifts
- Action-collapse correlations
- Causal explanations

---

## Failure Taxonomy

```python
from phase_d import FailureTaxonomy

taxonomy = FailureTaxonomy()

# Classify single run
mode_type = taxonomy.classify_run(run_data)

# Analyze all runs
summary = taxonomy.analyze_runs(all_runs)

# Save taxonomy
taxonomy.save(Path("outputs/taxonomy.json"))
```

### Four Collapse Modes

| Mode | Timing | Depth | Dominant Actions | Intervention Window |
|------|--------|-------|------------------|---------------------|
| Cohesion-Led | TQ | 0.2-0.4 | WITHDRAW, ROUTINE | Early (>30 days) |
| Strain-Spike | Early | 0.4-0.7 | ASSERT, CONFRONT | Short (<10 days) |
| Dyadic Fracture | TQ | 0.3-0.5 | CONFRONT, WITHDRAW | Early (>40 days) |
| Monotony Erosion | Late | 0.15-0.35 | ROUTINE | Long (>50 days) |

---

## Output Structure

```
phase_d/outputs/
├── mission_duration/
│   ├── duration_baseline.json
│   ├── duration_minus_10pct.json
│   ├── duration_minus_20pct.json
│   ├── duration_plus_10pct.json
│   └── duration_plus_20pct.json
├── crew_composition/
│   ├── crew_variant_1.json
│   ├── crew_variant_2.json
│   └── crew_variant_3.json
├── intervention_timing/
│   ├── intervention_no_intervention.json
│   ├── intervention_early_intervention.json
│   └── intervention_late_intervention.json
├── run_data/
│   └── [all runs as RunData objects]
├── analysis/
│   ├── duration_effects.json
│   ├── action_correlation.json
│   └── causal_explanation_example.json
└── failure_taxonomy.json
```

---

## Key Constraints

**DO NOT:**
- ❌ Modify Phases A, B, or C
- ❌ Add new LLM features
- ❌ Add learning or adaptation
- ❌ Refactor architecture

**Phase D is analysis and evidence only.**

---

## Integration Points

Phase D uses but does not modify:
- `phase4.ruthless_core`: Core dynamics model
- `agents`: Phase B agentic layer
- `fingerprinting`: Collapse fingerprinting
- `crew`: Crew profiles and dyadic analysis

---

## Publishable Outputs

1. **Duration-Collapse Correlations**: Show predictable shifts
2. **Action-Collapse Tables**: Link patterns to outcomes
3. **Failure Taxonomy**: Four modes with signatures
4. **Causal Explanations**: "X changed because Y crossed Z"

All suitable for paper Results section.

---

## Common Tasks

### Run Single Experiment

```python
from phase_d import ExperimentHarness, ExperimentConfig, ExperimentFamily

harness = ExperimentHarness()

config = ExperimentConfig(
    experiment_id="my_test",
    family=ExperimentFamily.MISSION_DURATION,
    baseline_duration=200,
    duration_multiplier=1.2,  # +20%
)

result = harness.run_experiment(config)
```

### Compare Two Runs

```python
analyzer = CounterfactualAnalyzer()
analyzer.load_runs([run1, run2])

explanation = analyzer.generate_causal_explanation(
    run_id_baseline=run1.run_id,
    run_id_variant=run2.run_id
)

print(explanation["causal_factors"])
```

### Export Results for Paper

```python
import json

# Load all results
collector = DataCollector()
all_runs = collector.load_all_runs()

# Generate summary table
summary = collector.get_summary_table(all_runs)

# Export to JSON for plotting
with open("results_for_paper.json", "w") as f:
    json.dump(summary, f, indent=2)
```

---

## Troubleshooting

**Validation fails:**
1. Check Python environment: `python --version` (3.10+)
2. Verify previous phases: `python -m agents.demo_phase_c`
3. Check imports: All dependencies in place?

**Demo hangs:**
- Normal runtime: 2-5 minutes for 11 experiments
- Each experiment ~10-30 seconds

**Missing outputs:**
- Check `phase_d/outputs/` directory exists
- Verify file permissions

---

## Next Steps

After running Phase D:
1. Review `outputs/failure_taxonomy.json`
2. Examine `outputs/analysis/` for correlations
3. Use taxonomy for mission planning
4. Generate publication figures

---

For detailed documentation, see [README.md](README.md)
