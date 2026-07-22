"""
Resource Layer — Objective consumable tracking for 3QP twin engine.

Tracks mission-critical physical resources independently of agent internal state.
Resources never directly affect agent psychology — they flow only through the
Perception Model into Belief Update, then into Internal State Drift.
"""

from .resource_model import (
    ResourceState,
    ResourceConfig,
    ResourceResupply,
    ResourceEngine,
)

__all__ = [
    "ResourceState",
    "ResourceConfig",
    "ResourceResupply",
    "ResourceEngine",
]
