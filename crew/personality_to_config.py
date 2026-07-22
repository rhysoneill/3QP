"""
Personality to RuthlessCoreConfig Mapper

Maps Big Five personality traits to Ruthless Core Model parameters in a
transparent, deterministic way.

This module does NOT modify the core engine - it only provides a mapping
layer from psychological traits to model configuration.

Mapping Logic:
--------------
The mapping is designed to be interpretable and align with psychological
research on how personality traits relate to stress, social dynamics, and
adaptation in isolated confined environments (ICE).

Neuroticism (emotional instability):
  - Higher neuroticism -> higher initial_strain (start more stressed)
  - Higher neuroticism -> slightly higher q_peak (more sensitive to TQ pressure)

Conscientiousness (discipline, organization):
  - Higher conscientiousness -> lower s_workload (better at managing workload)
  - Higher conscientiousness -> higher c_rebound (better recovery post-TQ)

Agreeableness (cooperativeness):
  - Higher agreeableness -> lower c_strain (cohesion less affected by stress)
  - Higher agreeableness -> lower c_q (cohesion more resilient to TQ pressure)

Extraversion (social engagement):
  - Higher extraversion -> higher m_base (more sensitive to monotony/isolation)
  - Higher extraversion -> higher m_novelty (greater benefit from social novelty)

Openness (curiosity, adaptability):
  - Higher openness -> higher m_novelty (more benefit from novel experiences)
  - Higher openness -> higher c_shared_success (more engaged in shared goals)

All mappings use linear interpolation between baseline values and adjusted
values to keep parameters within reasonable ranges.
"""

import sys
from pathlib import Path

# Import RuthlessCoreConfig from Phase 4 without modifying it
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4" / "06_Ruthless_Core_Model"))
from ruthless_core import RuthlessCoreConfig

# Import our crew profile structures
from .profile import CrewProfile, PersonalityScores


