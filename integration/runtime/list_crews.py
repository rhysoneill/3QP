"""
List Available Crew Presets

Simple utility to show all available crew presets and their characteristics.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crew import get_crew_preset, list_available_presets

print("="*70)
print("Available Crew Presets for 3QP Simulation")
print("="*70)
print()

for preset_name in sorted(list_available_presets()):
    crew = get_crew_preset(preset_name)
    traits = crew.aggregate_traits()
    
    print(f"Preset: {preset_name}")
    print(f"  Name: {crew.crew_name}")
    print(f"  Size: {len(crew.members)} members")
    print(f"  Aggregate Personality:")
    print(f"    O: {traits.openness:.2f}  C: {traits.conscientiousness:.2f}  "
          f"E: {traits.extraversion:.2f}  A: {traits.agreeableness:.2f}  "
          f"N: {traits.neuroticism:.2f}")
    print()

print("="*70)
print("Usage:")
print("  python run_simulation.py --config <config.json>")
print()
print("Where config.json includes:")
print('  "crew_preset": "high_cohesion_team"')
print("="*70)
