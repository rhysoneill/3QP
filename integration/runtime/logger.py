"""
Logger for Phase 5 Integration Harness

Handles writing simulation outputs to files in /output/ directory.

This module writes:
- Full time series data (JSON)
- Mission summary (JSON)
- Encoded states (JSON)
- Trajectory results (JSON)
- Fingerprint schema (JSON)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Import fingerprinting for schema support
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from fingerprinting import FingerprintSchema


class SimulationLogger:
    """
    Logger for mission simulation outputs.
    
    Writes various output formats to the configured output directory.
    """
    
    def __init__(self, output_dir: str = "output", verbose: bool = True):
        """
        Initialize logger.
        
        Args:
            output_dir: Directory for output files
            verbose: Whether to print logging actions
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
    
    def log_mission_result(self, result, mission_name: str = None):
        """
        Log complete mission result to multiple output files.
        
        Creates:
        - {mission_name}_timeseries.json: Full time series data
        - {mission_name}_summary.json: Mission summary metrics
        - {mission_name}_encoded_states.json: Phase 4 encoded states
        - {mission_name}_trajectory.json: Trajectory classification
        - {mission_name}_dyadic_cohesion.json: Dyadic fractiousness (if crew profile used)
        
        Args:
            result: MissionResult object
            mission_name: Optional override for mission name
        """
        mission_name = mission_name or result.config.mission_name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Write full time series
        timeseries_path = self.output_dir / f"{mission_name}_timeseries.json"
        self._write_timeseries(result, timeseries_path)
        
        # Write summary
        summary_path = self.output_dir / f"{mission_name}_summary.json"
        self._write_summary(result, summary_path)
        
        # Write encoded states
        encoded_path = self.output_dir / f"{mission_name}_encoded_states.json"
        self._write_encoded_states(result, encoded_path)
        
        # Write trajectory result
        trajectory_path = self.output_dir / f"{mission_name}_trajectory.json"
        self._write_trajectory(result, trajectory_path)
        
        # Write dyadic fractiousness if available
        dyadic_path = None
        if result.dyadic_fractiousness is not None:
            dyadic_path = self.output_dir / f"{mission_name}_dyadic_cohesion.json"
            self._write_dyadic_fractiousness(result, dyadic_path)
        
        # Write collapse fingerprint if available
        fingerprint_path = None
        fingerprint_schema_path = None
        if result.collapse_fingerprint is not None:
            # Write raw fingerprint (legacy format)
            fingerprint_path = self.output_dir / f"{mission_name}_collapse_fingerprint.json"
            self._write_collapse_fingerprint(result, fingerprint_path)
            
            # Write fingerprint schema (Phase A format)
            fingerprint_schema_path = self.output_dir / f"fingerprint_schema_{mission_name}.json"
            self._write_fingerprint_schema(result, fingerprint_schema_path, timestamp)
        
        if self.verbose:
            print(f"[Logger] Outputs written to {self.output_dir}/")
            print(f"         - {timeseries_path.name}")
            print(f"         - {summary_path.name}")
            print(f"         - {encoded_path.name}")
            print(f"         - {trajectory_path.name}")
            if dyadic_path is not None:
                print(f"         - {dyadic_path.name}")
            if fingerprint_path is not None:
                print(f"         - {fingerprint_path.name}")
            if fingerprint_schema_path is not None:
                print(f"         - {fingerprint_schema_path.name}")
    
    def _write_timeseries(self, result, filepath: Path):
        """Write full time series data."""
        data = result.core_output.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _write_summary(self, result, filepath: Path):
        """Write mission summary."""
        summary = result.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def _write_encoded_states(self, result, filepath: Path):
        """Write Phase 4 encoded states."""
        data = {
            "mission_name": result.config.mission_name,
            "num_states": len(result.encoded_states),
            "states": result.encoded_states,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _write_trajectory(self, result, filepath: Path):
        """Write trajectory classification result."""
        with open(filepath, 'w') as f:
            json.dump(result.trajectory_result, f, indent=2)
    
    def _write_dyadic_fractiousness(self, result, filepath: Path):
        """Write dyadic fractiousness analysis results."""
        dyadic = result.dyadic_fractiousness
        
        # Convert pair results to dictionaries
        pair_results = []
        for pr in dyadic.pair_results:
            pair_results.append({
                "member_i": pr.member_i,
                "member_j": pr.member_j,
                "compatibility_score": pr.compatibility_score,
                "min_cohesion": pr.min_cohesion,
                "min_cohesion_day": pr.min_cohesion_day,
                "min_cohesion_progress": pr.min_cohesion_progress,
                "final_cohesion": pr.final_cohesion,
            })
        
        data = {
            "mission_name": result.config.mission_name,
            "fractiousness_index": dyadic.fractiousness_index,
            "pair_results": pair_results,
            "metadata": dyadic.metadata,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _write_collapse_fingerprint(self, result, filepath: Path):
        """Write collapse fingerprint (TQP Signature) results."""
        fingerprint = result.collapse_fingerprint
        
        data = {
            "mission_name": result.config.mission_name,
            "collapse_timing": fingerprint.collapse_timing,
            "collapse_depth": fingerprint.collapse_depth,
            "collapse_day": fingerprint.collapse_day,
            "fractiousness_index": fingerprint.fractiousness_index,
            "weakest_pairs": fingerprint.weakest_pairs,
            "risk_score": fingerprint.risk_score,
            "risk_category": fingerprint.risk_category,
            "metadata": fingerprint.metadata,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _write_fingerprint_schema(self, result, filepath: Path, timestamp: str):
        """Write fingerprint schema (Phase A format) for cross-run analysis."""
        fingerprint = result.collapse_fingerprint
        
        # Extract crew_id if available
        crew_id = None
        if hasattr(result.config, 'crew_profile') and result.config.crew_profile is not None:
            crew_id = result.config.crew_profile.get('crew_id', None)
        
        # Build run metadata from core_config if available
        run_metadata = {
            "mission_length_days": result.config.mission_length_days,
            "trajectory_archetype": result.trajectory_result["archetype_id"],
            "trajectory_label": result.trajectory_result["label"],
        }
        
        # Add core config parameters if available
        if result.core_config is not None:
            run_metadata["config_params"] = {
                "q_peak": result.core_config.q_peak,
                "q_center": result.core_config.q_center,
                "q_width": result.core_config.q_width,
                "c_strain": result.core_config.c_strain,
                "c_q": result.core_config.c_q,
                "m_base": result.core_config.m_base,
                "s_workload": result.core_config.s_workload,
                "s_recovery": result.core_config.s_recovery,
            }
        
        # Create FingerprintSchema
        schema = FingerprintSchema(
            fingerprint=fingerprint,
            mission_name=result.config.mission_name,
            crew_id=crew_id,
            timestamp=timestamp,
            run_metadata=run_metadata,
        )
        
        # Save using FingerprintSchema's serialization
        schema.save(filepath)
    
    def write_console_summary(self, result):
        """
        Print a brief summary to console.
        
        Args:
            result: MissionResult object
        """
        summary = result.get_summary()
        
        print("\n" + "="*60)
        print(f"MISSION SUMMARY: {summary['mission_name']}")
        print("="*60)
        print(f"Duration: {summary['mission_length_days']} days")
        print(f"Trajectory: {summary['trajectory_label']}")
        print()
        print("KEY METRICS:")
        print(f"  Cohesion minimum: {summary['metrics']['cohesion']['minimum']:.3f} "
              f"(day {summary['metrics']['cohesion']['minimum_day']}, "
              f"{summary['metrics']['cohesion']['minimum_progress']:.1%} progress)")
        print(f"  Strain maximum:   {summary['metrics']['strain']['maximum']:.3f} "
              f"(day {summary['metrics']['strain']['maximum_day']})")
        print(f"  TQ pressure peak: {summary['metrics']['tq_pressure']['peak']:.3f} "
              f"(day {summary['metrics']['tq_pressure']['peak_day']}, "
              f"{summary['metrics']['tq_pressure']['peak_progress']:.1%} progress)")
        print()
        print(f"  Initial cohesion: {summary['metrics']['cohesion']['initial']:.3f}")
        print(f"  Final cohesion:   {summary['metrics']['cohesion']['final']:.3f}")
        
        # Add dyadic fractiousness summary if available
        if 'dyadic_fractiousness' in summary:
            dyadic = summary['dyadic_fractiousness']
            print()
            print("DYADIC FRACTIOUSNESS:")
            print(f"  Fractiousness index: {dyadic['fractiousness_index']:.4f}")
            print(f"  Pairs analyzed:      {dyadic['num_pairs']}")
            print(f"  Min of min cohesion: {dyadic['min_of_min_cohesion']:.3f}")
            print(f"  Max of min cohesion: {dyadic['max_of_min_cohesion']:.3f}")
        
        # Add collapse fingerprint summary if available
        if 'collapse_fingerprint' in summary:
            fingerprint = summary['collapse_fingerprint']
            print()
            print("COLLAPSE FINGERPRINT (TQP SIGNATURE):")
            print(f"  Risk category:       {fingerprint['risk_category'].upper()}")
            print(f"  Risk score:          {fingerprint['risk_score']:.4f}")
            print(f"  Collapse timing:     {fingerprint['collapse_timing']:.1%} (day {fingerprint['collapse_day']})")
            print(f"  Collapse depth:      {fingerprint['collapse_depth']:.3f}")
            if fingerprint['fractiousness_index'] is not None:
                print(f"  Fractiousness index: {fingerprint['fractiousness_index']:.4f}")
        
        print("="*60 + "\n")


def write_mission_outputs(result, output_dir: str = "output", verbose: bool = True):
    """
    Convenience function to log mission results.
    
    Args:
        result: MissionResult object
        output_dir: Output directory
        verbose: Whether to print progress
    """
    logger = SimulationLogger(output_dir, verbose)
    logger.log_mission_result(result)
    
    if verbose:
        logger.write_console_summary(result)
