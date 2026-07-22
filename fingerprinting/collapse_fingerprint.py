"""
Collapse Fingerprint Generator

Produces a compact, interpretable summary ("TQP Signature") for each mission run.

This fingerprint integrates:
- Global collapse timing (when minimum cohesion occurs)
- Global collapse depth (minimum cohesion value)
- Dyadic fractiousness score (variance in pair-level collapse)
- Identification of weakest pairs
- Risk categorization for crew selection and intervention planning

The fingerprint enables:
- Comparing crews to each other
- Comparing interventions to baselines
- Selecting crew compositions
- Pre-launch behavioral risk scoring

This module performs ONLY additive analysis and does NOT modify
any existing runtime, core model, or module logic.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Import dyadic fractiousness for integration
sys.path.insert(0, str(Path(__file__).parent.parent))
from crew.dyadic_fractiousness import DyadicFractiousnessSummary


@dataclass
class CollapseFingerprint:
    """
    Compact TQP Signature summarizing a mission's collapse profile.
    
    Attributes:
        collapse_timing: Mission progress (0.0–1.0) when global minimum cohesion occurs
        collapse_depth: Minimum global cohesion value reached
        collapse_day: Day index when minimum cohesion occurred
        fractiousness_index: Standard deviation of dyadic minimum cohesion values
                           (None if no crew profile used)
        weakest_pairs: List of the weakest dyadic pairs with their metrics
                      (None if no crew profile used)
        risk_score: Computed risk score combining depth, timing, and fractiousness (0.0–1.0)
        risk_category: Human-readable risk category ("low risk", "moderate risk", "high risk")
        metadata: Additional computation details and parameters
    """
    collapse_timing: float
    collapse_depth: float
    collapse_day: int
    fractiousness_index: Optional[float] = None
    weakest_pairs: Optional[List[Dict[str, Any]]] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CollapseFingerprintGenerator:
    """
    Generator for collapse fingerprints from mission simulation data.
    
    Computes a compact signature integrating global cohesion collapse patterns
    with optional dyadic fractiousness analysis for crew-based missions.
    """
    
    def __init__(
        self,
        num_weakest_pairs: int = 3,
        risk_weight_depth: float = 0.5,
        risk_weight_timing: float = 0.3,
        risk_weight_fractiousness: float = 0.2,
        high_risk_threshold: float = 0.75,
        moderate_risk_threshold: float = 0.45
    ):
        """
        Initialize the collapse fingerprint generator.
        
        Args:
            num_weakest_pairs: Number of weakest dyadic pairs to include (default: 3)
            risk_weight_depth: Weight for collapse depth in risk score (default: 0.5)
            risk_weight_timing: Weight for collapse timing in risk score (default: 0.3)
            risk_weight_fractiousness: Weight for fractiousness in risk score (default: 0.2)
            high_risk_threshold: Threshold for "high risk" categorization (default: 0.75)
            moderate_risk_threshold: Threshold for "moderate risk" categorization (default: 0.45)
        """
        self.num_weakest_pairs = num_weakest_pairs
        self.risk_weight_depth = risk_weight_depth
        self.risk_weight_timing = risk_weight_timing
        self.risk_weight_fractiousness = risk_weight_fractiousness
        self.high_risk_threshold = high_risk_threshold
        self.moderate_risk_threshold = moderate_risk_threshold
    
    def generate(
        self,
        global_cohesion: List[float],
        dyadic_summary: Optional[DyadicFractiousnessSummary],
        mission_length_days: int
    ) -> CollapseFingerprint:
        """
        Generate a collapse fingerprint from mission data.
        
        Args:
            global_cohesion: List of global cohesion values across mission timeline
            dyadic_summary: Optional dyadic fractiousness analysis result
            mission_length_days: Length of mission in days
            
        Returns:
            CollapseFingerprint containing all computed metrics
        """
        # STEP 1: GLOBAL COLLAPSE TIMING
        # Find the index where cohesion is minimal
        t_min = global_cohesion.index(min(global_cohesion))
        
        # Compute collapse timing as mission progress (0.0 = start, 1.0 = end)
        # Handle edge case of single-day mission
        if mission_length_days <= 1:
            collapse_timing = 0.0
        else:
            collapse_timing = t_min / (mission_length_days - 1)
        
        # STEP 2: GLOBAL COLLAPSE DEPTH
        collapse_depth = global_cohesion[t_min]
        
        # STEP 3: FRACTIOUSNESS INDEX (if dyadic data available)
        fractiousness_index = None
        if dyadic_summary is not None:
            fractiousness_index = dyadic_summary.fractiousness_index
        
        # STEP 4: WEAKEST PAIRS (if dyadic data available)
        weakest_pairs = None
        if dyadic_summary is not None:
            weakest_pairs = self._extract_weakest_pairs(dyadic_summary)
        
        # STEP 5: RISK SCORE
        # Compute a transparent risk score combining:
        # - Normalized collapse depth (lower depth = higher risk)
        # - Collapse timing (earlier collapse = higher risk)
        # - Fractiousness index (more variance = higher risk)
        #
        # Formula:
        #   risk_score = w1 * (1 - collapse_depth) +
        #                w2 * (1 - collapse_timing) +
        #                w3 * (fractiousness_index or 0)
        #
        # Where:
        #   w1 = risk_weight_depth (default: 0.5)
        #   w2 = risk_weight_timing (default: 0.3)
        #   w3 = risk_weight_fractiousness (default: 0.2)
        #
        # Risk score is clamped to [0.0, 1.0]
        
        depth_risk = 1.0 - collapse_depth
        timing_risk = 1.0 - collapse_timing
        fractiousness_risk = fractiousness_index if fractiousness_index is not None else 0.0
        
        risk_score = (
            self.risk_weight_depth * depth_risk +
            self.risk_weight_timing * timing_risk +
            self.risk_weight_fractiousness * fractiousness_risk
        )
        
        # Clamp risk score to [0.0, 1.0]
        risk_score = max(0.0, min(1.0, risk_score))
        
        # STEP 6: RISK CATEGORY
        if risk_score >= self.high_risk_threshold:
            risk_category = "high risk"
        elif risk_score >= self.moderate_risk_threshold:
            risk_category = "moderate risk"
        else:
            risk_category = "low risk"
        
        # STEP 7: METADATA
        metadata = {
            "t_min": t_min,
            "mission_length_days": mission_length_days,
            "risk_weight_depth": self.risk_weight_depth,
            "risk_weight_timing": self.risk_weight_timing,
            "risk_weight_fractiousness": self.risk_weight_fractiousness,
            "high_risk_threshold": self.high_risk_threshold,
            "moderate_risk_threshold": self.moderate_risk_threshold,
            "depth_risk_component": depth_risk,
            "timing_risk_component": timing_risk,
            "fractiousness_risk_component": fractiousness_risk,
        }
        
        return CollapseFingerprint(
            collapse_timing=collapse_timing,
            collapse_depth=collapse_depth,
            collapse_day=t_min,
            fractiousness_index=fractiousness_index,
            weakest_pairs=weakest_pairs,
            risk_score=risk_score,
            risk_category=risk_category,
            metadata=metadata,
        )
    
    def _extract_weakest_pairs(
        self,
        dyadic_summary: DyadicFractiousnessSummary
    ) -> List[Dict[str, Any]]:
        """
        Extract the weakest dyadic pairs from the fractiousness analysis.
        
        Args:
            dyadic_summary: Dyadic fractiousness analysis result
            
        Returns:
            List of dictionaries containing weakest pair information
        """
        # Sort pairs by min_cohesion (ascending - lowest first)
        sorted_pairs = sorted(
            dyadic_summary.pair_results,
            key=lambda pr: pr.min_cohesion
        )
        
        # Take the bottom N pairs
        weakest = sorted_pairs[:self.num_weakest_pairs]
        
        # Convert to dictionaries with relevant metrics
        result = []
        for pair in weakest:
            result.append({
                "member_i": pair.member_i,
                "member_j": pair.member_j,
                "min_cohesion": pair.min_cohesion,
                "min_cohesion_day": pair.min_cohesion_day,
                "min_cohesion_progress": pair.min_cohesion_progress,
                "compatibility_score": pair.compatibility_score,
                "final_cohesion": pair.final_cohesion,
            })
        
        return result
