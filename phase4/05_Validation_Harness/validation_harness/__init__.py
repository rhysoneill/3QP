"""
Phase 4 / Workstream 5 – Validation Harness

End-to-end validation harness that exercises the Phase 4 stack (WS1–WS4)
against expected qualitative behaviors and Phase 3 definitions.

This workstream provides orchestration and checking capabilities without
introducing new behavioral logic.
"""

from .config import (
    ExpectedPattern,
    ExpectedTrajectory,
    ValidationScenarioConfig,
    ValidationRunConfig,
)
from .checks import CheckResult, ValidationRunResult
from .pipeline import run_validation
from .reporting import render_text_report, render_dict_report

__all__ = [
    "ExpectedPattern",
    "ExpectedTrajectory",
    "ValidationScenarioConfig",
    "ValidationRunConfig",
    "CheckResult",
    "ValidationRunResult",
    "run_validation",
    "render_text_report",
    "render_dict_report",
]
