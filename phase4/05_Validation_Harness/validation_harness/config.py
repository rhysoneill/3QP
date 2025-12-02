"""
Validation configuration dataclasses.

Defines configuration structures for validation runs using only
qualitative and categorical fields.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ExpectedPattern:
    """
    Expected pattern definition for validation scenarios.
    
    Attributes:
        pattern_type: Type of pattern expected (e.g., "third_quarter_signature")
        required: If True, absence of this pattern causes validation failure
        description: Human-readable description of the pattern expectation
    """
    pattern_type: str
    required: bool
    description: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "pattern_type": self.pattern_type,
            "required": self.required,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExpectedPattern":
        """Create instance from dictionary."""
        return cls(
            pattern_type=data["pattern_type"],
            required=data["required"],
            description=data["description"],
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the expected pattern configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.pattern_type or not self.pattern_type.strip():
            return False, "pattern_type cannot be empty"
        if not self.description or not self.description.strip():
            return False, "description cannot be empty"
        return True, ""


@dataclass
class ExpectedTrajectory:
    """
    Expected trajectory archetype for validation scenarios.
    
    Attributes:
        archetype_id: ID of the expected trajectory archetype
        required: If True, absence of this archetype causes validation failure
        description: Human-readable description of the trajectory expectation
    """
    archetype_id: str
    required: bool
    description: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "archetype_id": self.archetype_id,
            "required": self.required,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExpectedTrajectory":
        """Create instance from dictionary."""
        return cls(
            archetype_id=data["archetype_id"],
            required=data["required"],
            description=data["description"],
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the expected trajectory configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.archetype_id or not self.archetype_id.strip():
            return False, "archetype_id cannot be empty"
        if not self.description or not self.description.strip():
            return False, "description cannot be empty"
        return True, ""


@dataclass
class ValidationScenarioConfig:
    """
    Configuration for a validation scenario.
    
    A scenario defines what patterns and trajectories are expected
    for a particular test case.
    
    Attributes:
        scenario_id: Unique identifier for this scenario
        label: Short human-readable label
        description: Detailed description of the scenario
        expected_patterns: List of expected pattern definitions
        expected_trajectories: List of expected trajectory definitions
        metadata: Additional categorical metadata
    """
    scenario_id: str
    label: str
    description: str
    expected_patterns: list[ExpectedPattern]
    expected_trajectories: list[ExpectedTrajectory]
    metadata: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "scenario_id": self.scenario_id,
            "label": self.label,
            "description": self.description,
            "expected_patterns": [p.to_dict() for p in self.expected_patterns],
            "expected_trajectories": [t.to_dict() for t in self.expected_trajectories],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ValidationScenarioConfig":
        """Create instance from dictionary."""
        return cls(
            scenario_id=data["scenario_id"],
            label=data["label"],
            description=data["description"],
            expected_patterns=[
                ExpectedPattern.from_dict(p) for p in data["expected_patterns"]
            ],
            expected_trajectories=[
                ExpectedTrajectory.from_dict(t) for t in data["expected_trajectories"]
            ],
            metadata=data.get("metadata", {}),
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the scenario configuration.
        
        Checks:
        - Non-empty IDs and labels
        - No duplicate pattern types
        - No duplicate archetype IDs
        - All sub-components are valid
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.scenario_id or not self.scenario_id.strip():
            return False, "scenario_id cannot be empty"
        
        if not self.label or not self.label.strip():
            return False, "label cannot be empty"
        
        if not self.description or not self.description.strip():
            return False, "description cannot be empty"
        
        # Validate all expected patterns
        pattern_types = set()
        for pattern in self.expected_patterns:
            is_valid, error = pattern.validate()
            if not is_valid:
                return False, f"Invalid expected pattern: {error}"
            
            if pattern.pattern_type in pattern_types:
                return False, f"Duplicate pattern_type: {pattern.pattern_type}"
            pattern_types.add(pattern.pattern_type)
        
        # Validate all expected trajectories
        archetype_ids = set()
        for trajectory in self.expected_trajectories:
            is_valid, error = trajectory.validate()
            if not is_valid:
                return False, f"Invalid expected trajectory: {error}"
            
            if trajectory.archetype_id in archetype_ids:
                return False, f"Duplicate archetype_id: {trajectory.archetype_id}"
            archetype_ids.add(trajectory.archetype_id)
        
        return True, ""


@dataclass
class ValidationRunConfig:
    """
    Configuration for a single validation run.
    
    Attributes:
        run_id: Unique identifier for this run
        scenario: The scenario configuration to validate against
        notes: Optional notes about this validation run
        metadata: Additional categorical metadata
    """
    run_id: str
    scenario: ValidationScenarioConfig
    notes: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "run_id": self.run_id,
            "scenario": self.scenario.to_dict(),
            "notes": self.notes,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ValidationRunConfig":
        """Create instance from dictionary."""
        return cls(
            run_id=data["run_id"],
            scenario=ValidationScenarioConfig.from_dict(data["scenario"]),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {}),
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the run configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.run_id or not self.run_id.strip():
            return False, "run_id cannot be empty"
        
        is_valid, error = self.scenario.validate()
        if not is_valid:
            return False, f"Invalid scenario: {error}"
        
        return True, ""
