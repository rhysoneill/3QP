"""
Quick test to verify crew preset integration works
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crew import get_crew_preset, PersonalityToConfigMapper, list_available_presets

# Test 1: List available presets
print("Available crew presets:")
for preset in list_available_presets():
    print(f"  - {preset}")
print()

# Test 2: Load and map each preset
mapper = PersonalityToConfigMapper()

for preset_name in list_available_presets():
    print(f"\n{'='*60}")
    print(f"Testing preset: {preset_name}")
    print('='*60)
    
    crew = get_crew_preset(preset_name)
    print(f"Crew: {crew.crew_name}")
    print(f"Members: {len(crew.members)}")
    
    # Show aggregate traits
    traits = crew.aggregate_traits()
    print(f"\nAggregate personality traits:")
    print(f"  Openness:          {traits.openness:.3f}")
    print(f"  Conscientiousness: {traits.conscientiousness:.3f}")
    print(f"  Extraversion:      {traits.extraversion:.3f}")
    print(f"  Agreeableness:     {traits.agreeableness:.3f}")
    print(f"  Neuroticism:       {traits.neuroticism:.3f}")
    
    # Map to config
    config = mapper.map_to_ruthless_config(crew, mission_length_days=200)
    
    print(f"\nMapped RuthlessCoreConfig parameters:")
    print(f"  initial_strain:    {config.initial_strain:.4f}")
    print(f"  q_peak:            {config.q_peak:.4f}")
    print(f"  s_workload:        {config.s_workload:.4f}")
    print(f"  c_rebound:         {config.c_rebound:.4f}")
    print(f"  c_strain:          {config.c_strain:.4f}")
    print(f"  c_q:               {config.c_q:.4f}")
    print(f"  m_base:            {config.m_base:.4f}")
    print(f"  m_novelty:         {config.m_novelty:.4f}")
    print(f"  c_shared_success:  {config.c_shared_success:.4f}")

print(f"\n{'='*60}")
print("All crew presets mapped successfully!")
print('='*60)
