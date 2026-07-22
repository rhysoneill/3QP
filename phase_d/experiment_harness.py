"""
Counterfactual Experiment Harness (D.1)

Provides explicit, controlled sweeps where only one variable changes at a time.

Experiment families:
1. Mission Duration: Baseline, -10-20%, +10-20%
2. Crew Composition: Same avg traits, different dyadic compatibility
3. Intervention Timing: No intervention, early, late
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from enum import Enum

# Import existing infrastructure
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4" / "06_Ruthless_Core_Model"))
from ruthless_core import RuthlessCoreConfig

sys.path.insert(0, str(Path(__file__).parent.parent))
from crew.profile import CrewProfile, CrewMember, PersonalityScores
from agents import AgenticCoreModel


class ExperimentFamily(Enum):
    """Supported experiment types."""
    MISSION_DURATION = "mission_duration"
    CREW_COMPOSITION = "crew_composition"
    INTERVENTION_TIMING = "intervention_timing"


@dataclass
class ExperimentConfig:
    """
    Configuration for a single experimental run.
    
    Attributes:
        experiment_id: Unique identifier for this experiment
        family: Which experiment family this belongs to
        baseline_duration: Baseline mission duration in days
        duration_multiplier: Multiplier for mission duration (1.0 = baseline)
        crew_profile: Optional crew profile for composition experiments
        intervention_day: Optional day to apply intervention (None = no intervention)
        enable_narrative: Whether to enable Phase C narrative layer
        metadata: Additional run-specific metadata
    """
    experiment_id: str
    family: ExperimentFamily
    baseline_duration: int = 200
    duration_multiplier: float = 1.0
    crew_profile: Optional[CrewProfile] = None
    intervention_day: Optional[int] = None
    enable_narrative: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_mission_duration(self) -> int:
        """Calculate actual mission duration based on multiplier."""
        return int(self.baseline_duration * self.duration_multiplier)
    
    def get_description(self) -> str:
        """Generate human-readable description of this experiment."""
        if self.family == ExperimentFamily.MISSION_DURATION:
            pct = (self.duration_multiplier - 1.0) * 100
            sign = "+" if pct >= 0 else ""
            return f"Duration {sign}{pct:.0f}% ({self.get_mission_duration()} days)"
        elif self.family == ExperimentFamily.CREW_COMPOSITION:
            crew_name = self.crew_profile.crew_name if self.crew_profile else "baseline"
            return f"Crew: {crew_name}"
        elif self.family == ExperimentFamily.INTERVENTION_TIMING:
            if self.intervention_day is None:
                return "No intervention"
            else:
                return f"Intervention at day {self.intervention_day}"
        return self.experiment_id


@dataclass
class ExperimentResult:
    """
    Results from a single experimental run.
    
    This wraps the outputs from the existing infrastructure and adds
    experiment-specific metadata for analysis.
    
    Attributes:
        config: The experiment configuration used
        mission_name: Name of the mission executed
        core_output: Raw output from RuthlessCoreModel
        fingerprint: Collapse fingerprint
        action_log: Action log from Phase B
        narrative_log: Narrative log from Phase C (if enabled)
        timestamp: When this experiment was run
        runtime_seconds: How long the experiment took
        metadata: Additional result metadata
    """
    config: ExperimentConfig
    mission_name: str
    core_output: Any  # RuthlessCoreOutput
    fingerprint: Any  # CollapseFingerprint
    action_log: Any  # ActionLogger
    narrative_log: Optional[Any] = None  # NarrativeLogger
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    runtime_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary for storage."""
        from fingerprinting.fingerprint_schema import FingerprintSchema
        
        # Create fingerprint schema
        fp_schema = FingerprintSchema(
            fingerprint=self.fingerprint,
            mission_name=self.mission_name,
            timestamp=self.timestamp,
            run_metadata={
                "experiment_id": self.config.experiment_id,
                "family": self.config.family.value,
                "duration_multiplier": self.config.duration_multiplier,
                "mission_duration": self.config.get_mission_duration(),
                "intervention_day": self.config.intervention_day,
                **self.config.metadata,
            }
        )
        
        # Serialize action log
        action_data = None
        if self.action_log:
            action_data = {
                "action_counts": self.action_log.log.get_action_counts(),
                "action_sequence": self.action_log.log.get_action_sequence(),
                "pre_collapse_actions": [
                    {
                        "day": a.day,
                        "action_type": str(a.action_type),
                        "metadata": a.metadata or {},
                    }
                    for a in self.action_log.log.get_pre_collapse_actions(
                        self.fingerprint.collapse_day, window_days=20
                    )
                ],
            }
        
        # Serialize narrative log (if present)
        narrative_data = None
        if self.narrative_log:
            narrative_data = {
                "count": len(self.narrative_log.log.narratives),
                "critical_moments": [
                    {
                        "day": n.day,
                        "action": n.action,
                        "summary": n.narrative_summary,
                    }
                    for n in self.narrative_log.log.get_critical_moments()
                ],
            }
        
        return {
            "experiment_id": self.config.experiment_id,
            "experiment_family": self.config.family.value,
            "description": self.config.get_description(),
            "mission_name": self.mission_name,
            "timestamp": self.timestamp,
            "runtime_seconds": self.runtime_seconds,
            "fingerprint": fp_schema.to_dict(),
            "actions": action_data,
            "narratives": narrative_data,
            "metadata": self.metadata,
        }


