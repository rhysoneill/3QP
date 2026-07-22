"""
Failure Mode Taxonomy (D.4)

Derives taxonomy of collapse modes using fingerprints + action traces:
1. Cohesion-led collapse
2. Strain-spike collapse
3. Dyadic fracture-driven collapse
4. Gradual monotony erosion

Each mode has:
- Fingerprint signature
- Characteristic action pattern
- Sensitivity window for intervention
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import json
from pathlib import Path

from .data_collector import RunData


class CollapseModeType(Enum):
    """Types of collapse modes identified in taxonomy."""
    COHESION_LED = "cohesion_led"
    STRAIN_SPIKE = "strain_spike"
    DYADIC_FRACTURE = "dyadic_fracture"
    MONOTONY_EROSION = "monotony_erosion"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class CollapseModeSignature:
    """
    Fingerprint signature for a collapse mode.
    
    Defines the characteristic fingerprint patterns that identify
    this mode of collapse.
    
    Attributes:
        collapse_timing: Expected collapse timing category (early/tq/late)
        collapse_depth_range: (min, max) depth values characteristic of this mode
        risk_category: Expected risk category
        fractiousness_threshold: Fractiousness index threshold (if applicable)
        description: Human-readable signature description
    """
    collapse_timing: Optional[str] = None
    collapse_depth_range: Optional[Tuple[float, float]] = None
    risk_category: Optional[str] = None
    fractiousness_threshold: Optional[float] = None
    description: str = ""


@dataclass
class ActionPattern:
    """
    Characteristic action pattern for a collapse mode.
    
    Attributes:
        dominant_actions: Most frequent action types in this mode
        action_diversity: Expected action diversity (low/medium/high)
        pre_collapse_sequence: Characteristic action sequence before collapse
        description: Human-readable pattern description
    """
    dominant_actions: List[str] = field(default_factory=list)
    action_diversity: str = "medium"  # low/medium/high
    pre_collapse_sequence: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class InterventionWindow:
    """
    Sensitivity window for intervention effectiveness.
    
    Defines when interventions are most/least effective for this collapse mode.
    
    Attributes:
        optimal_timing: Optimal intervention timing (early/mid/late in mission)
        critical_days_before_collapse: Days before collapse when intervention critical
        effectiveness_description: Description of intervention effectiveness
    """
    optimal_timing: str = "early"  # early/mid/late
    critical_days_before_collapse: int = 20
    effectiveness_description: str = ""


@dataclass
class CollapseMode:
    """
    Complete collapse mode definition.
    
    Combines fingerprint signature, action pattern, and intervention window
    to fully characterize a mode of crew collapse.
    
    This is a publishable artifact.
    
    Attributes:
        mode_type: Type of collapse mode
        name: Human-readable name
        signature: Fingerprint signature
        action_pattern: Characteristic action pattern
        intervention_window: Intervention sensitivity window
        examples: Example run IDs exhibiting this mode
        prevalence: How common this mode is (0-1)
        description: Detailed mode description
    """
    mode_type: CollapseModeType
    name: str
    signature: CollapseModeSignature
    action_pattern: ActionPattern
    intervention_window: InterventionWindow
    examples: List[str] = field(default_factory=list)
    prevalence: float = 0.0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "mode_type": self.mode_type.value,
            "name": self.name,
            "signature": {
                "collapse_timing": self.signature.collapse_timing,
                "collapse_depth_range": self.signature.collapse_depth_range,
                "risk_category": self.signature.risk_category,
                "fractiousness_threshold": self.signature.fractiousness_threshold,
                "description": self.signature.description,
            },
            "action_pattern": {
                "dominant_actions": self.action_pattern.dominant_actions,
                "action_diversity": self.action_pattern.action_diversity,
                "pre_collapse_sequence": self.action_pattern.pre_collapse_sequence,
                "description": self.action_pattern.description,
            },
            "intervention_window": {
                "optimal_timing": self.intervention_window.optimal_timing,
                "critical_days_before_collapse": self.intervention_window.critical_days_before_collapse,
                "effectiveness_description": self.intervention_window.effectiveness_description,
            },
            "examples": self.examples,
            "prevalence": self.prevalence,
            "description": self.description,
        }


class FailureTaxonomy:
    """
    Taxonomy of crew collapse modes.
    
    Derives and organizes collapse modes from experimental data,
    providing a structured classification system for mission failures.
    """
    
    def __init__(self):
        """Initialize taxonomy."""
        self.modes: List[CollapseMode] = []
        self._define_base_taxonomy()
    
    def _define_base_taxonomy(self):
        """Define the base taxonomy of collapse modes."""
        
        # Mode 1: Cohesion-Led Collapse
        cohesion_led = CollapseMode(
            mode_type=CollapseModeType.COHESION_LED,
            name="Cohesion-Led Collapse",
            signature=CollapseModeSignature(
                collapse_timing="tq",  # Often occurs in third quarter
                collapse_depth_range=(0.2, 0.4),  # Moderate to deep collapse
                risk_category="high",
                description="Gradual erosion of cohesion leading to systemic breakdown",
            ),
            action_pattern=ActionPattern(
                dominant_actions=["WITHDRAW", "ROUTINE"],
                action_diversity="low",
                pre_collapse_sequence=["ROUTINE", "WITHDRAW", "WITHDRAW"],
                description="Increasing withdrawal and routine adherence as cohesion fails",
            ),
            intervention_window=InterventionWindow(
                optimal_timing="early",
                critical_days_before_collapse=30,
                effectiveness_description="Intervention most effective before cohesion drops below 0.4",
            ),
            description=(
                "Characterized by steady decline in crew cohesion without compensatory "
                "mechanisms. Crew members increasingly withdraw from interaction, "
                "maintaining only routine task performance. Collapse occurs when cohesion "
                "falls below critical threshold."
            ),
        )
        
        # Mode 2: Strain-Spike Collapse
        strain_spike = CollapseMode(
            mode_type=CollapseModeType.STRAIN_SPIKE,
            name="Strain-Spike Collapse",
            signature=CollapseModeSignature(
                collapse_timing="early",  # Can occur early or late
                collapse_depth_range=(0.4, 0.7),  # Deep collapse
                risk_category="critical",
                description="Rapid collapse triggered by acute strain event",
            ),
            action_pattern=ActionPattern(
                dominant_actions=["ASSERT", "CONFRONT"],
                action_diversity="high",
                pre_collapse_sequence=["ASSERT", "CONFRONT", "WITHDRAW"],
                description="High-intensity actions followed by sudden withdrawal",
            ),
            intervention_window=InterventionWindow(
                optimal_timing="mid",
                critical_days_before_collapse=10,
                effectiveness_description="Short intervention window; must act quickly once strain spikes",
            ),
            description=(
                "Characterized by sudden, acute strain event that overwhelms crew capacity. "
                "Often follows period of tension (assertions, confrontations) that culminates "
                "in breakdown. Collapse is rapid and deep once triggered."
            ),
        )
        
        # Mode 3: Dyadic Fracture-Driven Collapse
        dyadic_fracture = CollapseMode(
            mode_type=CollapseModeType.DYADIC_FRACTURE,
            name="Dyadic Fracture-Driven Collapse",
            signature=CollapseModeSignature(
                collapse_timing="tq",
                collapse_depth_range=(0.3, 0.5),
                risk_category="high",
                fractiousness_threshold=0.6,
                description="Collapse driven by breakdown of specific dyadic relationships",
            ),
            action_pattern=ActionPattern(
                dominant_actions=["CONFRONT", "WITHDRAW"],
                action_diversity="medium",
                pre_collapse_sequence=["CONFRONT", "WITHDRAW", "ROUTINE"],
                description="Confrontations followed by withdrawal, fracturing key relationships",
            ),
            intervention_window=InterventionWindow(
                optimal_timing="early",
                critical_days_before_collapse=40,
                effectiveness_description="Most effective when targeting specific dyadic pairs early",
            ),
            description=(
                "Collapse initiated by breakdown of critical crew relationships. "
                "High fractiousness index indicates incompatible dyadic pairs. "
                "As key relationships deteriorate, overall cohesion follows, "
                "leading to systemic collapse."
            ),
        )
        
        # Mode 4: Monotony Erosion Collapse
        monotony_erosion = CollapseMode(
            mode_type=CollapseModeType.MONOTONY_EROSION,
            name="Gradual Monotony Erosion",
            signature=CollapseModeSignature(
                collapse_timing="late",
                collapse_depth_range=(0.15, 0.35),  # Moderate depth
                risk_category="moderate",
                description="Slow erosion from sustained monotony and routine",
            ),
            action_pattern=ActionPattern(
                dominant_actions=["ROUTINE", "WITHDRAW"],
                action_diversity="low",
                pre_collapse_sequence=["ROUTINE", "ROUTINE", "WITHDRAW"],
                description="Overwhelming dominance of routine actions, minimal social engagement",
            ),
            intervention_window=InterventionWindow(
                optimal_timing="mid",
                critical_days_before_collapse=50,
                effectiveness_description="Long intervention window; gradual deterioration allows time",
            ),
            description=(
                "Characterized by prolonged exposure to monotonous conditions without "
                "sufficient variety or engagement. Crew settles into rigid routines, "
                "gradually losing cohesion through disengagement. Collapse is slow "
                "but predictable."
            ),
        )
        
        self.modes = [cohesion_led, strain_spike, dyadic_fracture, monotony_erosion]
    
    def classify_run(self, run: RunData) -> CollapseModeType:
        """
        Classify a run into a collapse mode based on its fingerprint and actions.
        
        Args:
            run: RunData to classify
            
        Returns:
            CollapseModeType classification
        """
        fp = run.fingerprint
        
        # Extract key metrics
        collapse_timing = fp.get("collapse_timing", "unknown")
        collapse_depth = fp.get("collapse_depth", 0.0)
        risk_category = fp.get("risk_category", "unknown")
        fractiousness = fp.get("fractiousness_index", 0.0)
        
        dominant_action = run.get_dominant_action()
        action_diversity = run.get_action_diversity()
        
        # Classification logic
        scores = {}
        
        # Check cohesion-led
        cohesion_score = 0
        if collapse_timing == "tq":
            cohesion_score += 1
        if 0.2 <= collapse_depth <= 0.4:
            cohesion_score += 1
        if dominant_action in ["WITHDRAW", "ROUTINE"]:
            cohesion_score += 1
        if action_diversity < 0.4:  # Low diversity
            cohesion_score += 1
        scores[CollapseModeType.COHESION_LED] = cohesion_score
        
        # Check strain-spike
        strain_score = 0
        if collapse_depth >= 0.4:
            strain_score += 1
        if risk_category == "critical":
            strain_score += 1
        if dominant_action in ["ASSERT", "CONFRONT"]:
            strain_score += 1
        if action_diversity > 0.6:  # High diversity
            strain_score += 1
        scores[CollapseModeType.STRAIN_SPIKE] = strain_score
        
        # Check dyadic fracture
        dyadic_score = 0
        if fractiousness and fractiousness >= 0.6:
            dyadic_score += 2  # Strong signal
        if collapse_timing == "tq":
            dyadic_score += 1
        if dominant_action in ["CONFRONT", "WITHDRAW"]:
            dyadic_score += 1
        scores[CollapseModeType.DYADIC_FRACTURE] = dyadic_score
        
        # Check monotony erosion
        monotony_score = 0
        if collapse_timing == "late":
            monotony_score += 1
        if collapse_depth <= 0.35:
            monotony_score += 1
        if dominant_action == "ROUTINE":
            monotony_score += 1
        if action_diversity < 0.3:  # Very low diversity
            monotony_score += 1
        scores[CollapseModeType.MONOTONY_EROSION] = monotony_score
        
        # Return highest scoring mode
        if max(scores.values()) >= 2:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return CollapseModeType.UNKNOWN
    
    def analyze_runs(self, runs: List[RunData]) -> Dict[str, Any]:
        """
        Analyze runs and update taxonomy with examples and prevalence.
        
        Args:
            runs: List of RunData to analyze
            
        Returns:
            Analysis summary
        """
        # Classify all runs
        classifications = {}
        mode_counts = {mode.mode_type: 0 for mode in self.modes}
        mode_counts[CollapseModeType.UNKNOWN] = 0
        
        for run in runs:
            mode_type = self.classify_run(run)
            classifications[run.run_id] = mode_type
            mode_counts[mode_type] += 1
        
        # Update mode examples and prevalence
        for mode in self.modes:
            mode.examples = [
                run_id for run_id, mode_type in classifications.items()
                if mode_type == mode.mode_type
            ]
            mode.prevalence = mode_counts[mode.mode_type] / len(runs) if runs else 0.0
        
        # Generate summary
        summary = {
            "total_runs": len(runs),
            "classifications": {
                mode.mode_type.value: {
                    "count": mode_counts[mode.mode_type],
                    "prevalence": mode.prevalence,
                    "examples": mode.examples[:3],  # First 3 examples
                }
                for mode in self.modes
            },
            "unclassified": {
                "count": mode_counts[CollapseModeType.UNKNOWN],
                "prevalence": mode_counts[CollapseModeType.UNKNOWN] / len(runs) if runs else 0.0,
            },
        }
        
        return summary
    
    def get_mode(self, mode_type: CollapseModeType) -> Optional[CollapseMode]:
        """
        Get mode definition by type.
        
        Args:
            mode_type: Mode type to retrieve
            
        Returns:
            CollapseMode if found, None otherwise
        """
        for mode in self.modes:
            if mode.mode_type == mode_type:
                return mode
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize taxonomy to dictionary."""
        return {
            "taxonomy_version": "1.0",
            "num_modes": len(self.modes),
            "modes": [mode.to_dict() for mode in self.modes],
        }
    
    def save(self, output_file: Path):
        """
        Save taxonomy to JSON file.
        
        Args:
            output_file: Path to output file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, input_file: Path) -> 'FailureTaxonomy':
        """
        Load taxonomy from JSON file.
        
        Args:
            input_file: Path to input file
            
        Returns:
            FailureTaxonomy instance
        """
        # For now, just return a new instance with base taxonomy
        # Could extend to deserialize from file in future
        return cls()
