"""
Example Crew Profiles

Provides pre-configured crew profiles with different personality
compositions for testing and demonstration purposes.

These examples are designed to produce meaningfully different
RuthlessCoreConfig outputs when mapped through PersonalityToConfigMapper.
"""

from .profile import PersonalityScores, CrewMember, CrewProfile


# Example 1: High Cohesion Team
# Characteristics: Agreeable, emotionally stable, conscientious
# Expected behavior: Resilient cohesion, good stress management, stable TQ response

high_cohesion_team = CrewProfile(
    crew_name="High Cohesion Team",
    members=[
        CrewMember(
            name="Commander Sarah Chen",
            role="Commander",
            personality=PersonalityScores(
                openness=0.7,           # Curious and adaptable
                conscientiousness=0.8,  # Highly organized
                extraversion=0.6,       # Moderately social
                agreeableness=0.8,      # Very cooperative
                neuroticism=0.2         # Emotionally stable
            )
        ),
        CrewMember(
            name="Engineer Marcus Rodriguez",
            role="Flight Engineer",
            personality=PersonalityScores(
                openness=0.6,
                conscientiousness=0.85,  # Extremely disciplined
                extraversion=0.5,
                agreeableness=0.75,      # Cooperative
                neuroticism=0.25         # Stable
            )
        ),
        CrewMember(
            name="Pilot Lisa Anderson",
            role="Pilot",
            personality=PersonalityScores(
                openness=0.65,
                conscientiousness=0.75,
                extraversion=0.55,
                agreeableness=0.80,      # Very agreeable
                neuroticism=0.20         # Very stable
            )
        ),
        CrewMember(
            name="Medical Officer Raj Patel",
            role="Medical Officer",
            personality=PersonalityScores(
                openness=0.75,           # Open and curious
                conscientiousness=0.70,
                extraversion=0.65,
                agreeableness=0.85,      # Extremely agreeable
                neuroticism=0.30         # Stable
            )
        )
    ]
)


# Example 2: Fragile Team
# Characteristics: Higher neuroticism, lower agreeableness, more introverted
# Expected behavior: Higher strain accumulation, cohesion more vulnerable,
# stronger TQ impact

fragile_team = CrewProfile(
    crew_name="Fragile Team",
    members=[
        CrewMember(
            name="Commander Tom Harrison",
            role="Commander",
            personality=PersonalityScores(
                openness=0.5,
                conscientiousness=0.6,
                extraversion=0.35,       # Introverted
                agreeableness=0.45,      # Less cooperative
                neuroticism=0.65         # High anxiety/stress reactivity
            )
        ),
        CrewMember(
            name="Engineer Kate Wilson",
            role="Flight Engineer",
            personality=PersonalityScores(
                openness=0.45,
                conscientiousness=0.55,  # Less organized
                extraversion=0.30,       # Very introverted
                agreeableness=0.40,      # Low agreeableness
                neuroticism=0.70         # High neuroticism
            )
        ),
        CrewMember(
            name="Pilot James Foster",
            role="Pilot",
            personality=PersonalityScores(
                openness=0.50,
                conscientiousness=0.65,
                extraversion=0.40,       # Introverted
                agreeableness=0.50,      # Moderate
                neuroticism=0.60         # Moderately high neuroticism
            )
        ),
        CrewMember(
            name="Medical Officer Emily Carter",
            role="Medical Officer",
            personality=PersonalityScores(
                openness=0.55,
                conscientiousness=0.70,
                extraversion=0.45,
                agreeableness=0.55,
                neuroticism=0.55         # Moderately high neuroticism
            )
        )
    ]
)


# Example 3: Extroverted Explorer Team
# Characteristics: High extraversion and openness, moderate on other traits
# Expected behavior: More sensitive to monotony but highly responsive to novelty,
# good shared success benefits

extroverted_explorers = CrewProfile(
    crew_name="Extroverted Explorers",
    members=[
        CrewMember(
            name="Commander Alex Rivera",
            role="Commander",
            personality=PersonalityScores(
                openness=0.85,           # Very open/curious
                conscientiousness=0.65,
                extraversion=0.80,       # Very extraverted
                agreeableness=0.70,
                neuroticism=0.40
            )
        ),
        CrewMember(
            name="Engineer Sofia Nakamura",
            role="Flight Engineer",
            personality=PersonalityScores(
                openness=0.80,           # Very open
                conscientiousness=0.70,
                extraversion=0.75,       # Highly extraverted
                agreeableness=0.65,
                neuroticism=0.35
            )
        ),
        CrewMember(
            name="Pilot David Kim",
            role="Pilot",
            personality=PersonalityScores(
                openness=0.75,
                conscientiousness=0.60,
                extraversion=0.85,       # Extremely extraverted
                agreeableness=0.60,
                neuroticism=0.45
            )
        ),
        CrewMember(
            name="Medical Officer Maya Johnson",
            role="Medical Officer",
            personality=PersonalityScores(
                openness=0.90,           # Extremely open
                conscientiousness=0.65,
                extraversion=0.70,       # Extraverted
                agreeableness=0.75,
                neuroticism=0.30
            )
        )
    ]
)


# Registry of all available crew presets
_CREW_PRESETS = {
    "high_cohesion_team": high_cohesion_team,
    "fragile_team": fragile_team,
    "extroverted_explorers": extroverted_explorers,
}


def get_crew_preset(name: str) -> CrewProfile:
    """
    Get a crew profile by preset name.
    
    Args:
        name: Name of the crew preset
        
    Returns:
        CrewProfile instance
        
    Raises:
        KeyError: If preset name not found
    """
    if name not in _CREW_PRESETS:
        available = ", ".join(_CREW_PRESETS.keys())
        raise KeyError(
            f"Unknown crew preset '{name}'. "
            f"Available presets: {available}"
        )
    
    return _CREW_PRESETS[name]


def list_available_presets() -> list:
    """
    Get list of all available crew preset names.
    
    Returns:
        List of preset names
    """
    return list(_CREW_PRESETS.keys())
