"""
Mission Runner for Phase 5 Integration Harness

Orchestrates the execution of the Ruthless Core Model and wraps outputs
for Phase 4 integration without modifying the core engine.

This module:
- Imports and calls RuthlessCoreModel.run()
- Uses existing Phase 4 adapters (to_phase4_encoded_states, to_phase4_trajectory_result)
- Returns structured MissionResult for downstream processing
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import Ruthless Core Model from Phase 4
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase4" / "06_Ruthless_Core_Model"))
from ruthless_core import (
    RuthlessCoreModel,
    RuthlessCoreConfig,
    RuthlessCoreOutput,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)

from runtime_config import RuntimeConfig

# Import crew dyadic analysis (optional extension)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from crew.dyadic_fractiousness import DyadicFractiousnessModel, DyadicFractiousnessSummary
from crew.profile import CrewProfile

# Import collapse fingerprint generator (optional extension)
from fingerprinting.collapse_fingerprint import CollapseFingerprintGenerator, CollapseFingerprint

# Import Phase B agent system (optional extension)
from agents import AgenticCoreModel, ActionLogger


@dataclass
class MissionResult:
    """
    Container for mission simulation results.
    
    Wraps the RuthlessCoreOutput and Phase 4 integration outputs for
    easy access by logger and validator.
    
    Attributes:
        config: Runtime configuration used
        core_output: Raw output from RuthlessCoreModel
        encoded_states: Phase 4 WS2 encoded state format
        trajectory_result: Phase 4 trajectory classification result
        metadata: Additional runtime metadata
        dyadic_fractiousness: Optional dyadic fractiousness analysis results
                            (only populated when crew profile is used)
        collapse_fingerprint: Optional collapse fingerprint (TQP signature)
        core_config: RuthlessCoreConfig used for this run
    """
    config: RuntimeConfig
    core_output: RuthlessCoreOutput
    encoded_states: List[Dict[str, Any]]
    trajectory_result: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    dyadic_fractiousness: Optional[DyadicFractiousnessSummary] = None
    collapse_fingerprint: Optional[CollapseFingerprint] = None
    core_config: Optional[RuthlessCoreConfig] = None
    action_log: Optional[ActionLogger] = None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of mission results.
        
        Returns:
            Dictionary with key metrics and findings
        """
        cohesion = self.core_output.cohesion
        strain = self.core_output.strain
        monotony = self.core_output.monotony
        tq_pressure = self.core_output.tq_pressure
        
        min_cohesion = min(cohesion)
        min_cohesion_idx = cohesion.index(min_cohesion)
        min_cohesion_day = self.core_output.days[min_cohesion_idx]
        
        max_strain = max(strain)
        max_strain_idx = strain.index(max_strain)
        max_strain_day = self.core_output.days[max_strain_idx]
        
        max_tq = max(tq_pressure)
        max_tq_idx = tq_pressure.index(max_tq)
        max_tq_day = self.core_output.days[max_tq_idx]
        
        summary = {
            "mission_name": self.config.mission_name,
            "mission_length_days": self.config.mission_length_days,
            "trajectory_archetype": self.trajectory_result["archetype_id"],
            "trajectory_label": self.trajectory_result["label"],
            "metrics": {
                "cohesion": {
                    "initial": cohesion[0],
                    "final": cohesion[-1],
                    "minimum": min_cohesion,
                    "minimum_day": min_cohesion_day,
                    "minimum_progress": min_cohesion_day / len(cohesion),
                },
                "strain": {
                    "initial": strain[0],
                    "final": strain[-1],
                    "maximum": max_strain,
                    "maximum_day": max_strain_day,
                },
                "monotony": {
                    "initial": monotony[0],
                    "final": monotony[-1],
                    "maximum": max(monotony),
                },
                "tq_pressure": {
                    "peak": max_tq,
                    "peak_day": max_tq_day,
                    "peak_progress": max_tq_day / len(tq_pressure),
                }
            },
            "metadata": self.metadata,
        }
        
        # Add dyadic fractiousness summary if available
        if self.dyadic_fractiousness is not None:
            summary["dyadic_fractiousness"] = {
                "fractiousness_index": self.dyadic_fractiousness.fractiousness_index,
                "num_pairs": self.dyadic_fractiousness.metadata.get("num_pairs", 0),
                "min_of_min_cohesion": self.dyadic_fractiousness.metadata.get("min_of_min_cohesion", 0.0),
                "max_of_min_cohesion": self.dyadic_fractiousness.metadata.get("max_of_min_cohesion", 0.0),
            }
        
        # Add collapse fingerprint summary if available
        if self.collapse_fingerprint is not None:
            summary["collapse_fingerprint"] = {
                "collapse_timing": self.collapse_fingerprint.collapse_timing,
                "collapse_depth": self.collapse_fingerprint.collapse_depth,
                "collapse_day": self.collapse_fingerprint.collapse_day,
                "fractiousness_index": self.collapse_fingerprint.fractiousness_index,
                "risk_score": self.collapse_fingerprint.risk_score,
                "risk_category": self.collapse_fingerprint.risk_category,
            }
        
        # Add action log summary if available
        if self.action_log is not None:
            action_stats = self.action_log.get_statistics()
            summary["agent_actions"] = action_stats
        
        return summary