class ExperimentHarness:
    """
    Harness for running controlled counterfactual experiments.
    
    Executes single-variable manipulations and collects structured outputs
    for comparison and analysis.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize experiment harness.
        
        Args:
            output_dir: Directory to save experiment results (default: phase_d/outputs)
        """
        if output_dir is None:
            output_dir = Path(__file__).parent / "outputs"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[ExperimentResult] = []
    
    def run_experiment(
        self,
        config: ExperimentConfig,
        save_result: bool = True
    ) -> ExperimentResult:
        """
        Run a single experiment with the given configuration.
        
        Args:
            config: Experiment configuration
            save_result: Whether to save result to disk
            
        Returns:
            ExperimentResult with all collected data
        """
        import time
        from fingerprinting.collapse_fingerprint import CollapseFingerprintGenerator
        
        start_time = time.time()
        
        # Build mission name
        mission_name = f"{config.experiment_id}_{config.family.value}"
        
        # Create core config
        core_config = RuthlessCoreConfig(
            mission_length_days=config.get_mission_duration()
        )
        
        # Create agentic model with Phase B actions
        model = AgenticCoreModel(
            core_config=core_config,
            enable_actions=True,
            enable_narrative=config.enable_narrative,
        )
        
        # Run mission (always returns 3-tuple)
        core_output, action_log, narrative_log = model.run(mission_name)
        
        # Generate fingerprint
        fp_gen = CollapseFingerprintGenerator()
        fingerprint = fp_gen.generate(
            global_cohesion=core_output.cohesion,
            dyadic_summary=None,  # No crew profile in base experiments
            mission_length_days=config.get_mission_duration(),
        )
        
        # Calculate runtime
        runtime_seconds = time.time() - start_time
        
        # Create result
        result = ExperimentResult(
            config=config,
            mission_name=mission_name,
            core_output=core_output,
            fingerprint=fingerprint,
            action_log=action_log,
            narrative_log=narrative_log,
            runtime_seconds=runtime_seconds,
        )
        
        # Store result
        self.results.append(result)
        
        # Save to disk if requested
        if save_result:
            self._save_result(result)
        
        return result
    
    def run_batch(
        self,
        configs: List[ExperimentConfig],
        verbose: bool = True
    ) -> List[ExperimentResult]:
        """
        Run multiple experiments in sequence.
        
        Args:
            configs: List of experiment configurations
            verbose: Whether to print progress
            
        Returns:
            List of experiment results
        """
        results = []
        
        for i, config in enumerate(configs, 1):
            if verbose:
                print(f"Running experiment {i}/{len(configs)}: {config.get_description()}")
            
            result = self.run_experiment(config, save_result=True)
            results.append(result)
            
            if verbose:
                print(f"  ✓ Completed in {result.runtime_seconds:.2f}s")
                print(f"  Collapse: {result.fingerprint.collapse_timing} "
                      f"(day {result.fingerprint.collapse_day}, "
                      f"depth {result.fingerprint.collapse_depth:.3f})")
        
        return results
    
    def _save_result(self, result: ExperimentResult):
        """Save experiment result to disk."""
        import json
        
        # Create experiment family directory
        family_dir = self.output_dir / result.config.family.value
        family_dir.mkdir(parents=True, exist_ok=True)
        
        # Save result as JSON
        output_file = family_dir / f"{result.config.experiment_id}.json"
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def load_results(self, family: Optional[ExperimentFamily] = None) -> List[Dict[str, Any]]:
        """
        Load saved experiment results from disk.
        
        Args:
            family: Optional filter by experiment family
            
        Returns:
            List of result dictionaries
        """
        import json
        
        results = []
        
        if family:
            family_dir = self.output_dir / family.value
            if family_dir.exists():
                for result_file in family_dir.glob("*.json"):
                    with open(result_file, 'r') as f:
                        results.append(json.load(f))
        else:
            for family_dir in self.output_dir.iterdir():
                if family_dir.is_dir():
                    for result_file in family_dir.glob("*.json"):
                        with open(result_file, 'r') as f:
                            results.append(json.load(f))
        
        return results
