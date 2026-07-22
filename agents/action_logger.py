"""
Action Logger - Phase B

Logging and tracking system for agent actions.

Records every action selection with full context for later analysis
and correlation with collapse fingerprints.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from pathlib import Path
import json

from .actions import AgentAction, ActionType


@dataclass
class ActionLog:
    """
    Complete log of agent actions over a mission.
    
    Attributes:
        mission_name: Identifier for this mission
        actions: List of all actions taken, in chronological order
        metadata: Additional context about the mission
    """
    mission_name: str
    actions: List[AgentAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_action(self, action: AgentAction):
        """
        Add an action to the log.
        
        Args:
            action: The action to record
        """
        self.actions.append(action)
    
    def get_action_counts(self) -> Dict[str, int]:
        """
        Get frequency count of each action type.
        
        Returns:
            Dictionary mapping action type to count
        """
        counts = Counter(str(action.action_type) for action in self.actions)
        return dict(counts)
    
    def get_actions_by_day(self) -> Dict[int, List[AgentAction]]:
        """
        Group actions by day.
        
        Returns:
            Dictionary mapping day to list of actions
        """
        by_day = defaultdict(list)
        for action in self.actions:
            by_day[action.day].append(action)
        return dict(by_day)
    
    def get_action_sequence(self, window_size: int = 10) -> List[str]:
        """
        Get sequence of action types.
        
        Args:
            window_size: If provided, return only the last N actions
            
        Returns:
            List of action type strings
        """
        sequence = [str(action.action_type) for action in self.actions]
        if window_size and len(sequence) > window_size:
            return sequence[-window_size:]
        return sequence
    
    def get_pre_collapse_actions(
        self,
        collapse_day: int,
        window_days: int = 20
    ) -> List[AgentAction]:
        """
        Get actions in the window before collapse.
        
        Args:
            collapse_day: Day when collapse occurred
            window_days: Number of days before collapse to include
            
        Returns:
            List of actions in the pre-collapse window
        """
        start_day = max(0, collapse_day - window_days)
        return [
            action for action in self.actions
            if start_day <= action.day <= collapse_day
        ]
    
    def get_dominant_pre_collapse_action(
        self,
        collapse_day: int,
        window_days: int = 20
    ) -> Optional[str]:
        """
        Get the most frequent action type before collapse.
        
        Args:
            collapse_day: Day when collapse occurred
            window_days: Number of days before collapse to examine
            
        Returns:
            Most frequent action type string, or None if no actions
        """
        pre_actions = self.get_pre_collapse_actions(collapse_day, window_days)
        if not pre_actions:
            return None
        
        counts = Counter(str(action.action_type) for action in pre_actions)
        return counts.most_common(1)[0][0]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert log to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "mission_name": self.mission_name,
            "metadata": self.metadata,
            "actions": [action.to_dict() for action in self.actions],
            "summary": {
                "total_actions": len(self.actions),
                "action_counts": self.get_action_counts(),
            }
        }
    
    def to_json(self) -> str:
        """
        Convert log to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: Path):
        """
        Save log to JSON file.
        
        Args:
            filepath: Path to output file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(self.to_json())


class ActionLogger:
    """
    Logger for tracking agent actions during a mission.
    
    Creates and maintains an ActionLog throughout the simulation.
    """
    
    def __init__(self, mission_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize action logger.
        
        Args:
            mission_name: Identifier for the mission
            metadata: Optional metadata to attach to log
        """
        self.log = ActionLog(
            mission_name=mission_name,
            metadata=metadata or {}
        )
    
    def log_action(self, action: AgentAction):
        """
        Log an agent action.
        
        Args:
            action: The action to log
        """
        self.log.add_action(action)
    
    def get_log(self) -> ActionLog:
        """
        Get the complete action log.
        
        Returns:
            ActionLog instance
        """
        return self.log
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for logged actions.
        
        Returns:
            Dictionary of statistics
        """
        action_counts = self.log.get_action_counts()
        total = len(self.log.actions)
        
        stats = {
            "total_actions": total,
            "action_counts": action_counts,
            "action_frequencies": {
                action: count / total if total > 0 else 0
                for action, count in action_counts.items()
            },
        }
        
        # Identify dominant action overall
        if action_counts:
            dominant = max(action_counts.items(), key=lambda x: x[1])
            stats["dominant_action"] = dominant[0]
            stats["dominant_action_frequency"] = dominant[1] / total if total > 0 else 0
        
        return stats
    
    def get_fingerprint_metadata(self, collapse_day: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate metadata suitable for attachment to FingerprintSchema.
        
        Args:
            collapse_day: Optional day of collapse for pre-collapse analysis
            
        Returns:
            Dictionary of action-related metadata for fingerprint
        """
        stats = self.get_statistics()
        
        metadata = {
            "action_summary": {
                "total_actions": stats["total_actions"],
                "action_counts": stats["action_counts"],
                "action_frequencies": stats["action_frequencies"],
            }
        }
        
        if "dominant_action" in stats:
            metadata["action_summary"]["dominant_action"] = stats["dominant_action"]
            metadata["action_summary"]["dominant_frequency"] = stats["dominant_action_frequency"]
        
        # Add pre-collapse analysis if collapse day provided
        if collapse_day is not None:
            pre_collapse_actions = self.log.get_pre_collapse_actions(collapse_day, window_days=20)
            pre_collapse_sequence = [str(a.action_type) for a in pre_collapse_actions]
            pre_collapse_counts = Counter(pre_collapse_sequence)
            
            metadata["pre_collapse_actions"] = {
                "window_days": 20,
                "action_sequence": pre_collapse_sequence[-10:],  # Last 10 actions
                "action_counts": dict(pre_collapse_counts),
                "dominant_action": self.log.get_dominant_pre_collapse_action(collapse_day),
            }
        
        return metadata
