"""
Data Collection and Storage (D.2)

Collects and stores required outputs per run:
- Collapse fingerprint
- Action frequency distributions
- Action sequences in pre-collapse window
- Narrative summaries (paired with mechanisms)

All outputs timestamped and reproducible.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class RunData:
    """
    Complete data package for a single experimental run.
    
    This is the canonical record of everything needed for analysis,
    combining fingerprint, actions, and narratives.
    
    Attributes:
        run_id: Unique identifier for this run
        experiment_family: Which experiment family (duration, composition, timing)
        timestamp: ISO timestamp of run execution
        mission_duration: Actual mission length in days
        
        # Core outputs
        fingerprint: Collapse fingerprint data
        action_frequencies: Count of each action type
        action_sequence: Full sequence of action types
        pre_collapse_actions: Actions in 20-day window before collapse
        
        # Optional narrative outputs
        narrative_count: Number of narratives generated (if enabled)
        critical_narratives: Key narrative moments with mechanistic refs
        
        # Metadata
        config_metadata: Configuration details for reproducibility
        runtime_seconds: Execution time
    """
    run_id: str
    experiment_family: str
    timestamp: str
    mission_duration: int
    
    # Fingerprint
    fingerprint: Dict[str, Any]
    
    # Actions
    action_frequencies: Dict[str, int]
    action_sequence: List[str]
    pre_collapse_actions: List[Dict[str, Any]]
    
    # Narratives (optional)
    narrative_count: int = 0
    critical_narratives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    config_metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunData':
        """Deserialize from dictionary."""
        return cls(**data)
    
    def get_collapse_day(self) -> int:
        """Extract collapse day from fingerprint."""
        return self.fingerprint.get("collapse_day", -1)
    
    def get_collapse_depth(self) -> float:
        """Extract collapse depth from fingerprint."""
        return self.fingerprint.get("collapse_depth", 0.0)
    
    def get_collapse_timing(self) -> str:
        """Extract collapse timing category from fingerprint."""
        return self.fingerprint.get("collapse_timing", "unknown")
    
    def get_risk_category(self) -> str:
        """Extract risk category from fingerprint."""
        return self.fingerprint.get("risk_category", "unknown")
    
    def get_dominant_action(self) -> Optional[str]:
        """Get the most frequent action type."""
        if not self.action_frequencies:
            return None
        return max(self.action_frequencies.items(), key=lambda x: x[1])[0]
    
    def get_action_diversity(self) -> float:
        """
        Calculate action diversity (normalized entropy).
        
        Returns:
            Value in [0, 1] where 0 = all same action, 1 = uniform distribution
        """
        if not self.action_frequencies:
            return 0.0
        
        total = sum(self.action_frequencies.values())
        if total == 0:
            return 0.0
        
        # Calculate entropy
        import math
        entropy = 0.0
        for count in self.action_frequencies.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize by max entropy (log2 of num action types)
        num_types = len(self.action_frequencies)
        max_entropy = math.log2(num_types) if num_types > 1 else 1.0
        
        return entropy / max_entropy if max_entropy > 0 else 0.0


class DataCollector:
    """
    Collector for experiment run data.
    
    Handles storage, retrieval, and organization of experimental results
    for downstream analysis.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize data collector.
        
        Args:
            storage_dir: Directory to store run data (default: phase_d/outputs/run_data)
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent / "outputs" / "run_data"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.runs: Dict[str, RunData] = {}
    
    def collect_from_result(self, result) -> RunData:
        """
        Create RunData from an ExperimentResult.
        
        Args:
            result: ExperimentResult from experiment harness
            
        Returns:
            RunData object with all collected information
        """
        # Extract fingerprint data
        fp = result.fingerprint
        fingerprint_data = {
            "collapse_timing": fp.collapse_timing,
            "collapse_depth": fp.collapse_depth,
            "collapse_day": fp.collapse_day,
            "fractiousness_index": fp.fractiousness_index,
            "weakest_pairs": fp.weakest_pairs,
            "risk_score": fp.risk_score,
            "risk_category": fp.risk_category,
        }
        
        # Extract action data
        action_log = result.action_log.log if result.action_log else None
        if action_log:
            action_frequencies = action_log.get_action_counts()
            action_sequence = action_log.get_action_sequence()
            pre_collapse = [
                {
                    "day": a.day,
                    "action_type": str(a.action_type),
                    "metadata": a.metadata or {},
                }
                for a in action_log.get_pre_collapse_actions(
                    fp.collapse_day, window_days=20
                )
            ]
        else:
            action_frequencies = {}
            action_sequence = []
            pre_collapse = []
        
        # Extract narrative data (if present)
        narrative_count = 0
        critical_narratives = []
        if result.narrative_log:
            narrative_count = len(result.narrative_log.log.narratives)
            critical_moments = result.narrative_log.log.get_critical_moments()
            critical_narratives = [
                {
                    "day": n.day,
                    "action": n.action,
                    "narrative_summary": n.narrative_summary,
                    "mechanistic_reference": n.mechanistic_reference,
                }
                for n in critical_moments
            ]
        
        # Create RunData
        run_data = RunData(
            run_id=result.config.experiment_id,
            experiment_family=result.config.family.value,
            timestamp=result.timestamp,
            mission_duration=result.config.get_mission_duration(),
            fingerprint=fingerprint_data,
            action_frequencies=action_frequencies,
            action_sequence=action_sequence,
            pre_collapse_actions=pre_collapse,
            narrative_count=narrative_count,
            critical_narratives=critical_narratives,
            config_metadata={
                "duration_multiplier": result.config.duration_multiplier,
                "intervention_day": result.config.intervention_day,
                **result.config.metadata,
            },
            runtime_seconds=result.runtime_seconds,
        )
        
        # Store in memory
        self.runs[run_data.run_id] = run_data
        
        return run_data
    
    def save_run(self, run_data: RunData):
        """
        Save run data to disk.
        
        Args:
            run_data: RunData to save
        """
        # Create family subdirectory
        family_dir = self.storage_dir / run_data.experiment_family
        family_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        output_file = family_dir / f"{run_data.run_id}.json"
        with open(output_file, 'w') as f:
            json.dump(run_data.to_dict(), f, indent=2)
    
    def load_run(self, run_id: str, family: Optional[str] = None) -> Optional[RunData]:
        """
        Load run data from disk.
        
        Args:
            run_id: Run identifier
            family: Optional experiment family (speeds up search)
            
        Returns:
            RunData if found, None otherwise
        """
        if family:
            family_dir = self.storage_dir / family
            run_file = family_dir / f"{run_id}.json"
            if run_file.exists():
                with open(run_file, 'r') as f:
                    data = json.load(f)
                return RunData.from_dict(data)
        else:
            # Search all families
            for family_dir in self.storage_dir.iterdir():
                if family_dir.is_dir():
                    run_file = family_dir / f"{run_id}.json"
                    if run_file.exists():
                        with open(run_file, 'r') as f:
                            data = json.load(f)
                        return RunData.from_dict(data)
        
        return None
    
    def load_all_runs(self, family: Optional[str] = None) -> List[RunData]:
        """
        Load all run data from disk.
        
        Args:
            family: Optional filter by experiment family
            
        Returns:
            List of RunData objects
        """
        runs = []
        
        if family:
            family_dir = self.storage_dir / family
            if family_dir.exists():
                for run_file in family_dir.glob("*.json"):
                    with open(run_file, 'r') as f:
                        data = json.load(f)
                    runs.append(RunData.from_dict(data))
        else:
            for family_dir in self.storage_dir.iterdir():
                if family_dir.is_dir():
                    for run_file in family_dir.glob("*.json"):
                        with open(run_file, 'r') as f:
                            data = json.load(f)
                        runs.append(RunData.from_dict(data))
        
        return runs
    
    def get_summary_table(self, runs: Optional[List[RunData]] = None) -> List[Dict[str, Any]]:
        """
        Generate summary table for runs.
        
        Args:
            runs: Optional list of runs (uses all loaded runs if None)
            
        Returns:
            List of summary dictionaries suitable for tabular display
        """
        if runs is None:
            runs = list(self.runs.values())
        
        summary = []
        for run in runs:
            summary.append({
                "run_id": run.run_id,
                "family": run.experiment_family,
                "duration": run.mission_duration,
                "collapse_day": run.get_collapse_day(),
                "collapse_depth": f"{run.get_collapse_depth():.3f}",
                "collapse_timing": run.get_collapse_timing(),
                "risk_category": run.get_risk_category(),
                "dominant_action": run.get_dominant_action(),
                "action_diversity": f"{run.get_action_diversity():.3f}",
                "runtime_s": f"{run.runtime_seconds:.2f}",
            })
        
        return summary
