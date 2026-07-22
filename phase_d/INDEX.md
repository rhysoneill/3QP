# Phase D: Counterfactual Validation and Evidence Generation

## Quick Navigation

### Getting Started
- **Quick Start**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full Documentation**: See [README.md](README.md)
- **Implementation Details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### Running Phase D

```bash
# Quick validation (30 seconds)
python -m phase_d.validate_phase_d

# Full demonstration (2-5 minutes)
python -m phase_d.demo_phase_d

# Quick test with minimal experiments (30 seconds)
python -m phase_d.quick_test
```

---

## What Phase D Does

Generates **evidence** that 3QP:
1. ✅ Produces stable causal outcomes
2. ✅ Supports counterfactual mission design
3. ✅ Remains explainable
4. ✅ Provides decision-grade usefulness

**No new features. Pure analysis and evidence.**

---

## Three Experiment Families

### 1. Mission Duration
- Tests: -20%, -10%, baseline, +10%, +20%
- Shows: Predictable fingerprint shifts

### 2. Crew Composition
- Tests: 3 crews, same avg traits, different dyadic compatibility
- Shows: Relationship structures matter

### 3. Intervention Timing
- Tests: No intervention, early, late
- Shows: Intervention windows are quantifiable

---

## Four Collapse Modes

| Mode | Signature | Intervention |
|------|-----------|--------------|
| **Cohesion-Led** | TQ, moderate depth | Early (>30 days) |
| **Strain-Spike** | Early, deep, critical | Short (<10 days) |
| **Dyadic Fracture** | TQ, high fractiousness | Target pairs (>40 days) |
| **Monotony Erosion** | Late, moderate depth | Long window (>50 days) |

---

## File Structure

```
phase_d/
├── INDEX.md                         # This file
├── README.md                        # Full documentation
├── QUICK_REFERENCE.md               # Quick start guide
├── IMPLEMENTATION_SUMMARY.md        # What was built
│
├── __init__.py                      # Package exports
├── experiment_harness.py            # D.1: Experiment framework
├── experiment_runner.py             # D.1: Pre-configured experiments
├── data_collector.py                # D.2: Data collection
├── failure_taxonomy.py              # D.4: Collapse mode taxonomy
│
├── analysis/
│   ├── __init__.py
│   └── counterfactual_analysis.py   # D.3: Analysis routines
│
├── validate_phase_d.py              # Quick validation
├── demo_phase_d.py                  # Full demonstration
├── quick_test.py                    # Minimal test
│
└── outputs/                         # Generated at runtime
    ├── mission_duration/
    ├── crew_composition/
    ├── intervention_timing/
    ├── run_data/
    ├── analysis/
    └── failure_taxonomy.json
```

---

## Key Outputs

### Experiment Data
- 11 experimental runs (default)
- Each with fingerprint + actions + narratives (optional)
- Timestamped and reproducible

### Analysis
- Duration-collapse correlations
- Action-collapse patterns
- Causal explanations
- Threshold crossings

### Taxonomy
- 4 collapse modes
- Fingerprint signatures
- Action patterns
- Intervention windows

---

## Programmatic Usage

```python
# Run experiments
from phase_d import run_mission_duration_sweep
results = run_mission_duration_sweep()

# Collect data
from phase_d import DataCollector
collector = DataCollector()
all_runs = collector.load_all_runs()

# Analyze
from phase_d.analysis import CounterfactualAnalyzer
analyzer = CounterfactualAnalyzer()
analyzer.load_runs(all_runs)
analysis = analyzer.analyze_duration_effects()

# Generate taxonomy
from phase_d import FailureTaxonomy
taxonomy = FailureTaxonomy()
summary = taxonomy.analyze_runs(all_runs)
```

---

## Integration

Phase D **uses** existing infrastructure:
- Phase A: Behavioral physics
- Phase B: Agentic actions
- Phase C: Narratives (optional)
- Phase 4: Ruthless Core
- Fingerprinting utilities
- Crew profiles

**No modifications to existing code.**

---

## Success Metrics

✅ Validation passes  
✅ All experiments run  
✅ Data collected and stored  
✅ Analysis generates insights  
✅ Taxonomy classifies collapse modes  
✅ Outputs ready for publication  

---

## Next Steps

1. Run `validate_phase_d.py`
2. Run `demo_phase_d.py`
3. Review outputs in `outputs/`
4. Generate publication figures
5. Use taxonomy for mission planning

---

## Questions?

- **Quick start?** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full details?** → [README.md](README.md)
- **What was built?** → [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **How does it work?** → See code comments in each module

---

**Phase D is complete and validated.**
