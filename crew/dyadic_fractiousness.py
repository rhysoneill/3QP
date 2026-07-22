"""
Dyadic Fractiousness Analysis

Estimates how fractured a crew's third-quarter collapse is by analyzing
pairwise (dyadic) cohesion trajectories based on personality compatibility
and global cohesion time series.

This module does NOT modify core dynamics - it performs post-hoc analysis
of existing cohesion data to understand interpersonal variation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import statistics

from crew.profile import CrewProfile, CrewMember, PersonalityScores


@dataclass
class PairCohesionResult:
    """
    Results for a single crew member pair's cohesion trajectory.
    
    Attributes:
        member_i: First member's name
        member_j: Second member's name
        compatibility_score: Personality-based compatibility [0.0, 1.0]
        min_cohesion: Lowest cohesion value reached by this pair
        min_cohesion_day: Day index when minimum cohesion occurred
        min_cohesion_progress: Mission progress when minimum occurred [0.0, 1.0]
        final_cohesion: Final cohesion value for this pair
    """
    member_i: str
    member_j: str
    compatibility_score: float
    min_cohesion: float
    min_cohesion_day: int
    min_cohesion_progress: float
    final_cohesion: float


@dataclass
class DyadicFractiousnessSummary:
    """
    Summary of dyadic fractiousness analysis for entire crew.
    
    Attributes:
        fractiousness_index: Standard deviation of pairwise min_cohesion values
                           (higher = more fractured collapse patterns)
        pair_results: Individual results for all crew member pairs
        metadata: Additional metrics (num_pairs, min/max values, etc.)
    """
    fractiousness_index: float
    pair_results: List[PairCohesionResult]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DyadicFractiousnessModel:
    """
    Analyzes pairwise cohesion trajectories to measure crew fractiousness.
    
    The model uses personality compatibility to modulate global cohesion
    into pair-specific trajectories, then measures how uniformly (or not)
    different pairs experience their minimum cohesion.
    """
    
    def __init__(self, agreeableness_weight: float = 1.5, neuroticism_weight: float = 1.5):
        """
        Initialize the dyadic fractiousness model.
        
        Args:
            agreeableness_weight: Weight for agreeableness trait in compatibility
            neuroticism_weight: Weight for neuroticism trait in compatibility
        """
        self.agreeableness_weight = agreeableness_weight
        self.neuroticism_weight = neuroticism_weight
    
    def compute_compatibility(
        self, 
        personality_i: PersonalityScores, 
        personality_j: PersonalityScores
    ) -> float:
        """
        Compute personality-based compatibility between two crew members.
        
        Uses Big Five trait distances with optional weighting for traits
        that are particularly important for interpersonal dynamics:
        - Agreeableness (cooperation, compassion)
        - Neuroticism (emotional stability)
        
        Args:
            personality_i: First member's personality scores
            personality_j: Second member's personality scores
            
        Returns:
            Compatibility score in [0.0, 1.0] where:
            - 1.0 = identical personalities (maximally compatible)
            - 0.0 = maximally different personalities
        """
        # Compute weighted trait distances
        # Agreeableness and neuroticism are weighted more heavily because:
        # - Agreeableness affects cooperative behavior under stress
        # - Neuroticism affects emotional regulation and conflict escalation
        
        distances = [
            abs(personality_i.openness - personality_j.openness),
            abs(personality_i.conscientiousness - personality_j.conscientiousness),
            abs(personality_i.extraversion - personality_j.extraversion),
            self.agreeableness_weight * abs(personality_i.agreeableness - personality_j.agreeableness),
            self.neuroticism_weight * abs(personality_i.neuroticism - personality_j.neuroticism),
        ]
        
        # Total possible weighted distance
        total_weight = 3.0 + self.agreeableness_weight + self.neuroticism_weight
        
        # Average weighted distance
        avg_distance = sum(distances) / total_weight
        
        # Convert distance to compatibility (inverse relationship)
        compatibility = 1.0 - avg_distance
        
        # Clamp to valid range (should already be valid, but ensure it)
        return max(0.0, min(1.0, compatibility))
    
    def compute_pairwise_cohesion(
        self, 
        global_cohesion: List[float], 
        compatibility: float
    ) -> List[float]:
        """
        Compute pairwise cohesion trajectory from global cohesion.
        
        More compatible pairs track above the global cohesion curve,
        less compatible pairs track below it.
        
        Formula: pair_cohesion(t) = global_cohesion(t) * (0.5 + 0.5 * compatibility)
        
        This ensures:
        - compatibility = 1.0 (perfect): pair tracks at 100% of global
        - compatibility = 0.5 (neutral): pair tracks at 75% of global
        - compatibility = 0.0 (minimum): pair tracks at 50% of global
        
        Args:
            global_cohesion: Time series of global cohesion values
            compatibility: Compatibility score [0.0, 1.0]
            
        Returns:
            Pairwise cohesion time series
        """
        scaling_factor = 0.5 + 0.5 * compatibility
        return [c * scaling_factor for c in global_cohesion]
    
    def analyze_pair(
        self,
        member_i: CrewMember,
        member_j: CrewMember,
        global_cohesion: List[float]
    ) -> PairCohesionResult:
        """
        Analyze cohesion trajectory for a single pair of crew members.
        
        Args:
            member_i: First crew member
            member_j: Second crew member
            global_cohesion: Global cohesion time series
            
        Returns:
            PairCohesionResult with trajectory analysis
        """
        # Compute personality compatibility
        compatibility = self.compute_compatibility(
            member_i.personality,
            member_j.personality
        )
        
        # Generate pairwise cohesion trajectory
        pair_cohesion = self.compute_pairwise_cohesion(global_cohesion, compatibility)
        
        # Find minimum cohesion and when it occurred
        min_cohesion = min(pair_cohesion)
        min_cohesion_day = pair_cohesion.index(min_cohesion)
        
        # Compute mission progress at minimum (0.0 to 1.0)
        mission_length = len(global_cohesion)
        min_cohesion_progress = min_cohesion_day / (mission_length - 1) if mission_length > 1 else 0.0
        
        # Get final cohesion
        final_cohesion = pair_cohesion[-1]
        
        return PairCohesionResult(
            member_i=member_i.name,
            member_j=member_j.name,
            compatibility_score=compatibility,
            min_cohesion=min_cohesion,
            min_cohesion_day=min_cohesion_day,
            min_cohesion_progress=min_cohesion_progress,
            final_cohesion=final_cohesion
        )
    
    def analyze(
        self,
        crew: CrewProfile,
        global_cohesion: List[float]
    ) -> DyadicFractiousnessSummary:
        """
        Perform full dyadic fractiousness analysis for a crew.
        
        Generates all unique pairs of crew members, computes their
        compatibility-modulated cohesion trajectories, and measures
        how uniformly (or not) the crew experiences third-quarter collapse.
        
        Args:
            crew: CrewProfile with personality data for all members
            global_cohesion: Global cohesion time series from mission
            
        Returns:
            DyadicFractiousnessSummary with fractiousness metrics and
            detailed pair-by-pair results
        """
        if len(crew.members) < 2:
            # Edge case: need at least 2 members for dyadic analysis
            return DyadicFractiousnessSummary(
                fractiousness_index=0.0,
                pair_results=[],
                metadata={
                    "num_pairs": 0,
                    "num_members": len(crew.members),
                    "error": "Need at least 2 crew members for dyadic analysis"
                }
            )
        
        # Generate all unique pairs (i, j) where i < j
        pair_results = []
        for i in range(len(crew.members)):
            for j in range(i + 1, len(crew.members)):
                pair_result = self.analyze_pair(
                    crew.members[i],
                    crew.members[j],
                    global_cohesion
                )
                pair_results.append(pair_result)
        
        # Extract min_cohesion values for all pairs
        min_cohesions = [pr.min_cohesion for pr in pair_results]
        
        # Compute fractiousness index as standard deviation of min_cohesion
        # Higher std dev = more fractured (some pairs collapse much more than others)
        # Lower std dev = more uniform (all pairs experience similar collapse)
        if len(min_cohesions) > 1:
            fractiousness_index = statistics.stdev(min_cohesions)
        elif len(min_cohesions) == 1:
            # Only one pair - no variation possible
            fractiousness_index = 0.0
        else:
            fractiousness_index = 0.0
        
        # Compute metadata
        metadata = {
            "num_pairs": len(pair_results),
            "num_members": len(crew.members),
            "min_of_min_cohesion": min(min_cohesions) if min_cohesions else 0.0,
            "max_of_min_cohesion": max(min_cohesions) if min_cohesions else 0.0,
            "mean_min_cohesion": statistics.mean(min_cohesions) if min_cohesions else 0.0,
            "mean_compatibility": statistics.mean(
                pr.compatibility_score for pr in pair_results
            ) if pair_results else 0.0,
        }
        
        return DyadicFractiousnessSummary(
            fractiousness_index=fractiousness_index,
            pair_results=pair_results,
            metadata=metadata
        )
