"""
Narrative Logger - Phase C

Logging and tracking system for narrative outputs.

Tracks all narrative expressions separately from action logs,
maintaining clean separation between causal (action) and
non-causal (narrative) outputs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from .narrative_renderer import NarrativeOutput


@dataclass
class NarrativeLog:
    """
    Complete log of narrative expressions over a mission.
    
    Attributes:
        mission_name: Identifier for this mission
        narratives: List of all narrative outputs, in chronological order
        metadata: Additional context
    """
    mission_name: str
    narratives: List[NarrativeOutput] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_narrative(self, narrative: NarrativeOutput):
        """
        Add a narrative output to the log.
        
        Args:
            narrative: The narrative output to record
        """
        self.narratives.append(narrative)
    
    def get_narratives_by_day(self) -> Dict[int, List[NarrativeOutput]]:
        """
        Group narratives by day.
        
        Returns:
            Dictionary mapping day to list of narratives
        """
        by_day = {}
        for narrative in self.narratives:
            day = narrative.day
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(narrative)
        return by_day
    
    def get_narratives_by_action(self) -> Dict[str, List[NarrativeOutput]]:
        """
        Group narratives by action type.
        
        Returns:
            Dictionary mapping action type to narratives
        """
        by_action = {}
        for narrative in self.narratives:
            action = narrative.action
            if action not in by_action:
                by_action[action] = []
            by_action[action].append(narrative)
        return by_action
    
    def get_critical_moments(self) -> List[NarrativeOutput]:
        """
        Extract narratives for critical moments.
        
        Returns narratives where mechanistic reference includes
        critical conditions.
        
        Returns:
            List of critical moment narratives
        """
        critical = []
        critical_keywords = [
            "strain_critical",
            "cohesion_critical",
            "critical_intervention_needed",
        ]
        
        for narrative in self.narratives:
            if any(kw in narrative.mechanistic_reference for kw in critical_keywords):
                critical.append(narrative)
        
        return critical
    
    def get_dialogue_exchanges(self) -> List[NarrativeOutput]:
        """
        Get all narratives that include dialogue.
        
        Returns:
            List of narratives with dialogue
        """
        return [n for n in self.narratives if n.dialogue is not None]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert log to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "mission_name": self.mission_name,
            "narratives": [n.to_dict() for n in self.narratives],
            "metadata": self.metadata,
            "statistics": self.get_statistics(),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Compute summary statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self.narratives:
            return {
                "total_narratives": 0,
                "dialogue_count": 0,
                "critical_moments": 0,
            }
        
        return {
            "total_narratives": len(self.narratives),
            "dialogue_count": len(self.get_dialogue_exchanges()),
            "critical_moments": len(self.get_critical_moments()),
            "narratives_by_action": {
                action: len(narratives)
                for action, narratives in self.get_narratives_by_action().items()
            },
        }
    
    def save_json(self, output_path: Path):
        """
        Save log to JSON file.
        
        Args:
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_json(cls, input_path: Path) -> 'NarrativeLog':
        """
        Load log from JSON file.
        
        Args:
            input_path: Path to input file
            
        Returns:
            NarrativeLog instance
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        log = cls(
            mission_name=data["mission_name"],
            metadata=data.get("metadata", {})
        )
        
        for n_dict in data["narratives"]:
            narrative = NarrativeOutput(
                agent_id=n_dict["agent_id"],
                day=n_dict["day"],
                action=n_dict["action"],
                expressed_intent=n_dict["expressed_intent"],
                dialogue=n_dict.get("dialogue"),
                narrative_summary=n_dict["narrative_summary"],
                mechanistic_reference=n_dict["mechanistic_reference"],
            )
            log.add_narrative(narrative)
        
        return log


class NarrativeLogger:
    """
    Logger for narrative outputs during mission execution.
    
    Provides real-time logging interface that integrates with
    the agentic core model.
    """
    
    def __init__(self, mission_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize narrative logger.
        
        Args:
            mission_name: Name of the mission
            metadata: Additional metadata
        """
        self.log = NarrativeLog(
            mission_name=mission_name,
            metadata=metadata or {}
        )
    
    def log_narrative(self, narrative: NarrativeOutput):
        """
        Log a narrative output.
        
        Args:
            narrative: Narrative output to log
        """
        self.log.add_narrative(narrative)
    
    def get_log(self) -> NarrativeLog:
        """
        Get the complete log.
        
        Returns:
            NarrativeLog instance
        """
        return self.log
    
    def save(self, output_path: Path):
        """
        Save log to file.
        
        Args:
            output_path: Path to output file
        """
        self.log.save_json(output_path)
    
    def get_recent_narratives(self, n: int = 10) -> List[NarrativeOutput]:
        """
        Get the n most recent narratives.
        
        Args:
            n: Number of narratives to retrieve
            
        Returns:
            List of recent narratives
        """
        return self.log.narratives[-n:] if self.log.narratives else []
    
    def print_summary(self):
        """Print a summary of the logged narratives."""
        stats = self.log.get_statistics()
        print(f"\n=== Narrative Log Summary: {self.log.mission_name} ===")
        print(f"Total narratives: {stats['total_narratives']}")
        print(f"Dialogue exchanges: {stats['dialogue_count']}")
        print(f"Critical moments: {stats['critical_moments']}")
        print(f"\nNarratives by action:")
        for action, count in stats['narratives_by_action'].items():
            print(f"  {action}: {count}")
