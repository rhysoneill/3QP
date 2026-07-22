"""
Comprehensive Demo of Crew Profile System

This script demonstrates the complete crew profile system, showing:
1. How personality traits map to model parameters
2. How different crews produce different simulation outcomes
3. The interpretability of the mapping
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from crew import get_crew_preset, PersonalityToConfigMapper, list_available_presets
from runtime_config import RuntimeConfig
from mission_runner import run_mission

print("="*70)
print("3QP Crew Profile System - Comprehensive Demo")
print("="*70)
print()

print("Available crew presets:")
for preset in list_available_presets():
    crew = get_crew_preset(preset)
    print(f"  • {preset}: {crew.crew_name}")
print()

# Compare three crews
crews_to_compare = ["high_cohesion_team", "fragile_team", "extroverted_explorers"]

print("="*70)
print("Comparing Crew Profiles and Outcomes")
print("="*70)
print()

mapper = PersonalityToConfigMapper()
results = []

for preset_name in crews_to_compare:
    print(f"\n{'─'*70}")
    print(f"CREW: {preset_name.replace('_', ' ').title()}")
    print('─'*70)
    
    # Load crew
    crew = get_crew_preset(preset_name)
    traits = crew.aggregate_traits()
    
    print(f"\nPersonality Profile (aggregate):")
    print(f"  Openness:          {traits.openness:.3f}")
    print(f"  Conscientiousness: {traits.conscientiousness:.3f}")
    print(f"  Extraversion:      {traits.extraversion:.3f}")
    print(f"  Agreeableness:     {traits.agreeableness:.3f}")
    print(f"  Neuroticism:       {traits.neuroticism:.3f}")
    
    # Map to config
    config = mapper.map_to_ruthless_config(crew, mission_length_days=200)
    
    print(f"\nKey Mapped Parameters:")
    print(f"  Initial strain:    {config.initial_strain:.4f} (neuroticism → start stress)")
    print(f"  TQ peak:           {config.q_peak:.4f} (neuroticism → TQ sensitivity)")
    print(f"  Workload stress:   {config.s_workload:.4f} (conscientiousness → workload mgmt)")
    print(f"  Cohesion vs strain:{config.c_strain:.4f} (agreeableness → cohesion resilience)")
    print(f"  Monotony buildup:  {config.m_base:.4f} (extraversion → isolation sensitivity)")
    print(f"  Novelty benefit:   {config.m_novelty:.4f} (extraversion+openness → novelty response)")
    
    # Run quick simulation
    print(f"\nRunning simulation...")
    runtime_config = RuntimeConfig(
        mission_name=f"{preset_name}_demo",
        mission_length_days=200,
        output_dir="output",
        enable_validation=False,
        enable_logging=False,
        verbose=False
    )
    
    result = run_mission(runtime_config, core_config=config)
    
    # Extract key metrics
    metrics = {
        'crew_name': crew.crew_name,
        'preset': preset_name,
        'initial_cohesion': result.core_output.cohesion[0],
        'min_cohesion': min(result.core_output.cohesion),
        'min_cohesion_day': result.core_output.cohesion.index(min(result.core_output.cohesion)),
        'final_cohesion': result.core_output.cohesion[-1],
        'max_strain': max(result.core_output.strain),
        'initial_strain': result.core_output.strain[0],
        'trajectory': result.trajectory_result['archetype_id'],
        'traits': traits,
    }
    results.append(metrics)
    
    print(f"\nSimulation Results:")
    print(f"  Initial cohesion:  {metrics['initial_cohesion']:.3f}")
    print(f"  Minimum cohesion:  {metrics['min_cohesion']:.3f} (day {metrics['min_cohesion_day']})")
    print(f"  Final cohesion:    {metrics['final_cohesion']:.3f}")
    print(f"  Initial strain:    {metrics['initial_strain']:.3f}")
    print(f"  Maximum strain:    {metrics['max_strain']:.3f}")
    print(f"  Trajectory type:   {metrics['trajectory']}")

# Summary comparison
print("\n" + "="*70)
print("COMPARATIVE SUMMARY")
print("="*70)
print()

print(f"{'Crew':<25} {'Min Cohesion':<15} {'Max Strain':<15} {'Final Cohesion':<15}")
print("─"*70)
for r in results:
    print(f"{r['crew_name']:<25} {r['min_cohesion']:<15.3f} {r['max_strain']:<15.3f} {r['final_cohesion']:<15.3f}")

print()
print("Key Insights:")
print("─"*70)

# Find best and worst
best_cohesion = max(results, key=lambda x: x['min_cohesion'])
worst_cohesion = min(results, key=lambda x: x['min_cohesion'])

print(f"\n1. COHESION RESILIENCE:")
print(f"   Best:  {best_cohesion['crew_name']}")
print(f"          High agreeableness ({best_cohesion['traits'].agreeableness:.2f}) → ")
print(f"          cohesion resilient to stress")
print(f"   Worst: {worst_cohesion['crew_name']}")
print(f"          Lower agreeableness ({worst_cohesion['traits'].agreeableness:.2f}) → ")
print(f"          cohesion more vulnerable")

most_stressed = max(results, key=lambda x: x['max_strain'])
least_stressed = min(results, key=lambda x: x['max_strain'])

print(f"\n2. STRESS ACCUMULATION:")
print(f"   Highest: {most_stressed['crew_name']}")
print(f"            High neuroticism ({most_stressed['traits'].neuroticism:.2f}) → ")
print(f"            more strain buildup")
print(f"   Lowest:  {least_stressed['crew_name']}")
print(f"            Low neuroticism ({least_stressed['traits'].neuroticism:.2f}) → ")
print(f"            better stress management")

print()
print("="*70)
print("Demonstration complete!")
print()
print("The crew profile system successfully maps personality traits to")
print("simulation outcomes in a transparent, interpretable way.")
print("="*70)
