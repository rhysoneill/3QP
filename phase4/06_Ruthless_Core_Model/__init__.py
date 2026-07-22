"""
Ruthless Core Model (Phase 4 / Workstream 6)

This module provides a minimal dynamical core for generating third quarter
trajectories in long-duration isolated confined environments. Unlike WS1-5,
this is a COMPUTATIONAL module that implements simple differential equations
for state variables over time.

The Ruthless Core Model is designed to:
- Generate synthetic trajectories for calibration and validation
- Provide a transparent, interpretable baseline for third quarter dynamics
- Serve as a lightweight engine underneath more complex agentic architectures

Public API:
-----------
Configuration:
    - RuthlessCoreConfig: Configuration dataclass for model parameters
    
Model:
    - RuthlessCoreModel: Main simulation engine
    
Output:
    - RuthlessCoreOutput: Time series output container
    
Adapters:
    - to_phase4_encoded_states: Convert output to Phase 4 encoded states
    - to_phase4_trajectory_result: Convert output to trajectory classification result

Version: 0.1.0
"""

__version__ = "0.1.0"

from .ruthless_core import (
    RuthlessCoreConfig,
    RuthlessCoreModel,
    RuthlessCoreOutput,
    to_phase4_encoded_states,
    to_phase4_trajectory_result,
)

__all__ = [
    "__version__",
    "RuthlessCoreConfig",
    "RuthlessCoreModel",
    "RuthlessCoreOutput",
    "to_phase4_encoded_states",
    "to_phase4_trajectory_result",
]