class MissionRunner:
    """
    Mission simulation orchestrator.
    
    Wraps the Ruthless Core Model execution and handles Phase 4 integration
    without modifying the core engine.
    """
    
    def __init__(
        self, 
        runtime_config: RuntimeConfig, 
        core_config: RuthlessCoreConfig = None,
        crew_profile: Optional[CrewProfile] = None,
        enable_agents: bool = False
    ):
        """
        Initialize mission runner.
        
        Args:
            runtime_config: Runtime configuration for the mission
            core_config: Optional pre-configured RuthlessCoreConfig (if None, will be created)
            crew_profile: Optional crew profile for dyadic analysis
            enable_agents: If True, use AgenticCoreModel with action selection (Phase B)
        """
        self.runtime_config = runtime_config
        self.verbose = runtime_config.verbose
        self._provided_core_config = core_config
        self._crew_profile = crew_profile
        self.enable_agents = enable_agents
    
    def _create_core_config(self) -> RuthlessCoreConfig:
        """
        Create RuthlessCoreConfig from runtime configuration.
        
        If a core_config was provided at initialization, uses that.
        Otherwise, applies any overrides from runtime_config.core_config_override.
        
        Returns:
            RuthlessCoreConfig instance
        """
        # If core config was provided externally, use it
        if self._provided_core_config is not None:
            return self._provided_core_config
        
        # Otherwise create from runtime config
        # Start with defaults
        kwargs = {"mission_length_days": self.runtime_config.mission_length_days}
        
        # Apply overrides if provided
        if self.runtime_config.core_config_override:
            kwargs.update(self.runtime_config.core_config_override)
        
        return RuthlessCoreConfig(**kwargs)
    
    def run(self) -> MissionResult:
        """
        Run the mission simulation.
        
        This method:
        1. Creates RuthlessCoreConfig
        2. Instantiates RuthlessCoreModel
        3. Calls model.run()
        4. Applies Phase 4 adapters
        5. Returns wrapped MissionResult
        
        Returns:
            MissionResult containing all outputs
        """
        start_time = datetime.now()
        
        if self.verbose:
            print(f"[MissionRunner] Starting mission: {self.runtime_config.mission_name}")
            print(f"[MissionRunner] Mission length: {self.runtime_config.mission_length_days} days")
        
        # Step 1: Create core configuration
        core_config = self._create_core_config()
        
        if self.verbose:
            print(f"[MissionRunner] Created RuthlessCoreConfig")
            print(f"                TQ center: {core_config.q_center:.2f}")
            print(f"                TQ peak: {core_config.q_peak:.2f}")
        
        # Step 2: Instantiate and run model
        action_logger = None
        narrative_logger = None
        
        if self.enable_agents:
            # Use agentic core model (Phase B)
            if self.verbose:
                print(f"[MissionRunner] Running AgenticCoreModel (Phase B enabled)...")
            
            agentic_model = AgenticCoreModel(
                core_config=core_config,
                enable_actions=True,
                agent_id="crew",
                enable_narrative=False,  # Phase C disabled by default
            )
            core_output, action_logger, narrative_logger = agentic_model.run(
                mission_name=self.runtime_config.mission_name
            )
            
            if self.verbose:
                print(f"[MissionRunner] Agentic simulation complete ({len(core_output)} days)")
                if action_logger:
                    stats = action_logger.get_statistics()
                    print(f"[MissionRunner] Agent actions logged: {stats['total_actions']}")
                    print(f"                Dominant action: {stats.get('dominant_action', 'N/A')}")
        else:
            # Use standard core model
            if self.verbose:
                print(f"[MissionRunner] Running RuthlessCoreModel (baseline mode)...")
            
            model = RuthlessCoreModel(core_config)
            core_output = model.run()
            
            if self.verbose:
                print(f"[MissionRunner] Simulation complete ({len(core_output)} days)")
        
        # Step 3: Apply Phase 4 adapters
        if self.verbose:
            print(f"[MissionRunner] Applying Phase 4 adapters...")
        
        encoded_states = to_phase4_encoded_states(core_output)
        trajectory_result = to_phase4_trajectory_result(core_output)
        
        if self.verbose:
            print(f"[MissionRunner] Trajectory detected: {trajectory_result['label']}")
        
        # Step 4: Dyadic fractiousness analysis (optional, only if crew profile provided)
        dyadic_result = None
        if self._crew_profile is not None:
            if self.verbose:
                print(f"[MissionRunner] Running dyadic fractiousness analysis...")
            
            try:
                dyadic_model = DyadicFractiousnessModel()
                dyadic_result = dyadic_model.analyze(
                    crew=self._crew_profile,
                    global_cohesion=core_output.cohesion
                )
                
                if self.verbose:
                    print(f"[MissionRunner] Dyadic analysis complete:")
                    print(f"                Fractiousness index: {dyadic_result.fractiousness_index:.4f}")
                    print(f"                Pairs analyzed: {dyadic_result.metadata.get('num_pairs', 0)}")
            except Exception as e:
                if self.verbose:
                    print(f"[MissionRunner] Warning: Dyadic analysis failed: {e}")
                # Don't fail the whole mission if dyadic analysis fails
                dyadic_result = None
        
        # Step 5: Generate collapse fingerprint
        # Always generate fingerprint for ALL missions (crew or baseline)
        # Dyadic components will be None for baseline missions
        collapse_fingerprint = None
        if self.verbose:
            print(f"[MissionRunner] Generating collapse fingerprint...")
        
        try:
            fingerprint_generator = CollapseFingerprintGenerator()
            collapse_fingerprint = fingerprint_generator.generate(
                global_cohesion=core_output.cohesion,
                dyadic_summary=dyadic_result,
                mission_length_days=self.runtime_config.mission_length_days
            )
            
            # Attach action metadata to fingerprint if available (Phase B)
            if action_logger is not None and collapse_fingerprint is not None:
                action_metadata = action_logger.get_fingerprint_metadata(
                    collapse_day=collapse_fingerprint.collapse_day
                )
                collapse_fingerprint.metadata.update(action_metadata)
                
                if self.verbose:
                    dominant = action_metadata.get("action_summary", {}).get("dominant_action")
                    print(f"[MissionRunner] Action metadata attached to fingerprint")
                    print(f"                Dominant action: {dominant}")
            
            if self.verbose:
                print(f"[MissionRunner] Collapse fingerprint generated:")
                print(f"                Risk score: {collapse_fingerprint.risk_score:.4f} ({collapse_fingerprint.risk_category})")
                print(f"                Collapse timing: {collapse_fingerprint.collapse_timing:.2%} (day {collapse_fingerprint.collapse_day})")
                print(f"                Collapse depth: {collapse_fingerprint.collapse_depth:.3f}")
        except Exception as e:
            if self.verbose:
                print(f"[MissionRunner] Warning: Fingerprint generation failed: {e}")
            # Don't fail the whole mission if fingerprint generation fails
            collapse_fingerprint = None
        
        # Step 6: Package results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        metadata = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "ruthless_core_version": core_output.metadata.get("version", "unknown"),
        }
        
        result = MissionResult(
            config=self.runtime_config,
            core_output=core_output,
            encoded_states=encoded_states,
            trajectory_result=trajectory_result,
            metadata=metadata,
            dyadic_fractiousness=dyadic_result,
            collapse_fingerprint=collapse_fingerprint,
            core_config=core_config,
            action_log=action_logger,
        )
        
        if self.verbose:
            print(f"[MissionRunner] Mission complete in {duration:.2f}s")
        
        return result


def run_mission(
    runtime_config: RuntimeConfig, 
    core_config: RuthlessCoreConfig = None,
    crew_profile: Optional[CrewProfile] = None,
    enable_agents: bool = False
) -> MissionResult:
    """
    Convenience function to run a mission simulation.
    
    Args:
        runtime_config: Runtime configuration
        core_config: Optional pre-configured RuthlessCoreConfig
        crew_profile: Optional crew profile for dyadic analysis
        enable_agents: If True, use AgenticCoreModel (Phase B)
        
    Returns:
        MissionResult with all outputs
    """
    runner = MissionRunner(
        runtime_config, 
        core_config=core_config, 
        crew_profile=crew_profile,
        enable_agents=enable_agents
    )
    return runner.run()
