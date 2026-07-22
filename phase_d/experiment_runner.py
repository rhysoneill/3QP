"""
Experiment Runner Functions (D.1)

Provides pre-configured experiment builders for the three required families:
1. Mission Duration Sweep
2. Crew Composition Sweep
3. Intervention Timing Sweep
"""

from typing import List
from .experiment_harness import (
    ExperimentConfig,
    ExperimentFamily,
    ExperimentHarness,
    ExperimentResult,
)
from crew.profile import CrewProfile, CrewMember, PersonalityScores


def run_mission_duration_sweep(
    baseline_duration: int = 200,
    harness: ExperimentHarness = None,
    enable_narrative: bool = False,
) -> List[ExperimentResult]:
    """
    Run Experiment 1: Mission Duration Sweep
    
    Tests stability under duration changes:
    - Baseline duration
    - -10%, -20% duration
    - +10%, +20% duration
    
    Args:
        baseline_duration: Baseline mission length in days (default: 200)
        harness: Optional existing harness (creates new if None)
        enable_narrative: Whether to enable Phase C narratives
        
    Returns:
        List of experiment results for each duration variant
    """
    if harness is None:
        harness = ExperimentHarness()
    
    # Define duration multipliers
    multipliers = [
        (0.80, "minus_20pct"),
        (0.90, "minus_10pct"),
        (1.00, "baseline"),
        (1.10, "plus_10pct"),
        (1.20, "plus_20pct"),
    ]
    
    configs = []
    for multiplier, label in multipliers:
        config = ExperimentConfig(
            experiment_id=f"duration_{label}",
            family=ExperimentFamily.MISSION_DURATION,
            baseline_duration=baseline_duration,
            duration_multiplier=multiplier,
            enable_narrative=enable_narrative,
            metadata={"label": label},
        )
        configs.append(config)
    
    print("\n=== Mission Duration Sweep ===")
    print(f"Baseline: {baseline_duration} days")
    print(f"Variants: {len(configs)}")
    print()
    
    results = harness.run_batch(configs)
    
    print(f"\n✓ Duration sweep completed: {len(results)} runs")
    return results


def run_crew_composition_sweep(
    baseline_duration: int = 200,
    harness: ExperimentHarness = None,
    enable_narrative: bool = False,
) -> List[ExperimentResult]:
    """
    Run Experiment 2: Crew Composition Sweep
    
    Tests sensitivity to dyadic compatibility while holding average traits constant.
    
    Creates crews with:
    - Same average Big Five scores
    - Different dyadic compatibility structures
    
    Args:
        baseline_duration: Mission length in days (held constant)
        harness: Optional existing harness (creates new if None)
        enable_narrative: Whether to enable Phase C narratives
        
    Returns:
        List of experiment results for each crew variant
    """
    if harness is None:
        harness = ExperimentHarness()
    
    # Define crew profiles with same average but different dyadic compatibility
    crews = _create_crew_variants()
    
    configs = []
    for i, crew in enumerate(crews, 1):
        config = ExperimentConfig(
            experiment_id=f"crew_variant_{i}",
            family=ExperimentFamily.CREW_COMPOSITION,
            baseline_duration=baseline_duration,
            duration_multiplier=1.0,
            crew_profile=crew,
            enable_narrative=enable_narrative,
            metadata={"crew_name": crew.crew_name},
        )
        configs.append(config)
    
    print("\n=== Crew Composition Sweep ===")
    print(f"Mission duration: {baseline_duration} days (constant)")
    print(f"Crew variants: {len(configs)}")
    print()
    
    results = harness.run_batch(configs)
    
    print(f"\n✓ Crew composition sweep completed: {len(results)} runs")
    return results


