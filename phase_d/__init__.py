"""
Phase D: Counterfactual Validation and Evidence Generation

This phase demonstrates:
- Stable causal outcomes
- Counterfactual mission design support
- Explainability even when narratives vary
- Insights that LLM-first simulations cannot provide

Phase D is about evidence, not new capability.
"""

from .experiment_harness import (
    ExperimentHarness,
    ExperimentConfig,
    ExperimentFamily,
    ExperimentResult,
)

from .experiment_runner import (
    run_mission_duration_sweep,
    run_crew_composition_sweep,
    run_intervention_timing_sweep,
)

from .data_collector import (
    RunData,
    DataCollector,
)

from .failure_taxonomy import (
    CollapseMode,
    FailureTaxonomy,
)

__all__ = [
    'ExperimentHarness',
    'ExperimentConfig',
    'ExperimentFamily',
    'ExperimentResult',
    'run_mission_duration_sweep',
    'run_crew_composition_sweep',
    'run_intervention_timing_sweep',
    'RunData',
    'DataCollector',
    'CollapseMode',
    'FailureTaxonomy',
]
