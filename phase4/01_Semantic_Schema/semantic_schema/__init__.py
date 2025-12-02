"""
Semantic Schema Layer for Phase 4 of the Three Question Protocol (3QP).

This package provides typed data structures and interfaces for representing
Phase 3 concepts:
- Baseline states (multi-domain starting configurations)
- Scenario definitions and events
- Pattern definitions and instances
- Thread definitions and instances
- Trajectory archetypes and instances

This layer is purely representational—it defines schemas without implementing
simulation or business logic.
"""

from semantic_schema.baseline import (
    BaselineProfile,
    DomainState,
    SemanticTag,
    ModuleReference,
)
from semantic_schema.scenarios import (
    ScenarioTemplate,
    EventDescriptor,
    EventStoryline,
)
from semantic_schema.patterns import (
    PatternDefinition,
    PatternInstance,
    PatternClass,
)
from semantic_schema.threads import (
    ThreadDefinition,
    ThreadInstance,
)
from semantic_schema.trajectories import (
    TrajectoryArchetype,
    TrajectoryInstance,
)

__all__ = [
    # Baseline
    "BaselineProfile",
    "DomainState",
    "SemanticTag",
    "ModuleReference",
    # Scenarios
    "ScenarioTemplate",
    "EventDescriptor",
    "EventStoryline",
    # Patterns
    "PatternDefinition",
    "PatternInstance",
    "PatternClass",
    # Threads
    "ThreadDefinition",
    "ThreadInstance",
    # Trajectories
    "TrajectoryArchetype",
    "TrajectoryInstance",
]

__version__ = "0.1.0"