def run_intervention_timing_sweep(
    baseline_duration: int = 200,
    harness: ExperimentHarness = None,
    enable_narrative: bool = False,
) -> List[ExperimentResult]:
    """
    Run Experiment 3: Intervention Timing Sweep
    
    Tests intervention effectiveness at different mission phases:
    - No intervention (control)
    - Early intervention (day 40 = ~20% through 200-day mission)
    - Late intervention (day 140 = ~70% through 200-day mission)
    
    Note: This creates the experimental framework. Actual intervention
    mechanisms would be implemented in Phase B if needed.
    
    Args:
        baseline_duration: Mission length in days (default: 200)
        harness: Optional existing harness (creates new if None)
        enable_narrative: Whether to enable Phase C narratives
        
    Returns:
        List of experiment results for each intervention timing
    """
    if harness is None:
        harness = ExperimentHarness()
    
    # Define intervention timings
    # Early = ~20% through mission, Late = ~70% through mission
    early_day = int(baseline_duration * 0.2)
    late_day = int(baseline_duration * 0.7)
    
    interventions = [
        (None, "no_intervention"),
        (early_day, "early_intervention"),
        (late_day, "late_intervention"),
    ]
    
    configs = []
    for intervention_day, label in interventions:
        config = ExperimentConfig(
            experiment_id=f"intervention_{label}",
            family=ExperimentFamily.INTERVENTION_TIMING,
            baseline_duration=baseline_duration,
            duration_multiplier=1.0,
            intervention_day=intervention_day,
            enable_narrative=enable_narrative,
            metadata={"label": label},
        )
        configs.append(config)
    
    print("\n=== Intervention Timing Sweep ===")
    print(f"Mission duration: {baseline_duration} days")
    print(f"Early intervention: day {early_day}")
    print(f"Late intervention: day {late_day}")
    print()
    
    results = harness.run_batch(configs)
    
    print(f"\n✓ Intervention timing sweep completed: {len(results)} runs")
    return results


def _create_crew_variants() -> List[CrewProfile]:
    """
    Create crew variants with same average traits but different dyadic compatibility.
    
    Strategy:
    - All crews have same average Big Five scores (O=0.6, C=0.7, E=0.5, A=0.6, N=0.4)
    - Variant 1: Homogeneous crew (all similar)
    - Variant 2: Polarized crew (high variance)
    - Variant 3: Balanced crew (moderate variance with complementary roles)
    
    Returns:
        List of CrewProfile objects
    """
    
    # Variant 1: Homogeneous - all members similar
    crew_homogeneous = CrewProfile(
        crew_name="Homogeneous Crew",
        members=[
            CrewMember(
                name="Alice",
                role="Commander",
                personality=PersonalityScores(
                    openness=0.6, conscientiousness=0.7, extraversion=0.5,
                    agreeableness=0.6, neuroticism=0.4
                )
            ),
            CrewMember(
                name="Bob",
                role="Engineer",
                personality=PersonalityScores(
                    openness=0.6, conscientiousness=0.7, extraversion=0.5,
                    agreeableness=0.6, neuroticism=0.4
                )
            ),
            CrewMember(
                name="Carol",
                role="Scientist",
                personality=PersonalityScores(
                    openness=0.6, conscientiousness=0.7, extraversion=0.5,
                    agreeableness=0.6, neuroticism=0.4
                )
            ),
        ]
    )
    
    # Variant 2: Polarized - high variance, potential conflicts
    crew_polarized = CrewProfile(
        crew_name="Polarized Crew",
        members=[
            CrewMember(
                name="David",
                role="Commander",
                personality=PersonalityScores(
                    openness=0.9, conscientiousness=0.9, extraversion=0.8,
                    agreeableness=0.9, neuroticism=0.1
                )
            ),
            CrewMember(
                name="Eve",
                role="Engineer",
                personality=PersonalityScores(
                    openness=0.3, conscientiousness=0.5, extraversion=0.2,
                    agreeableness=0.3, neuroticism=0.7
                )
            ),
            CrewMember(
                name="Frank",
                role="Scientist",
                personality=PersonalityScores(
                    openness=0.6, conscientiousness=0.7, extraversion=0.5,
                    agreeableness=0.6, neuroticism=0.4
                )
            ),
        ]
    )
    
    # Variant 3: Balanced - moderate variance, complementary
    crew_balanced = CrewProfile(
        crew_name="Balanced Crew",
        members=[
            CrewMember(
                name="Grace",
                role="Commander",
                personality=PersonalityScores(
                    openness=0.7, conscientiousness=0.8, extraversion=0.6,
                    agreeableness=0.7, neuroticism=0.3
                )
            ),
            CrewMember(
                name="Henry",
                role="Engineer",
                personality=PersonalityScores(
                    openness=0.5, conscientiousness=0.7, extraversion=0.4,
                    agreeableness=0.5, neuroticism=0.5
                )
            ),
            CrewMember(
                name="Iris",
                role="Scientist",
                personality=PersonalityScores(
                    openness=0.6, conscientiousness=0.6, extraversion=0.5,
                    agreeableness=0.6, neuroticism=0.4
                )
            ),
        ]
    )
    
    return [crew_homogeneous, crew_polarized, crew_balanced]