class PersonalityToConfigMapper:
    """
    Maps crew personality profiles to RuthlessCoreConfig parameters.
    
    The mapping is deterministic and interpretable - given the same crew
    profile and mission length, it will always produce the same configuration.
    """
    
    # Baseline values (match RuthlessCoreConfig defaults)
    BASELINE_INITIAL_STRAIN = 0.0
    BASELINE_Q_PEAK = 0.55
    BASELINE_S_WORKLOAD = 0.03
    BASELINE_C_REBOUND = 0.01
    BASELINE_C_STRAIN = 0.008
    BASELINE_C_Q = 0.033
    BASELINE_M_BASE = 0.008
    BASELINE_M_NOVELTY = 0.2
    BASELINE_C_SHARED_SUCCESS = 0.06
    
    def __init__(self):
        """Initialize the mapper."""
        pass
    
    def map_to_ruthless_config(
        self, 
        crew: CrewProfile, 
        mission_length_days: int
    ) -> RuthlessCoreConfig:
        """
        Map crew personality profile to RuthlessCoreConfig.
        
        Args:
            crew: CrewProfile with personality data
            mission_length_days: Mission duration in days
            
        Returns:
            RuthlessCoreConfig configured based on crew personality
        """
        # Get aggregate personality traits
        traits = crew.aggregate_traits()
        
        # Map personality to config parameters
        config_params = {
            "mission_length_days": mission_length_days,
        }
        
        # Neuroticism affects initial strain and TQ sensitivity
        # Higher neuroticism = more initial strain and stronger TQ response
        config_params["initial_strain"] = self._map_neuroticism_to_initial_strain(
            traits.neuroticism
        )
        config_params["q_peak"] = self._map_neuroticism_to_q_peak(
            traits.neuroticism
        )
        
        # Conscientiousness affects workload management and recovery
        # Higher conscientiousness = better workload handling and recovery
        config_params["s_workload"] = self._map_conscientiousness_to_s_workload(
            traits.conscientiousness
        )
        config_params["c_rebound"] = self._map_conscientiousness_to_c_rebound(
            traits.conscientiousness
        )
        
        # Agreeableness affects cohesion resilience
        # Higher agreeableness = cohesion less affected by strain and TQ
        config_params["c_strain"] = self._map_agreeableness_to_c_strain(
            traits.agreeableness
        )
        config_params["c_q"] = self._map_agreeableness_to_c_q(
            traits.agreeableness
        )
        
        # Extraversion affects monotony sensitivity and novelty benefit
        # Higher extraversion = more affected by isolation but more responsive to novelty
        config_params["m_base"] = self._map_extraversion_to_m_base(
            traits.extraversion
        )
        config_params["m_novelty"] = self._map_extraversion_to_m_novelty(
            traits.extraversion
        )
        
        # Openness affects novelty benefit and shared success impact
        # Higher openness = more benefit from novel experiences and shared goals
        config_params["m_novelty"] = self._adjust_for_openness_m_novelty(
            config_params["m_novelty"],
            traits.openness
        )
        config_params["c_shared_success"] = self._map_openness_to_c_shared_success(
            traits.openness
        )
        
        return RuthlessCoreConfig(**config_params)
    
    # Neuroticism mappings
    
    def _map_neuroticism_to_initial_strain(self, neuroticism: float) -> float:
        """
        Map neuroticism to initial strain.
        
        Higher neuroticism -> higher starting strain (0.0 to 0.15 range)
        """
        return 0.0 + (neuroticism * 0.15)
    
    def _map_neuroticism_to_q_peak(self, neuroticism: float) -> float:
        """
        Map neuroticism to TQ peak amplitude.
        
        Higher neuroticism -> slightly stronger TQ response (0.50 to 0.65 range)
        """
        return 0.50 + (neuroticism * 0.15)
    
    # Conscientiousness mappings
    
    def _map_conscientiousness_to_s_workload(self, conscientiousness: float) -> float:
        """
        Map conscientiousness to workload strain coefficient.
        
        Higher conscientiousness -> lower workload impact (0.035 down to 0.020)
        """
        return 0.035 - (conscientiousness * 0.015)
    
    def _map_conscientiousness_to_c_rebound(self, conscientiousness: float) -> float:
        """
        Map conscientiousness to cohesion rebound rate.
        
        Higher conscientiousness -> better recovery (0.008 up to 0.015)
        """
        return 0.008 + (conscientiousness * 0.007)
    
    # Agreeableness mappings
    
    def _map_agreeableness_to_c_strain(self, agreeableness: float) -> float:
        """
        Map agreeableness to strain impact on cohesion.
        
        Higher agreeableness -> cohesion less affected by strain (0.012 down to 0.005)
        """
        return 0.012 - (agreeableness * 0.007)
    
    def _map_agreeableness_to_c_q(self, agreeableness: float) -> float:
        """
        Map agreeableness to TQ pressure impact on cohesion.
        
        Higher agreeableness -> cohesion less affected by TQ (0.040 down to 0.025)
        """
        return 0.040 - (agreeableness * 0.015)
    
    # Extraversion mappings
    
    def _map_extraversion_to_m_base(self, extraversion: float) -> float:
        """
        Map extraversion to baseline monotony accumulation.
        
        Higher extraversion -> more sensitive to isolation (0.006 up to 0.011)
        """
        return 0.006 + (extraversion * 0.005)
    
    def _map_extraversion_to_m_novelty(self, extraversion: float) -> float:
        """
        Map extraversion to novelty event impact.
        
        Higher extraversion -> more benefit from social novelty (0.15 up to 0.25)
        """
        return 0.15 + (extraversion * 0.10)
    
    # Openness mappings
    
    def _adjust_for_openness_m_novelty(
        self, 
        base_m_novelty: float, 
        openness: float
    ) -> float:
        """
        Adjust novelty impact based on openness.
        
        Higher openness -> additional benefit from novelty (boost by up to 20%)
        """
        boost_factor = 1.0 + (openness * 0.2)
        return base_m_novelty * boost_factor
    
    def _map_openness_to_c_shared_success(self, openness: float) -> float:
        """
        Map openness to shared success impact on cohesion.
        
        Higher openness -> more engagement with shared goals (0.05 up to 0.08)
        """
        return 0.05 + (openness * 0.03)
