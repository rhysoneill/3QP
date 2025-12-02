"""
Social Network & Clique Formation Module

This module provides graph-based representation of interpersonal relationships
in small crews, including tie strength dynamics, clique detection, and
structural metrics.
"""

from .types import (
    InteractionSignal,
    NodeDefinition,
    EdgeDefinition,
    NodeState,
    EdgeState,
    GraphSnapshot,
    CliqueDescriptor,
    CliqueSnapshot,
    CentralityScores,
    StructuralMetrics,
    NetworkConfiguration,
)

from .graph_store import GraphStore
from .drift_engine import DriftEngine
from .clique_detector import CliqueDetector
from .metric_calculator import MetricCalculator
from .social_network_module import SocialNetworkModule

__all__ = [
    'InteractionSignal',
    'NodeDefinition',
    'EdgeDefinition',
    'NodeState',
    'EdgeState',
    'GraphSnapshot',
    'CliqueDescriptor',
    'CliqueSnapshot',
    'CentralityScores',
    'StructuralMetrics',
    'NetworkConfiguration',
    'GraphStore',
    'DriftEngine',
    'CliqueDetector',
    'MetricCalculator',
    'SocialNetworkModule',
]

__version__ = '1.0.0'
