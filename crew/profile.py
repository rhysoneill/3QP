"""
Crew Profile Data Structures

Defines dataclasses for representing crew members with personality traits
based on the Big Five personality model (OCEAN).

This module does NOT modify any core dynamics - it provides a clean
interface for describing crews in terms of psychological traits.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class PersonalityScores:
    """
    Big Five personality trait scores (OCEAN model).
    
    All scores are normalized to [0.0, 1.0] range where:
    - 0.0 = extremely low on this trait
    - 0.5 = average/moderate
    - 1.0 = extremely high on this trait
    
    Attributes:
        openness: Openness to experience (curious, creative vs. conventional)
        conscientiousness: Conscientiousness (organized, disciplined vs. careless)
        extraversion: Extraversion (outgoing, energetic vs. introverted)
        agreeableness: Agreeableness (cooperative, compassionate vs. competitive)
        neuroticism: Neuroticism (anxious, emotionally reactive vs. stable)
    """
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    def __post_init__(self):
        """Validate that all scores are in valid range."""
        traits = [
            ("openness", self.openness),
            ("conscientiousness", self.conscientiousness),
            ("extraversion", self.extraversion),
            ("agreeableness", self.agreeableness),
            ("neuroticism", self.neuroticism)
        ]
        
        for name, value in traits:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be in range [0.0, 1.0], got {value}"
                )


@dataclass
class CrewMember:
    """
    Individual crew member with role and personality.
    
    Attributes:
        name: Crew member's name
        role: Mission role (e.g., "Commander", "Engineer", "Pilot")
        personality: Big Five personality scores
    """
    name: str
    role: str
    personality: PersonalityScores


@dataclass
class CrewProfile:
    """
    Complete crew profile for a mission.
    
    Attributes:
        crew_name: Human-readable identifier for this crew
        members: List of crew members
    """
    crew_name: str
    members: List[CrewMember]
    
    def aggregate_traits(self) -> PersonalityScores:
        """
        Compute average Big Five scores across all crew members.
        
        Returns:
            PersonalityScores with mean values across the crew
        """
        if not self.members:
            return PersonalityScores()
        
        n = len(self.members)
        
        avg_openness = sum(m.personality.openness for m in self.members) / n
        avg_conscientiousness = sum(m.personality.conscientiousness for m in self.members) / n
        avg_extraversion = sum(m.personality.extraversion for m in self.members) / n
        avg_agreeableness = sum(m.personality.agreeableness for m in self.members) / n
        avg_neuroticism = sum(m.personality.neuroticism for m in self.members) / n
        
        return PersonalityScores(
            openness=avg_openness,
            conscientiousness=avg_conscientiousness,
            extraversion=avg_extraversion,
            agreeableness=avg_agreeableness,
            neuroticism=avg_neuroticism
        )
