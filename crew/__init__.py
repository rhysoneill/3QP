"""
Crew Profile Layer for 3QP

Provides personality-based crew configuration interface for the
Ruthless Core Model.
"""

from .profile import PersonalityScores, CrewMember, CrewProfile
from .personality_to_config import PersonalityToConfigMapper
from .examples import get_crew_preset, list_available_presets

__all__ = [
    "PersonalityScores",
    "CrewMember", 
    "CrewProfile",
    "PersonalityToConfigMapper",
    "get_crew_preset",
    "list_available_presets",
]
